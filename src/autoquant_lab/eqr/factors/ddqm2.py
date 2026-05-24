"""DDQM2-style factor-return modeling, allocation, and backtesting."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd

from .definitions import FactorDefinition
from ..models.registry import create_model


@dataclass(frozen=True)
class FactorModelResult:
    predictions: pd.DataFrame
    metrics: pd.DataFrame


DDQM2_US_25_BASE_MACRO = (
    "sp500",
    "nasdaq",
    "treasury_2y",
    "treasury_10y",
    "treasury_10_3_diff",
    "treasury_10_2_diff",
    "fed_funds",
    "tips_10y",
    "breakeven_10y",
    "cpi",
    "core_cpi",
    "pce",
    "payrolls",
    "unemployment",
    "housing_starts",
    "retail_sales",
    "industrial_prod",
    "vix",
    "hy_spread",
    "baa_10y_spread",
    "nfci",
    "fed_total_assets",
    "dxy_proxy",
    "usd_jpy",
    "wti",
)

EXPANDED_US_MACRO_BASES = (*DDQM2_US_25_BASE_MACRO, "consumer_sentiment")


def macro_design_columns(feature_panel: pd.DataFrame, design: str = "current_macro_family") -> tuple[list[str], list[str]]:
    """Return available macro columns and explicit missing fields for a design."""

    available = {col for col in feature_panel.columns if col.startswith("macro__")}
    if design == "current_macro_family":
        return sorted(available), []
    if design == "ddqm2_25x3_us_macro":
        requested = [f"macro__{base}{suffix}" for base in DDQM2_US_25_BASE_MACRO for suffix in ("", "_c20", "_c60")]
    elif design == "expanded_us_macro":
        requested = [f"macro__{base}{suffix}" for base in EXPANDED_US_MACRO_BASES for suffix in ("", "_c20", "_c60", "_m1", "_m3", "_yoy")]
    else:
        raise ValueError(f"Unsupported macro feature design: {design}")
    used = [col for col in requested if col in available]
    missing = [col for col in requested if col not in available]
    return used, missing


def macro_design_matrix(feature_panel: pd.DataFrame, design: str = "current_macro_family") -> pd.DataFrame:
    macro_cols, _ = macro_design_columns(feature_panel, design)
    if not macro_cols:
        raise ValueError(f"feature_panel contains no macro__ columns for DDQM2 modeling design={design}")
    macro = feature_panel[["formation_date", *macro_cols]].copy()
    macro["formation_date"] = pd.to_datetime(macro["formation_date"], errors="coerce")
    macro_dates = pd.Series(macro["formation_date"], index=macro.index)
    macro = macro.loc[macro_dates.notna()].copy()
    macro = macro.groupby("formation_date", as_index=False)[macro_cols].last()
    return macro.sort_values(["formation_date"]).reset_index(drop=True)


def _split_dates(dates: pd.Series, validation_fraction: float, holdout_fraction: float) -> tuple[list[Any], list[Any], list[Any]]:
    unique = [pd.Timestamp(date) for date in sorted(pd.Series(dates).dropna().unique()) if pd.notna(date)]
    if len(unique) < 6:
        raise ValueError("At least six dates are required for DDQM2 factor modeling")
    holdout_n = max(1, int(round(len(unique) * holdout_fraction)))
    valid_n = max(1, int(round(len(unique) * validation_fraction)))
    train_end = max(1, len(unique) - valid_n - holdout_n)
    return unique[:train_end], unique[train_end : train_end + valid_n], unique[train_end + valid_n :]


def train_factor_return_models(
    factor_returns: pd.DataFrame,
    feature_panel: pd.DataFrame,
    *,
    model_name: str = "lightgbm",
    model_params: dict[str, Any] | None = None,
    validation_fraction: float = 0.15,
    holdout_fraction: float = 0.15,
    min_observations: int = 24,
    evaluation_mode: str = "single_holdout",
    walk_forward_test_periods: int = 12,
    walk_forward_validation_periods: int = 12,
    macro_feature_design: str = "current_macro_family",
) -> FactorModelResult:
    """Train one CPU model per factor to forecast next 1M factor return."""

    macro = macro_design_matrix(feature_panel, macro_feature_design)
    frame = factor_returns.merge(macro, on="formation_date", how="inner")
    frame = frame.dropna(subset=["factor_long_short_ret_1m"])
    feature_cols = [col for col in macro.columns if col != "formation_date"]
    predictions: list[pd.DataFrame] = []
    metrics: list[dict[str, Any]] = []
    for factor_id, group in frame.groupby("factor_id", sort=True):
        group = group.sort_values("formation_date").reset_index(drop=True)
        if len(group) < min_observations:
            continue
        if evaluation_mode == "walk_forward":
            unique_dates = [pd.Timestamp(date) for date in sorted(pd.Series(group["formation_date"]).dropna().unique()) if pd.notna(date)]
            factor_predictions: list[pd.DataFrame] = []
            validation_targets: list[float] = []
            validation_predictions: list[float] = []
            holdout_targets: list[float] = []
            holdout_predictions: list[float] = []
            train_rows_total = 0
            validation_rows_total = 0
            runtime_total = 0.0
            start_index = min_observations + max(0, walk_forward_validation_periods)
            step = max(1, walk_forward_test_periods)
            for test_start in range(start_index, len(unique_dates), step):
                test_dates = unique_dates[test_start : test_start + step]
                valid_start = max(min_observations, test_start - max(0, walk_forward_validation_periods))
                valid_dates = unique_dates[valid_start:test_start]
                train_dates = unique_dates[:valid_start]
                train = group.loc[group["formation_date"].isin(train_dates)].copy()
                valid = group.loc[group["formation_date"].isin(valid_dates)].copy()
                holdout = group.loc[group["formation_date"].isin(test_dates)].copy()
                if train.empty or holdout.empty:
                    continue
                model = create_model(model_name, model_params or {})
                start = perf_counter()
                model.fit(train[feature_cols], train["factor_long_short_ret_1m"], periods=train["formation_date"])
                holdout_pred = model.predict(holdout[feature_cols])
                runtime_total += perf_counter() - start
                train_rows_total += int(len(train))
                if not valid.empty:
                    valid_pred = model.predict(valid[feature_cols])
                    validation_rows_total += int(len(valid))
                    validation_targets.extend(valid["factor_long_short_ret_1m"].to_list())
                    validation_predictions.extend(np.asarray(valid_pred, dtype=float).tolist())
                holdout_targets.extend(holdout["factor_long_short_ret_1m"].to_list())
                holdout_predictions.extend(np.asarray(holdout_pred, dtype=float).tolist())
                out = holdout[["formation_date", "factor_id", "factor_long_short_ret_1m"]].copy()
                out["prediction"] = holdout_pred
                out["split"] = "holdout"
                out["model"] = model_name
                out["fold_start"] = test_dates[0]
                factor_predictions.append(out)
            if not factor_predictions:
                continue
            predictions.append(pd.concat(factor_predictions, ignore_index=True))
            valid_series = pd.Series(validation_targets, dtype="float64")
            valid_pred_series = pd.Series(validation_predictions, dtype="float64")
            holdout_series = pd.Series(holdout_targets, dtype="float64")
            holdout_pred_series = pd.Series(holdout_predictions, dtype="float64")
            metrics.append(
                {
                    "factor_id": factor_id,
                    "model": model_name,
                    "evaluation_mode": evaluation_mode,
                    "fold_count": int(len(factor_predictions)),
                    "train_rows": train_rows_total,
                    "validation_rows": validation_rows_total,
                    "holdout_rows": int(len(holdout_series)),
                    "validation_correlation": float(valid_pred_series.corr(valid_series, method="spearman")) if len(valid_series) > 1 else None,
                    "holdout_correlation": float(holdout_pred_series.corr(holdout_series, method="spearman")) if len(holdout_series) > 1 else None,
                    "validation_mae": float(np.mean(np.abs(valid_pred_series.to_numpy() - valid_series.to_numpy()))) if len(valid_series) else None,
                    "holdout_mae": float(np.mean(np.abs(holdout_pred_series.to_numpy() - holdout_series.to_numpy()))),
                    "runtime_seconds": float(runtime_total),
                }
            )
            continue
        if evaluation_mode != "single_holdout":
            raise ValueError(f"Unsupported DDQM2 evaluation mode: {evaluation_mode}")
        train_dates, valid_dates, holdout_dates = _split_dates(pd.Series(group["formation_date"]), validation_fraction, holdout_fraction)
        train = group.loc[group["formation_date"].isin(train_dates)].copy()
        valid = group.loc[group["formation_date"].isin(valid_dates)].copy()
        holdout = group.loc[group["formation_date"].isin(holdout_dates)].copy()
        if train.empty or valid.empty or holdout.empty:
            continue
        model = create_model(model_name, model_params or {})
        start = perf_counter()
        model.fit(train[feature_cols], train["factor_long_short_ret_1m"], periods=train["formation_date"])
        train_pred = model.predict(train[feature_cols])
        valid_pred = model.predict(valid[feature_cols])
        holdout_pred = model.predict(holdout[feature_cols])
        runtime = perf_counter() - start
        for split_name, split, pred in (("train", train, train_pred), ("validation", valid, valid_pred), ("holdout", holdout, holdout_pred)):
            out = split[["formation_date", "factor_id", "factor_long_short_ret_1m"]].copy()
            out["prediction"] = pred
            out["split"] = split_name
            out["model"] = model_name
            predictions.append(out)
        metrics.append(
            {
                "factor_id": factor_id,
                "model": model_name,
                "evaluation_mode": evaluation_mode,
                "fold_count": 1,
                "train_rows": int(len(train)),
                "validation_rows": int(len(valid)),
                "holdout_rows": int(len(holdout)),
                "validation_correlation": float(pd.Series(valid_pred).corr(valid["factor_long_short_ret_1m"], method="spearman")) if len(valid) > 1 else None,
                "holdout_correlation": float(pd.Series(holdout_pred).corr(holdout["factor_long_short_ret_1m"], method="spearman")) if len(holdout) > 1 else None,
                "validation_mae": float(np.mean(np.abs(np.asarray(valid_pred) - valid["factor_long_short_ret_1m"].to_numpy()))),
                "holdout_mae": float(np.mean(np.abs(np.asarray(holdout_pred) - holdout["factor_long_short_ret_1m"].to_numpy()))),
                "runtime_seconds": float(runtime),
            }
        )
    if not predictions:
        return FactorModelResult(pd.DataFrame(), pd.DataFrame(metrics))
    return FactorModelResult(pd.concat(predictions, ignore_index=True), pd.DataFrame(metrics))


def select_factor_universe(
    factor_returns: pd.DataFrame,
    feature_panel: pd.DataFrame,
    definitions: Sequence[FactorDefinition],
    *,
    universe: str = "all_implemented_current",
    target_count: int = 13,
    overrides: Sequence[str] | None = None,
    macro_feature_design: str = "current_macro_family",
) -> tuple[tuple[FactorDefinition, ...], pd.DataFrame]:
    """Select the eligible factor universe for DDQM2-style modeling.

    ``selected_13_global_local`` is a reproducible approximation of the DDQM2
    global/local alpha screen: long-run factor return strength plus the best
    macro-state-conditioned factor potential across median-split macro states.
    ``selected_13_plus_us_overrides`` keeps the same screen but seeds the set
    with configured U.S. substitute factor ids before filling by score.
    """

    definitions_by_id = {definition.factor_id: definition for definition in definitions}
    if universe == "all_implemented_current":
        metadata = pd.DataFrame([definition.to_dict() for definition in definitions])
        metadata["selection_reason"] = "all_implemented_current"
        metadata["selection_rank"] = range(1, len(metadata) + 1)
        return tuple(definitions), metadata
    if universe not in {"selected_13_global_local", "selected_13_plus_us_overrides"}:
        raise ValueError(f"Unsupported factor universe: {universe}")
    if factor_returns.empty:
        return (), pd.DataFrame()

    returns = factor_returns.copy()
    returns["formation_date"] = pd.to_datetime(returns["formation_date"], errors="coerce")
    returns["factor_long_short_ret_1m"] = pd.to_numeric(returns["factor_long_short_ret_1m"], errors="coerce")
    returns = returns.dropna(subset=["formation_date", "factor_id", "factor_long_short_ret_1m"])
    global_scores = _global_alpha_scores(returns)
    local_scores = _local_alpha_scores(returns, feature_panel, macro_feature_design)
    combined = global_scores.merge(local_scores, on="factor_id", how="outer").fillna(0.0)
    combined["combined_score"] = combined["global_score"].rank(pct=True) + combined["local_score"].rank(pct=True)
    combined = combined.sort_values(["combined_score", "global_score", "local_score", "factor_id"], ascending=[False, False, False, True])

    selected: list[str] = []
    if universe == "selected_13_plus_us_overrides":
        for factor_id in overrides or ():
            if factor_id in definitions_by_id and factor_id not in selected:
                selected.append(factor_id)
    for factor_id in combined["factor_id"].astype(str):
        if factor_id in definitions_by_id and factor_id not in selected:
            selected.append(factor_id)
        if len(selected) >= target_count:
            break

    selected = selected[:target_count]
    selected_defs = tuple(definitions_by_id[factor_id] for factor_id in selected)
    score_map = combined.set_index("factor_id").to_dict("index")
    rows: list[dict[str, Any]] = []
    for rank, definition in enumerate(selected_defs, start=1):
        row = definition.to_dict()
        row.update(score_map.get(definition.factor_id, {}))
        row["selection_rank"] = rank
        row["selection_reason"] = "us_override_seed" if universe == "selected_13_plus_us_overrides" and definition.factor_id in set(overrides or ()) else "global_local_alpha"
        rows.append(row)
    return selected_defs, pd.DataFrame(rows)


def _global_alpha_scores(returns: pd.DataFrame) -> pd.DataFrame:
    grouped = returns.groupby("factor_id")["factor_long_short_ret_1m"]
    scores = grouped.agg(mean_return="mean", volatility=lambda values: values.std(ddof=0), observations="count").reset_index()
    scores["global_score"] = scores["mean_return"] / (scores["volatility"].replace(0.0, np.nan).fillna(scores["mean_return"].abs().median() + 1e-9))
    scores["global_score"] = scores["global_score"].clip(lower=0.0)
    return scores[["factor_id", "global_score", "mean_return", "volatility", "observations"]]


def _local_alpha_scores(returns: pd.DataFrame, feature_panel: pd.DataFrame, macro_feature_design: str) -> pd.DataFrame:
    macro = macro_design_matrix(feature_panel, macro_feature_design)
    feature_cols = [col for col in macro.columns if col != "formation_date"]
    state_cols = [col for col in feature_cols if macro[col].nunique(dropna=True) > 1][:8]
    if not state_cols:
        return pd.DataFrame({"factor_id": sorted(returns["factor_id"].unique()), "local_score": 0.0})
    states = macro[["formation_date", *state_cols]].copy()
    for col in state_cols:
        median = pd.to_numeric(states[col], errors="coerce").median()
        states[f"{col}__state"] = np.where(pd.to_numeric(states[col], errors="coerce") >= median, "high", "low")
    state_cols = [f"{col}__state" for col in state_cols]
    merged = returns.merge(states[["formation_date", *state_cols]], on="formation_date", how="inner")
    rows: list[dict[str, Any]] = []
    for factor_id, group in merged.groupby("factor_id", sort=True):
        best = 0.0
        for state_col in state_cols:
            state_means = group.groupby(state_col)["factor_long_short_ret_1m"].mean()
            if not state_means.empty:
                best = max(best, float(state_means.max()))
        rows.append({"factor_id": factor_id, "local_score": max(0.0, best)})
    return pd.DataFrame(rows)


def build_factor_allocations(predictions: pd.DataFrame, *, min_weight: float = 0.0) -> pd.DataFrame:
    """Convert predicted factor returns into DDQM2 non-negative factor weights."""

    if predictions.empty:
        return pd.DataFrame({"formation_date": pd.Series(dtype="datetime64[ns]"), "factor_id": pd.Series(dtype="object"), "prediction": pd.Series(dtype="float64"), "weight": pd.Series(dtype="float64"), "split": pd.Series(dtype="object")})
    frame = predictions.copy()
    frame["positive_prediction"] = pd.Series(pd.to_numeric(frame["prediction"], errors="coerce"), index=frame.index).clip(lower=0.0)
    rows: list[pd.DataFrame] = []
    for _, group in frame.groupby(["formation_date", "split"], sort=True):
        denom = group["positive_prediction"].sum()
        out = group.loc[:, ["formation_date", "factor_id", "prediction", "split"]].copy()
        if pd.isna(denom) or denom <= 0:
            out["weight"] = 1.0 / len(out)
        else:
            out["weight"] = group["positive_prediction"] / denom
            if min_weight > 0:
                out["weight"] = pd.Series(out["weight"], index=out.index).clip(lower=min_weight)
                out["weight"] = out["weight"] / out["weight"].sum()
        rows.append(out)
    return pd.concat(rows, ignore_index=True)


def backtest_factor_allocations(allocations: pd.DataFrame, factor_returns: pd.DataFrame) -> pd.DataFrame:
    """Backtest the predicted factor-weight portfolio using realized factor returns."""

    if allocations.empty:
        return pd.DataFrame({"formation_date": pd.Series(dtype="datetime64[ns]"), "split": pd.Series(dtype="object"), "portfolio_return": pd.Series(dtype="float64"), "cumulative_return": pd.Series(dtype="float64")})
    realized = factor_returns.loc[:, ["formation_date", "factor_id", "factor_long_short_ret_1m"]].copy()
    merged = allocations.merge(realized, on=["formation_date", "factor_id"], how="left")
    merged["weighted_return"] = merged["weight"] * merged["factor_long_short_ret_1m"]
    portfolio = merged.groupby(["formation_date", "split"], as_index=False).agg(portfolio_return=("weighted_return", "sum"))
    portfolio = pd.DataFrame(portfolio).sort_values(by=["split", "formation_date"]).reset_index(drop=True)
    portfolio["cumulative_return"] = portfolio.groupby("split", group_keys=False)["portfolio_return"].transform(lambda returns: (1.0 + returns.fillna(0.0)).cumprod() - 1.0)
    return portfolio.sort_values(by=["formation_date"]).reset_index(drop=True)


def backtest_stock_score_qspread(
    allocations: pd.DataFrame,
    factor_scores: pd.DataFrame,
    panel: pd.DataFrame,
    *,
    return_column: str = "ret_1m_fwd",
    quantile: float = 0.10,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Backtest DDQM2-like stock-score top/bottom QSpread with diagnostics."""

    if allocations.empty or factor_scores.empty:
        empty = pd.DataFrame({"formation_date": pd.Series(dtype="datetime64[ns]"), "split": pd.Series(dtype="object"), "portfolio_return": pd.Series(dtype="float64"), "cumulative_return": pd.Series(dtype="float64")})
        return empty, pd.DataFrame()
    required = {"formation_date", "permno", return_column}
    missing = sorted(required.difference(panel.columns))
    if missing:
        raise ValueError(f"panel is missing QSpread return columns: {missing}")

    weights = allocations.loc[:, ["formation_date", "factor_id", "weight", "split"]].copy()
    scores = factor_scores.loc[:, ["formation_date", "permno", "factor_id", "factor_score"]].copy()
    merged = scores.merge(weights, on=["formation_date", "factor_id"], how="inner")
    merged["weighted_factor_score"] = pd.to_numeric(merged["factor_score"], errors="coerce") * pd.to_numeric(merged["weight"], errors="coerce")
    stock_scores = merged.groupby(["formation_date", "permno", "split"], as_index=False).agg(
        stock_score=("weighted_factor_score", "sum"),
        factors_used=("factor_id", "nunique"),
        max_factor_weight=("weight", "max"),
        herfindahl_weight=("weight", lambda values: float(np.square(pd.to_numeric(values, errors="coerce").fillna(0.0)).sum())),
    )
    realized = panel.loc[:, ["formation_date", "permno", return_column]].copy().rename(columns={return_column: "forward_return"})
    stock_scores = stock_scores.merge(realized, on=["formation_date", "permno"], how="left")
    rows: list[dict[str, Any]] = []
    leg_rows: list[dict[str, Any]] = []
    prev_long: set[Any] = set()
    prev_short: set[Any] = set()
    for (formation_date, split), group in stock_scores.groupby(["formation_date", "split"], sort=True):
        clean = group.dropna(subset=["stock_score", "forward_return"]).copy()
        if clean.empty:
            continue
        long_cut = clean["stock_score"].quantile(1.0 - quantile)
        short_cut = clean["stock_score"].quantile(quantile)
        long_leg = clean.loc[clean["stock_score"] >= long_cut]
        short_leg = clean.loc[clean["stock_score"] <= short_cut]
        long_set = set(long_leg["permno"].tolist())
        short_set = set(short_leg["permno"].tolist())
        long_turnover = _turnover(prev_long, long_set)
        short_turnover = _turnover(prev_short, short_set)
        prev_long, prev_short = long_set, short_set
        portfolio_return = float(long_leg["forward_return"].mean() - short_leg["forward_return"].mean()) if not long_leg.empty and not short_leg.empty else np.nan
        rows.append(
            {
                "formation_date": formation_date,
                "split": split,
                "portfolio_return": portfolio_return,
                "long_count": int(len(long_leg)),
                "short_count": int(len(short_leg)),
                "long_turnover": long_turnover,
                "short_turnover": short_turnover,
                "turnover": float(np.nanmean([long_turnover, short_turnover])),
                "max_factor_weight": float(clean["max_factor_weight"].max()),
                "mean_herfindahl_weight": float(clean["herfindahl_weight"].mean()),
            }
        )
        for leg_name, leg in (("long", long_leg), ("short", short_leg)):
            leg_rows.extend(
                {
                    "formation_date": formation_date,
                    "split": split,
                    "leg": leg_name,
                    "permno": row.permno,
                    "stock_score": row.stock_score,
                    "forward_return": row.forward_return,
                }
                for row in leg.itertuples(index=False)
            )
    portfolio = pd.DataFrame(rows)
    if not portfolio.empty:
        portfolio = portfolio.sort_values(["split", "formation_date"]).reset_index(drop=True)
        portfolio["cumulative_return"] = portfolio.groupby("split", group_keys=False)["portfolio_return"].transform(lambda returns: (1.0 + returns.fillna(0.0)).cumprod() - 1.0)
        portfolio = portfolio.sort_values("formation_date").reset_index(drop=True)
    return portfolio, pd.DataFrame(leg_rows)


def conservative_cost_tax_assumptions() -> dict[str, float | str]:
    """Return documented conservative defaults for long-only research costs.

    These are not tax advice.  They are deliberately simple research assumptions
    for a monthly-rebalanced long-only backtest:

    - ``transaction_cost_bps`` is charged against one-way turnover.
    - ``tax_rate`` is applied to positive monthly gains on the fraction of the
      portfolio assumed to be realized by turnover.
    """

    return {
        "transaction_cost_bps": 50.0,
        "tax_rate": 0.408,
        "taxable_gain_policy": "positive_monthly_gain_times_turnover",
        "description": "Conservative research proxy: 50 bps one-way turnover cost plus 40.8% tax drag on positive gains realized by turnover; not tax advice.",
    }


def backtest_stock_score_long_only_qspread(
    allocations: pd.DataFrame,
    factor_scores: pd.DataFrame,
    panel: pd.DataFrame,
    *,
    return_column: str = "ret_1m_fwd",
    quantile: float = 0.10,
    transaction_cost_bps: float = 50.0,
    tax_rate: float = 0.408,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Backtest a top-q equal-weight long-only stock-score QSpread surface.

    The strategy is fully invested in the highest-scoring ``quantile`` of names
    each period and has no short leg.  ``portfolio_return`` is the conservative
    net return used as the primary research lens; gross and drag components are
    retained in separate columns for auditability.
    """

    if allocations.empty or factor_scores.empty:
        empty = pd.DataFrame(
            {
                "formation_date": pd.Series(dtype="datetime64[ns]"),
                "split": pd.Series(dtype="object"),
                "portfolio_return": pd.Series(dtype="float64"),
                "portfolio_return_gross": pd.Series(dtype="float64"),
                "cumulative_return": pd.Series(dtype="float64"),
                "cumulative_return_gross": pd.Series(dtype="float64"),
            }
        )
        return empty, pd.DataFrame()
    required = {"formation_date", "permno", return_column}
    missing = sorted(required.difference(panel.columns))
    if missing:
        raise ValueError(f"panel is missing long-only QSpread return columns: {missing}")
    if not 0.0 < quantile < 1.0:
        raise ValueError("quantile must be in (0, 1) for long-only QSpread")

    weights = allocations.loc[:, ["formation_date", "factor_id", "weight", "split"]].copy()
    scores = factor_scores.loc[:, ["formation_date", "permno", "factor_id", "factor_score"]].copy()
    merged = scores.merge(weights, on=["formation_date", "factor_id"], how="inner")
    merged["weighted_factor_score"] = pd.to_numeric(merged["factor_score"], errors="coerce") * pd.to_numeric(merged["weight"], errors="coerce")
    stock_scores = merged.groupby(["formation_date", "permno", "split"], as_index=False).agg(
        stock_score=("weighted_factor_score", "sum"),
        factors_used=("factor_id", "nunique"),
        max_factor_weight=("weight", "max"),
        herfindahl_weight=("weight", lambda values: float(np.square(pd.to_numeric(values, errors="coerce").fillna(0.0)).sum())),
    )
    realized = panel.loc[:, ["formation_date", "permno", return_column]].copy().rename(columns={return_column: "forward_return"})
    stock_scores = stock_scores.merge(realized, on=["formation_date", "permno"], how="left")

    cost_rate = float(transaction_cost_bps) / 10_000.0
    tax_rate = float(tax_rate)
    rows: list[dict[str, Any]] = []
    leg_rows: list[dict[str, Any]] = []
    previous_by_split: dict[str, set[Any]] = {}
    for (formation_date, split), group in stock_scores.groupby(["formation_date", "split"], sort=True):
        clean = group.dropna(subset=["stock_score", "forward_return"]).copy()
        if clean.empty:
            continue
        long_cut = clean["stock_score"].quantile(1.0 - quantile)
        long_leg = clean.loc[clean["stock_score"] >= long_cut].copy()
        long_set = set(long_leg["permno"].tolist())
        split_key = str(split)
        turnover = _turnover(previous_by_split.get(split_key, set()), long_set)
        previous_by_split[split_key] = long_set
        gross_return = float(long_leg["forward_return"].mean()) if not long_leg.empty else np.nan
        trading_cost = float(turnover * cost_rate) if not pd.isna(gross_return) else np.nan
        taxable_gain = max(gross_return, 0.0) * min(max(turnover, 0.0), 1.0) if not pd.isna(gross_return) else np.nan
        tax_drag = float(taxable_gain * tax_rate) if not pd.isna(taxable_gain) else np.nan
        net_return = float(gross_return - trading_cost - tax_drag) if not pd.isna(gross_return) else np.nan
        rows.append(
            {
                "formation_date": formation_date,
                "split": split,
                "portfolio_return": net_return,
                "portfolio_return_net": net_return,
                "portfolio_return_gross": gross_return,
                "trading_cost_return": trading_cost,
                "tax_drag_return": tax_drag,
                "long_count": int(len(long_leg)),
                "short_count": 0,
                "turnover": turnover,
                "long_turnover": turnover,
                "short_turnover": 0.0,
                "transaction_cost_bps": float(transaction_cost_bps),
                "tax_rate": tax_rate,
                "max_factor_weight": float(clean["max_factor_weight"].max()),
                "mean_herfindahl_weight": float(clean["herfindahl_weight"].mean()),
            }
        )
        leg_rows.extend(
            {
                "formation_date": formation_date,
                "split": split,
                "leg": "long",
                "permno": row.permno,
                "stock_score": row.stock_score,
                "forward_return": row.forward_return,
                "position_weight": 1.0 / len(long_leg) if len(long_leg) else 0.0,
            }
            for row in long_leg.itertuples(index=False)
        )
    portfolio = pd.DataFrame(rows)
    if not portfolio.empty:
        portfolio = portfolio.sort_values(["split", "formation_date"]).reset_index(drop=True)
        portfolio["cumulative_return"] = portfolio.groupby("split", group_keys=False)["portfolio_return"].transform(lambda returns: (1.0 + returns.fillna(0.0)).cumprod() - 1.0)
        portfolio["cumulative_return_net"] = portfolio["cumulative_return"]
        portfolio["cumulative_return_gross"] = portfolio.groupby("split", group_keys=False)["portfolio_return_gross"].transform(lambda returns: (1.0 + returns.fillna(0.0)).cumprod() - 1.0)
        portfolio = portfolio.sort_values("formation_date").reset_index(drop=True)
    return portfolio, pd.DataFrame(leg_rows)


def cost_tax_sensitivity(portfolio: pd.DataFrame, *, cost_bps_grid: Sequence[float] = (10.0, 25.0, 50.0, 100.0), tax_rate_grid: Sequence[float] = (0.0, 0.20, 0.35, 0.408)) -> pd.DataFrame:
    """Recompute simple long-only net outcomes across cost/tax assumptions."""

    if portfolio.empty or "portfolio_return_gross" not in portfolio.columns:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    frame = portfolio.copy()
    gross = pd.to_numeric(frame["portfolio_return_gross"], errors="coerce").fillna(0.0)
    turnover = pd.to_numeric(frame.get("turnover", 0.0), errors="coerce").fillna(0.0).clip(lower=0.0, upper=1.0)
    for split, split_index in frame.groupby("split", sort=True).groups.items():
        idx = list(split_index)
        for cost_bps in cost_bps_grid:
            cost_rate = float(cost_bps) / 10_000.0
            for tax_rate in tax_rate_grid:
                net = gross.loc[idx] - turnover.loc[idx] * cost_rate - gross.loc[idx].clip(lower=0.0) * turnover.loc[idx] * float(tax_rate)
                equity = (1.0 + net).cumprod()
                drawdown = equity / equity.cummax() - 1.0
                rows.append(
                    {
                        "split": split,
                        "transaction_cost_bps": float(cost_bps),
                        "tax_rate": float(tax_rate),
                        "periods": int(len(net)),
                        "mean_monthly_return": float(net.mean()),
                        "volatility_monthly": float(net.std(ddof=0)),
                        "cumulative_return": float(equity.iloc[-1] - 1.0) if len(equity) else 0.0,
                        "max_drawdown": float(drawdown.min()) if len(drawdown) else 0.0,
                    }
                )
    return pd.DataFrame(rows)


def _turnover(previous: set[Any], current: set[Any]) -> float:
    if not current:
        return 0.0
    if not previous:
        return 1.0
    return 1.0 - (len(previous.intersection(current)) / len(current))
