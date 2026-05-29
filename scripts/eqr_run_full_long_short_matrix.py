#!/usr/bin/env python3
"""Run a sequential full-panel long/short QSpread matrix.

This harness is intentionally single-owner / single-heavy-run-at-a-time.  It is
designed for weak-memory environments where OMX team/swarm style concurrent
experiment execution would create avoidable OOM risk.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "server_full.yaml"
DEFAULT_PANEL = PROJECT_ROOT / "experiments" / "prepared" / "panel" / "monthly_labels.parquet"
DEFAULT_FEATURE_DIR = PROJECT_ROOT / "experiments" / "prepared" / "features_full_chunked"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "experiments" / "ddqm2_full_long_short"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "full_long_short_qspread_full_chunked_report.md"
DEFAULT_LEDGER = PROJECT_ROOT / "reports" / "full_long_short_qspread_full_chunked_ledger.json"
DATA_BOUNDARY = "local_artifacts_only_no_wrds_login_no_runtime_external_data"
RESEARCH_ONLY_DISCLAIMER = (
    "Research diagnostics only; not investment, trading, legal, tax, production, "
    "or deployment advice."
)
NO_CLOUD_POLICY = "no_cloud_or_oci_auto_provisioning"
REQUIRED_INTERPRETABILITY_EVIDENCE = (
    "model_factor_importance",
    "global_local_table",
    "leg_attribution",
    "worst_drawdown_explanation",
    "next_hypothesis",
    "limitations_or_defer_reason",
)
ARTIFACT_NO_OVERWRITE_POLICY = {
    "control_ledger": "fail_if_exists_unique_path_required",
    "control_report_md": "fail_if_exists_unique_path_required",
    "matrix_csv_sidecar": "fail_if_exists_unique_path_required",
    "sensitivity_csv": "fail_if_exists_unique_path_required",
    "per_run_manifest": "skip_existing_never_overwrite",
    "existing_run_dir_without_manifest": "do_not_write_mark_failed",
    "temporary_test_outputs": "unique_tmp_path_or_mktemp_required",
}

MODEL_SAFETY_OVERRIDES: dict[str, dict[str, Any]] = {
    "lightgbm": {"n_jobs": 1},
    "random_forest": {"n_jobs": 1},
    "extra_trees": {"n_jobs": 1},
}

MODEL_PARAM_PROFILES: dict[str, tuple[str, dict[str, Any]]] = {
    "lightgbm_conservative": ("lightgbm", {"n_estimators": 120, "learning_rate": 0.03, "num_leaves": 15, "min_child_samples": 80, "n_jobs": 1}),
    "ridge_high_alpha": ("ridge", {"alpha": 10.0}),
    "elasticnet_sparse": ("elasticnet", {"alpha": 0.01, "l1_ratio": 0.8, "max_iter": 3000}),
    "extra_trees_shallow": ("extra_trees", {"n_estimators": 80, "max_depth": 5, "min_samples_leaf": 40, "n_jobs": 1}),
}

PRIOR_125M_ANCHORS = [
    {"label": "prior_125m_q20", "q": 0.20, "cumulative_return": 5202.0665, "implied_cagr": 0.3075, "max_drawdown": -0.3602, "turnover": 0.7193},
    {"label": "prior_125m_q30", "q": 0.30, "cumulative_return": 4366.4377, "implied_cagr": 0.3003, "max_drawdown": -0.3571, "turnover": 0.7139},
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sequential 2.08M full-panel long/short QSpread matrix harness.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--feature-dir", type=Path, default=DEFAULT_FEATURE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--models", nargs="+", default=["baseline_mean", "ridge", "elasticnet", "lightgbm", "random_forest", "extra_trees"])
    parser.add_argument("--quantiles", nargs="+", type=float, default=[0.10, 0.20, 0.30])
    parser.add_argument("--factor-universes", nargs="+", default=["selected_13_global_local"])
    parser.add_argument("--factor-selection-policies", nargs="+", default=["selected_13_global_local"], choices=("selected_13_global_local", "local_only", "global_only", "quota", "category_capped"))
    parser.add_argument("--factor-counts", nargs="+", type=int, default=[13])
    parser.add_argument("--global-local-quotas", nargs="+", default=[])
    parser.add_argument("--category-caps", nargs="+", type=int, default=[])
    parser.add_argument("--macro-feature-designs", nargs="+", default=["ddqm2_25x3_us_macro"], choices=("current_macro_family", "ddqm2_25x3_us_macro", "expanded_us_macro"))
    parser.add_argument("--portfolio-surfaces", nargs="+", default=["stock_score_qspread_ddqm2"], choices=("weighted_factor_return_current", "stock_score_qspread_ddqm2", "stock_score_long_only_qspread"))
    parser.add_argument("--evaluation-modes", nargs="+", default=["walk_forward"], choices=("single_holdout", "walk_forward"))
    parser.add_argument("--min-weights", nargs="+", type=float, default=[0.0])
    parser.add_argument("--q-edge", action="store_true", help="Also include q=0.05 and q=0.40.")
    parser.add_argument("--hyperparam-probes", action="store_true", help="Run small profile probes at --probe-quantile after the core grid.")
    parser.add_argument("--probe-quantile", type=float, default=0.20)
    parser.add_argument("--model-param-profiles", nargs="+", default=["lightgbm_conservative", "ridge_high_alpha", "elasticnet_sparse", "extra_trees_shallow"])
    parser.add_argument("--run-prefix", default=None)
    parser.add_argument("--factor-score-chunk-dates", type=int, default=12)
    parser.add_argument("--walk-forward-test-periods", type=int, default=12)
    parser.add_argument("--walk-forward-validation-periods", type=int, default=12)
    parser.add_argument("--min-observations", type=int, default=None)
    parser.add_argument("--max-runs", type=int, default=0, help="Optional cap for this invocation; 0 means all generated specs.")
    parser.add_argument("--dry-run", action="store_true", help="Write planned ledger/report without launching heavy experiments.")
    parser.add_argument("--sequential-plan", type=Path, default=None, help="Optional additive sequential full-run plan artifact path.")
    parser.add_argument("--continue-on-error", action="store_true", default=False)
    parser.add_argument(
        "--drop-factor-scores-after-run",
        action="store_true",
        help=(
            "Pass storage-light cleanup to the child DDQM2 runner: after a run "
            "finishes, remove only that run's large factor-score intermediate "
            "parquet files and preserve reports, manifests, portfolio returns, "
            "qspread legs, and diagnostics."
        ),
    )
    parser.add_argument(
        "--execute-heavy-experiments",
        action="store_true",
        help=(
            "Explicitly permit launching the underlying DDQM2 runner. "
            "Omit for harness-only validation."
        ),
    )
    return parser.parse_args(argv)


def _unique_floats(values: Iterable[float]) -> list[float]:
    seen: set[str] = set()
    out: list[float] = []
    for value in values:
        key = f"{float(value):.4f}"
        if key not in seen:
            seen.add(key)
            out.append(float(value))
    return out


def _safe_label(value: Any) -> str:
    text = str(value).strip().replace(":", "x").replace(".", "p")
    return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in text).strip("_")


def _parse_quota(value: str) -> tuple[int, int]:
    if ":" not in value:
        raise ValueError(f"Invalid global/local quota '{value}'; expected G:L")
    left, right = value.split(":", 1)
    global_count, local_count = int(left), int(right)
    if global_count < 0 or local_count < 0 or global_count + local_count <= 0:
        raise ValueError(f"Invalid global/local quota '{value}'; counts must be non-negative and non-zero in total")
    return global_count, local_count


def _meminfo() -> dict[str, int]:
    info: dict[str, int] = {}
    path = Path("/proc/meminfo")
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if ":" not in line:
                continue
            key, rest = line.split(":", 1)
            parts = rest.strip().split()
            if parts and parts[0].isdigit():
                info[key] = int(parts[0]) * 1024
    return info


def _environment_snapshot() -> dict[str, Any]:
    mem = _meminfo()
    return {
        "cpu_count": os.cpu_count(),
        "mem_total_bytes": mem.get("MemTotal"),
        "mem_available_bytes": mem.get("MemAvailable"),
        "policy": "single_heavy_experiment_at_a_time_no_omx_team_no_swarm",
    }


def run_specs(args: argparse.Namespace) -> list[dict[str, Any]]:
    quantiles = _unique_floats([*args.quantiles, *([0.05, 0.40] if args.q_edge else [])])
    specs: list[dict[str, Any]] = []
    base_axes = []
    for factor_universe in args.factor_universes:
        for factor_count in args.factor_counts:
            if int(factor_count) <= 0:
                raise ValueError("factor-counts must be positive integers")
            for policy in args.factor_selection_policies:
                if policy == "quota":
                    quotas = args.global_local_quotas or [None]
                    for quota in quotas:
                        rejection = None
                        if quota is None:
                            rejection = "quota policy requires --global-local-quotas G:L"
                        else:
                            _parse_quota(str(quota))
                        base_axes.append(
                            {
                                "factor_universe": factor_universe,
                                "factor_selection_policy": policy,
                                "factor_universe_target_count": int(factor_count),
                                "global_local_quota": quota,
                                "category_cap": None,
                                "optional_axis_state": {
                                    "global_local_quota": "active" if quota is not None and rejection is None else "rejected",
                                    "category_cap": "ignored" if args.category_caps else "not_provided",
                                    "rejection_reason": rejection,
                                },
                                "invalid_axis_reason": rejection,
                            }
                        )
                    continue
                if policy == "category_capped":
                    caps = args.category_caps or [None]
                    for cap in caps:
                        rejection = None
                        if cap is None or int(cap) <= 0:
                            rejection = "category_capped policy requires positive --category-caps"
                        base_axes.append(
                            {
                                "factor_universe": factor_universe,
                                "factor_selection_policy": policy,
                                "factor_universe_target_count": int(factor_count),
                                "global_local_quota": None,
                                "category_cap": int(cap) if cap is not None else None,
                                "optional_axis_state": {
                                    "global_local_quota": "ignored" if args.global_local_quotas else "not_provided",
                                    "category_cap": "active" if cap is not None and rejection is None else "rejected",
                                    "rejection_reason": rejection,
                                },
                                "invalid_axis_reason": rejection,
                            }
                        )
                    continue
                base_axes.append(
                    {
                        "factor_universe": factor_universe,
                        "factor_selection_policy": policy,
                        "factor_universe_target_count": int(factor_count),
                        "global_local_quota": None,
                        "category_cap": None,
                        "optional_axis_state": {
                            "global_local_quota": "ignored" if args.global_local_quotas else "not_provided",
                            "category_cap": "ignored" if args.category_caps else "not_provided",
                            "rejection_reason": None,
                        },
                        "invalid_axis_reason": None,
                    }
                )
    for model in args.models:
        for quantile in quantiles:
            for axes in base_axes:
                for macro_design in args.macro_feature_designs:
                    for portfolio_surface in args.portfolio_surfaces:
                        for evaluation_mode in args.evaluation_modes:
                            for min_weight in args.min_weights:
                                specs.append(
                                    {
                                        "label": model,
                                        "model": model,
                                        "quantile": quantile,
                                        "model_params": dict(MODEL_SAFETY_OVERRIDES.get(model, {})),
                                        "experiment_family": "full_long_short_factor_router",
                                        "hypothesis": "Full-panel long/short QSpread branch under existing walk-forward OOS protocol with factor-router axes.",
                                        "macro_feature_design": macro_design,
                                        "portfolio_surface": portfolio_surface,
                                        "evaluation_mode": evaluation_mode,
                                        "min_weight": float(min_weight),
                                        **axes,
                                    }
                                )
    if args.hyperparam_probes:
        for profile in args.model_param_profiles:
            if profile not in MODEL_PARAM_PROFILES:
                raise ValueError(f"Unknown model profile: {profile}")
            model, params = MODEL_PARAM_PROFILES[profile]
            for axes in base_axes:
                specs.append(
                    {
                        "label": profile,
                        "model": model,
                        "quantile": float(args.probe_quantile),
                        "model_params": dict(params),
                        "experiment_family": "full_long_short_hypothesis_probe",
                        "hypothesis": f"Profile probe {profile} tests whether a conservative parameterization improves robustness.",
                        "macro_feature_design": args.macro_feature_designs[0],
                        "portfolio_surface": args.portfolio_surfaces[0],
                        "evaluation_mode": args.evaluation_modes[0],
                        "min_weight": float(args.min_weights[0]),
                        **axes,
                    }
                )
    return specs[: args.max_runs] if args.max_runs > 0 else specs


def build_command(args: argparse.Namespace, spec: dict[str, Any], run_id: str) -> list[str]:
    command = [
        sys.executable,
        "scripts/eqr_run_ddqm2.py",
        "--config",
        str(args.config),
        "--panel",
        str(args.panel),
        "--feature-dir",
        str(args.feature_dir),
        "--output-dir",
        str(args.output_dir),
        "--run-id",
        run_id,
        "--model",
        str(spec["model"]),
        "--quantile",
        f"{float(spec['quantile']):.2f}",
        "--factor-universe",
        str(spec.get("factor_universe", "selected_13_global_local")),
        "--factor-selection-policy",
        str(spec.get("factor_selection_policy", "selected_13_global_local")),
        "--factor-universe-target-count",
        str(spec.get("factor_universe_target_count", 13)),
        "--macro-feature-design",
        str(spec.get("macro_feature_design", "ddqm2_25x3_us_macro")),
        "--portfolio-surface",
        str(spec.get("portfolio_surface", "stock_score_qspread_ddqm2")),
        "--evaluation-mode",
        str(spec.get("evaluation_mode", "walk_forward")),
        "--walk-forward-test-periods",
        str(args.walk_forward_test_periods),
        "--walk-forward-validation-periods",
        str(args.walk_forward_validation_periods),
        "--factor-score-chunk-dates",
        str(args.factor_score_chunk_dates),
        "--min-weight",
        f"{float(spec.get('min_weight', 0.0)):.4f}",
    ]
    if spec.get("global_local_quota"):
        command.extend(["--global-local-quota", str(spec["global_local_quota"])])
    if spec.get("category_cap") is not None:
        command.extend(["--category-cap", str(spec["category_cap"])])
    if args.min_observations is not None:
        command.extend(["--min-observations", str(args.min_observations)])
    if args.drop_factor_scores_after_run:
        command.append("--drop-factor-scores-after-run")
    params = spec.get("model_params") or {}
    if params:
        command.extend(["--model-params-json", json.dumps(params, sort_keys=True)])
    return command



def _planned_output_paths(args: argparse.Namespace) -> list[Path]:
    paths = [
        args.ledger,
        args.report,
        args.report.with_suffix(".csv"),
        args.report.with_name(f"{args.report.stem}_sensitivity.csv"),
    ]
    if args.sequential_plan is not None:
        paths.append(args.sequential_plan)
    return paths


def ensure_output_paths_available(args: argparse.Namespace) -> None:
    existing = [path for path in _planned_output_paths(args) if path.exists()]
    if existing:
        formatted = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            "Refusing to overwrite existing autonomous harness artifact(s): "
            f"{formatted}. Use a unique output path."
        )


def validate_heavy_execution_scope(args: argparse.Namespace) -> None:
    if args.execute_heavy_experiments and not args.dry_run and args.max_runs != 1:
        raise ValueError(
            "Heavy experiment execution is single-run gated in this harness; "
            "pass --max-runs 1 and use unique output/report/ledger paths."
        )


def changed_axes_from_spec(spec: dict[str, Any]) -> list[str]:
    axes = ["q_grid", "model_subset"]
    if spec.get("model_params"):
        axes.append("model_hyperparams")
    if spec.get("experiment_family") == "full_long_short_hypothesis_probe":
        axes.append("hypothesis_probe")
    if int(spec.get("factor_universe_target_count", 13)) != 13:
        axes.append("factor_count_selection")
    if spec.get("factor_selection_policy") != "selected_13_global_local":
        axes.append("factor_selection_policy")
    if spec.get("global_local_quota"):
        axes.append("global_local_quota")
    if spec.get("category_cap") is not None:
        axes.append("category_cap")
    if spec.get("macro_feature_design") != "ddqm2_25x3_us_macro":
        axes.append("macro_design_grid")
    if float(spec.get("min_weight", 0.0)) != 0.0:
        axes.append("min_weight_grid")
    return axes


def run_suffix_from_spec(spec: dict[str, Any]) -> str:
    q_label = f"q{int(round(float(spec['quantile']) * 100)):02d}"
    parts = [str(spec["label"]), q_label]
    material = [
        ("n", spec.get("factor_universe_target_count", 13)),
        ("pol", spec.get("factor_selection_policy", "selected_13_global_local")),
        ("quota", spec.get("global_local_quota")),
        ("cap", spec.get("category_cap")),
        ("macro", spec.get("macro_feature_design", "ddqm2_25x3_us_macro")),
        ("mw", spec.get("min_weight", 0.0)),
    ]
    if (
        int(spec.get("factor_universe_target_count", 13)) == 13
        and spec.get("factor_selection_policy", "selected_13_global_local") == "selected_13_global_local"
        and not spec.get("global_local_quota")
        and spec.get("category_cap") is None
        and spec.get("macro_feature_design", "ddqm2_25x3_us_macro") == "ddqm2_25x3_us_macro"
        and float(spec.get("min_weight", 0.0)) == 0.0
    ):
        return "_".join(parts)
    for key, value in material:
        if value is None:
            continue
        parts.append(f"{key}{_safe_label(value)}")
    return "_".join(parts)


def default_interpretability_evidence(
    *,
    next_hypothesis: str | None = None,
    limitations_or_defer_reason: str | None = None,
) -> dict[str, bool]:
    evidence = {key: False for key in REQUIRED_INTERPRETABILITY_EVIDENCE}
    evidence["next_hypothesis"] = bool(next_hypothesis)
    evidence["limitations_or_defer_reason"] = bool(limitations_or_defer_reason)
    return evidence


def missing_interpretability_evidence(evidence: dict[str, Any] | None) -> list[str]:
    evidence = evidence or {}
    return [key for key in REQUIRED_INTERPRETABILITY_EVIDENCE if not bool(evidence.get(key))]


def build_scorecard(item: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    evidence = item.get("interpretability_evidence") or default_interpretability_evidence(
        next_hypothesis=item.get("next_hypothesis"),
        limitations_or_defer_reason=item.get("limitations_or_defer_reason"),
    )
    missing = missing_interpretability_evidence(evidence)
    status = str(row.get("status", item.get("branch_decision", "")))
    metrics_available = bool(row.get("periods", 0)) and status.startswith("ok")
    if status.startswith("ok"):
        decision = "defer" if missing else "adopt"
    elif status in {"planned", "dry_run_planned"} or item.get("dry_run"):
        decision = "continue"
    elif "skipped" in str(item.get("branch_decision", "")):
        decision = "defer" if missing else "adopt"
    else:
        decision = "stop"
    if decision == "defer":
        rationale = "Missing required interpretation evidence: " + ", ".join(missing)
    elif decision == "adopt":
        rationale = "All required interpretation evidence is present; adoption remains research-only."
    elif decision == "continue":
        rationale = "Planned or dry-run branch; no adoption decision until a later experiment-execution phase."
    else:
        rationale = "Failed or unsafe branch; stop or ledger before further action."
    if item.get("invalid_axis_reason"):
        router_state = "stop_or_defer"
        rationale = f"Rejected invalid factor-router axes before subprocess execution: {item['invalid_axis_reason']}"
    elif item.get("dry_run") or status in {"planned", "dry_run_planned"}:
        router_state = "planned_only"
    elif not metrics_available:
        router_state = "insufficient_evidence" if decision in {"continue", "defer"} else "stop_or_defer"
    elif decision == "adopt":
        router_state = "preferred_research_branch"
    elif decision == "defer":
        router_state = "candidate"
    else:
        router_state = "stop_or_defer"
    return {
        "decision": decision,
        "decision_rationale": rationale,
        "router_state": router_state,
        "router_rationale": rationale,
        "adoption_eligible": decision == "adopt",
        "dimensions": {
            "gross_oos_performance": {
                "available": metrics_available,
                "cumulative_return": row.get("cumulative_return"),
                "cagr": row.get("cagr"),
            },
            "net_robustness": {"available": bool(item.get("sensitivity_path"))},
            "drawdown": {"available": metrics_available, "mdd": row.get("mdd")},
            "turnover_resource_realism": {"available": metrics_available, "turnover": row.get("turnover")},
            "interpretability": {"available": not missing, "missing": missing, "evidence": evidence},
            "reproducibility": {
                "available": bool(item.get("command"))
                and item.get("data_boundary") == DATA_BOUNDARY
                and row.get("data_boundary") == DATA_BOUNDARY,
                "data_boundary": item.get("data_boundary"),
                "child_manifest_data_boundary": row.get("data_boundary"),
            },
        },
    }


def attach_scorecards(ledger: dict[str, Any]) -> None:
    for item in ledger.get("matrix_runs", []):
        row = _summary_to_row(item)
        scorecard = build_scorecard(item, row)
        item["scorecard"] = scorecard
        item["router_state"] = scorecard["router_state"]
        item["router_recommendation"] = scorecard["router_rationale"]
        item["autonomous_decision"] = scorecard["decision"]
        item["decision_rationale"] = scorecard["decision_rationale"]
        item.setdefault(
            "next_hypothesis",
            item.get("hypothesis", "Review scorecard and decide the next local-data branch."),
        )
        item.setdefault(
            "limitations_or_defer_reason",
            scorecard["decision_rationale"]
            if scorecard["decision"] == "defer"
            else "Research-only backtest diagnostic; no production claim.",
        )


def _run(command: list[str], *, cwd: Path = PROJECT_ROOT) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    return {
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "returncode": completed.returncode,
        "stdout": completed.stdout[-8000:],
        "stderr": completed.stderr[-8000:],
    }


def _load_manifest(run_dir: Path) -> dict[str, Any] | None:
    path = run_dir / "manifest.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _summary_to_row(item: dict[str, Any]) -> dict[str, Any]:
    manifest = _load_manifest(Path(item["run_dir"]))
    if manifest is None:
        return {
            "run_id": item["run_id"],
            "family": item.get("experiment_family", ""),
            "label": item.get("label", item["model"]),
            "model": item["model"],
            "q": item["quantile"],
            "status": "planned" if item.get("dry_run") else "failed",
            "periods": 0,
            "cumulative_return": 0.0,
            "cagr": 0.0,
            "mdd": 0.0,
            "turnover": 0.0,
            "long_turnover": 0.0,
            "short_turnover": 0.0,
            "data_boundary": None,
        }
    summary = manifest.get("portfolio_summary", {})
    periods = int(summary.get("periods", 0) or 0)
    cumulative = float(summary.get("cumulative_return", 0.0) or 0.0)
    cagr = (1.0 + cumulative) ** (12.0 / periods) - 1.0 if periods > 0 and cumulative > -1.0 else 0.0
    return {
        "run_id": item["run_id"],
        "family": item.get("experiment_family", ""),
        "label": item.get("label", item["model"]),
        "model": manifest.get("model", item["model"]),
        "q": float(manifest.get("quantile", item["quantile"])),
        "status": "ok" if item.get("returncode") == 0 else "failed_after_manifest",
        "periods": periods,
        "cumulative_return": cumulative,
        "cagr": cagr,
        "mdd": float(summary.get("max_drawdown", 0.0) or 0.0),
        "turnover": float(summary.get("turnover", 0.0) or 0.0),
        "long_turnover": float(summary.get("long_turnover", 0.0) or 0.0),
        "short_turnover": float(summary.get("short_turnover", 0.0) or 0.0),
        "data_boundary": manifest.get("data_boundary"),
    }


def long_short_sensitivity(
    portfolio: pd.DataFrame,
    *,
    cost_bps_grid: Iterable[float] = (10.0, 25.0, 50.0, 100.0),
    borrow_bps_grid: Iterable[float] = (0.0, 50.0, 150.0, 300.0),
    slippage_bps_grid: Iterable[float] = (0.0, 10.0, 25.0),
    tax_proxy_grid: Iterable[float] = (0.0, 0.408),
) -> pd.DataFrame:
    """Compute a simple long/short cost/borrow/slippage/tax sensitivity proxy.

    This is a research diagnostic, not a production execution model or tax
    advice.  Borrow is charged as a monthly short-notional drag, cost/slippage
    are charged on long plus short turnover, and the optional tax proxy is a
    simplified monthly drag on positive post-cost returns.
    """

    if portfolio.empty or "portfolio_return" not in portfolio.columns:
        return pd.DataFrame()
    frame = portfolio.copy()
    returns = pd.to_numeric(frame["portfolio_return"], errors="coerce").fillna(0.0)
    long_turnover = pd.to_numeric(frame.get("long_turnover", frame.get("turnover", 0.0)), errors="coerce").fillna(0.0).clip(lower=0.0)
    short_turnover = pd.to_numeric(frame.get("short_turnover", frame.get("turnover", 0.0)), errors="coerce").fillna(0.0).clip(lower=0.0)
    total_turnover = long_turnover + short_turnover
    rows: list[dict[str, Any]] = []
    for split, split_index in frame.groupby("split", sort=True).groups.items():
        idx = list(split_index)
        for cost_bps in cost_bps_grid:
            cost_rate = float(cost_bps) / 10_000.0
            for borrow_bps in borrow_bps_grid:
                monthly_borrow = float(borrow_bps) / 10_000.0 / 12.0
                for slippage_bps in slippage_bps_grid:
                    slippage_rate = float(slippage_bps) / 10_000.0
                    pre_tax = returns.loc[idx] - total_turnover.loc[idx] * (cost_rate + slippage_rate) - monthly_borrow
                    for tax_proxy_rate in tax_proxy_grid:
                        tax_rate = float(tax_proxy_rate)
                        tax_drag = pre_tax.clip(lower=0.0) * tax_rate
                        net = pre_tax - tax_drag
                        equity = (1.0 + net).cumprod()
                        drawdown = equity / equity.cummax() - 1.0
                        rows.append(
                            {
                                "split": split,
                                "transaction_cost_bps": float(cost_bps),
                                "borrow_bps_annual": float(borrow_bps),
                                "slippage_bps": float(slippage_bps),
                                "tax_proxy_rate": tax_rate,
                                "periods": int(len(net)),
                                "mean_monthly_return": float(net.mean()),
                                "volatility_monthly": float(net.std(ddof=0)),
                                "mean_tax_drag": float(tax_drag.mean()),
                                "cumulative_return": float(equity.iloc[-1] - 1.0) if len(equity) else 0.0,
                                "max_drawdown": float(drawdown.min()) if len(drawdown) else 0.0,
                            }
                        )
    return pd.DataFrame(rows)


def _write_sensitivity(args: argparse.Namespace, rows: list[dict[str, Any]]) -> Path | None:
    sensitivity_rows: list[pd.DataFrame] = []
    for item in rows:
        manifest = _load_manifest(Path(item["run_dir"]))
        if manifest is None:
            continue
        portfolio_path = Path(item["run_dir"]) / "portfolio_returns.parquet"
        if not portfolio_path.exists():
            continue
        portfolio = pd.read_parquet(portfolio_path)
        sensitivity = long_short_sensitivity(portfolio)
        if sensitivity.empty:
            continue
        sensitivity.insert(0, "run_id", item["run_id"])
        sensitivity.insert(1, "model", item["model"])
        sensitivity.insert(2, "q", float(item["quantile"]))
        sensitivity_rows.append(sensitivity)
    if not sensitivity_rows:
        return None
    path = args.report.with_name(f"{args.report.stem}_sensitivity.csv")
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing sensitivity CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(sensitivity_rows, ignore_index=True).to_csv(path, index=False)
    return path


def render_report(args: argparse.Namespace, ledger: dict[str, Any]) -> None:
    matrix_rows = [_summary_to_row(item) for item in ledger["matrix_runs"]]
    frame = pd.DataFrame(matrix_rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    csv_path = args.report.with_suffix(".csv")
    if csv_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing matrix CSV: {csv_path}")
    if args.report.exists():
        raise FileExistsError(f"Refusing to overwrite existing report: {args.report}")
    frame.to_csv(csv_path, index=False)
    sensitivity_path = Path(ledger["sensitivity_path"]) if ledger.get("sensitivity_path") else None
    ok = frame.loc[frame["status"].astype(str).str.startswith("ok")].copy() if not frame.empty else pd.DataFrame()
    best = ok.sort_values("cumulative_return", ascending=False).head(5).to_dict("records") if not ok.empty else []
    lines = [
        "# Full-panel Long/Short QSpread Sequential Harness Report",
        "",
        f"Date: {datetime.now(timezone.utc).date().isoformat()}",
        "",
        "## Data boundary and execution policy",
        "",
        f"- Data boundary: `{DATA_BOUNDARY}`.",
        "- No WRDS login, no external API, no new raw data.",
        f"- Cloud policy: `{NO_CLOUD_POLICY}`; no OCI/cloud auto-provisioning.",
        "- Execution policy: one heavy experiment at a time; no OMX team/swarm experiment execution.",
        f"- Advice boundary: {RESEARCH_ONLY_DISCLAIMER}",
        f"- Feature dir: `{args.feature_dir}`.",
        f"- Output dir: `{args.output_dir}`.",
        "",
        "## Walk-forward OOS protocol",
        "",
        "- Portfolio surface: `stock_score_qspread_ddqm2`.",
        "- Evaluation mode: `walk_forward`.",
        f"- Test periods per fold: {args.walk_forward_test_periods}.",
        f"- Validation periods per fold: {args.walk_forward_validation_periods}.",
        "- Headline metrics come from holdout/OOS rows when available.",
        "",
        "## Prior 1.25M date-balanced anchors",
        "",
        "| Label | q | Cumulative return | Implied CAGR | MDD | Turnover |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in PRIOR_125M_ANCHORS:
        lines.append(
            f"| {row['label']} | {row['q']:.2f} | "
            f"{row['cumulative_return']:.4f} | {row['implied_cagr']:.2%} | "
            f"{row['max_drawdown']:.2%} | {row['turnover']:.2%} |"
        )
    lines.extend(["", "## Current full-panel matrix rows", ""])
    if frame.empty:
        lines.append("No rows were planned.")
    else:
        lines.append(
            "| Status | Family | Model | q | Periods | Cumulative | CAGR | MDD | "
            "Turnover | Long turnover | Short turnover | Run ID |"
        )
        lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
        for row in frame.to_dict("records"):
            lines.append(
                f"| {row['status']} | {row['family']} | {row['model']} | {float(row['q']):.2f} | {int(row['periods'])} | "
                f"{float(row['cumulative_return']):.6f} | {float(row['cagr']):.2%} | {float(row['mdd']):.2%} | "
                f"{float(row['turnover']):.2%} | {float(row['long_turnover']):.2%} | {float(row['short_turnover']):.2%} | `{row['run_id']}` |"
            )
    lines.extend(["", "## Autonomous branch scorecard", ""])
    lines.append(
        "| Router state | Decision | Changed axes | Factor policy | Hypothesis / next hypothesis | "
        "Missing interpretation evidence | Rationale | Run ID |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for item in ledger.get("matrix_runs", []):
        scorecard = item.get("scorecard", {})
        missing = scorecard.get("dimensions", {}).get("interpretability", {}).get("missing", [])
        axes = ", ".join(item.get("changed_axes", [])) or "none"
        policy = item.get("factor_selection_policy", "selected_13_global_local")
        hypothesis = item.get("next_hypothesis") or item.get("hypothesis", "")
        decision = scorecard.get("decision", item.get("autonomous_decision", ""))
        router_state = scorecard.get("router_state", item.get("router_state", ""))
        missing_text = ", ".join(missing) if missing else "none"
        rationale = scorecard.get("decision_rationale", item.get("decision_rationale", ""))
        lines.append(
            f"| {router_state} | {decision} | {axes} | {policy} | {hypothesis} | {missing_text} | "
            f"{rationale} | `{item.get('run_id', '')}` |"
        )
    lines.extend(
        [
            "",
            "## Factor-router axis semantics",
            "",
            "- `category` is a report alias for `FactorDefinition.family`; category caps limit selections per family.",
            "- `selected_13_global_local`, `local_only`, and `global_only` ignore quota/cap axes unless a capped policy is selected.",
            "- `quota` requires one `G:L` global/local quota; invalid combinations are rejected before subprocess execution.",
            "- `category_capped` requires one positive family cap; invalid values are rejected before subprocess execution.",
            "- Dry-run router state `planned_only` never uses observed OOS, MDD, turnover, or net performance.",
        ]
    )
    lines.extend(["", "## Best completed rows", ""])
    if best:
        for row in best:
            lines.append(
                f"- `{row['run_id']}`: cumulative "
                f"{float(row['cumulative_return']):.6f}, "
                f"CAGR {float(row['cagr']):.2%}, MDD {float(row['mdd']):.2%}."
            )
    else:
        lines.append("No completed run yet; this report is a planned/dry-run ledger.")
    lines.extend(
        [
            "",
            "## Stop trigger policy",
            "",
            "- Complete the full-panel long/short walk-forward OOS anchor grid or ledger failures.",
            "- Run cost/borrow/slippage/tax-proxy sensitivity for Pareto candidates when feasible.",
            "- Diagnose drawdowns and stress months before declaring a strategy-quality conclusion.",
            "- Stop after two consecutive hypothesis batches without material Pareto "
            "improvement, repeated memory failures, or scope drift outside DDQM/DDQM2/EQR.",
            "",
            "## Artifacts",
            "",
            f"- Matrix CSV: `{csv_path}`",
            f"- Ledger: `{args.ledger}`",
            f"- Artifact no-overwrite policy: `{ARTIFACT_NO_OVERWRITE_POLICY}`",
            f"- Sensitivity CSV: `{sensitivity_path}`" if sensitivity_path else "- Sensitivity CSV: not yet produced.",
            "",
            RESEARCH_ONLY_DISCLAIMER,
            "The tax-proxy sensitivity is not tax-lot accounting.",
            "",
        ]
    )
    args.report.write_text("\n".join(lines), encoding="utf-8")


def write_sequential_plan(args: argparse.Namespace, ledger: dict[str, Any]) -> Path | None:
    completed = [
        item
        for item in ledger.get("matrix_runs", [])
        if item.get("returncode") == 0 and _load_manifest(Path(item["run_dir"])) is not None
    ]
    if not completed:
        return None
    path = args.sequential_plan or args.report.with_name(f"{args.report.stem}_sequential_plan.md")
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing sequential plan artifact: {path}")
    anchor = completed[0]
    stamp_placeholder = "$(date -u +%Y%m%dT%H%M%SZ)"
    command_templates = [
        {
            "label": "selected-factor-count-7",
            "args": "--models baseline_mean --quantiles 0.30 --factor-selection-policies selected_13_global_local --factor-counts 7 --max-runs 1",
            "rationale": "Check whether a narrower selected-factor set changes the balanced scorecard after the N=13 anchor.",
        },
        {
            "label": "local-only",
            "args": "--models baseline_mean --quantiles 0.30 --factor-selection-policies local_only --factor-counts 13 --max-runs 1",
            "rationale": "Isolate local-state factor families under the same OOS protocol.",
        },
        {
            "label": "global-only",
            "args": "--models baseline_mean --quantiles 0.30 --factor-selection-policies global_only --factor-counts 13 --max-runs 1",
            "rationale": "Isolate global-return factor families under the same OOS protocol.",
        },
        {
            "label": "quota-policy",
            "args": "--models baseline_mean --quantiles 0.30 --factor-selection-policies quota --global-local-quotas 6:7 --factor-counts 13 --max-runs 1",
            "rationale": "Force explicit global/local allocation and inspect selection metadata coverage.",
        },
        {
            "label": "family-cap-policy",
            "args": "--models baseline_mean --quantiles 0.30 --factor-selection-policies category_capped --category-caps 3 --factor-counts 13 --max-runs 1",
            "rationale": "Reduce family concentration and compare drawdown/turnover diagnostics.",
        },
    ]
    lines = [
        "# Factor Router Sequential Full-Run Plan",
        "",
        f"Created: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Anchor evidence",
        "",
        f"- Anchor run id: `{anchor['run_id']}`",
        f"- Anchor run dir: `{anchor['run_dir']}`",
        f"- Anchor ledger: `{args.ledger}`",
        f"- Anchor report: `{args.report}`",
        "",
        "## Execution boundaries",
        "",
        f"- Data boundary: `{DATA_BOUNDARY}`.",
        "- Use local prepared parquet artifacts only; no WRDS login, no external/new raw data.",
        "- No team, no swarm, no parallel heavy experiments. Run exactly one command at a time.",
        "- Stop on failure, OOM, path collision, missing manifest, or scope drift; ledger the blocker before the next run.",
        f"- Advice boundary: {RESEARCH_ONLY_DISCLAIMER}",
        "",
        "## Ordered one-run command templates",
        "",
        "Each command must use a fresh UTC stamp and unique output/report/ledger paths.",
        "",
    ]
    for index, template in enumerate(command_templates, start=1):
        run_prefix = f"factor_router_seq_{index}_{template['label']}_{stamp_placeholder}"
        output_dir = f"experiments/ddqm2_factor_router_seq_{index}_{template['label']}_{stamp_placeholder}"
        report = f"reports/factor_router_seq_{index}_{template['label']}_{stamp_placeholder}.md"
        ledger_path = f"reports/factor_router_seq_{index}_{template['label']}_{stamp_placeholder}.json"
        lines.extend(
            [
                f"### {index}. {template['label']}",
                "",
                f"Balanced-scorecard rationale: {template['rationale']}",
                "",
                "```bash",
                "STAMP=\"$(date -u +%Y%m%dT%H%M%SZ)\"",
                "PYTHONPATH=src:. .venv/bin/python scripts/eqr_run_full_long_short_matrix.py \\",
                "  --execute-heavy-experiments \\",
                f"  {template['args']} \\",
                "  --factor-universes selected_13_global_local \\",
                "  --macro-feature-designs ddqm2_25x3_us_macro \\",
                "  --portfolio-surfaces stock_score_qspread_ddqm2 \\",
                "  --evaluation-modes walk_forward \\",
                "  --walk-forward-test-periods 12 \\",
                "  --walk-forward-validation-periods 12 \\",
                "  --factor-score-chunk-dates 12 \\",
                "  --min-weights 0.00 \\",
                f"  --run-prefix \"{run_prefix.replace(stamp_placeholder, '${STAMP}')}\" \\",
                f"  --output-dir \"{output_dir.replace(stamp_placeholder, '${STAMP}')}\" \\",
                f"  --report \"{report.replace(stamp_placeholder, '${STAMP}')}\" \\",
                f"  --ledger \"{ledger_path.replace(stamp_placeholder, '${STAMP}')}\"",
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Router interpretation rule",
            "",
            "Prefer branches only when the balanced scorecard improves or explains gross OOS, drawdown, turnover/resource realism, net/cost sensitivity when available, interpretability metadata, novelty coverage, and reproducibility. A preferred branch remains a research diagnostic, not production approval.",
            "",
            RESEARCH_ONLY_DISCLAIMER,
            "The tax-proxy sensitivity is not tax-lot accounting or tax advice.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_matrix(args: argparse.Namespace, prefix: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for spec in run_specs(args):
        run_id = f"{prefix}_{run_suffix_from_spec(spec)}"
        run_dir = args.output_dir / run_id
        invalid_axis_reason = spec.get("invalid_axis_reason")
        command = [] if invalid_axis_reason else build_command(args, spec, run_id)
        item = {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "model": spec["model"],
            "label": spec["label"],
            "quantile": spec["quantile"],
            "model_params": spec.get("model_params", {}),
            "factor_universe": spec.get("factor_universe", "selected_13_global_local"),
            "factor_selection_policy": spec.get("factor_selection_policy", "selected_13_global_local"),
            "factor_universe_target_count": spec.get("factor_universe_target_count", 13),
            "global_local_quota": spec.get("global_local_quota"),
            "category_cap": spec.get("category_cap"),
            "macro_feature_design": spec.get("macro_feature_design", "ddqm2_25x3_us_macro"),
            "portfolio_surface": spec.get("portfolio_surface", "stock_score_qspread_ddqm2"),
            "evaluation_mode": spec.get("evaluation_mode", "walk_forward"),
            "min_weight": spec.get("min_weight", 0.0),
            "optional_axis_state": spec.get("optional_axis_state", {}),
            "invalid_axis_reason": invalid_axis_reason,
            "experiment_family": spec["experiment_family"],
            "hypothesis": spec["hypothesis"],
            "command": command,
            "data_boundary": DATA_BOUNDARY,
            "cloud_policy": NO_CLOUD_POLICY,
            "storage_policy": {
                "drop_factor_scores_after_run": bool(args.drop_factor_scores_after_run),
                "scope": "future_child_run_directory_only",
                "preserves_existing_experiment_outputs": True,
            },
            "advice_boundary": RESEARCH_ONLY_DISCLAIMER,
            "changed_axes": changed_axes_from_spec(spec),
            "required_interpretability_evidence": list(REQUIRED_INTERPRETABILITY_EVIDENCE),
            "interpretability_evidence": default_interpretability_evidence(
                next_hypothesis=spec["hypothesis"],
                limitations_or_defer_reason="No completed diagnostics yet; harness-only phase or missing artifacts.",
            ),
            "next_hypothesis": spec["hypothesis"],
            "limitations_or_defer_reason": "No completed diagnostics yet; harness-only phase or missing artifacts.",
            "branch_decision": "planned",
        }
        manifest_path = run_dir / "manifest.json"
        if invalid_axis_reason:
            item.update(
                {
                    "started_at": None,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "returncode": 2,
                    "stdout": "",
                    "stderr": f"invalid factor-router axis combination: {invalid_axis_reason}",
                    "branch_decision": "rejected_invalid_axis_combination",
                }
            )
        elif manifest_path.exists():
            item.update(
                {
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "returncode": 0,
                    "stdout": f"skipped existing manifest: {manifest_path}",
                    "stderr": "",
                    "branch_decision": "skipped_existing_manifest",
                }
            )
        elif run_dir.exists():
            item.update(
                {
                    "started_at": None,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "returncode": 2,
                    "stdout": "",
                    "stderr": f"refusing to write into existing run directory without manifest: {run_dir}",
                    "branch_decision": "failed_existing_run_dir_without_manifest",
                }
            )
        elif args.dry_run:
            item.update(
                {
                    "started_at": None,
                    "finished_at": None,
                    "returncode": None,
                    "stdout": "",
                    "stderr": "",
                    "dry_run": True,
                    "branch_decision": "dry_run_planned",
                }
            )
        elif not args.execute_heavy_experiments:
            item.update(
                {
                    "started_at": None,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "returncode": 3,
                    "stdout": "",
                    "stderr": "heavy experiment execution requires --execute-heavy-experiments",
                    "branch_decision": "blocked_requires_execute_heavy_experiments",
                }
            )
        else:
            result = _run(command)
            item.update(result)
            item["branch_decision"] = "completed" if result["returncode"] == 0 else "failed_ledgered"
        results.append(item)
        if item.get("returncode") not in (0, None) and not args.continue_on_error:
            break
    return results


def main() -> int:
    args = parse_args()
    prefix = args.run_prefix or f"full_long_short_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    validate_heavy_execution_scope(args)
    ensure_output_paths_available(args)
    ledger: dict[str, Any] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data_boundary": DATA_BOUNDARY,
        "guardrails": {
            "no_wrds_login": True,
            "no_external_data": True,
            "no_new_raw_data": True,
            "no_team_or_swarm_experiment_execution": True,
            "single_heavy_experiment_at_a_time": True,
            "additive_outputs_only": True,
            "no_cloud_or_oci_auto_provisioning": True,
            "not_investment_trading_legal_tax_or_production_advice": True,
        },
        "config": str(args.config),
        "panel": str(args.panel),
        "feature_dir": str(args.feature_dir),
        "output_dir": str(args.output_dir),
        "run_prefix": prefix,
        "models": args.models,
        "quantiles": args.quantiles,
        "factor_universes": args.factor_universes,
        "factor_selection_policies": args.factor_selection_policies,
        "factor_counts": args.factor_counts,
        "global_local_quotas": args.global_local_quotas,
        "category_caps": args.category_caps,
        "macro_feature_designs": args.macro_feature_designs,
        "portfolio_surfaces": args.portfolio_surfaces,
        "evaluation_modes": args.evaluation_modes,
        "min_weights": args.min_weights,
        "environment": _environment_snapshot(),
        "artifact_no_overwrite_policy": ARTIFACT_NO_OVERWRITE_POLICY,
        "advice_boundary": RESEARCH_ONLY_DISCLAIMER,
        "cloud_policy": NO_CLOUD_POLICY,
        "storage_policy": {
            "drop_factor_scores_after_run": bool(args.drop_factor_scores_after_run),
            "scope": "future_child_run_directory_only",
            "preserves_existing_experiment_outputs": True,
        },
        "run_specs": run_specs(args),
        "matrix_runs": [],
    }
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger["matrix_runs"] = run_matrix(args, prefix)
    sensitivity_path = _write_sensitivity(args, ledger["matrix_runs"])
    ledger["sensitivity_path"] = str(sensitivity_path) if sensitivity_path else None
    if sensitivity_path:
        for item in ledger["matrix_runs"]:
            if _load_manifest(Path(item["run_dir"])) is not None:
                item["sensitivity_path"] = str(sensitivity_path)
    attach_scorecards(ledger)
    sequential_plan_path = write_sequential_plan(args, ledger)
    ledger["sequential_plan_path"] = str(sequential_plan_path) if sequential_plan_path else None
    if args.ledger.exists():
        raise FileExistsError(f"Refusing to overwrite existing ledger: {args.ledger}")
    args.ledger.write_text(json.dumps(ledger, indent=2, default=str), encoding="utf-8")
    render_report(args, ledger)
    failures = [run for run in ledger["matrix_runs"] if run.get("returncode") not in (0, None)]
    blocked_heavy = [run for run in ledger["matrix_runs"] if run.get("returncode") == 3]
    print(
        json.dumps(
            {
                "report": str(args.report),
                "ledger": str(args.ledger),
                "runs": len(ledger["matrix_runs"]),
                "failures": len(failures),
                "dry_run": bool(args.dry_run),
            },
            indent=2,
        )
    )
    return 1 if blocked_heavy or (failures and not args.continue_on_error) else 0


if __name__ == "__main__":
    raise SystemExit(main())
