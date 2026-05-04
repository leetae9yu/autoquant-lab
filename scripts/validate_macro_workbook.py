#!/usr/bin/env python3
# pyright: reportAttributeAccessIssue=false, reportMissingTypeStubs=false
"""Validate the expanded macro market feature workbook."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKBOOK = PROJECT_ROOT / "expanded_macro_market_features.xlsx"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print validation stats for a macro feature workbook.")
    parser.add_argument(
        "workbook",
        nargs="?",
        type=Path,
        default=DEFAULT_WORKBOOK,
        help="Workbook path to validate.",
    )
    parser.add_argument("--head", type=int, default=5, help="Number of rows to print from the workbook head.")
    return parser.parse_args()


def load_workbook(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Workbook not found: {path}")
    return pd.read_excel(path, index_col=0)


def print_validation_stats(df: pd.DataFrame, head_rows: int) -> None:
    df.index = pd.to_datetime(df.index, errors="coerce")
    null_counts = df.isna().sum()
    missing_columns = null_counts[null_counts > 0]

    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")
    print(f"Start date: {df.index.min().strftime('%Y-%m-%d') if not df.empty else 'n/a'}")
    print(f"End date: {df.index.max().strftime('%Y-%m-%d') if not df.empty else 'n/a'}")
    print(f"Total missing values: {int(null_counts.sum())}")
    print(f"Columns with missing values: {missing_columns.shape[0]}")
    if not missing_columns.empty:
        print("Missing values by column:")
        print(missing_columns.to_string())
    print("Head:")
    print(df.head(head_rows).to_string())


def main() -> None:
    args = parse_args()
    df = load_workbook(args.workbook)
    print_validation_stats(df, args.head)


if __name__ == "__main__":
    main()
