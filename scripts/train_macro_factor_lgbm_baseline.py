#!/usr/bin/env python3
# pyright: reportAny=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportExplicitAny=false, reportMissingImports=false, reportMissingTypeStubs=false, reportReturnType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnusedCallResult=false
"""Train a macro-factor LightGBM baseline and persist experiment artifacts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
from numpy.typing import NDArray
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from autoquant_lab import schemas


DEFAULT_INPUT = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "macro_factor_model_ready.parquet"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "experiments" / "macro_factor_lgbm"
TARGET_COLUMN = "target_long_short_return"
DATASET_NAME = "canonical macro_factor_model_ready"
PROTOTYPE_WARNING = (
    "Warning: this DDQM2-lite LightGBM run uses prototype_only public yfinance/current-membership "
    "factor labels and macro data plumbing. It is not survivorship-bias-free, tradable, or research-grade performance."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a pooled macro-factor LightGBM baseline with persisted artifacts.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Macro-factor model-ready CSV or Parquet path.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Experiment artifact output directory.")
    parser.add_argument("--valid-fraction", type=float, default=0.2, help="Recent formation-date fraction for validation.")
    parser.add_argument("--min-train-rows", type=int, default=50, help="Minimum rows required in the training split.")
    parser.add_argument("--min-valid-rows", type=int, default=10, help="Minimum rows required in the validation split.")
    parser.add_argument("--n-estimators", type=int, default=500, help="Maximum boosting rounds.")
    parser.add_argument("--learning-rate", type=float, default=0.05, help="LightGBM learning rate.")
    parser.add_argument("--num-leaves", type=int, default=31, help="LightGBM num_leaves.")
    parser.add_argument("--early-stopping-rounds", type=int, default=50, help="Early stopping patience.")
    parser.add_argument("--seed", type=int, default=42, help="Reproducibility seed.")
    parser.add_argument("--smoke", action="store_true", help="Use relaxed row counts and fewer estimators for tiny smoke artifacts.")
    return parser.parse_args()


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        float_value = float(value)
        return float_value if np.isfinite(float_value) else None
    if isinstance(value, float):
        return value if np.isfinite(value) else None
    if isinstance(value, (pd.Timestamp, datetime)):
        return pd.Timestamp(value).strftime("%Y-%m-%d")
    if isinstance(value, Path):
        return str(value)
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(json_ready(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def apply_smoke_overrides(args: argparse.Namespace) -> argparse.Namespace:
    if not args.smoke:
        return args
    args.min_train_rows = min(args.min_train_rows, 20)
    args.min_valid_rows = min(args.min_valid_rows, 5)
    args.n_estimators = min(args.n_estimators, 25)
    args.early_stopping_rounds = min(args.early_stopping_rounds, 5)
    return args


def get_git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    commit = result.stdout.strip()
    return commit or None


def prepare_model_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    schemas.require_columns(df, schemas.MACRO_FACTOR_MODEL_REQUIRED_COLUMNS, DATASET_NAME)
    schemas.require_prototype_only(df, DATASET_NAME)
    schemas.require_unique_key(df, schemas.MACRO_FACTOR_MODEL_KEY_COLUMNS, DATASET_NAME)

    macro_columns = sorted(column for column in df.columns if column.startswith(schemas.MACRO_FEATURE_PREFIX))
    if not macro_columns:
        raise ValueError(f"{DATASET_NAME} has no {schemas.MACRO_FEATURE_PREFIX} feature columns")

    data = df.copy()
    data["formation_date"] = pd.to_datetime(data["formation_date"], errors="coerce")
    data["macro_asof_date"] = pd.to_datetime(data["macro_asof_date"], errors="coerce")
    if bool(data["formation_date"].isna().any()):
        raise ValueError(f"{DATASET_NAME} contains invalid formation_date rows")
    if bool(data["macro_asof_date"].isna().any()):
        raise ValueError(f"{DATASET_NAME} contains invalid macro_asof_date rows")
    data["formation_date"] = data["formation_date"].dt.tz_localize(None)
    data["macro_asof_date"] = data["macro_asof_date"].dt.tz_localize(None)

    data[TARGET_COLUMN] = pd.to_numeric(data[TARGET_COLUMN], errors="coerce")
    data.loc[:, macro_columns] = data.loc[:, macro_columns].apply(pd.to_numeric, errors="coerce")
    required_model_columns = ["formation_date", "factor_name", "horizon_trading_days", TARGET_COLUMN, "prototype_only", *macro_columns]
    model_frame = data.loc[:, required_model_columns].dropna(subset=[TARGET_COLUMN, *macro_columns]).copy()
    if model_frame.empty:
        raise ValueError("No usable rows remain after dropping missing target/features.")

    factor_names = sorted(model_frame["factor_name"].astype(str).unique().tolist())
    model_frame["factor_name"] = pd.Categorical(model_frame["factor_name"].astype(str), categories=factor_names, ordered=True)
    encoded = pd.get_dummies(model_frame["factor_name"], prefix="factor", dtype=float)
    encoded = encoded.reindex(columns=[f"factor_{name}" for name in factor_names], fill_value=0.0)
    model_frame = pd.concat([model_frame.reset_index(drop=True), encoded.reset_index(drop=True)], axis=1)
    factor_feature_columns = list(encoded.columns)
    feature_columns = [*macro_columns, *factor_feature_columns]
    model_frame = model_frame.sort_values(["formation_date", "factor_name", "horizon_trading_days"]).reset_index(drop=True)
    return model_frame, feature_columns, macro_columns


def time_holdout_split(
    model_frame: pd.DataFrame,
    valid_fraction: float,
    min_train_rows: int,
    min_valid_rows: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    if not 0 < valid_fraction < 1:
        raise ValueError("valid-fraction must be in (0, 1)")
    unique_dates = pd.Series(sorted(model_frame["formation_date"].dropna().unique()))
    if unique_dates.shape[0] < 2:
        raise ValueError("Need at least two unique formation dates for a time-based split.")
    valid_date_count = max(1, int(np.ceil(unique_dates.shape[0] * valid_fraction)))
    split_index = max(1, unique_dates.shape[0] - valid_date_count)
    cutoff = pd.Timestamp(unique_dates.iloc[split_index])
    train = model_frame.loc[model_frame["formation_date"] < cutoff, :].copy()
    valid = model_frame.loc[model_frame["formation_date"] >= cutoff, :].copy()
    if len(train) < min_train_rows:
        raise ValueError(f"Training split too small: {len(train)} rows, need {min_train_rows}")
    if len(valid) < min_valid_rows:
        raise ValueError(f"Validation split too small: {len(valid)} rows, need {min_valid_rows}")
    return train, valid, cutoff


def regression_metrics(y_true: NDArray[np.float64], y_pred: NDArray[np.float64]) -> dict[str, float]:
    residual = y_true - y_pred
    mae = float(np.mean(np.abs(residual)))
    rmse = float(np.sqrt(np.mean(np.square(residual))))
    total_sum_squares = float(np.sum(np.square(y_true - np.mean(y_true))))
    residual_sum_squares = float(np.sum(np.square(residual)))
    r2 = float(1.0 - residual_sum_squares / total_sum_squares) if total_sum_squares > 0 else float("nan")
    if np.std(y_true) == 0 or np.std(y_pred) == 0:
        pearson_ic = float("nan")
    else:
        pearson_ic = float(np.corrcoef(y_true, y_pred)[0, 1])
    return {"mae": mae, "rmse": rmse, "r2": r2, "pearson_ic": pearson_ic}


def grouped_mean_ic(scored: pd.DataFrame, group_column: str) -> float:
    values: list[float] = []
    for _, group in scored.groupby(group_column, observed=False):
        if group.shape[0] < 2:
            continue
        if group[TARGET_COLUMN].nunique() < 2 or group["prediction"].nunique() < 2:
            continue
        values.append(float(group[TARGET_COLUMN].corr(group["prediction"])))
    return float(np.mean(values)) if values else float("nan")


def evaluate_predictions(frame: pd.DataFrame, predictions: NDArray[np.float64]) -> dict[str, float]:
    scored = frame.loc[:, ["formation_date", "factor_name", TARGET_COLUMN]].copy()
    scored["prediction"] = predictions
    metrics = regression_metrics(scored[TARGET_COLUMN].to_numpy(dtype=float), predictions)
    metrics["mean_date_ic"] = grouped_mean_ic(scored, "formation_date")
    metrics["mean_factor_ic"] = grouped_mean_ic(scored, "factor_name")
    return metrics


def naive_predictions(train: pd.DataFrame, valid: pd.DataFrame, full_frame: pd.DataFrame) -> dict[str, NDArray[np.float64]]:
    train_mean = float(train[TARGET_COLUMN].mean())
    predictions = {
        "zero_return": np.zeros(len(valid), dtype=float),
        "train_mean_return": np.full(len(valid), train_mean, dtype=float),
    }

    history = full_frame.loc[:, ["formation_date", "factor_name", TARGET_COLUMN]].copy()
    history = history.sort_values(["factor_name", "formation_date"])
    history["last_factor_return"] = history.groupby("factor_name", observed=False)[TARGET_COLUMN].shift(1)
    valid_with_history = valid.loc[:, ["formation_date", "factor_name"]].merge(
        history.loc[:, ["formation_date", "factor_name", "last_factor_return"]],
        on=["formation_date", "factor_name"],
        how="left",
    )
    if not bool(valid_with_history["last_factor_return"].isna().any()):
        predictions["last_factor_return"] = valid_with_history["last_factor_return"].to_numpy(dtype=float)
    return predictions


def train_lgbm(
    train: pd.DataFrame,
    valid: pd.DataFrame,
    feature_columns: list[str],
    args: argparse.Namespace,
) -> tuple[Any, NDArray[np.float64], NDArray[np.float64], int | None]:
    import lightgbm as lgb

    model = lgb.LGBMRegressor(
        objective="regression",
        n_estimators=args.n_estimators,
        learning_rate=args.learning_rate,
        num_leaves=args.num_leaves,
        random_state=args.seed,
        deterministic=True,
        force_col_wise=True,
        n_jobs=-1,
        verbosity=-1,
    )
    model.fit(
        train.loc[:, feature_columns],
        train[TARGET_COLUMN],
        eval_set=[(valid.loc[:, feature_columns], valid[TARGET_COLUMN])],
        eval_metric=["rmse", "mae"],
        callbacks=[lgb.early_stopping(args.early_stopping_rounds, first_metric_only=True, verbose=False)],
    )
    train_predictions = np.asarray(model.predict(train.loc[:, feature_columns], num_iteration=model.best_iteration_), dtype=float)
    valid_predictions = np.asarray(model.predict(valid.loc[:, feature_columns], num_iteration=model.best_iteration_), dtype=float)
    return model, train_predictions, valid_predictions, model.best_iteration_


def build_predictions_frame(
    run_id: str,
    train: pd.DataFrame,
    valid: pd.DataFrame,
    train_predictions: NDArray[np.float64],
    valid_predictions: NDArray[np.float64],
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for split_name, split_frame, predictions in (
        ("train", train, train_predictions),
        ("validation", valid, valid_predictions),
    ):
        output = split_frame.loc[:, ["formation_date", "factor_name", "horizon_trading_days", TARGET_COLUMN, "prototype_only"]].copy()
        output["prediction"] = predictions
        output["split"] = split_name
        output["run_id"] = run_id
        frames.append(output)
    predictions_frame = pd.concat(frames, ignore_index=True)
    return predictions_frame.loc[:, schemas.EXPERIMENT_PREDICTIONS_REQUIRED_COLUMNS]


def build_feature_importance_frame(run_id: str, model: Any, feature_columns: list[str]) -> pd.DataFrame:
    gain = pd.DataFrame(
        {
            "feature": feature_columns,
            "importance": model.booster_.feature_importance(importance_type="gain"),
            "importance_type": "gain",
            "run_id": run_id,
        }
    )
    split = pd.DataFrame(
        {
            "feature": feature_columns,
            "importance": model.booster_.feature_importance(importance_type="split"),
            "importance_type": "split",
            "run_id": run_id,
        }
    )
    importance = pd.concat([gain, split], ignore_index=True)
    return importance.loc[:, schemas.EXPERIMENT_FEATURE_IMPORTANCE_REQUIRED_COLUMNS]


def artifact_path(output_dir: Path, filename: str) -> str:
    return str((output_dir / filename).resolve())


def print_run_summary(output_dir: Path, metrics: dict[str, Any], train: pd.DataFrame, valid: pd.DataFrame, feature_columns: list[str]) -> None:
    print(PROTOTYPE_WARNING)
    print(f"Output dir: {output_dir}")
    print(f"Feature columns: {len(feature_columns)}")
    print(f"Train rows: {len(train)}")
    print(f"Validation rows: {len(valid)}")
    print(f"Train date range: {train['formation_date'].min().strftime('%Y-%m-%d')} to {train['formation_date'].max().strftime('%Y-%m-%d')}")
    print(f"Validation date range: {valid['formation_date'].min().strftime('%Y-%m-%d')} to {valid['formation_date'].max().strftime('%Y-%m-%d')}")
    print("Validation metrics:")
    for model_name, model_metrics in metrics["validation"].items():
        print(f"{model_name}: RMSE={model_metrics['rmse']:.8f}, MAE={model_metrics['mae']:.8f}, R2={model_metrics['r2']:.8f}, IC={model_metrics['pearson_ic']:.8f}")


def main() -> None:
    args = apply_smoke_overrides(parse_args())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_id = args.output_dir.name

    raw = schemas.read_dataset(args.input)
    model_frame, feature_columns, macro_columns = prepare_model_frame(raw)
    train, valid, cutoff = time_holdout_split(model_frame, args.valid_fraction, args.min_train_rows, args.min_valid_rows)
    model, train_predictions, valid_predictions, best_iteration = train_lgbm(train, valid, feature_columns, args)

    validation_metrics: dict[str, dict[str, float]] = {"lightgbm": evaluate_predictions(valid, valid_predictions)}
    baseline_predictions = naive_predictions(train, valid, model_frame)
    validation_metrics.update({name: evaluate_predictions(valid, predictions) for name, predictions in baseline_predictions.items()})
    train_metrics = {"lightgbm": evaluate_predictions(train, train_predictions)}
    metrics = {
        "target_column": TARGET_COLUMN,
        "primary_metric": "validation.lightgbm.rmse",
        "best_iteration": best_iteration,
        "validation": validation_metrics,
        "train": train_metrics,
        "baseline_names": sorted(baseline_predictions),
    }

    predictions_frame = build_predictions_frame(run_id, train, valid, train_predictions, valid_predictions)
    importance_frame = build_feature_importance_frame(run_id, model, feature_columns)

    config = {
        "run_id": run_id,
        "input": str(args.input.resolve()),
        "output_dir": str(args.output_dir.resolve()),
        "valid_fraction": args.valid_fraction,
        "min_train_rows": args.min_train_rows,
        "min_valid_rows": args.min_valid_rows,
        "n_estimators": args.n_estimators,
        "learning_rate": args.learning_rate,
        "num_leaves": args.num_leaves,
        "early_stopping_rounds": args.early_stopping_rounds,
        "seed": args.seed,
        "smoke": bool(args.smoke),
        "factor_encoding": "deterministic_pandas_one_hot",
        "target_column": TARGET_COLUMN,
    }
    manifest = {
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": get_git_commit(),
        "input_artifact_path": str(args.input.resolve()),
        "output_dir": str(args.output_dir.resolve()),
        "split_method": "time_holdout_by_formation_date_no_random_split",
        "split_boundary_date": cutoff.strftime("%Y-%m-%d"),
        "train_start_date": train["formation_date"].min().strftime("%Y-%m-%d"),
        "train_end_date": train["formation_date"].max().strftime("%Y-%m-%d"),
        "validation_start_date": valid["formation_date"].min().strftime("%Y-%m-%d"),
        "validation_end_date": valid["formation_date"].max().strftime("%Y-%m-%d"),
        "target_column": TARGET_COLUMN,
        "feature_columns": feature_columns,
        "macro_feature_columns": macro_columns,
        "factor_encoding": "deterministic_pandas_one_hot",
        "row_counts": {"train": len(train), "validation": len(valid), "total": len(model_frame)},
        "factor_count": int(model_frame["factor_name"].nunique()),
        "metrics_artifact": artifact_path(args.output_dir, "metrics.json"),
        "predictions_artifact": artifact_path(args.output_dir, "predictions.parquet"),
        "feature_importance_artifact": artifact_path(args.output_dir, "feature_importance.csv"),
        "config_artifact": artifact_path(args.output_dir, "config.json"),
        "prototype_warning": PROTOTYPE_WARNING,
    }

    write_json(args.output_dir / "config.json", config)
    write_json(args.output_dir / "metrics.json", metrics)
    schemas.write_dataset(predictions_frame, args.output_dir / "predictions.parquet")
    importance_frame.to_csv(args.output_dir / "feature_importance.csv", index=False)
    write_json(args.output_dir / "manifest.json", manifest)
    print_run_summary(args.output_dir, metrics, train, valid, feature_columns)


if __name__ == "__main__":
    main()
