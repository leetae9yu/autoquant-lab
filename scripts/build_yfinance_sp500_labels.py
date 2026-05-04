#!/usr/bin/env python3
# pyright: reportAny=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportMissingImports=false, reportMissingTypeStubs=false, reportReturnType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnusedCallResult=false
"""Build prototype S&P 500 price and 1-month forward-return labels from yfinance."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
import time

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "prototypes" / "yfinance_sp500" / "sp500_yfinance_labels.csv"
WIKIPEDIA_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
SOURCE_NAME = "yfinance"
PROTOTYPE_ONLY = True


@dataclass(frozen=True)
class UniverseMember:
    ticker: str
    yahoo_ticker: str
    company: str
    gics_sector: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a WRDS-free, prototype-only S&P 500 price/label dataset from yfinance. "
            "This uses current public membership and is not survivorship-bias-free."
        )
    )
    parser.add_argument("--start-date", default="2020-01-01", help="Start date in YYYY-MM-DD format.")
    parser.add_argument(
        "--end-date",
        default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        help="End date in YYYY-MM-DD format. Defaults to today.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output path ending in .csv or .parquet.",
    )
    parser.add_argument(
        "--universe-csv",
        type=Path,
        default=None,
        help="Optional CSV with Symbol, Security, and GICS Sector columns. Defaults to Wikipedia.",
    )
    parser.add_argument("--max-tickers", type=int, default=None, help="Limit tickers for quick prototype checks.")
    parser.add_argument("--chunk-size", type=int, default=75, help="Ticker count per yfinance request.")
    parser.add_argument("--horizon-days", type=int, default=21, help="Trading-day horizon for forward returns.")
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


def load_universe(universe_csv: Path | None, max_tickers: int | None) -> list[UniverseMember]:
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
    return members


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
        except Exception as exc:  # noqa: BLE001 - network/API failures are expected in fallback mode.
            print(f"Batch failed: {exc}")
            failed.extend(tickers)
            continue

        for yahoo_ticker in tickers:
            ticker_frame = extract_ticker_frame(downloaded, yahoo_ticker, len(tickers))
            if ticker_frame.empty:
                failed.append(yahoo_ticker)
                continue

            member = member_by_yahoo[yahoo_ticker]
            normalized = normalize_price_frame(ticker_frame, member)
            if normalized.empty:
                failed.append(yahoo_ticker)
                continue
            frames.append(normalized)

        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    if not frames:
        raise RuntimeError("No yfinance price data was downloaded.")
    return pd.concat(frames, ignore_index=True), sorted(set(failed))


def normalize_price_frame(frame: pd.DataFrame, member: UniverseMember) -> pd.DataFrame:
    price_column = "Adj Close" if "Adj Close" in frame.columns else "Close"
    required_columns = {price_column, "Close", "Volume"}
    if required_columns.difference(frame.columns):
        return pd.DataFrame()

    out = frame.reset_index().rename(columns={"Date": "date", price_column: "adj_close", "Close": "close", "Volume": "volume"})
    out["date"] = pd.to_datetime(out["date"]).dt.tz_localize(None)
    out = out.loc[:, ["date", "adj_close", "close", "volume"]].dropna(subset=["date", "adj_close"])
    out["ticker"] = member.ticker
    out["yahoo_ticker"] = member.yahoo_ticker
    out["company"] = member.company
    out["gics_sector"] = member.gics_sector
    return out


def add_forward_return_labels(prices: pd.DataFrame, horizon_days: int) -> pd.DataFrame:
    if horizon_days < 1:
        raise ValueError("horizon_days must be at least 1")
    ordered = prices.sort_values(["ticker", "date"]).copy()
    grouped = ordered.groupby("ticker", sort=False)["adj_close"]
    ordered[f"forward_return_{horizon_days}d"] = grouped.shift(-horizon_days) / ordered["adj_close"] - 1.0
    ordered["label_horizon_trading_days"] = horizon_days
    ordered["source"] = SOURCE_NAME
    ordered["prototype_only"] = PROTOTYPE_ONLY
    ordered["universe_source"] = "current_public_sp500_membership"
    ordered["universe_asof_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return ordered


def write_dataset(df: pd.DataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix == ".parquet":
        df.to_parquet(output, index=False)
    elif output.suffix == ".csv":
        df.to_csv(output, index=False)
    else:
        raise ValueError("Output must end in .csv or .parquet")
    print(f"Wrote {len(df):,} rows to {output}")


def write_failures(failed_tickers: list[str], output: Path) -> None:
    if not failed_tickers:
        return
    failure_path = output.with_suffix(".failed_tickers.txt")
    failure_path.write_text("\n".join(failed_tickers) + "\n", encoding="utf-8")
    print(f"Failed tickers: {len(failed_tickers)} written to {failure_path}")


def main() -> None:
    args = parse_args()
    members = load_universe(args.universe_csv, args.max_tickers)
    print(f"Loaded {len(members)} S&P 500 prototype universe members")
    print("Warning: this current-membership yfinance dataset is prototype_only and not survivorship-bias-free.")

    prices, failed_tickers = download_prices(
        members=members,
        start_date=args.start_date,
        end_date=args.end_date,
        chunk_size=args.chunk_size,
        timeout=args.timeout,
        sleep_seconds=args.sleep_seconds,
        threads=args.threads,
    )
    labeled = add_forward_return_labels(prices, args.horizon_days)
    write_dataset(labeled, args.output)
    write_failures(failed_tickers, args.output)

    label_column = f"forward_return_{args.horizon_days}d"
    usable_labels = labeled[label_column].notna().sum()
    print(f"Usable non-null labels: {usable_labels:,}")


if __name__ == "__main__":
    main()
