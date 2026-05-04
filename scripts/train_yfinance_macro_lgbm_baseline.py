#!/usr/bin/env python3
# pyright: reportAny=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportMissingImports=false, reportMissingTypeStubs=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnusedCallResult=false
"""Train a prototype LightGBM baseline on yfinance plus macro assembled data."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "sp500_yfinance_macro_model_ready.csv"
PROTOTYPE_WARNING = (
    "Warning: this LightGBM run uses prototype_only yfinance/current-membership data and is not "
    "survivorship-bias-free DDQM2 research performance."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a prototype LightGBM regression baseline on assembled yfinance + macro data."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="CSV or Parquet assembled dataset path.")
    parser.add_argument("--label-column", default=None, help="Label column. Defaults to first forward_return_* column.")
    parser.add_argument("--valid-fraction", type=float, default=0.2, help="Recent date fraction used for validation.")
    parser.add_argument("--min-train-rows", type=int, default=50, help="Minimum rows required in the training split.")
    parser.add_argument("--min-valid-rows", type=int, default=10, help="Minimum rows required in the validation split.")
    parser.add_argument("--n-estimators", type=int, default=500, help="Maximum number of boosting rounds.")
    parser.add_argument("--learning-rate", type=float, default=0.05, help="LightGBM learning rate.")
    parser.add_argument("--num-leaves", type=int, default=31, help="LightGBM num_leaves.")
    parser.add_argument("--early-stopping-rounds", type=int, default=50, help="Early stopping patience.")
    parser.add_argument("--seed", type=int, default=42, help="Reproducibility seed.")
    return parser.parse_args()


def read_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError("Dataset must end in .csv or .parquet")


def resolve_label_column(df: pd.DataFrame, label_column: str | None) -> str:
    if label_column is not None:
        if label_column not in df.columns:
            raise ValueError(f"Label column not found: {label_column}")
        return label_column
    candidates = [column for column in df.columns if column.startswith("forward_return_")]
    if not candidates:
        raise ValueError("No forward_return_* label column found.")
    return candidates[0]


def prototype_true_count(series: pd.Series) -> int:
    if series.dtype == bool:
        return int(series.sum())
    return int(series.astype(str).str.lower().eq("true").sum())


def prepare_model_frame(df: pd.DataFrame, label_column: str) -> tuple[pd.DataFrame, list[str]]:
    required = {"date", label_column, "prototype_only"}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    feature_columns = [column for column in df.columns if column.startswith("macro__")]
    if not feature_columns:
        raise ValueError("No macro__ feature columns found.")

    if prototype_true_count(df["prototype_only"]) != len(df):
        raise ValueError("All rows must have prototype_only=True for this prototype baseline.")

    model_frame = df.loc[:, ["date", label_column, *feature_columns]].copy()
    model_frame["date"] = pd.to_datetime(model_frame["date"], errors="coerce")
    if bool(model_frame["date"].isna().any()):
        raise ValueError("Dataset contains invalid dates.")
    model_frame = model_frame.dropna(subset=[label_column, *feature_columns]).sort_values("date")
    if model_frame.empty:
        raise ValueError("No usable rows remain after dropping missing label/features.")
    return model_frame, feature_columns


def time_holdout_split(
    model_frame: pd.DataFrame,
    valid_fraction: float,
    min_train_rows: int,
    min_valid_rows: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 < valid_fraction < 1:
        raise ValueError("valid-fraction must be in (0, 1)")

    unique_dates = pd.Series(sorted(model_frame["date"].dropna().unique()))
    if unique_dates.shape[0] < 2:
        raise ValueError("Need at least two unique dates for a time-based split.")

    valid_date_count = max(1, int(np.ceil(unique_dates.shape[0] * valid_fraction)))
    split_index = max(1, unique_dates.shape[0] - valid_date_count)
    cutoff = unique_dates.iloc[split_index]

    train_mask = model_frame["date"] < cutoff
    valid_mask = model_frame["date"] >= cutoff
    train = model_frame.loc[train_mask, :].copy()
    valid = model_frame.loc[valid_mask, :].copy()
    if len(train) < min_train_rows:
        raise ValueError(f"Training split too small: {len(train)} rows, need {min_train_rows}")
    if len(valid) < min_valid_rows:
        raise ValueError(f"Validation split too small: {len(valid)} rows, need {min_valid_rows}")
    return train, valid


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


def mean_daily_ic(valid: pd.DataFrame, label_column: str, predictions: NDArray[np.float64]) -> float:
    scored = valid.loc[:, ["date", label_column]].copy()
    scored["prediction"] = predictions
    daily_values: list[float] = []
    for _, group in scored.groupby("date"):
        if group.shape[0] < 2:
            continue
        if group[label_column].nunique() < 2 or group["prediction"].nunique() < 2:
            continue
        daily_values.append(float(group[label_column].corr(group["prediction"])))
    return float(np.mean(daily_values)) if daily_values else float("nan")


def train_baseline(
    train: pd.DataFrame,
    valid: pd.DataFrame,
    feature_columns: list[str],
    label_column: str,
    args: argparse.Namespace,
) -> tuple[NDArray[np.float64], int | None]:
    import lightgbm as lgb

    x_train = train.loc[:, feature_columns]
    y_train = train[label_column]
    x_valid = valid.loc[:, feature_columns]
    y_valid = valid[label_column]

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
        x_train,
        y_train,
        eval_set=[(x_valid, y_valid)],
        eval_metric=["rmse", "mae"],
        callbacks=[lgb.early_stopping(args.early_stopping_rounds, first_metric_only=True, verbose=False)],
    )
    predictions = model.predict(x_valid, num_iteration=model.best_iteration_)
    return np.asarray(predictions, dtype=float), model.best_iteration_


def print_run_summary(
    dataset: Path,
    label_column: str,
    feature_columns: list[str],
    train: pd.DataFrame,
    valid: pd.DataFrame,
    metrics: dict[str, float],
    daily_ic: float,
    best_iteration: int | None,
) -> None:
    print(PROTOTYPE_WARNING)
    print(f"Input: {dataset}")
    print(f"Label: {label_column}")
    print(f"Feature columns: {len(feature_columns)}")
    print(f"Train rows: {len(train)}")
    print(f"Validation rows: {len(valid)}")
    print(f"Train date range: {train['date'].min().strftime('%Y-%m-%d')} to {train['date'].max().strftime('%Y-%m-%d')}")
    print(f"Validation date range: {valid['date'].min().strftime('%Y-%m-%d')} to {valid['date'].max().strftime('%Y-%m-%d')}")
    print(f"Best iteration: {best_iteration if best_iteration is not None else 'n/a'}")
    print("Validation metrics:")
    print(f"MAE: {metrics['mae']:.8f}")
    print(f"RMSE: {metrics['rmse']:.8f}")
    print(f"R2: {metrics['r2']:.8f}")
    print(f"Pearson IC: {metrics['pearson_ic']:.8f}")
    print(f"Mean daily IC: {daily_ic:.8f}")


def main() -> None:
    args = parse_args()
    raw = read_dataset(args.input)
    label_column = resolve_label_column(raw, args.label_column)
    model_frame, feature_columns = prepare_model_frame(raw, label_column)
    train, valid = time_holdout_split(model_frame, args.valid_fraction, args.min_train_rows, args.min_valid_rows)
    predictions, best_iteration = train_baseline(train, valid, feature_columns, label_column, args)
    y_valid = valid[label_column].to_numpy(dtype=float)
    metrics = regression_metrics(y_valid, predictions)
    daily_ic = mean_daily_ic(valid, label_column, predictions)
    print_run_summary(args.input, label_column, feature_columns, train, valid, metrics, daily_ic, best_iteration)


if __name__ == "__main__":
    main()
