#!/usr/bin/env python3
# pyright: reportAny=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportMissingImports=false, reportMissingTypeStubs=false, reportReturnType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnusedCallResult=false
"""Build canonical prototype price/volume factor scores from a yfinance price panel."""

from __future__ import annotations

import argparse
from collections.abc import Callable
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


DEFAULT_PRICE_PANEL = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "canonical_price_panel.parquet"
DEFAULT_OUTPUT = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "factor_scores.parquet"
DATASET_NAME = "canonical yfinance price panel"
SOURCE_NAME = "yfinance"
PROTOTYPE_ONLY = True
TRADING_DAY_LOOKBACKS = {
    "1w": 5,
    "1m": 21,
    "3m": 63,
    "6m": 126,
    "12m": 252,
}


@dataclass(frozen=True)
class FactorDefinition:
    name: str
    family: str
    lookback_days: int
    direction: str
    source_columns: tuple[str, ...]


FACTOR_DEFINITIONS: tuple[FactorDefinition, ...] = (
    FactorDefinition("mom_1m", "momentum", TRADING_DAY_LOOKBACKS["1m"], "high", ("price_adjusted",)),
    FactorDefinition("mom_3m", "momentum", TRADING_DAY_LOOKBACKS["3m"], "high", ("price_adjusted",)),
    FactorDefinition("mom_6m", "momentum", TRADING_DAY_LOOKBACKS["6m"], "high", ("price_adjusted",)),
    FactorDefinition("mom_12m", "momentum", TRADING_DAY_LOOKBACKS["12m"], "high", ("price_adjusted",)),
    FactorDefinition("rev_1w", "reversal", TRADING_DAY_LOOKBACKS["1w"], "high", ("price_adjusted",)),
    FactorDefinition("rev_1m", "reversal", TRADING_DAY_LOOKBACKS["1m"], "high", ("price_adjusted",)),
    FactorDefinition("vol_1m", "volatility", TRADING_DAY_LOOKBACKS["1m"], "low", ("total_return",)),
    FactorDefinition("vol_3m", "volatility", TRADING_DAY_LOOKBACKS["3m"], "low", ("total_return",)),
    FactorDefinition("vol_6m", "volatility", TRADING_DAY_LOOKBACKS["6m"], "low", ("total_return",)),
    FactorDefinition("max_dd_1m", "drawdown", TRADING_DAY_LOOKBACKS["1m"], "low", ("price_adjusted",)),
    FactorDefinition("max_dd_3m", "drawdown", TRADING_DAY_LOOKBACKS["3m"], "low", ("price_adjusted",)),
    FactorDefinition("max_dd_6m", "drawdown", TRADING_DAY_LOOKBACKS["6m"], "low", ("price_adjusted",)),
    FactorDefinition(
        "dollar_volume_1m", "liquidity", TRADING_DAY_LOOKBACKS["1m"], "high", ("close", "volume")
    ),
    FactorDefinition("volume_z_1m", "liquidity", TRADING_DAY_LOOKBACKS["1m"], "high", ("volume",)),
    FactorDefinition(
        "amihud_illiq_1m", "liquidity", TRADING_DAY_LOOKBACKS["1m"], "low", ("total_return", "close", "volume")
    ),
    FactorDefinition("beta_spy_6m", "market_sensitivity", TRADING_DAY_LOOKBACKS["6m"], "neutral", ("total_return",)),
    FactorDefinition("corr_spy_6m", "market_sensitivity", TRADING_DAY_LOOKBACKS["6m"], "neutral", ("total_return",)),
)
DEFINITION_BY_NAME = {definition.name: definition for definition in FACTOR_DEFINITIONS}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build prototype-only canonical factor_scores from a yfinance canonical price panel. "
            "Factors are trailing raw values only; no cross-sectional ranks are calculated."
        )
    )
    parser.add_argument("--price-panel", type=Path, default=DEFAULT_PRICE_PANEL, help="Input CSV or Parquet price panel.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output path ending in .csv or .parquet.")
    parser.add_argument("--smoke", action="store_true", help="Print smoke-mode context; factor math is unchanged.")
    return parser.parse_args()


def validate_price_panel(df: pd.DataFrame) -> pd.DataFrame:
    schemas.require_columns(df, schemas.PRICE_PANEL_REQUIRED_COLUMNS, DATASET_NAME)
    schemas.require_unique_key(df, schemas.PRICE_PANEL_KEY_COLUMNS, DATASET_NAME)

    data = df.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    invalid_dates = int(data["date"].isna().sum())
    if invalid_dates:
        raise ValueError(f"{DATASET_NAME} contains invalid dates: {invalid_dates}")

    for column in ("asset_id", "asset_id_type", "source"):
        blank_count = int(data[column].isna().sum() + data[column].astype(str).str.strip().eq("").sum())
        if blank_count:
            raise ValueError(f"{DATASET_NAME} contains blank {column} values: {blank_count}")

    schemas.require_prototype_only(data, DATASET_NAME)
    for column in ("price_adjusted", "close", "volume", "total_return"):
        data[column] = pd.to_numeric(data[column], errors="coerce")

    missing_price = int(data["price_adjusted"].isna().sum())
    if missing_price:
        raise ValueError(f"{DATASET_NAME} contains missing price_adjusted values: {missing_price}")
    if bool((data["price_adjusted"] <= 0).any()) or bool((data["close"].dropna() <= 0).any()):
        raise ValueError(f"{DATASET_NAME} price_adjusted and close must be positive when present")
    if bool((data["volume"].dropna() < 0).any()):
        raise ValueError(f"{DATASET_NAME} volume must be non-negative when present")

    return data.sort_values(["asset_id", "date"]).reset_index(drop=True)


def trailing_drawdown(price: pd.Series, lookback_days: int) -> pd.Series:
    def max_drawdown(window: np.ndarray[tuple[int], np.dtype[np.float64]]) -> float:
        running_max = np.maximum.accumulate(window)
        drawdowns = window / running_max - 1.0
        return float(-np.min(drawdowns))

    return price.rolling(lookback_days, min_periods=lookback_days).apply(max_drawdown, raw=True)


def add_asset_time_series_factors(data: pd.DataFrame) -> pd.DataFrame:
    enriched = data.copy()
    grouped = enriched.groupby("asset_id", sort=False)
    price = grouped["price_adjusted"]
    total_return = grouped["total_return"]
    volume = grouped["volume"]
    dollar_volume = enriched["close"] * enriched["volume"]
    enriched["_dollar_volume"] = dollar_volume
    enriched["_amihud_daily"] = enriched["total_return"].abs() / dollar_volume.replace(0, np.nan)

    for suffix, lookback_days in (("1m", 21), ("3m", 63), ("6m", 126), ("12m", 252)):
        enriched[f"mom_{suffix}"] = price.pct_change(periods=lookback_days, fill_method=None)
    enriched["rev_1w"] = -price.pct_change(periods=5, fill_method=None)
    enriched["rev_1m"] = -price.pct_change(periods=21, fill_method=None)

    for suffix, lookback_days in (("1m", 21), ("3m", 63), ("6m", 126)):
        enriched[f"vol_{suffix}"] = total_return.rolling(lookback_days, min_periods=lookback_days).std().reset_index(level=0, drop=True)
        enriched[f"max_dd_{suffix}"] = price.transform(_drawdown_transform(lookback_days))

    enriched["dollar_volume_1m"] = (
        enriched.groupby("asset_id", sort=False)["_dollar_volume"]
        .rolling(21, min_periods=21)
        .mean()
        .reset_index(level=0, drop=True)
    )
    volume_mean_1m = volume.rolling(21, min_periods=21).mean().reset_index(level=0, drop=True)
    volume_std_1m = volume.rolling(21, min_periods=21).std().reset_index(level=0, drop=True)
    enriched["volume_z_1m"] = (enriched["volume"] - volume_mean_1m) / volume_std_1m.replace(0, np.nan)
    enriched["amihud_illiq_1m"] = (
        enriched.groupby("asset_id", sort=False)["_amihud_daily"]
        .rolling(21, min_periods=21)
        .mean()
        .reset_index(level=0, drop=True)
    )
    return enriched


def _drawdown_transform(lookback_days: int) -> Callable[[pd.Series], pd.Series]:
    def transform(series: pd.Series) -> pd.Series:
        return trailing_drawdown(series, lookback_days)

    return transform


def factor_family(name: str) -> str:
    return DEFINITION_BY_NAME[name].family


def factor_lookback_days(name: str) -> int:
    return DEFINITION_BY_NAME[name].lookback_days


def factor_direction(name: str) -> str:
    return DEFINITION_BY_NAME[name].direction


def factor_source_columns(name: str) -> str:
    return ",".join(DEFINITION_BY_NAME[name].source_columns)


def add_market_sensitivity_factors(data: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    if "SPY" not in set(data["asset_id"].astype(str)):
        warning = "Warning: SPY not present; skipping beta_spy_6m and corr_spy_6m."
        return data, [warning]

    enriched = data.copy()
    spy_returns = (
        enriched.loc[enriched["asset_id"].astype(str).eq("SPY"), ["date", "total_return"]]
        .drop_duplicates("date")
        .rename(columns={"total_return": "_spy_return"})
    )
    enriched = enriched.merge(spy_returns, on="date", how="left", validate="many_to_one")
    min_market_observations = 63
    beta = pd.Series(index=enriched.index, dtype="float64")
    correlation = pd.Series(index=enriched.index, dtype="float64")
    for _, asset_frame in enriched.groupby("asset_id", sort=False):
        covariance = asset_frame["total_return"].rolling(126, min_periods=min_market_observations).cov(asset_frame["_spy_return"])
        spy_variance = asset_frame["_spy_return"].rolling(126, min_periods=min_market_observations).var()
        beta.loc[asset_frame.index] = covariance / spy_variance.replace(0, np.nan)
        correlation.loc[asset_frame.index] = asset_frame["total_return"].rolling(
            126, min_periods=min_market_observations
        ).corr(asset_frame["_spy_return"])
    enriched["beta_spy_6m"] = beta
    enriched["corr_spy_6m"] = correlation
    return enriched, []


def factor_columns_with_coverage(data: pd.DataFrame) -> list[str]:
    factor_names: list[str] = []
    for definition in FACTOR_DEFINITIONS:
        if definition.name in data.columns and int(np.isfinite(pd.to_numeric(data[definition.name], errors="coerce")).sum()):
            factor_names.append(definition.name)
        elif definition.name in {"beta_spy_6m", "corr_spy_6m"}:
            print(f"Warning: {definition.name} has no finite observations and will be skipped.")
    if not factor_names:
        raise ValueError("No factor columns have finite observations; input history is too short.")
    return factor_names


def build_factor_scores(price_panel: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    data = validate_price_panel(price_panel)
    data = add_asset_time_series_factors(data)
    data, warnings = add_market_sensitivity_factors(data)
    factor_names = factor_columns_with_coverage(data)

    id_columns = ["date", "asset_id", "asset_id_type", "permno", "permco", "gvkey"]
    long_scores = data.melt(
        id_vars=id_columns,
        value_vars=factor_names,
        var_name="factor_name",
        value_name="factor_value",
    )
    long_scores["factor_value"] = pd.to_numeric(long_scores["factor_value"], errors="coerce")
    long_scores = long_scores.loc[np.isfinite(long_scores["factor_value"].to_numpy(dtype=float))].copy()

    factor_names_as_str = long_scores["factor_name"].astype(str)
    long_scores["factor_family"] = factor_names_as_str.map(factor_family)
    long_scores["lookback_days"] = factor_names_as_str.map(factor_lookback_days)
    long_scores["direction"] = factor_names_as_str.map(factor_direction)
    long_scores["source_columns"] = factor_names_as_str.map(factor_source_columns)
    long_scores["rank_method"] = "raw_no_cross_sectional_rank"
    long_scores["winsorization_method"] = "none"
    long_scores["source"] = SOURCE_NAME
    long_scores["prototype_only"] = PROTOTYPE_ONLY

    output = long_scores.loc[:, list(schemas.FACTOR_SCORES_REQUIRED_COLUMNS)].sort_values(
        ["date", "asset_id", "factor_name"]
    )
    schemas.require_unique_key(output, schemas.FACTOR_SCORES_KEY_COLUMNS, "factor_scores")
    return output.reset_index(drop=True), warnings


def print_build_summary(factor_scores: pd.DataFrame, output: Path, smoke: bool) -> None:
    print(f"Wrote {len(factor_scores):,} rows and {factor_scores.shape[1]} columns to {output}")
    print(f"Smoke mode: {smoke}")
    print(f"Assets: {factor_scores['asset_id'].nunique()}")
    print(f"Factors: {factor_scores['factor_name'].nunique()}")
    print(f"Start date: {factor_scores['date'].min().strftime('%Y-%m-%d') if not factor_scores.empty else 'n/a'}")
    print(f"End date: {factor_scores['date'].max().strftime('%Y-%m-%d') if not factor_scores.empty else 'n/a'}")
    print("Rows by factor:")
    print(factor_scores["factor_name"].value_counts().sort_index().to_string())
    print("Rows by factor family:")
    print(factor_scores["factor_family"].value_counts().sort_index().to_string())


def main() -> None:
    args = parse_args()
    price_panel = schemas.read_dataset(args.price_panel)
    factor_scores, warnings = build_factor_scores(price_panel)
    schemas.write_dataset(factor_scores, args.output)
    for warning in warnings:
        print(warning)
    print("Warning: yfinance factor scores are prototype_only raw public-data signals, not research-grade factors.")
    print_build_summary(factor_scores, args.output, args.smoke)


if __name__ == "__main__":
    main()
