from __future__ import annotations
# pyright: reportMissingImports=false, reportMissingTypeStubs=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportCallIssue=false, reportUnusedCallResult=false

from pathlib import Path
import subprocess
import sys

import pandas as pd

from autoquant_lab.eqr.factors import (
    FactorDefinition,
    backtest_factor_allocations,
    backtest_stock_score_long_only_qspread,
    backtest_stock_score_qspread,
    build_factor_allocations,
    build_factor_long_short_returns,
    build_factor_scores,
    macro_design_columns,
    select_factor_universe,
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


def test_selected_13_global_local_factor_universe_is_reproducible() -> None:
    frame = _synthetic_panel(months=18, assets=20)
    factor_scores, definitions_metadata = build_factor_scores(frame)
    returns = build_factor_long_short_returns(factor_scores, frame, quantile=0.2)
    definitions = tuple(
        definition
        for definition in implemented_factor_definitions()
        if definition.factor_id in set(definitions_metadata["factor_id"].astype(str))
    )

    selected, metadata = select_factor_universe(
        returns,
        frame,
        definitions,
        universe="selected_13_global_local",
        target_count=13,
    )

    assert len(selected) == 13
    assert len({definition.factor_id for definition in selected}) == 13
    assert metadata["selection_rank"].tolist() == list(range(1, 14))
    assert metadata["selection_reason"].eq("global_local_alpha").all()


def test_macro_feature_design_variants_select_expected_columns() -> None:
    frame = _synthetic_panel(months=6, assets=12)
    frame["macro__sp500"] = 1.0
    frame["macro__sp500_c20"] = 1.0
    frame["macro__sp500_c60"] = 1.0
    current, current_missing = macro_design_columns(frame, "current_macro_family")
    ddqm2, ddqm2_missing = macro_design_columns(frame, "ddqm2_25x3_us_macro")

    assert "macro__term_spread" in current
    assert current_missing == []
    assert {"macro__sp500", "macro__sp500_c20", "macro__sp500_c60"}.issubset(set(ddqm2))
    assert "macro__treasury_2y" in ddqm2_missing


def test_stock_score_qspread_surface_records_turnover_and_legs() -> None:
    frame = _synthetic_panel(months=12, assets=20)
    definitions = (
        FactorDefinition("quality", "Quality", "quality", "global", "compustat__revenue_yoy", 1.0, "implemented", "test"),
        FactorDefinition("value", "Value", "valuation", "global", "compustat__pb", -1.0, "implemented", "test"),
    )
    scores, _ = build_factor_scores(frame, definitions)
    returns = build_factor_long_short_returns(scores, frame, quantile=0.2)
    result = train_factor_return_models(returns, frame, model_name="baseline_mean", validation_fraction=0.2, holdout_fraction=0.2, min_observations=6)
    allocations = build_factor_allocations(result.predictions)

    portfolio, legs = backtest_stock_score_qspread(allocations, scores, frame, quantile=0.10)

    assert not portfolio.empty
    assert {"long_count", "short_count", "turnover", "max_factor_weight", "mean_herfindahl_weight"}.issubset(portfolio.columns)
    assert portfolio["long_count"].min() > 0
    assert portfolio["short_count"].min() > 0
    assert not legs.empty


def test_stock_score_long_only_qspread_is_top_q_equal_weight_net_of_costs() -> None:
    frame = _synthetic_panel(months=12, assets=20)
    definitions = (
        FactorDefinition("quality", "Quality", "quality", "global", "compustat__revenue_yoy", 1.0, "implemented", "test"),
        FactorDefinition("value", "Value", "valuation", "global", "compustat__pb", -1.0, "implemented", "test"),
    )
    scores, _ = build_factor_scores(frame, definitions)
    returns = build_factor_long_short_returns(scores, frame, quantile=0.2)
    result = train_factor_return_models(returns, frame, model_name="baseline_mean", validation_fraction=0.2, holdout_fraction=0.2, min_observations=6)
    allocations = build_factor_allocations(result.predictions)

    portfolio, legs = backtest_stock_score_long_only_qspread(
        allocations,
        scores,
        frame,
        quantile=0.20,
        transaction_cost_bps=100.0,
        tax_rate=0.50,
    )

    assert not portfolio.empty
    assert not legs.empty
    assert set(legs["leg"]) == {"long"}
    assert portfolio["short_count"].eq(0).all()
    assert portfolio["long_count"].min() > 0
    assert {"portfolio_return_gross", "portfolio_return_net", "trading_cost_return", "tax_drag_return", "cumulative_return_gross"}.issubset(portfolio.columns)
    assert portfolio["portfolio_return"].equals(portfolio["portfolio_return_net"])
    first = portfolio.sort_values("formation_date").iloc[0]
    expected_net = first["portfolio_return_gross"] - first["trading_cost_return"] - first["tax_drag_return"]
    assert abs(first["portfolio_return_net"] - expected_net) < 1e-12


def test_walk_forward_models_emit_long_oos_holdout() -> None:
    frame = _synthetic_panel(months=36, assets=20)
    factor_scores, _ = build_factor_scores(frame)
    returns = build_factor_long_short_returns(factor_scores, frame)

    result = train_factor_return_models(
        returns,
        frame,
        model_name="baseline_mean",
        min_observations=12,
        evaluation_mode="walk_forward",
        walk_forward_test_periods=6,
        walk_forward_validation_periods=6,
    )

    assert not result.predictions.empty
    assert set(result.predictions["split"]) == {"holdout"}
    assert result.predictions["formation_date"].nunique() > 6
    assert result.metrics["fold_count"].max() > 1


def test_backtest_cumulative_return_resets_by_split() -> None:
    allocations = pd.DataFrame(
        [
            {"formation_date": pd.Timestamp("2020-01-31"), "factor_id": "f1", "prediction": 1.0, "weight": 1.0, "split": "train"},
            {"formation_date": pd.Timestamp("2020-02-29"), "factor_id": "f1", "prediction": 1.0, "weight": 1.0, "split": "holdout"},
        ]
    )
    factor_returns = pd.DataFrame(
        [
            {"formation_date": pd.Timestamp("2020-01-31"), "factor_id": "f1", "factor_long_short_ret_1m": 1.0},
            {"formation_date": pd.Timestamp("2020-02-29"), "factor_id": "f1", "factor_long_short_ret_1m": 0.1},
        ]
    )

    portfolio = backtest_factor_allocations(allocations, factor_returns)

    holdout_cumulative = portfolio.loc[portfolio["split"] == "holdout", "cumulative_return"].iloc[0]
    assert abs(holdout_cumulative - 0.1) < 1e-12


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
            "--factor-score-chunk-dates",
            "0",
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


def test_eqr_run_ddqm2_chunked_cli_matches_unchunked_returns(tmp_path: Path) -> None:
    panel_path = tmp_path / "panel.parquet"
    feature_dir = tmp_path / "features"
    output_dir = tmp_path / "ddqm2"
    feature_dir.mkdir()
    frame = _synthetic_panel(months=10, assets=20)
    panel = frame[["formation_date", "permno", "permco", "exchcd", "ret_1m_fwd"]].copy()
    features = frame.drop(columns=["permco", "ret_1m_fwd"])
    panel.to_parquet(panel_path, index=False)
    features.to_parquet(feature_dir / "features.parquet", index=False)

    common_args = [
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
        "--min-observations",
        "6",
    ]
    subprocess.run(
        [*common_args, "--run-id", "unit_full", "--factor-score-chunk-dates", "0"],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [*common_args, "--run-id", "unit_chunked", "--factor-score-chunk-dates", "3"],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    full_returns = pd.read_parquet(output_dir / "unit_full" / "factor_returns.parquet")
    chunked_returns = pd.read_parquet(output_dir / "unit_chunked" / "factor_returns.parquet")
    pd.testing.assert_frame_equal(full_returns, chunked_returns)
    assert (output_dir / "unit_full" / "factor_scores.parquet").exists()
    score_parts = sorted((output_dir / "unit_chunked" / "factor_scores").glob("part-*.parquet"))
    assert len(score_parts) == 4
    chunked_score_rows = sum(len(pd.read_parquet(path)) for path in score_parts)
    assert chunked_score_rows == len(pd.read_parquet(output_dir / "unit_full" / "factor_scores.parquet"))


def test_eqr_run_ddqm2_chunked_stock_score_qspread_matches_unchunked_portfolio(tmp_path: Path) -> None:
    panel_path = tmp_path / "panel.parquet"
    feature_dir = tmp_path / "features"
    output_dir = tmp_path / "ddqm2"
    feature_dir.mkdir()
    frame = _synthetic_panel(months=12, assets=20)
    panel = frame[["formation_date", "permno", "permco", "exchcd", "ret_1m_fwd"]].copy()
    features = frame.drop(columns=["permco", "ret_1m_fwd"])
    panel.to_parquet(panel_path, index=False)
    features.to_parquet(feature_dir / "features.parquet", index=False)

    common_args = [
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
        "--min-observations",
        "6",
        "--portfolio-surface",
        "stock_score_qspread_ddqm2",
    ]
    subprocess.run(
        [*common_args, "--run-id", "unit_qspread_full", "--factor-score-chunk-dates", "0"],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [*common_args, "--run-id", "unit_qspread_chunked", "--factor-score-chunk-dates", "3"],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    full_portfolio = pd.read_parquet(output_dir / "unit_qspread_full" / "portfolio_returns.parquet")
    chunked_portfolio = pd.read_parquet(output_dir / "unit_qspread_chunked" / "portfolio_returns.parquet")
    pd.testing.assert_frame_equal(full_portfolio, chunked_portfolio)


def test_eqr_run_ddqm2_cli_writes_report_with_sparse_holdout_metrics(tmp_path: Path) -> None:
    panel_path = tmp_path / "panel.parquet"
    feature_dir = tmp_path / "features"
    output_dir = tmp_path / "ddqm2"
    feature_dir.mkdir()
    frame = _synthetic_panel(months=6, assets=20)
    panel = frame[["formation_date", "permno", "permco", "exchcd", "ret_1m_fwd"]].copy()
    features = frame.drop(columns=["permco", "ret_1m_fwd"])
    panel.to_parquet(panel_path, index=False)
    features.to_parquet(feature_dir / "features.parquet", index=False)

    subprocess.run(
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
            "unit_sparse_metrics",
            "--min-observations",
            "6",
            "--factor-score-chunk-dates",
            "2",
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    report = (output_dir / "unit_sparse_metrics" / "report.md").read_text(encoding="utf-8")
    assert "Top holdout factor models" in report


def test_eqr_run_ddqm2_cli_rejects_factor_score_budget(tmp_path: Path) -> None:
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
            "unit_guarded",
            "--max-factor-score-rows",
            "1",
        ],
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "Estimated factor-score rows exceed safety cap" in completed.stderr
    assert not (output_dir / "unit_guarded").exists()


def test_eqr_run_ddqm2_budget_guard_runs_before_feature_load(tmp_path: Path) -> None:
    panel_path = tmp_path / "panel.parquet"
    output_dir = tmp_path / "ddqm2"
    frame = _synthetic_panel(months=10, assets=20)
    panel = frame[["formation_date", "permno", "permco", "exchcd", "ret_1m_fwd"]].copy()
    panel.to_parquet(panel_path, index=False)

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/eqr_run_ddqm2.py",
            "--panel",
            str(panel_path),
            "--feature-dir",
            str(tmp_path / "missing_features"),
            "--output-dir",
            str(output_dir),
            "--model",
            "baseline_mean",
            "--run-id",
            "unit_guarded_no_features",
            "--max-factor-score-rows",
            "1",
        ],
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "Estimated factor-score rows exceed safety cap" in completed.stderr
    assert "Prepared feature directory" not in completed.stderr
    assert not (output_dir / "unit_guarded_no_features").exists()
