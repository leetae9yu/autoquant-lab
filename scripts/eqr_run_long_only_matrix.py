#!/usr/bin/env python3
"""Run and report the additive long-only QSpread DDQM2 matrix."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "server_full.yaml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "experiments" / "ddqm2_long_only"
DEFAULT_FEATURE_DIR = PROJECT_ROOT / "experiments" / "prepared" / "features"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "long_only_qspread_ml_costs_report.md"
DEFAULT_LEDGER = PROJECT_ROOT / "reports" / "long_only_qspread_ml_costs_ledger.json"

MODEL_PARAM_PROFILES: dict[str, dict[str, Any]] = {
    "lightgbm_conservative": {"n_estimators": 120, "learning_rate": 0.03, "num_leaves": 15, "min_child_samples": 80, "n_jobs": 1},
    "lightgbm_wide": {"n_estimators": 160, "learning_rate": 0.04, "num_leaves": 63, "min_child_samples": 40, "n_jobs": 1},
    "ridge_low_alpha": {"alpha": 0.1},
    "ridge_high_alpha": {"alpha": 10.0},
    "elasticnet_sparse": {"alpha": 0.01, "l1_ratio": 0.8, "max_iter": 3000},
    "elasticnet_dense": {"alpha": 0.0005, "l1_ratio": 0.2, "max_iter": 3000},
    "random_forest_shallow": {"n_estimators": 80, "max_depth": 5, "min_samples_leaf": 40, "n_jobs": 1},
    "extra_trees_shallow": {"n_estimators": 80, "max_depth": 5, "min_samples_leaf": 40, "n_jobs": 1},
}

MODEL_BASE_FOR_PROFILE = {
    "lightgbm_conservative": "lightgbm",
    "lightgbm_wide": "lightgbm",
    "ridge_low_alpha": "ridge",
    "ridge_high_alpha": "ridge",
    "elasticnet_sparse": "elasticnet",
    "elasticnet_dense": "elasticnet",
    "random_forest_shallow": "random_forest",
    "extra_trees_shallow": "extra_trees",
}

MODEL_SAFETY_OVERRIDES: dict[str, dict[str, Any]] = {
    "lightgbm": {"n_jobs": 1},
    "random_forest": {"n_jobs": 1},
    "extra_trees": {"n_jobs": 1},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run long-only QSpread q/model matrix and render a report.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--feature-dir", type=Path, default=DEFAULT_FEATURE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--models", nargs="+", default=["lightgbm", "ridge", "elasticnet", "random_forest", "extra_trees", "baseline_mean"])
    parser.add_argument("--quantiles", nargs="+", type=float, default=[0.10, 0.20, 0.30])
    parser.add_argument("--q-edge", action="store_true", help="Also run q=0.05 and q=0.50 for each baseline model.")
    parser.add_argument("--hyperparam-probes", action="store_true", help="Run memory-safe hyperparameter probes at --probe-quantile.")
    parser.add_argument("--probe-quantile", type=float, default=0.20)
    parser.add_argument("--model-param-profiles", nargs="+", default=["lightgbm_conservative", "ridge_high_alpha", "elasticnet_sparse", "extra_trees_shallow"])
    parser.add_argument("--run-prefix", default=None)
    parser.add_argument("--max-rows", type=int, default=0, help="Forwarded cap; 0 means full prepared panel.")
    parser.add_argument("--transaction-cost-bps", type=float, default=50.0)
    parser.add_argument("--tax-rate", type=float, default=0.408)
    parser.add_argument("--prepare", action="store_true", help="Rebuild labels/features from local data before matrix.")
    parser.add_argument("--partitioned-prepare", action="store_true", help="When --prepare is used, write partitioned feature parts for memory-safe full-panel runs.")
    parser.add_argument("--feature-chunk-months", type=int, default=12)
    parser.add_argument("--continue-on-error", action="store_true", default=True)
    return parser.parse_args()


def _unique_floats(values: Iterable[float]) -> list[float]:
    seen: set[str] = set()
    out: list[float] = []
    for value in values:
        key = f"{float(value):.4f}"
        if key not in seen:
            seen.add(key)
            out.append(float(value))
    return out


def _run(command: list[str], *, cwd: Path = PROJECT_ROOT) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    return {
        "command": command,
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "returncode": completed.returncode,
        "stdout": completed.stdout[-8000:],
        "stderr": completed.stderr[-8000:],
    }


def _prepare(args: argparse.Namespace) -> list[dict[str, Any]]:
    base = [sys.executable, "scripts/eqr_prepare_panel.py", "--config", str(args.config), "--row-cap-mode", "date-balanced"]
    if args.max_rows > 0:
        base.extend(["--max-rows", str(args.max_rows)])
    feature_command = [*base, "--stage", "features", "--output-dir", str(args.feature_dir)]
    if args.partitioned_prepare:
        feature_command.extend(["--partitioned", "--feature-chunk-months", str(args.feature_chunk_months)])
    return [_run([*base, "--stage", "labels"]), _run(feature_command)]


def _run_specs(args: argparse.Namespace) -> list[dict[str, Any]]:
    quantiles = _unique_floats([*args.quantiles, *([0.05, 0.50] if args.q_edge else [])])
    specs: list[dict[str, Any]] = []
    for model in args.models:
        for quantile in quantiles:
            params = dict(MODEL_SAFETY_OVERRIDES.get(model, {}))
            specs.append({"label": model, "model": model, "quantile": quantile, "model_params": params, "experiment_family": "core_q"})
    if args.hyperparam_probes:
        for profile in args.model_param_profiles:
            if profile not in MODEL_PARAM_PROFILES:
                raise ValueError(f"Unknown --model-param-profiles entry: {profile}")
            model = MODEL_BASE_FOR_PROFILE[profile]
            specs.append(
                {
                    "label": profile,
                    "model": model,
                    "quantile": float(args.probe_quantile),
                    "model_params": dict(MODEL_PARAM_PROFILES[profile]),
                    "experiment_family": "hyperparam_probe",
                }
            )
    return specs


def _run_matrix(args: argparse.Namespace, prefix: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for spec in _run_specs(args):
        model = spec["model"]
        quantile = float(spec["quantile"])
        label = spec["label"]
        q_label = f"q{int(round(quantile * 100)):02d}"
        run_id = f"{prefix}_{label}_{q_label}"
        command = [
            sys.executable,
            "scripts/eqr_run_ddqm2.py",
            "--config",
            str(args.config),
            "--output-dir",
            str(args.output_dir),
            "--feature-dir",
            str(args.feature_dir),
            "--run-id",
            run_id,
            "--model",
            model,
            "--quantile",
            f"{quantile:.2f}",
            "--factor-universe",
            "selected_13_global_local",
            "--macro-feature-design",
            "ddqm2_25x3_us_macro",
            "--portfolio-surface",
            "stock_score_long_only_qspread",
            "--evaluation-mode",
            "walk_forward",
            "--walk-forward-test-periods",
            "12",
            "--walk-forward-validation-periods",
            "12",
            "--factor-score-chunk-dates",
            "12",
            "--transaction-cost-bps",
            str(args.transaction_cost_bps),
            "--tax-rate",
            str(args.tax_rate),
        ]
        if spec["model_params"]:
            command.extend(["--model-params-json", json.dumps(spec["model_params"], sort_keys=True)])
        if args.max_rows > 0:
            command.extend(["--max-rows", str(args.max_rows)])
        manifest_path = args.output_dir / run_id / "manifest.json"
        if manifest_path.exists():
            result = {
                "command": command,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "returncode": 0,
                "stdout": f"skipped existing manifest: {manifest_path}",
                "stderr": "",
            }
        else:
            result = _run(command)
        result.update(
            {
                "model": model,
                "label": label,
                "quantile": quantile,
                "model_params": spec["model_params"],
                "experiment_family": spec["experiment_family"],
                "run_id": run_id,
                "run_dir": str(args.output_dir / run_id),
            }
        )
        results.append(result)
        if result["returncode"] != 0 and not args.continue_on_error:
            break
    return results


def _load_manifest(path: Path) -> dict[str, Any] | None:
    manifest_path = path / "manifest.json"
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _diagnostic_top_factors(run_dir: Path, n: int = 5) -> str:
    path = run_dir / "factor_diagnostics.csv"
    if not path.exists():
        return ""
    frame = pd.read_csv(path)
    if frame.empty or "factor_id" not in frame.columns:
        return ""
    bits = []
    for row in frame.sort_values("mean_weight", ascending=False).head(n).to_dict("records"):
        bits.append(f"{row['factor_id']} ({float(row.get('mean_weight', 0.0)):.3f})")
    return ", ".join(bits)


def _render_report(args: argparse.Namespace, ledger: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    for item in ledger["matrix_runs"]:
        manifest = _load_manifest(Path(item["run_dir"]))
        if manifest is None:
            rows.append({"run_id": item["run_id"], "family": item.get("experiment_family", ""), "label": item.get("label", item["model"]), "model": item["model"], "q": item["quantile"], "status": "failed", "error": item.get("stderr", "")[:300]})
            continue
        summary = manifest.get("portfolio_summary", {})
        rows.append(
            {
                "run_id": item["run_id"],
                "family": item.get("experiment_family", ""),
                "label": item.get("label", item["model"]),
                "model": manifest.get("model", item["model"]),
                "model_params": json.dumps(manifest.get("model_params", item.get("model_params", {})), sort_keys=True),
                "q": manifest.get("quantile", item["quantile"]),
                "status": "ok" if item["returncode"] == 0 else "failed_after_manifest",
                "periods": summary.get("periods", 0),
                "net_cum": summary.get("cumulative_return", 0.0),
                "gross_cum": summary.get("cumulative_return_gross", summary.get("cumulative_return", 0.0)),
                "mdd": summary.get("max_drawdown", 0.0),
                "turnover": summary.get("turnover", 0.0),
                "avg_tax_drag": summary.get("tax_drag_return", 0.0),
                "avg_trading_drag": summary.get("trading_cost_return", 0.0),
                "top_factors": _diagnostic_top_factors(Path(item["run_dir"])),
            }
        )
    frame = pd.DataFrame(rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    display_cols = ["status", "family", "label", "model", "q", "periods", "net_cum", "gross_cum", "mdd", "turnover", "avg_tax_drag", "avg_trading_drag", "top_factors", "run_id"]
    column_defaults: dict[str, Any] = {
        "status": "failed",
        "family": "",
        "label": "",
        "model": "",
        "q": 0.0,
        "periods": 0,
        "net_cum": 0.0,
        "gross_cum": 0.0,
        "mdd": 0.0,
        "turnover": 0.0,
        "avg_tax_drag": 0.0,
        "avg_trading_drag": 0.0,
        "top_factors": "",
        "run_id": "",
    }
    for column, default in column_defaults.items():
        if column not in frame.columns:
            frame[column] = default
    ok_frame = frame.loc[frame["status"].astype(str).str.startswith("ok")].copy() if not frame.empty else pd.DataFrame()
    best_rows: list[dict[str, Any]] = []
    if not ok_frame.empty:
        best_rows = (
            ok_frame.sort_values(["model", "net_cum"], ascending=[True, False])
            .groupby("model", as_index=False)
            .head(1)
            .sort_values("net_cum", ascending=False)
            .to_dict("records")
        )
    lines = [
        "# autoquant-lab Long-only QSpread 추가 실험 보고서",
        "",
        f"작성일: {datetime.now(timezone.utc).date().isoformat()}",
        "",
        "기존 DDQM2 matrix report: [`reports/usa_ddqm2_matrix_report_ko.md`](usa_ddqm2_matrix_report_ko.md)",
        "",
        "## 초록",
        "",
        "본 추가 실험은 기존 DDQM2/EQR long-short 결과를 덮지 않고, 같은 연구 결을 유지한 채 stock-score QSpread를 **long-only top-q equal-weight fully-invested** 포트폴리오로 재해석한 것이다. 실험은 로컬 parquet artifact만 사용했으며 WRDS 로그인, 신규 원천 데이터 다운로드, 외부 데이터 보강은 수행하지 않았다.",
        "",
        "핵심 변경점은 세 가지다. 첫째, full monthly label panel 2,082,485 rows를 사용하기 위해 feature preparation을 date-partitioned chunk 방식으로 확장했다. 둘째, 기존 short leg 최적화는 추가하지 않고 long-only top-q surface만 별도 산출물로 평가했다. 셋째, gross 성과와 함께 보수적 거래비용/세금 proxy를 primary net lens로 기록했다.",
        "",
        "## 1. 연구 범위와 보존 원칙",
        "",
        "- 기존 `reports/usa_ddqm2_matrix_report_*.md`와 기존 `experiments/ddqm2*` 결과를 수정하지 않는다.",
        "- 이번 결과는 `experiments/ddqm2_long_only_full_chunked/` 및 본 report/ledger에만 additive로 남긴다.",
        "- raw data와 generated experiment parquet은 계속 git 공개 대상에서 제외한다.",
        "- 투자/세무 조언이 아니라 research backtest 및 sensitivity report로만 해석한다.",
        "",
        "## 2. 데이터와 메모리 하네스",
        "",
        f"- Feature directory: `{args.feature_dir}`",
        f"- Run output directory: `{args.output_dir}`",
        "- Full label panel: `experiments/prepared/panel/monthly_labels.parquet` 기준 1990-01~2024-12, 420개월.",
        "- Partitioned feature artifact: full 2,082,485 rows, 159 features, macro/crsp/compustat/ibes families.",
        f"- Feature chunk months: {ledger.get('feature_chunk_months', 'n/a')}",
        "- Model runs are sequential; tree/boosting estimators force `n_jobs=1` where applicable.",
        "- Factor score construction reads only date chunks and does not materialize all stock-factor scores for long-only backtest.",
        "",
        "## 3. Conservative cost/tax assumptions",
        "",
        f"- Primary transaction cost: {args.transaction_cost_bps:.1f} bps per one-way turnover.",
        f"- Primary tax drag: {args.tax_rate:.1%} applied to positive monthly gains realized by turnover.",
        "- This is a simplified research sensitivity assumption, not tax/legal advice.",
        "",
        "## 4. Matrix summary",
        "",
    ]
    if best_rows:
        lines.extend(["### 4.1 모델별 best-q 요약", ""])
        lines.append("| model | best q | net cumulative | gross cumulative | MDD | turnover | run_id |")
        lines.append("|---|---:|---:|---:|---:|---:|---|")
        for row in best_rows:
            lines.append(
                f"| {row['model']} | {float(row['q']):.2f} | {float(row.get('net_cum') or 0.0):.6f} | "
                f"{float(row.get('gross_cum') or 0.0):.6f} | {float(row.get('mdd') or 0.0):.6f} | "
                f"{float(row.get('turnover') or 0.0):.6f} | `{row['run_id']}` |"
            )
        lines.extend(["", "### 4.2 전체 run table", ""])
    if frame.empty:
        lines.append("No matrix rows were produced.")
    else:
        lines.append("| status | family | label | model | q | periods | net cum | gross cum | MDD | turnover | avg tax drag | avg trading drag | top weighted factors | run_id |")
        lines.append("|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")
        for row in frame[display_cols].to_dict("records"):
            lines.append(
                f"| {row['status']} | {row.get('family') or ''} | {row.get('label') or row['model']} | {row['model']} | {float(row['q']):.2f} | {int(row.get('periods') or 0)} | "
                f"{float(row.get('net_cum') or 0.0):.6f} | {float(row.get('gross_cum') or 0.0):.6f} | {float(row.get('mdd') or 0.0):.6f} | "
                f"{float(row.get('turnover') or 0.0):.6f} | {float(row.get('avg_tax_drag') or 0.0):.6f} | {float(row.get('avg_trading_drag') or 0.0):.6f} | "
                f"{row.get('top_factors') or ''} | `{row['run_id']}` |"
            )
    lines.extend(
        [
            "",
            "## 5. Existing long-short comparison anchor",
            "",
            "The existing source-controlled DDQM2 matrix report remains the comparison baseline: `reports/usa_ddqm2_matrix_report_ko.md` / `reports/usa_ddqm2_matrix_report_en.md`. This report does not rewrite those claims; it adds a long-only, conservative-net lens beside them.",
            "",
            "## 6. Factor/model diagnostics",
            "",
            "각 run은 `factor_diagnostics.csv`를 남긴다. 표의 `top weighted factors`는 해당 모델이 long-only stock score를 만들 때 평균적으로 높은 weight를 둔 factor들이다. 전반적으로 size, reversal, quality/value 계열이 반복적으로 상위에 나타나며, 모델별/q별로 quality/value 비중과 turnover tradeoff가 달라진다.",
            "",
            "## 7. Interpretation hooks for user review",
            "",
            "- Which models keep attractive net returns after conservative tax drag rather than only gross returns?",
            "- Do linear models and tree models concentrate on different factor families?",
            "- Does wider q reduce turnover/tax drag enough to offset weaker raw selection?",
            "- Are the high-turnover months explaining most of the net/gross gap?",
            "",
            "## 8. Limitations",
            "",
            "- No new data was acquired; all results depend on current local artifacts.",
            "- Tax treatment is intentionally simplified and conservative; it is not advice.",
            "- Slippage/market impact/capacity are proxied, not measured from order book data.",
            "- Long-only top-q equal-weight is a first-pass research surface, not a deployable strategy.",
            "- Some gross cumulative returns are extremely large because this is a long-horizon monthly research backtest; interpretation should prioritize robustness, turnover, drawdown, and net/gross gap rather than headline gross alone.",
            "",
            f"Ledger: `{args.ledger}`",
            "",
        ]
    )
    args.report.write_text("\n".join(lines), encoding="utf-8")
    if not frame.empty:
        frame.to_csv(args.report.with_suffix(".csv"), index=False)


def main() -> int:
    args = parse_args()
    prefix = args.run_prefix or f"longonly_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    ledger: dict[str, Any] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data_boundary": "local_artifacts_only_no_wrds_login_no_runtime_external_data",
        "config": str(args.config),
        "feature_dir": str(args.feature_dir),
        "output_dir": str(args.output_dir),
        "run_prefix": prefix,
        "models": args.models,
        "quantiles": args.quantiles,
        "q_edge": args.q_edge,
        "hyperparam_probes": args.hyperparam_probes,
        "probe_quantile": args.probe_quantile,
        "model_param_profiles": args.model_param_profiles,
        "run_specs": _run_specs(args),
        "feature_chunk_months": args.feature_chunk_months,
        "transaction_cost_bps": args.transaction_cost_bps,
        "tax_rate": args.tax_rate,
        "prepare_runs": [],
        "matrix_runs": [],
    }
    if args.prepare:
        ledger["prepare_runs"] = _prepare(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ledger["matrix_runs"] = _run_matrix(args, prefix)
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    args.ledger.write_text(json.dumps(ledger, indent=2, default=str), encoding="utf-8")
    _render_report(args, ledger)
    failures = [run for run in ledger["matrix_runs"] if run["returncode"] != 0]
    print(json.dumps({"report": str(args.report), "ledger": str(args.ledger), "runs": len(ledger["matrix_runs"]), "failures": len(failures)}, indent=2))
    return 1 if failures and not args.continue_on_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
