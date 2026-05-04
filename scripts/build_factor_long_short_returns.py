#!/usr/bin/env python3
# pyright: reportAny=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportMissingImports=false, reportMissingTypeStubs=false, reportReturnType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnusedCallResult=false
"""Build canonical factor long-short forward return labels."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from autoquant_lab import schemas


DEFAULT_FACTOR_SCORES = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "factor_scores.parquet"
DEFAULT_PRICE_PANEL = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "canonical_price_panel.parquet"
DEFAULT_OUTPUT = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "factor_long_short_returns.parquet"
DATASET_FACTOR_SCORES = "canonical factor_scores"
DATASET_PRICE_PANEL = "canonical price panel"
SOURCE_NAME = "yfinance"
LABEL_SOURCE = "equal_weight_factor_long_short"
RETURN_SOURCE = "canonical_price_panel.total_return"
PROTOTYPE_ONLY = True


@dataclass(frozen=True)
class ForwardReturn:
    asset_id: str
    formation_date: pd.Timestamp
    forward_return_start: pd.Timestamp
    forward_return_end: pd.Timestamp
    forward_return: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build canonical factor long-short forward return labels.")
    parser.add_argument("--factor-scores", type=Path, default=DEFAULT_FACTOR_SCORES, help="Input factor_scores CSV or Parquet.")
    parser.add_argument("--price-panel", type=Path, default=DEFAULT_PRICE_PANEL, help="Input canonical price panel CSV or Parquet.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output path ending in .csv or .parquet.")
    parser.add_argument("--horizon-trading-days", type=int, default=21, help="Forward return horizon in trading days.")
    parser.add_argument("--long-quantile", type=float, default=0.8, help="Long basket factor-value quantile threshold.")
    parser.add_argument("--short-quantile", type=float, default=0.2, help="Short basket factor-value quantile threshold.")
    parser.add_argument("--min-basket-size", type=int, default=25, help="Minimum assets required in each long/short basket.")
    parser.add_argument("--smoke", action="store_true", help="Use smoke-friendly minimum basket size when not explicitly lowered.")
    return parser.parse_args()


def effective_min_basket_size(requested: int, smoke: bool) -> int:
    if requested <= 0:
        raise ValueError("--min-basket-size must be positive")
    if smoke and requested == 25:
        return 2
    return requested


def validate_cli_args(horizon_trading_days: int, long_quantile: float, short_quantile: float) -> None:
    if horizon_trading_days <= 0:
        raise ValueError("--horizon-trading-days must be positive")
    if not 0.0 < short_quantile < long_quantile < 1.0:
        raise ValueError("Require 0 < --short-quantile < --long-quantile < 1")


def prepare_factor_scores(df: pd.DataFrame) -> pd.DataFrame:
    schemas.require_columns(df, schemas.FACTOR_SCORES_REQUIRED_COLUMNS, DATASET_FACTOR_SCORES)
    schemas.require_prototype_only(df, DATASET_FACTOR_SCORES)
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    invalid_dates = int(data["date"].isna().sum())
    if invalid_dates:
        raise ValueError(f"{DATASET_FACTOR_SCORES} contains invalid dates: {invalid_dates}")
    data["date"] = data["date"].dt.tz_localize(None)
    data["factor_value"] = pd.to_numeric(data["factor_value"], errors="coerce")
    non_finite_values = int((~np.isfinite(data["factor_value"].to_numpy(dtype=float))).sum())
    if non_finite_values:
        raise ValueError(f"{DATASET_FACTOR_SCORES} contains non-finite factor_value rows: {non_finite_values}")
    schemas.require_unique_key(data, schemas.FACTOR_SCORES_KEY_COLUMNS, DATASET_FACTOR_SCORES)
    return data.sort_values(["date", "factor_name", "asset_id"]).reset_index(drop=True)


def prepare_price_panel(df: pd.DataFrame) -> pd.DataFrame:
    schemas.require_columns(df, schemas.PRICE_PANEL_REQUIRED_COLUMNS, DATASET_PRICE_PANEL)
    schemas.require_prototype_only(df, DATASET_PRICE_PANEL)
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    invalid_dates = int(data["date"].isna().sum())
    if invalid_dates:
        raise ValueError(f"{DATASET_PRICE_PANEL} contains invalid dates: {invalid_dates}")
    data["date"] = data["date"].dt.tz_localize(None)
    schemas.require_unique_key(data, schemas.PRICE_PANEL_KEY_COLUMNS, DATASET_PRICE_PANEL)
    for column in ("price_adjusted", "total_return"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    missing_prices = int(data["price_adjusted"].isna().sum())
    if missing_prices:
        raise ValueError(f"{DATASET_PRICE_PANEL} contains missing price_adjusted rows: {missing_prices}")
    return data.sort_values(["asset_id", "date"]).reset_index(drop=True)


def monthly_formation_dates(factor_scores: pd.DataFrame) -> set[pd.Timestamp]:
    unique_dates = factor_scores.loc[:, "date"].drop_duplicates().sort_values().reset_index(drop=True)
    if unique_dates.empty:
        return set()
    month_keys = unique_dates.dt.to_period("M")
    return set(unique_dates.groupby(month_keys, sort=True).max())


def compute_forward_returns(price_panel: pd.DataFrame, horizon_trading_days: int) -> dict[tuple[str, pd.Timestamp], ForwardReturn]:
    forward_returns: dict[tuple[str, pd.Timestamp], ForwardReturn] = {}
    for asset_id, asset_frame in price_panel.groupby("asset_id", sort=True):
        asset_data = asset_frame.sort_values("date").reset_index(drop=True)
        dates = asset_data["date"].to_list()
        total_returns = asset_data["total_return"].to_numpy(dtype=float)
        for position, formation_date in enumerate(dates):
            start_position = position + 1
            end_position = position + horizon_trading_days
            if end_position >= len(asset_data):
                continue
            start_date = dates[start_position]
            end_date = dates[end_position]
            if start_date <= formation_date:
                continue
            horizon_returns = total_returns[start_position : end_position + 1]
            if len(horizon_returns) != horizon_trading_days or not np.isfinite(horizon_returns).all():
                continue
            forward_returns[(str(asset_id), formation_date)] = ForwardReturn(
                asset_id=str(asset_id),
                formation_date=formation_date,
                forward_return_start=start_date,
                forward_return_end=end_date,
                forward_return=float(np.prod(1.0 + horizon_returns) - 1.0),
            )
    return forward_returns


def build_factor_long_short_returns(
    factor_scores: pd.DataFrame,
    price_panel: pd.DataFrame,
    horizon_trading_days: int,
    long_quantile: float,
    short_quantile: float,
    min_basket_size: int,
) -> tuple[pd.DataFrame, Counter[str]]:
    scores = prepare_factor_scores(factor_scores)
    prices = prepare_price_panel(price_panel)
    formation_dates = monthly_formation_dates(scores)
    forward_returns = compute_forward_returns(prices, horizon_trading_days)
    skipped: Counter[str] = Counter()
    rows: list[dict[str, object]] = []

    monthly_scores = scores.loc[scores["date"].isin(formation_dates)].copy()
    for (formation_date, factor_name), group in monthly_scores.groupby(["date", "factor_name"], sort=True):
        factor_values = group["factor_value"].to_numpy(dtype=float)
        if len(group) < max(2, min_basket_size):
            skipped["insufficient_cross_section"] += 1
            continue
        short_threshold = float(np.quantile(factor_values, short_quantile, method="higher"))
        long_threshold = float(np.quantile(factor_values, long_quantile, method="lower"))
        long_assets = group.loc[group["factor_value"] >= long_threshold, "asset_id"].astype(str).tolist()
        short_assets = group.loc[group["factor_value"] <= short_threshold, "asset_id"].astype(str).tolist()
        if len(long_assets) < min_basket_size:
            skipped["insufficient_long_basket"] += 1
            continue
        if len(short_assets) < min_basket_size:
            skipped["insufficient_short_basket"] += 1
            continue

        long_forward = [forward_returns.get((asset_id, formation_date)) for asset_id in long_assets]
        short_forward = [forward_returns.get((asset_id, formation_date)) for asset_id in short_assets]
        if any(value is None for value in long_forward):
            skipped["missing_long_horizon_prices"] += 1
            continue
        if any(value is None for value in short_forward):
            skipped["missing_short_horizon_prices"] += 1
            continue

        long_valid = [value for value in long_forward if value is not None]
        short_valid = [value for value in short_forward if value is not None]
        long_start_dates = {value.forward_return_start for value in long_valid}
        long_end_dates = {value.forward_return_end for value in long_valid}
        short_start_dates = {value.forward_return_start for value in short_valid}
        short_end_dates = {value.forward_return_end for value in short_valid}
        if len(long_start_dates | short_start_dates) != 1 or len(long_end_dates | short_end_dates) != 1:
            skipped["inconsistent_forward_window"] += 1
            continue

        long_return = float(np.mean([value.forward_return for value in long_valid]))
        short_return = float(np.mean([value.forward_return for value in short_valid]))
        metadata = group.iloc[0]
        rows.append(
            {
                "formation_date": formation_date,
                "factor_name": factor_name,
                "horizon_trading_days": horizon_trading_days,
                "long_quantile": long_quantile,
                "short_quantile": short_quantile,
                "long_count": len(long_valid),
                "short_count": len(short_valid),
                "long_return": long_return,
                "short_return": short_return,
                "long_short_return": long_return - short_return,
                "forward_return_start": next(iter(long_start_dates | short_start_dates)),
                "forward_return_end": next(iter(long_end_dates | short_end_dates)),
                "return_source": RETURN_SOURCE,
                "label_source": LABEL_SOURCE,
                "factor_family": metadata["factor_family"],
                "lookback_days": metadata["lookback_days"],
                "direction": metadata["direction"],
                "rank_method": metadata["rank_method"],
                "winsorization_method": metadata["winsorization_method"],
                "source": SOURCE_NAME,
                "prototype_only": PROTOTYPE_ONLY,
            }
        )

    output = pd.DataFrame(rows, columns=list(schemas.FACTOR_LONG_SHORT_REQUIRED_COLUMNS))
    if not output.empty:
        output = output.sort_values(["formation_date", "factor_name", "horizon_trading_days"]).reset_index(drop=True)
        schemas.require_unique_key(output, schemas.FACTOR_LONG_SHORT_KEY_COLUMNS, "factor_long_short_returns")
    return output, skipped


def print_build_summary(labels: pd.DataFrame, skipped: Counter[str], output: Path, min_basket_size: int, smoke: bool) -> None:
    print(f"Wrote {len(labels):,} rows and {labels.shape[1]} columns to {output}")
    print(f"Smoke mode: {smoke}")
    print(f"Effective min basket size: {min_basket_size}")
    print(f"Factors: {labels['factor_name'].nunique() if not labels.empty else 0}")
    print(f"Start formation date: {labels['formation_date'].min().strftime('%Y-%m-%d') if not labels.empty else 'n/a'}")
    print(f"End formation date: {labels['formation_date'].max().strftime('%Y-%m-%d') if not labels.empty else 'n/a'}")
    print("Skipped factor/date combinations by reason:")
    if skipped:
        for reason in sorted(skipped):
            print(f"{reason}: {skipped[reason]}")
    else:
        print("none: 0")
    if not labels.empty:
        print("Rows by factor:")
        print(labels["factor_name"].value_counts().sort_index().to_string())
        print("Basket count summary:")
        print(labels[["long_count", "short_count"]].describe().to_string())


def main() -> None:
    args = parse_args()
    validate_cli_args(args.horizon_trading_days, args.long_quantile, args.short_quantile)
    min_basket_size = effective_min_basket_size(args.min_basket_size, args.smoke)
    factor_scores = schemas.read_dataset(args.factor_scores)
    price_panel = schemas.read_dataset(args.price_panel)
    labels, skipped = build_factor_long_short_returns(
        factor_scores=factor_scores,
        price_panel=price_panel,
        horizon_trading_days=args.horizon_trading_days,
        long_quantile=args.long_quantile,
        short_quantile=args.short_quantile,
        min_basket_size=min_basket_size,
    )
    schemas.write_dataset(labels, args.output)
    print("Warning: yfinance factor long-short labels are prototype_only public-data labels, not research-grade returns.")
    print_build_summary(labels, skipped, args.output, min_basket_size, args.smoke)


if __name__ == "__main__":
    main()
