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
    parser.add_argument("--continue-on-error", action="store_true", default=True)
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
    for model in args.models:
        for quantile in quantiles:
            specs.append(
                {
                    "label": model,
                    "model": model,
                    "quantile": quantile,
                    "model_params": dict(MODEL_SAFETY_OVERRIDES.get(model, {})),
                    "experiment_family": "full_long_short_core_q",
                    "hypothesis": "Full-panel long/short QSpread anchor under existing walk-forward OOS protocol.",
                }
            )
    if args.hyperparam_probes:
        for profile in args.model_param_profiles:
            if profile not in MODEL_PARAM_PROFILES:
                raise ValueError(f"Unknown model profile: {profile}")
            model, params = MODEL_PARAM_PROFILES[profile]
            specs.append(
                {
                    "label": profile,
                    "model": model,
                    "quantile": float(args.probe_quantile),
                    "model_params": dict(params),
                    "experiment_family": "full_long_short_hypothesis_probe",
                    "hypothesis": f"Profile probe {profile} tests whether a conservative parameterization improves robustness.",
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
        "selected_13_global_local",
        "--macro-feature-design",
        "ddqm2_25x3_us_macro",
        "--portfolio-surface",
        "stock_score_qspread_ddqm2",
        "--evaluation-mode",
        "walk_forward",
        "--walk-forward-test-periods",
        str(args.walk_forward_test_periods),
        "--walk-forward-validation-periods",
        str(args.walk_forward_validation_periods),
        "--factor-score-chunk-dates",
        str(args.factor_score_chunk_dates),
    ]
    if args.min_observations is not None:
        command.extend(["--min-observations", str(args.min_observations)])
    params = spec.get("model_params") or {}
    if params:
        command.extend(["--model-params-json", json.dumps(params, sort_keys=True)])
    return command



def _planned_output_paths(args: argparse.Namespace) -> list[Path]:
    return [
        args.ledger,
        args.report,
        args.report.with_suffix(".csv"),
        args.report.with_name(f"{args.report.stem}_sensitivity.csv"),
    ]


def ensure_output_paths_available(args: argparse.Namespace) -> None:
    existing = [path for path in _planned_output_paths(args) if path.exists()]
    if existing:
        formatted = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            "Refusing to overwrite existing autonomous harness artifact(s): "
            f"{formatted}. Use a unique output path."
        )


def changed_axes_from_spec(spec: dict[str, Any]) -> list[str]:
    axes = ["q_grid", "model_subset"]
    if spec.get("model_params"):
        axes.append("model_hyperparams")
    if spec.get("experiment_family") == "full_long_short_hypothesis_probe":
        axes.append("hypothesis_probe")
    return axes


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
    return {
        "decision": decision,
        "decision_rationale": rationale,
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
                "available": bool(item.get("command")) and item.get("data_boundary") == DATA_BOUNDARY,
                "data_boundary": item.get("data_boundary"),
            },
        },
    }


def attach_scorecards(ledger: dict[str, Any]) -> None:
    for item in ledger.get("matrix_runs", []):
        row = _summary_to_row(item)
        scorecard = build_scorecard(item, row)
        item["scorecard"] = scorecard
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
        "| Decision | Changed axes | Hypothesis / next hypothesis | "
        "Missing interpretation evidence | Rationale | Run ID |"
    )
    lines.append("|---|---|---|---|---|---|")
    for item in ledger.get("matrix_runs", []):
        scorecard = item.get("scorecard", {})
        missing = scorecard.get("dimensions", {}).get("interpretability", {}).get("missing", [])
        axes = ", ".join(item.get("changed_axes", [])) or "none"
        hypothesis = item.get("next_hypothesis") or item.get("hypothesis", "")
        decision = scorecard.get("decision", item.get("autonomous_decision", ""))
        missing_text = ", ".join(missing) if missing else "none"
        rationale = scorecard.get("decision_rationale", item.get("decision_rationale", ""))
        lines.append(
            f"| {decision} | {axes} | {hypothesis} | {missing_text} | "
            f"{rationale} | `{item.get('run_id', '')}` |"
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


def run_matrix(args: argparse.Namespace, prefix: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for spec in run_specs(args):
        q_label = f"q{int(round(float(spec['quantile']) * 100)):02d}"
        run_id = f"{prefix}_{spec['label']}_{q_label}"
        run_dir = args.output_dir / run_id
        command = build_command(args, spec, run_id)
        item = {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "model": spec["model"],
            "label": spec["label"],
            "quantile": spec["quantile"],
            "model_params": spec.get("model_params", {}),
            "experiment_family": spec["experiment_family"],
            "hypothesis": spec["hypothesis"],
            "command": command,
            "data_boundary": DATA_BOUNDARY,
            "cloud_policy": NO_CLOUD_POLICY,
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
        if manifest_path.exists():
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
        "environment": _environment_snapshot(),
        "artifact_no_overwrite_policy": ARTIFACT_NO_OVERWRITE_POLICY,
        "advice_boundary": RESEARCH_ONLY_DISCLAIMER,
        "cloud_policy": NO_CLOUD_POLICY,
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
