#!/usr/bin/env python3
# pyright: reportAny=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportExplicitAny=false, reportMissingImports=false, reportMissingTypeStubs=false, reportReturnType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false
"""Read-only Streamlit dashboard for DDQM2-lite smoke artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_DIR = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "experiments" / "smoke_lgbm"
DEFAULT_FACTOR_RETURNS = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "factor_long_short_returns_smoke.parquet"
DEFAULT_MODEL_DATASET = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "macro_factor_model_ready_smoke.parquet"
REQUIRED_EXPERIMENT_FILES = (
    "metrics.json",
    "manifest.json",
    "predictions.parquet",
    "feature_importance.csv",
)
PROTOTYPE_CAVEAT = (
    "DDQM2-lite prototype only: these views read public yfinance/current-membership smoke artifacts. "
    "They are not survivorship-bias-free, tradable, or research-grade performance evidence."
)
SMOKE_COMMANDS = (
    "PYTHONPATH=src python scripts/build_yfinance_price_panel.py --tickers AAPL MSFT SPY --start-date 2020-01-01 "
    "--end-date 2020-06-30 --output prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet\n"
    "PYTHONPATH=src python scripts/build_yfinance_factor_scores.py --price-panel prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet "
    "--output prototypes/yfinance_sp500/factor_scores_smoke.parquet\n"
    "PYTHONPATH=src python scripts/build_factor_long_short_returns.py --factor-scores prototypes/yfinance_sp500/factor_scores_smoke.parquet "
    "--price-panel prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet --output prototypes/yfinance_sp500/factor_long_short_returns_smoke.parquet --smoke\n"
    "PYTHONPATH=src python scripts/assemble_macro_factor_dataset.py --factor-returns prototypes/yfinance_sp500/factor_long_short_returns_smoke.parquet "
    "--macro-workbook expanded_macro_market_features.xlsx --output prototypes/yfinance_sp500/macro_factor_model_ready_smoke.parquet\n"
    "PYTHONPATH=src python scripts/train_macro_factor_lgbm_baseline.py --input prototypes/yfinance_sp500/macro_factor_model_ready_smoke.parquet "
    "--output-dir prototypes/yfinance_sp500/experiments/smoke_lgbm --smoke"
)


def read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, f"Missing JSON artifact: {path}"
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON artifact {path}: {exc}"
    except OSError as exc:
        return None, f"Could not read JSON artifact {path}: {exc}"
    if not isinstance(payload, dict):
        return None, f"JSON artifact must contain an object: {path}"
    return payload, None


def read_table(path: Path) -> tuple[pd.DataFrame | None, str | None]:
    try:
        if path.suffix == ".parquet":
            return pd.read_parquet(path), None
        if path.suffix == ".csv":
            return pd.read_csv(path), None
    except FileNotFoundError:
        return None, f"Missing table artifact: {path}"
    except (OSError, ValueError, ImportError) as exc:
        return None, f"Could not read table artifact {path}: {exc}"
    return None, f"Unsupported table extension for {path}; expected .parquet or .csv"


def as_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def relative_label(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path)


def show_missing_artifacts(experiment_dir: Path, factor_returns_path: Path, model_dataset_path: Path) -> None:
    expected = [experiment_dir / filename for filename in REQUIRED_EXPERIMENT_FILES]
    expected.extend([factor_returns_path, model_dataset_path])
    st.error("Some DDQM2-lite artifacts are missing or unreadable. The dashboard is read-only and will not generate them for you.")
    st.markdown("**Expected files**")
    st.code("\n".join(relative_label(path) for path in expected), language="text")
    st.markdown("**Smoke commands to generate artifacts outside the dashboard**")
    st.code(SMOKE_COMMANDS, language="bash")


def metrics_to_frame(metrics: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split_name in ("train", "validation"):
        split_metrics = metrics.get(split_name, {})
        if not isinstance(split_metrics, dict):
            continue
        for model_name, model_metrics in split_metrics.items():
            if isinstance(model_metrics, dict):
                row = {"split": split_name, "model": model_name}
                row.update(model_metrics)
                rows.append(row)
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    metric_columns = [column for column in frame.columns if column not in {"split", "model"}]
    for column in metric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def summarize_manifest(manifest: dict[str, Any]) -> pd.DataFrame:
    row_counts = manifest.get("row_counts", {}) if isinstance(manifest.get("row_counts"), dict) else {}
    fields = {
        "run_id": manifest.get("run_id"),
        "created_at_utc": manifest.get("created_at_utc"),
        "split_method": manifest.get("split_method"),
        "train_dates": f"{manifest.get('train_start_date', 'n/a')} to {manifest.get('train_end_date', 'n/a')}",
        "validation_dates": f"{manifest.get('validation_start_date', 'n/a')} to {manifest.get('validation_end_date', 'n/a')}",
        "rows_train": row_counts.get("train"),
        "rows_validation": row_counts.get("validation"),
        "factor_count": manifest.get("factor_count"),
        "feature_count": len(manifest.get("feature_columns", [])) if isinstance(manifest.get("feature_columns"), list) else None,
        "input_artifact_path": manifest.get("input_artifact_path"),
    }
    return pd.DataFrame([fields])


def validation_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    data = predictions.copy()
    if "formation_date" in data.columns:
        data["formation_date"] = pd.to_datetime(data["formation_date"], errors="coerce")
    if "split" in data.columns:
        valid = data.loc[data["split"].astype(str).eq("validation"), :].copy()
        return valid if not valid.empty else data
    return data


def regression_metrics(group: pd.DataFrame) -> pd.Series:
    actual = pd.to_numeric(group["target_long_short_return"], errors="coerce")
    predicted = pd.to_numeric(group["prediction"], errors="coerce")
    usable = pd.DataFrame({"actual": actual, "predicted": predicted}).dropna()
    if usable.empty:
        return pd.Series({"rows": 0, "mae": np.nan, "rmse": np.nan, "r2": np.nan, "pearson_ic": np.nan})
    residual = usable["actual"] - usable["predicted"]
    total_sum_squares = float(((usable["actual"] - usable["actual"].mean()) ** 2).sum())
    residual_sum_squares = float((residual**2).sum())
    r2 = 1.0 - residual_sum_squares / total_sum_squares if total_sum_squares > 0 else np.nan
    ic = usable["actual"].corr(usable["predicted"]) if usable["actual"].nunique() > 1 and usable["predicted"].nunique() > 1 else np.nan
    return pd.Series(
        {
            "rows": int(len(usable)),
            "mae": float(residual.abs().mean()),
            "rmse": float(np.sqrt((residual**2).mean())),
            "r2": r2,
            "pearson_ic": ic,
        }
    )


def factor_metric_breakdown(predictions: pd.DataFrame) -> pd.DataFrame:
    required = {"factor_name", "target_long_short_return", "prediction"}
    if not required.issubset(predictions.columns):
        return pd.DataFrame()
    valid = validation_predictions(predictions)
    return valid.groupby("factor_name", dropna=False, observed=False).apply(regression_metrics, include_groups=False).reset_index()


def date_summary(df: pd.DataFrame, column: str) -> tuple[str, str]:
    if column not in df.columns:
        return "n/a", "n/a"
    date_series = pd.to_datetime(df[column], errors="coerce")
    if not bool(date_series.notna().any()):
        return "n/a", "n/a"
    return date_series.min().strftime("%Y-%m-%d"), date_series.max().strftime("%Y-%m-%d")


def numeric_min(df: pd.DataFrame, column: str) -> float:
    if column not in df.columns:
        return float("nan")
    values = pd.to_numeric(df[column], errors="coerce")
    finite_values = values.dropna().to_numpy(dtype=float)
    return float(np.min(finite_values)) if finite_values.size else float("nan")


def coverage_table(model_dataset: pd.DataFrame | None, factor_returns: pd.DataFrame | None) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if model_dataset is not None and not model_dataset.empty:
        start_date, end_date = date_summary(model_dataset, "formation_date")
        macro_columns = [column for column in model_dataset.columns if str(column).startswith("macro__")]
        rows.append(
            {
                "artifact": "macro_factor_model_ready",
                "rows": len(model_dataset),
                "columns": model_dataset.shape[1],
                "factors": model_dataset["factor_name"].nunique() if "factor_name" in model_dataset.columns else np.nan,
                "start_date": start_date,
                "end_date": end_date,
                "missing_values": int(model_dataset.isna().sum().sum()),
                "macro_features": len(macro_columns),
                "min_long_count": np.nan,
                "min_short_count": np.nan,
            }
        )
    if factor_returns is not None and not factor_returns.empty:
        start_date, end_date = date_summary(factor_returns, "formation_date")
        rows.append(
            {
                "artifact": "factor_long_short_returns",
                "rows": len(factor_returns),
                "columns": factor_returns.shape[1],
                "factors": factor_returns["factor_name"].nunique() if "factor_name" in factor_returns.columns else np.nan,
                "start_date": start_date,
                "end_date": end_date,
                "missing_values": int(factor_returns.isna().sum().sum()),
                "macro_features": np.nan,
                "min_long_count": numeric_min(factor_returns, "long_count"),
                "min_short_count": numeric_min(factor_returns, "short_count"),
            }
        )
    return pd.DataFrame(rows)


def missingness_by_column(df: pd.DataFrame | None, artifact_name: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    missing = df.isna().sum().sort_values(ascending=False)
    return pd.DataFrame({"artifact": artifact_name, "column": missing.index, "missing_values": missing.values})


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: radial-gradient(circle at top left, #edf7f3 0, #f7f3e8 34%, #fbfaf6 72%); }
        .block-container { padding-top: 2.25rem; }
        [data-testid="stMetricValue"] { color: #173b36; }
        div[data-testid="stAlert"] { border-radius: 1rem; }
        h1, h2, h3 { letter-spacing: -0.035em; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard() -> None:
    st.set_page_config(page_title="DDQM2-lite artifact dashboard", page_icon="📊", layout="wide")
    apply_theme()
    st.title("DDQM2-lite Artifact Dashboard")
    st.caption("Read-only Streamlit view over persisted smoke artifacts. No downloads, rebuilds, retraining, or artifact mutation.")
    st.warning(PROTOTYPE_CAVEAT, icon="⚠️")

    with st.sidebar:
        st.header("Artifact paths")
        experiment_dir = as_path(st.text_input("Experiment directory", value=relative_label(DEFAULT_EXPERIMENT_DIR)))
        factor_returns_path = as_path(st.text_input("Factor returns path", value=relative_label(DEFAULT_FACTOR_RETURNS)))
        model_dataset_path = as_path(st.text_input("Model dataset path", value=relative_label(DEFAULT_MODEL_DATASET)))
        top_n = int(st.slider("Top-N feature importance", min_value=5, max_value=50, value=20, step=5))
        st.divider()
        st.caption("The dashboard only reads these paths with pandas/json/pathlib.")

    missing_files = [experiment_dir / filename for filename in REQUIRED_EXPERIMENT_FILES if not (experiment_dir / filename).exists()]
    metrics, metrics_error = read_json(experiment_dir / "metrics.json")
    manifest, manifest_error = read_json(experiment_dir / "manifest.json")
    predictions, predictions_error = read_table(experiment_dir / "predictions.parquet")
    importance, importance_error = read_table(experiment_dir / "feature_importance.csv")
    factor_returns, factor_returns_error = read_table(factor_returns_path) if factor_returns_path.exists() else (None, f"Missing table artifact: {factor_returns_path}")
    model_dataset, model_dataset_error = read_table(model_dataset_path) if model_dataset_path.exists() else (None, f"Missing table artifact: {model_dataset_path}")

    errors = [error for error in (metrics_error, manifest_error, predictions_error, importance_error, factor_returns_error, model_dataset_error) if error]
    if missing_files or errors:
        show_missing_artifacts(experiment_dir, factor_returns_path, model_dataset_path)
        if errors:
            st.markdown("**Read status**")
            st.code("\n".join(errors), language="text")
        return

    assert metrics is not None
    assert manifest is not None
    assert predictions is not None
    assert importance is not None

    st.subheader("Overview and run summary")
    warning_text = str(manifest.get("prototype_warning") or PROTOTYPE_CAVEAT)
    st.info(warning_text, icon="🧪")
    run_summary = summarize_manifest(manifest)
    counts = manifest.get("row_counts", {}) if isinstance(manifest.get("row_counts"), dict) else {}
    metric_cols = st.columns(4)
    metric_cols[0].metric("Run", str(manifest.get("run_id", "n/a")))
    metric_cols[1].metric("Factors", str(manifest.get("factor_count", "n/a")))
    metric_cols[2].metric("Validation rows", str(counts.get("validation", "n/a")))
    metric_cols[3].metric("Features", str(len(manifest.get("feature_columns", [])) if isinstance(manifest.get("feature_columns"), list) else "n/a"))
    st.dataframe(run_summary, width="stretch", hide_index=True)

    st.subheader("LightGBM vs naive baseline performance")
    metrics_frame = metrics_to_frame(metrics)
    if metrics_frame.empty:
        st.warning("metrics.json did not contain train/validation metric objects.")
    else:
        validation_metrics = metrics_frame.loc[metrics_frame["split"].eq("validation"), :].copy()
        st.dataframe(validation_metrics, width="stretch", hide_index=True)
        chart_metrics = [column for column in ("rmse", "mae", "r2", "pearson_ic", "mean_date_ic", "mean_factor_ic") if column in validation_metrics.columns]
        for metric_name in chart_metrics:
            chart_data = validation_metrics.loc[:, ["model", metric_name]].dropna().set_index("model")
            if not chart_data.empty:
                st.bar_chart(chart_data, height=240)

    st.subheader("Factor-level validation diagnostics")
    factor_breakdown = factor_metric_breakdown(predictions)
    if factor_breakdown.empty:
        st.warning("Could not compute factor-level metrics from predictions.parquet.")
    else:
        st.dataframe(factor_breakdown, width="stretch", hide_index=True)
        if "rmse" in factor_breakdown.columns:
            st.bar_chart(factor_breakdown.set_index("factor_name")[["rmse"]], height=280)

    st.subheader("Long-short factor returns")
    if factor_returns is not None and not factor_returns.empty and {"formation_date", "factor_name", "long_short_return"}.issubset(factor_returns.columns):
        returns = factor_returns.copy()
        returns["formation_date"] = pd.to_datetime(returns["formation_date"], errors="coerce")
        pivot = returns.pivot_table(index="formation_date", columns="factor_name", values="long_short_return", aggfunc="mean").sort_index()
        st.line_chart(pivot, height=280)
        cumulative = (1.0 + pivot.fillna(0.0)).cumprod() - 1.0
        st.line_chart(cumulative, height=280)
    else:
        st.warning("Factor returns artifact is empty or missing formation_date/factor_name/long_short_return columns.")

    st.subheader("Prediction diagnostics")
    valid_predictions = validation_predictions(predictions)
    if {"target_long_short_return", "prediction"}.issubset(valid_predictions.columns):
        scatter = valid_predictions.loc[:, ["target_long_short_return", "prediction", "factor_name"]].copy()
        scatter["target_long_short_return"] = pd.to_numeric(scatter["target_long_short_return"], errors="coerce")
        scatter["prediction"] = pd.to_numeric(scatter["prediction"], errors="coerce")
        st.scatter_chart(scatter.dropna(), x="prediction", y="target_long_short_return", color="factor_name", height=360)
        residual = (scatter["target_long_short_return"] - scatter["prediction"]).dropna()
        if not residual.empty:
            bins = min(30, max(5, int(np.sqrt(len(residual)))))
            counts_hist, edges = np.histogram(residual.to_numpy(dtype=float), bins=bins)
            histogram = pd.DataFrame({"residual_bin": [f"{edges[i]:.4f} to {edges[i + 1]:.4f}" for i in range(len(counts_hist))], "rows": counts_hist})
            st.bar_chart(histogram.set_index("residual_bin"), height=260)
    else:
        st.warning("Predictions artifact is missing target/prediction columns.")

    st.subheader("Feature importance")
    if not importance.empty and {"feature", "importance", "importance_type"}.issubset(importance.columns):
        importance_type = st.radio("Importance type", sorted(importance["importance_type"].astype(str).unique()), horizontal=True)
        top_importance = importance.loc[importance["importance_type"].astype(str).eq(importance_type), ["feature", "importance"]].copy()
        top_importance["importance"] = pd.to_numeric(top_importance["importance"], errors="coerce")
        top_importance = top_importance.sort_values("importance", ascending=False).head(top_n)
        st.bar_chart(top_importance.set_index("feature"), height=420)
        st.dataframe(top_importance, width="stretch", hide_index=True)
    else:
        st.warning("Feature importance artifact is empty or missing required columns.")

    st.subheader("Data coverage, missingness, and basket counts")
    coverage = coverage_table(model_dataset, factor_returns)
    if coverage.empty:
        st.warning("No model dataset or factor return coverage could be displayed.")
    else:
        st.dataframe(coverage, width="stretch", hide_index=True)
    missingness = pd.concat(
        [
            missingness_by_column(model_dataset, "macro_factor_model_ready"),
            missingness_by_column(factor_returns, "factor_long_short_returns"),
        ],
        ignore_index=True,
    )
    if not missingness.empty:
        st.dataframe(missingness.loc[missingness["missing_values"].gt(0), :], width="stretch", hide_index=True)
    if factor_returns is not None and {"factor_name", "long_count", "short_count"}.issubset(factor_returns.columns):
        basket = factor_returns.groupby("factor_name", dropna=False).agg(
            rows=("factor_name", "size"),
            min_long_count=("long_count", "min"),
            min_short_count=("short_count", "min"),
            median_long_count=("long_count", "median"),
            median_short_count=("short_count", "median"),
        )
        st.dataframe(basket.reset_index(), width="stretch", hide_index=True)


def main() -> None:
    render_dashboard()


if __name__ == "__main__":
    main()
