#!/usr/bin/env python3
# pyright: reportAny=false, reportAttributeAccessIssue=false, reportMissingTypeStubs=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnusedCallResult=false
"""Validate prototype yfinance S&P 500 labels."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "sp500_yfinance_labels.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print validation stats for yfinance S&P 500 prototype labels.")
    parser.add_argument("dataset", nargs="?", type=Path, default=DEFAULT_INPUT, help="CSV or Parquet dataset path.")
    parser.add_argument("--label-column", default=None, help="Label column to validate. Defaults to first forward_return_* column.")
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


def print_validation_stats(df: pd.DataFrame, label_column: str) -> None:
    required_columns = {"date", "ticker", "yahoo_ticker", "adj_close", "volume", label_column, "prototype_only"}
    missing_columns = sorted(required_columns.difference(df.columns))
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    duplicate_count = int(df.duplicated(["date", "ticker"]).sum())
    null_counts = df.loc[:, ["date", "ticker", "adj_close", "volume", label_column]].isna().sum()
    label_stats = df[label_column].describe(percentiles=[0.01, 0.05, 0.5, 0.95, 0.99])

    print(f"Rows: {len(df)}")
    print(f"Tickers: {df['ticker'].nunique()}")
    print(f"Start date: {df['date'].min().strftime('%Y-%m-%d') if not df.empty else 'n/a'}")
    print(f"End date: {df['date'].max().strftime('%Y-%m-%d') if not df.empty else 'n/a'}")
    print(f"Duplicate date/ticker rows: {duplicate_count}")
    print(f"Prototype-only rows: {int(df['prototype_only'].sum()) if df['prototype_only'].dtype == bool else df['prototype_only'].astype(str).str.lower().eq('true').sum()}")
    print("Missing values:")
    print(null_counts.to_string())
    print(f"Label stats for {label_column}:")
    print(label_stats.to_string())


def main() -> None:
    args = parse_args()
    df = read_dataset(args.dataset)
    label_column = resolve_label_column(df, args.label_column)
    print_validation_stats(df, label_column)


if __name__ == "__main__":
    main()
