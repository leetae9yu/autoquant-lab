#!/usr/bin/env python3
# pyright: reportAny=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportMissingImports=false, reportMissingTypeStubs=false, reportReturnType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnusedCallResult=false
"""Build a canonical prototype price/return panel from yfinance."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
import sys
import time

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from autoquant_lab import schemas


DEFAULT_OUTPUT = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "canonical_price_panel.parquet"
WIKIPEDIA_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
SOURCE_NAME = "yfinance"
PROTOTYPE_ONLY = True


@dataclass(frozen=True)
class UniverseMember:
    ticker: str
    yahoo_ticker: str
    company: str | None
    gics_sector: str | None


@dataclass(frozen=True)
class Universe:
    members: list[UniverseMember]
    source: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a canonical WRDS-ready, prototype-only price/return panel from yfinance. "
            "Current public S&P 500 membership is for pipeline testing only."
        )
    )
    parser.add_argument("--start-date", default="2020-01-01", help="Start date in YYYY-MM-DD format.")
    parser.add_argument(
        "--end-date",
        default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        help="End date in YYYY-MM-DD format. Defaults to today.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output path ending in .csv or .parquet.")
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=None,
        help="Deterministic ticker list for smoke runs. Overrides --universe-csv when supplied.",
    )
    parser.add_argument(
        "--universe-csv",
        type=Path,
        default=None,
        help="Optional CSV with Symbol, Security, and GICS Sector columns. Defaults to Wikipedia S&P 500 table.",
    )
    parser.add_argument("--max-tickers", type=int, default=None, help="Limit tickers for quick prototype checks.")
    parser.add_argument("--chunk-size", type=int, default=75, help="Ticker count per yfinance request.")
    parser.add_argument("--timeout", type=float, default=10.0, help="yfinance request timeout in seconds.")
    parser.add_argument("--sleep-seconds", type=float, default=0.5, help="Pause between chunks.")
    parser.add_argument("--threads", action="store_true", help="Enable yfinance threaded downloads.")
    return parser.parse_args()


def normalize_yahoo_ticker(ticker: str) -> str:
    """Normalize US class-share tickers for Yahoo without touching exchange suffixes."""
    cleaned = ticker.strip().upper()
    class_share_map = {
        "BRK.B": "BRK-B",
        "BF.B": "BF-B",
    }
    return class_share_map.get(cleaned, cleaned)


def load_ticker_universe(tickers: list[str], max_tickers: int | None) -> Universe:
    members: list[UniverseMember] = []
    seen: set[str] = set()
    for raw_ticker in tickers:
        ticker = raw_ticker.strip().upper()
        if not ticker or ticker in seen:
            continue
        seen.add(ticker)
        members.append(
            UniverseMember(
                ticker=ticker,
                yahoo_ticker=normalize_yahoo_ticker(ticker),
                company=None,
                gics_sector=None,
            )
        )
    if max_tickers is not None:
        members = members[:max_tickers]
    if not members:
        raise ValueError("Ticker universe is empty after loading and filtering.")
    return Universe(members=members, source="cli:tickers")


def load_sp500_universe(universe_csv: Path | None, max_tickers: int | None) -> Universe:
    if universe_csv is not None:
        raw = pd.read_csv(universe_csv)
        universe_source = str(universe_csv)
    else:
        response = requests.get(WIKIPEDIA_SP500_URL, headers={"User-Agent": "autoquant-lab/0.1"}, timeout=30)
        response.raise_for_status()
        raw = pd.read_html(StringIO(response.text))[0]
        universe_source = WIKIPEDIA_SP500_URL

    required_columns = {"Symbol", "Security", "GICS Sector"}
    missing_columns = required_columns.difference(raw.columns)
    if missing_columns:
        raise ValueError(f"Universe source {universe_source} is missing columns: {sorted(missing_columns)}")

    members: list[UniverseMember] = []
    for row in raw.loc[:, ["Symbol", "Security", "GICS Sector"]].itertuples(index=False):
        ticker = str(row[0]).strip().upper()
        members.append(
            UniverseMember(
                ticker=ticker,
                yahoo_ticker=normalize_yahoo_ticker(ticker),
                company=str(row[1]),
                gics_sector=str(row[2]),
            )
        )

    if max_tickers is not None:
        members = members[:max_tickers]
    if not members:
        raise ValueError("S&P 500 universe is empty after loading and filtering.")
    return Universe(members=members, source=universe_source)


def load_universe(tickers: list[str] | None, universe_csv: Path | None, max_tickers: int | None) -> Universe:
    if tickers is not None:
        return load_ticker_universe(tickers, max_tickers)
    return load_sp500_universe(universe_csv, max_tickers)


def chunked(items: list[UniverseMember], chunk_size: int) -> list[list[UniverseMember]]:
    if chunk_size < 1:
        raise ValueError("chunk_size must be at least 1")
    return [items[index : index + chunk_size] for index in range(0, len(items), chunk_size)]


def extract_ticker_frame(downloaded: pd.DataFrame, yahoo_ticker: str, requested_count: int) -> pd.DataFrame:
    if downloaded.empty:
        return pd.DataFrame()

    if requested_count == 1 and not isinstance(downloaded.columns, pd.MultiIndex):
        return downloaded.copy()

    if isinstance(downloaded.columns, pd.MultiIndex):
        if yahoo_ticker in downloaded.columns.get_level_values(0):
            return downloaded[yahoo_ticker].copy()
        if yahoo_ticker in downloaded.columns.get_level_values(-1):
            extracted = downloaded.xs(yahoo_ticker, axis=1, level=-1).copy()
            if isinstance(extracted, pd.Series):
                return extracted.to_frame()
            return extracted

    return pd.DataFrame()


def normalize_price_frame(frame: pd.DataFrame, member: UniverseMember) -> pd.DataFrame:
    price_column = "Adj Close" if "Adj Close" in frame.columns else "Close"
    required_columns = {price_column, "Close", "Volume"}
    if required_columns.difference(frame.columns):
        return pd.DataFrame()

    out = frame.reset_index().rename(
        columns={"Date": "date", price_column: "price_adjusted", "Close": "close", "Volume": "volume"}
    )
    out["date"] = pd.to_datetime(out["date"]).dt.tz_localize(None)
    out = out.loc[:, ["date", "price_adjusted", "close", "volume"]].dropna(subset=["date", "price_adjusted"])
    out["asset_id"] = member.ticker
    out["ticker"] = member.ticker
    out["yahoo_ticker"] = member.yahoo_ticker
    out["company"] = member.company
    out["gics_sector"] = member.gics_sector
    return out


def download_prices(
    members: list[UniverseMember],
    start_date: str,
    end_date: str,
    chunk_size: int,
    timeout: float,
    sleep_seconds: float,
    threads: bool,
) -> tuple[pd.DataFrame, list[str]]:
    import yfinance as yf

    frames: list[pd.DataFrame] = []
    failed: list[str] = []
    member_by_yahoo = {member.yahoo_ticker: member for member in members}

    for batch_number, batch in enumerate(chunked(members, chunk_size), start=1):
        tickers = [member.yahoo_ticker for member in batch]
        print(f"Downloading batch {batch_number}: {len(tickers)} tickers")
        try:
            downloaded = yf.download(
                tickers=tickers,
                start=start_date,
                end=end_date,
                auto_adjust=False,
                group_by="ticker",
                progress=False,
                threads=threads,
                timeout=timeout,
            )
        except Exception as exc:  # noqa: BLE001 - network/API failures are expected for prototype downloads.
            print(f"Batch failed: {exc}")
            failed.extend(member_by_yahoo[yahoo_ticker].ticker for yahoo_ticker in tickers)
            continue

        for yahoo_ticker in tickers:
            ticker_frame = extract_ticker_frame(downloaded, yahoo_ticker, len(tickers))
            if ticker_frame.empty:
                failed.append(member_by_yahoo[yahoo_ticker].ticker)
                continue

            member = member_by_yahoo[yahoo_ticker]
            normalized = normalize_price_frame(ticker_frame, member)
            if normalized.empty:
                failed.append(member.ticker)
                continue
            frames.append(normalized)

        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    if not frames:
        raise RuntimeError("No yfinance price data was downloaded.")
    return pd.concat(frames, ignore_index=True), sorted(set(failed))


def build_canonical_price_panel(prices: pd.DataFrame, universe: Universe) -> pd.DataFrame:
    generated_at_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ordered = prices.sort_values(["asset_id", "date"]).copy()
    ordered["return_1d"] = ordered.groupby("asset_id", sort=False)["price_adjusted"].pct_change(fill_method=None)
    ordered["total_return"] = ordered["return_1d"]

    ordered["asset_id_type"] = "ticker"
    ordered["permno"] = pd.NA
    ordered["permco"] = pd.NA
    ordered["gvkey"] = pd.NA
    ordered["delisting_return"] = pd.NA
    ordered["universe_source"] = universe.source
    ordered["universe_asof_utc"] = generated_at_utc
    ordered["generated_at_utc"] = generated_at_utc
    ordered["source"] = SOURCE_NAME
    ordered["prototype_only"] = PROTOTYPE_ONLY

    required_columns = list(schemas.PRICE_PANEL_REQUIRED_COLUMNS)
    optional_columns = ["ticker", "yahoo_ticker", "company", "gics_sector"]
    output_columns = required_columns + [column for column in optional_columns if column in ordered.columns]
    return ordered.loc[:, output_columns].sort_values(["asset_id", "date"]).reset_index(drop=True)


def write_failures(failed_tickers: list[str], output: Path) -> None:
    if not failed_tickers:
        return
    failure_path = output.with_suffix(".failed_tickers.txt")
    failure_path.write_text("\n".join(failed_tickers) + "\n", encoding="utf-8")
    print(f"Failed tickers: {len(failed_tickers)} written to {failure_path}")


def main() -> None:
    args = parse_args()
    universe = load_universe(args.tickers, args.universe_csv, args.max_tickers)
    print(f"Loaded {len(universe.members)} prototype universe members from {universe.source}")
    print("Warning: yfinance datasets are prototype_only and not survivorship-bias-free research data.")

    prices, failed_tickers = download_prices(
        members=universe.members,
        start_date=args.start_date,
        end_date=args.end_date,
        chunk_size=args.chunk_size,
        timeout=args.timeout,
        sleep_seconds=args.sleep_seconds,
        threads=args.threads,
    )
    canonical = build_canonical_price_panel(prices, universe)
    schemas.write_dataset(canonical, args.output)
    write_failures(failed_tickers, args.output)

    print(f"Wrote {len(canonical):,} rows and {canonical.shape[1]} columns to {args.output}")
    print(f"Assets: {canonical['asset_id'].nunique()}")
    print(f"Start date: {canonical['date'].min().strftime('%Y-%m-%d') if not canonical.empty else 'n/a'}")
    print(f"End date: {canonical['date'].max().strftime('%Y-%m-%d') if not canonical.empty else 'n/a'}")
    print("Canonical fields include price_adjusted, close, volume, return_1d, and total_return.")


if __name__ == "__main__":
    main()
