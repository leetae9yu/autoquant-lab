#!/usr/bin/env python3
# pyright: reportAny=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportMissingImports=false, reportMissingTypeStubs=false, reportReturnType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnusedCallResult=false
"""Validate canonical factor long-short forward return label artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from autoquant_lab import schemas


DEFAULT_INPUT = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "factor_long_short_returns.parquet"
DATASET_NAME = "canonical factor_long_short_returns"
METADATA_COLUMNS = (
    "return_source",
    "label_source",
    "factor_family",
    "lookback_days",
    "direction",
    "rank_method",
    "winsorization_method",
    "source",
    "prototype_only",
)
NUMERIC_RETURN_COLUMNS = ("long_return", "short_return", "long_short_return")
ALLOWED_DIRECTIONS = {"high", "low", "neutral"}
FULL_MIN_BASKET_SIZE = 25
SMOKE_MIN_BASKET_SIZE = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a canonical factor_long_short_returns CSV or Parquet artifact.")
    parser.add_argument("dataset", nargs="?", type=Path, default=DEFAULT_INPUT, help="CSV or Parquet dataset path.")
    parser.add_argument("--smoke", action="store_true", help="Allow smoke-friendly minimum basket size of 2.")
    return parser.parse_args()


def _require_nonblank(df: pd.DataFrame, column: str) -> None:
    blank_mask = df[column].isna() | df[column].astype(str).str.strip().eq("")
    blank_count = int(blank_mask.sum())
    if blank_count:
        raise ValueError(f"{DATASET_NAME} column {column!r} contains blank values: {blank_count}")


def _numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    values = pd.to_numeric(df[column], errors="coerce")
    invalid_count = int(values.isna().sum() - df[column].isna().sum())
    if invalid_count:
        raise ValueError(f"{DATASET_NAME} column {column!r} contains non-numeric values: {invalid_count}")
    return values


def validate_factor_long_short_returns(df: pd.DataFrame, smoke: bool) -> pd.DataFrame:
    schemas.require_columns(df, schemas.FACTOR_LONG_SHORT_REQUIRED_COLUMNS, DATASET_NAME)
    schemas.require_prototype_only(df, DATASET_NAME)

    data = df.copy()
    if data.empty:
        raise ValueError(f"{DATASET_NAME} must contain at least one label row")

    for column in ("formation_date", "forward_return_start", "forward_return_end"):
        data[column] = pd.to_datetime(data[column], errors="coerce")
        invalid_dates = int(data[column].isna().sum())
        if invalid_dates:
            raise ValueError(f"{DATASET_NAME} column {column!r} contains invalid dates: {invalid_dates}")
        data[column] = data[column].dt.tz_localize(None)

    schemas.require_unique_key(data, schemas.FACTOR_LONG_SHORT_KEY_COLUMNS, DATASET_NAME)

    for column in ("factor_name", *METADATA_COLUMNS):
        _require_nonblank(data, column)

    data["horizon_trading_days"] = _numeric_series(data, "horizon_trading_days")
    data["long_quantile"] = _numeric_series(data, "long_quantile")
    data["short_quantile"] = _numeric_series(data, "short_quantile")
    data["long_count"] = _numeric_series(data, "long_count")
    data["short_count"] = _numeric_series(data, "short_count")
    data["lookback_days"] = _numeric_series(data, "lookback_days")
    for column in NUMERIC_RETURN_COLUMNS:
        data[column] = _numeric_series(data, column)

    non_positive_horizons = int((data["horizon_trading_days"] <= 0).sum())
    if non_positive_horizons:
        raise ValueError(f"{DATASET_NAME} contains non-positive horizon_trading_days rows: {non_positive_horizons}")
    invalid_quantiles = int(
        (~((0.0 < data["short_quantile"]) & (data["short_quantile"] < data["long_quantile"]) & (data["long_quantile"] < 1.0))).sum()
    )
    if invalid_quantiles:
        raise ValueError(f"{DATASET_NAME} contains invalid long/short quantile rows: {invalid_quantiles}")

    leakage_rows = int((data["forward_return_start"] <= data["formation_date"]).sum())
    if leakage_rows:
        raise ValueError(f"{DATASET_NAME} has forward_return_start <= formation_date rows: {leakage_rows}")
    invalid_end_rows = int((data["forward_return_end"] < data["forward_return_start"]).sum())
    if invalid_end_rows:
        raise ValueError(f"{DATASET_NAME} has forward_return_end < forward_return_start rows: {invalid_end_rows}")

    min_basket_size = SMOKE_MIN_BASKET_SIZE if smoke else FULL_MIN_BASKET_SIZE
    invalid_long_counts = int((data["long_count"] < min_basket_size).sum())
    invalid_short_counts = int((data["short_count"] < min_basket_size).sum())
    if invalid_long_counts or invalid_short_counts:
        message = (
            f"{DATASET_NAME} has basket counts below {min_basket_size}: "
            f"long={invalid_long_counts}, short={invalid_short_counts}"
        )
        raise ValueError(message)
    non_integer_counts = int(((data["long_count"] % 1 != 0) | (data["short_count"] % 1 != 0)).sum())
    if non_integer_counts:
        raise ValueError(f"{DATASET_NAME} contains non-integer basket count rows: {non_integer_counts}")

    for column in NUMERIC_RETURN_COLUMNS:
        non_finite = int((~np.isfinite(data[column].to_numpy(dtype=float))).sum())
        if non_finite:
            raise ValueError(f"{DATASET_NAME} column {column!r} contains non-finite rows: {non_finite}")
    arithmetic_mismatches = int(
        (~np.isclose(data["long_short_return"], data["long_return"] - data["short_return"], rtol=1e-9, atol=1e-12)).sum()
    )
    if arithmetic_mismatches:
        raise ValueError(f"{DATASET_NAME} long_short_return != long_return - short_return rows: {arithmetic_mismatches}")

    invalid_lookbacks = int((data["lookback_days"].isna() | (data["lookback_days"] <= 0)).sum())
    if invalid_lookbacks:
        raise ValueError(f"{DATASET_NAME} contains invalid lookback_days rows: {invalid_lookbacks}")
    invalid_directions = sorted(set(data["direction"].astype(str)).difference(ALLOWED_DIRECTIONS))
    if invalid_directions:
        raise ValueError(f"{DATASET_NAME} contains invalid direction values: {invalid_directions}")

    metadata_combinations = data.groupby("factor_name", sort=True)[list(METADATA_COLUMNS[:-1])].nunique(dropna=False)
    unstable_metadata = metadata_combinations.gt(1).any(axis=1)
    if bool(unstable_metadata.any()):
        names = sorted(metadata_combinations.index[unstable_metadata].astype(str).tolist())
        raise ValueError(f"{DATASET_NAME} has inconsistent metadata within factor_name: {names}")

    return data.sort_values(["formation_date", "factor_name", "horizon_trading_days"]).reset_index(drop=True)


def print_validation_summary(data: pd.DataFrame, smoke: bool) -> None:
    prototype_rows = schemas.prototype_true_count(data["prototype_only"])
    duplicate_rows = int(data.duplicated(list(schemas.FACTOR_LONG_SHORT_KEY_COLUMNS)).sum())
    return_stats = data["long_short_return"].describe(percentiles=[0.01, 0.05, 0.5, 0.95, 0.99])

    print(f"Rows: {len(data)}")
    print(f"Columns: {data.shape[1]}")
    print(f"Smoke mode: {smoke}")
    print(f"Factors: {data['factor_name'].nunique()}")
    print(f"Start formation date: {data['formation_date'].min().strftime('%Y-%m-%d') if not data.empty else 'n/a'}")
    print(f"End formation date: {data['formation_date'].max().strftime('%Y-%m-%d') if not data.empty else 'n/a'}")
    print(f"Duplicate (formation_date, factor_name, horizon_trading_days) rows: {duplicate_rows}")
    print(f"Prototype-only rows: {prototype_rows}")
    print("Rows by factor:")
    print(data["factor_name"].value_counts().sort_index().to_string())
    print("Rows by factor family:")
    print(data["factor_family"].value_counts().sort_index().to_string())
    print("Basket count summary:")
    print(data[["long_count", "short_count"]].describe().to_string())
    print("Forward window summary:")
    forward_windows = data.groupby(["forward_return_start", "forward_return_end"], sort=True).size().to_frame("rows").reset_index()
    forward_windows["forward_return_start"] = forward_windows["forward_return_start"].dt.strftime("%Y-%m-%d")
    forward_windows["forward_return_end"] = forward_windows["forward_return_end"].dt.strftime("%Y-%m-%d")
    print(forward_windows.to_string(index=False))
    print("Source counts:")
    print(data["source"].value_counts().sort_index().to_string())
    print("Long-short return stats:")
    print(return_stats.to_string())


def main() -> None:
    args = parse_args()
    df = schemas.read_dataset(args.dataset)
    validated = validate_factor_long_short_returns(df, args.smoke)
    print_validation_summary(validated, args.smoke)


if __name__ == "__main__":
    main()
