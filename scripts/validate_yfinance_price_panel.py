#!/usr/bin/env python3
# pyright: reportAny=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportMissingImports=false, reportMissingTypeStubs=false, reportReturnType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnusedCallResult=false
"""Validate canonical prototype yfinance price/return panels."""

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


DEFAULT_INPUT = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "canonical_price_panel.parquet"
DATASET_NAME = "canonical yfinance price panel"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a canonical yfinance prototype price panel.")
    parser.add_argument("dataset", nargs="?", type=Path, default=DEFAULT_INPUT, help="CSV or Parquet dataset path.")
    return parser.parse_args()


def _require_constant_value(df: pd.DataFrame, column: str, expected: object) -> None:
    values = df[column].dropna().unique()
    if len(values) != 1 or values[0] != expected:
        observed = sorted(str(value) for value in values)
        raise ValueError(f"{DATASET_NAME} column {column!r} must be {expected!r}; observed {observed}")


def _require_null_column(df: pd.DataFrame, column: str) -> None:
    non_null_count = int(df[column].notna().sum())
    if non_null_count:
        raise ValueError(f"{DATASET_NAME} column {column!r} must be null for yfinance prototype rows: {non_null_count}")


def _numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    values = pd.to_numeric(df[column], errors="coerce")
    invalid_count = int(values.isna().sum() - df[column].isna().sum())
    if invalid_count:
        raise ValueError(f"{DATASET_NAME} column {column!r} contains non-numeric values: {invalid_count}")
    return values


def validate_price_panel(df: pd.DataFrame) -> pd.DataFrame:
    schemas.require_columns(df, schemas.PRICE_PANEL_REQUIRED_COLUMNS, DATASET_NAME)
    schemas.require_prototype_only(df, DATASET_NAME)

    data = df.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    if bool(data["date"].isna().any()):
        invalid_count = int(data["date"].isna().sum())
        raise ValueError(f"{DATASET_NAME} contains invalid dates: {invalid_count}")
    data["date"] = data["date"].dt.tz_localize(None)
    schemas.require_unique_key(data, schemas.PRICE_PANEL_KEY_COLUMNS, DATASET_NAME)

    _require_constant_value(data, "source", "yfinance")
    _require_constant_value(data, "asset_id_type", "ticker")
    for column in ("permno", "permco", "gvkey", "delisting_return"):
        _require_null_column(data, column)

    if bool(data["asset_id"].isna().any()) or bool(data["asset_id"].astype(str).str.strip().eq("").any()):
        raise ValueError(f"{DATASET_NAME} contains blank asset_id values")
    for column in ("universe_source", "universe_asof_utc", "generated_at_utc"):
        if bool(data[column].isna().any()) or bool(data[column].astype(str).str.strip().eq("").any()):
            raise ValueError(f"{DATASET_NAME} contains blank {column} values")

    price_adjusted = _numeric_series(data, "price_adjusted")
    close = _numeric_series(data, "close")
    volume = _numeric_series(data, "volume")
    _numeric_series(data, "return_1d")
    _numeric_series(data, "total_return")

    if int(price_adjusted.isna().sum()):
        raise ValueError(f"{DATASET_NAME} contains missing price_adjusted values: {int(price_adjusted.isna().sum())}")
    if int(close.isna().sum()):
        raise ValueError(f"{DATASET_NAME} contains missing close values: {int(close.isna().sum())}")
    if bool((price_adjusted <= 0).any()) or bool((close <= 0).any()):
        raise ValueError(f"{DATASET_NAME} price_adjusted and close must be positive")
    if bool((volume.dropna() < 0).any()):
        raise ValueError(f"{DATASET_NAME} volume must be non-negative when present")

    data = data.sort_values(["asset_id", "date"]).reset_index(drop=True)
    price_adjusted = pd.to_numeric(data["price_adjusted"], errors="coerce")
    expected_return = price_adjusted.groupby(data["asset_id"]).pct_change(fill_method=None)
    observed_return = pd.to_numeric(data["return_1d"], errors="coerce")
    observed_total_return = pd.to_numeric(data["total_return"], errors="coerce")

    first_row_mask = data.groupby("asset_id", sort=False).cumcount().eq(0)
    non_first_expected_mask = ~first_row_mask & expected_return.notna()
    missing_non_first_returns = int(observed_return.loc[non_first_expected_mask].isna().sum())
    if missing_non_first_returns:
        raise ValueError(f"{DATASET_NAME} has missing non-first return_1d values: {missing_non_first_returns}")

    finite_mask = non_first_expected_mask & observed_return.notna()
    non_finite_returns = int((~np.isfinite(observed_return.loc[finite_mask].to_numpy(dtype=float))).sum())
    if non_finite_returns:
        raise ValueError(f"{DATASET_NAME} has non-finite non-first return_1d values: {non_finite_returns}")

    mismatched_returns = int(
        (
            ~np.isclose(
                observed_return.loc[finite_mask].to_numpy(dtype=float),
                expected_return.loc[finite_mask].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-12,
            )
        ).sum()
    )
    if mismatched_returns:
        raise ValueError(f"{DATASET_NAME} return_1d does not match adjusted-price pct_change rows: {mismatched_returns}")

    mismatched_total_returns = int(
        (
            ~np.isclose(
                observed_total_return.loc[finite_mask].to_numpy(dtype=float),
                observed_return.loc[finite_mask].to_numpy(dtype=float),
                rtol=1e-12,
                atol=1e-12,
            )
        ).sum()
    )
    if mismatched_total_returns:
        raise ValueError(f"{DATASET_NAME} total_return must equal return_1d for yfinance rows: {mismatched_total_returns}")

    first_row_return_count = int(observed_return.loc[first_row_mask].notna().sum())
    if first_row_return_count:
        raise ValueError(f"{DATASET_NAME} first row per asset should have missing return_1d: {first_row_return_count}")

    return data


def print_validation_summary(data: pd.DataFrame) -> None:
    prototype_rows = schemas.prototype_true_count(data["prototype_only"])
    return_stats = data["return_1d"].describe(percentiles=[0.01, 0.05, 0.5, 0.95, 0.99])

    print(f"Rows: {len(data)}")
    print(f"Columns: {data.shape[1]}")
    print(f"Assets: {data['asset_id'].nunique()}")
    print(f"Start date: {data['date'].min().strftime('%Y-%m-%d') if not data.empty else 'n/a'}")
    print(f"End date: {data['date'].max().strftime('%Y-%m-%d') if not data.empty else 'n/a'}")
    print(f"Duplicate (date, asset_id) rows: {int(data.duplicated(list(schemas.PRICE_PANEL_KEY_COLUMNS)).sum())}")
    print(f"Prototype-only rows: {prototype_rows}")
    print("Source counts:")
    print(data["source"].value_counts().sort_index().to_string())
    print("Asset ID type counts:")
    print(data["asset_id_type"].value_counts().sort_index().to_string())
    print("Return stats:")
    print(return_stats.to_string())


def main() -> None:
    args = parse_args()
    df = schemas.read_dataset(args.dataset)
    validated = validate_price_panel(df)
    print_validation_summary(validated)


if __name__ == "__main__":
    main()
