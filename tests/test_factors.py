from __future__ import annotations
# pyright: reportMissingImports=false, reportMissingTypeStubs=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportCallIssue=false, reportUnusedCallResult=false

from pathlib import Path
import subprocess
import sys

import pandas as pd

from autoquant_lab.eqr.factors import (
    FactorDefinition,
    backtest_factor_allocations,
    build_factor_allocations,
    build_factor_long_short_returns,
    build_factor_scores,
    train_factor_return_models,
)
from autoquant_lab.eqr.factors.definitions import all_factor_definitions, implemented_factor_definitions


def _synthetic_panel(months: int = 12, assets: int = 12) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    dates = pd.date_range("2020-01-31", periods=months, freq="ME")
    for month_index, date in enumerate(dates):
        for permno in range(1, assets + 1):
            quality = float(permno + month_index * 0.1)
            value = float(assets - permno + month_index * 0.05)
            rows.append(
                {
                    "formation_date": date,
                    "permno": permno,
                    "permco": permno,
                    "exchcd": 1 if permno <= assets / 2 else 2,
                    "ret_1m_fwd": quality * 0.002 - value * 0.001 + month_index * 0.0005,
                    "compustat__pb": value,
                    "compustat__pe_proxy": value + 1.0,
                    "compustat__debt_to_assets": value / 10.0,
                    "compustat__revenue_yoy": quality,
                    "compustat__net_income_yoy": quality + 0.5,
                    "ibes__revision_1m": quality,
                    "ibes__surprise": quality / 2.0,
                    "ibes__estimate_dispersion": value / 3.0,
                    "ibes__target_price_mean": quality + 5.0,
                    "ibes__target_revision_balance_1m": quality / 4.0,
                    "crsp__mom_12_2": quality,
                    "crsp__mom_6_2": value,
                    "crsp__reversal_1m": value / 2.0,
                    "crsp__log_size": value + 2.0,
                    "macro__term_spread": float(month_index),
                    "macro__credit_spread": float(month_index % 3),
                }
            )
    return pd.DataFrame(rows)


def test_factor_registry_tracks_eqr_taxonomy() -> None:
    definitions = all_factor_definitions()
    assert len(definitions) == 55
    assert len(implemented_factor_definitions()) >= 50
    assert any(definition.status == "unavailable" for definition in definitions)


def test_factor_scores_and_long_short_returns() -> None:
    frame = _synthetic_panel(months=6, assets=20)
    definitions = (
        FactorDefinition("quality", "Quality", "quality", "global", "compustat__revenue_yoy", 1.0, "implemented", "test"),
        FactorDefinition("value_local", "Value", "valuation", "local", "compustat__pb", -1.0, "implemented", "test"),
    )
    scores, metadata = build_factor_scores(frame, definitions)
    returns = build_factor_long_short_returns(scores, frame, quantile=0.2)

    assert set(metadata["factor_id"]) == {"quality", "value_local"}
    assert set(scores["factor_id"]) == {"quality", "value_local"}
    assert set(returns["factor_id"]) == {"quality", "value_local"}
    assert returns["factor_long_short_ret_1m"].notna().all()
    assert (returns["long_count"] > 0).all()
    assert (returns["short_count"] > 0).all()


def test_ddqm2_models_allocations_and_backtest() -> None:
    frame = _synthetic_panel(months=12, assets=20)
    definitions = (
        FactorDefinition("quality", "Quality", "quality", "global", "compustat__revenue_yoy", 1.0, "implemented", "test"),
        FactorDefinition("value", "Value", "valuation", "global", "compustat__pb", -1.0, "implemented", "test"),
    )
    scores, _ = build_factor_scores(frame, definitions)
    returns = build_factor_long_short_returns(scores, frame, quantile=0.2)
    result = train_factor_return_models(returns, frame, model_name="baseline_mean", validation_fraction=0.2, holdout_fraction=0.2, min_observations=6)
    allocations = build_factor_allocations(result.predictions)
    portfolio = backtest_factor_allocations(allocations, returns)

    assert not result.predictions.empty
    assert not result.metrics.empty
    assert allocations.groupby(["formation_date", "split"])["weight"].sum().round(8).eq(1.0).all()
    assert not portfolio.empty
    assert "cumulative_return" in portfolio.columns


def test_eqr_run_ddqm2_cli_writes_artifacts(tmp_path: Path) -> None:
    panel_path = tmp_path / "panel.parquet"
    feature_dir = tmp_path / "features"
    output_dir = tmp_path / "ddqm2"
    feature_dir.mkdir()
    frame = _synthetic_panel(months=10, assets=20)
    panel = frame[["formation_date", "permno", "permco", "exchcd", "ret_1m_fwd"]].copy()
    features = frame.drop(columns=["permco", "ret_1m_fwd"])
    panel.to_parquet(panel_path, index=False)
    features.to_parquet(feature_dir / "features.parquet", index=False)

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/eqr_run_ddqm2.py",
            "--panel",
            str(panel_path),
            "--feature-dir",
            str(feature_dir),
            "--output-dir",
            str(output_dir),
            "--model",
            "baseline_mean",
            "--run-id",
            "unit_ddqm2",
            "--min-observations",
            "6",
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    assert "unit_ddqm2" in completed.stdout
    run_dir = output_dir / "unit_ddqm2"
    for name in (
        "factor_scores.parquet",
        "factor_metadata.csv",
        "factor_returns.parquet",
        "factor_predictions.parquet",
        "factor_model_metrics.csv",
        "factor_allocations.parquet",
        "portfolio_returns.parquet",
        "portfolio_summary.json",
        "report.md",
        "manifest.json",
    ):
        assert (run_dir / name).exists()
