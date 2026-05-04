#!/usr/bin/env python3
# pyright: reportAny=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportMissingImports=false, reportMissingTypeStubs=false, reportReturnType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnusedCallResult=false
"""Validate canonical prototype factor_scores artifacts."""

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


DEFAULT_INPUT = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "factor_scores.parquet"
DATASET_NAME = "canonical factor_scores"
METADATA_COLUMNS = (
    "factor_family",
    "lookback_days",
    "direction",
    "source_columns",
    "rank_method",
    "winsorization_method",
    "source",
    "prototype_only",
)
ALLOWED_DIRECTIONS = {"high", "low", "neutral"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a canonical factor_scores CSV or Parquet artifact.")
    parser.add_argument("dataset", nargs="?", type=Path, default=DEFAULT_INPUT, help="CSV or Parquet dataset path.")
    parser.add_argument("--smoke", action="store_true", help="Print smoke-mode context; validation rules are unchanged.")
    return parser.parse_args()


def _require_nonblank(df: pd.DataFrame, column: str) -> None:
    blank_mask = df[column].isna() | df[column].astype(str).str.strip().eq("")
    blank_count = int(blank_mask.sum())
    if blank_count:
        raise ValueError(f"{DATASET_NAME} column {column!r} contains blank values: {blank_count}")


def validate_factor_scores(df: pd.DataFrame) -> pd.DataFrame:
    schemas.require_columns(df, schemas.FACTOR_SCORES_REQUIRED_COLUMNS, DATASET_NAME)
    schemas.require_prototype_only(df, DATASET_NAME)

    data = df.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    invalid_dates = int(data["date"].isna().sum())
    if invalid_dates:
        raise ValueError(f"{DATASET_NAME} contains invalid dates: {invalid_dates}")
    data["date"] = data["date"].dt.tz_localize(None)
    schemas.require_unique_key(data, schemas.FACTOR_SCORES_KEY_COLUMNS, DATASET_NAME)

    if data.empty:
        raise ValueError(f"{DATASET_NAME} must contain at least one factor score row")

    for column in ("asset_id", "asset_id_type", "factor_name", *METADATA_COLUMNS):
        _require_nonblank(data, column)

    data["factor_value"] = pd.to_numeric(data["factor_value"], errors="coerce")
    non_finite_values = int((~np.isfinite(data["factor_value"].to_numpy(dtype=float))).sum())
    if non_finite_values:
        raise ValueError(f"{DATASET_NAME} contains non-finite factor_value rows: {non_finite_values}")

    data["lookback_days"] = pd.to_numeric(data["lookback_days"], errors="coerce")
    invalid_lookbacks = int((data["lookback_days"].isna() | (data["lookback_days"] <= 0)).sum())
    if invalid_lookbacks:
        raise ValueError(f"{DATASET_NAME} contains invalid lookback_days rows: {invalid_lookbacks}")

    invalid_directions = sorted(set(data["direction"].astype(str)).difference(ALLOWED_DIRECTIONS))
    if invalid_directions:
        raise ValueError(f"{DATASET_NAME} contains invalid direction values: {invalid_directions}")

    factor_coverage = data.groupby("factor_name", sort=True).size()
    empty_factor_count = int((factor_coverage <= 0).sum())
    if empty_factor_count or factor_coverage.empty:
        raise ValueError(f"{DATASET_NAME} has empty factor coverage")

    metadata_combinations = data.groupby("factor_name", sort=True)[list(METADATA_COLUMNS[:-1])].nunique(dropna=False)
    unstable_metadata = metadata_combinations.gt(1).any(axis=1)
    if bool(unstable_metadata.any()):
        names = sorted(metadata_combinations.index[unstable_metadata].astype(str).tolist())
        raise ValueError(f"{DATASET_NAME} has inconsistent metadata within factor_name: {names}")

    return data.sort_values(["date", "asset_id", "factor_name"]).reset_index(drop=True)


def print_validation_summary(data: pd.DataFrame, smoke: bool) -> None:
    prototype_rows = schemas.prototype_true_count(data["prototype_only"])
    duplicate_rows = int(data.duplicated(list(schemas.FACTOR_SCORES_KEY_COLUMNS)).sum())
    factor_stats = data["factor_value"].describe(percentiles=[0.01, 0.05, 0.5, 0.95, 0.99])

    print(f"Rows: {len(data)}")
    print(f"Columns: {data.shape[1]}")
    print(f"Smoke mode: {smoke}")
    print(f"Assets: {data['asset_id'].nunique()}")
    print(f"Factors: {data['factor_name'].nunique()}")
    print(f"Start date: {data['date'].min().strftime('%Y-%m-%d') if not data.empty else 'n/a'}")
    print(f"End date: {data['date'].max().strftime('%Y-%m-%d') if not data.empty else 'n/a'}")
    print(f"Duplicate (date, asset_id, factor_name) rows: {duplicate_rows}")
    print(f"Prototype-only rows: {prototype_rows}")
    print("Rows by factor:")
    print(data["factor_name"].value_counts().sort_index().to_string())
    print("Rows by factor family:")
    print(data["factor_family"].value_counts().sort_index().to_string())
    print("Date coverage by factor:")
    coverage = pd.DataFrame(data.groupby("factor_name", sort=True)["date"].agg(["min", "max", "nunique"]))
    coverage["min"] = coverage["min"].dt.strftime("%Y-%m-%d")
    coverage["max"] = coverage["max"].dt.strftime("%Y-%m-%d")
    print(coverage.to_string())
    print("Source counts:")
    print(data["source"].value_counts().sort_index().to_string())
    print("Factor value stats:")
    print(factor_stats.to_string())


def main() -> None:
    args = parse_args()
    df = schemas.read_dataset(args.dataset)
    validated = validate_factor_scores(df)
    print_validation_summary(validated, args.smoke)


if __name__ == "__main__":
    main()
