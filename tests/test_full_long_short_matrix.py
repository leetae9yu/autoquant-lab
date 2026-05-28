from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pandas as pd

from scripts import eqr_run_full_long_short_matrix as harness


def test_full_long_short_command_preserves_walk_forward_surface(tmp_path: Path) -> None:
    args = harness.parse_args(
        [
            "--ledger",
            str(tmp_path / "ledger.json"),
            "--report",
            str(tmp_path / "report.md"),
            "--output-dir",
            str(tmp_path / "runs"),
            "--models",
            "baseline_mean",
            "--quantiles",
            "0.30",
            "--dry-run",
        ]
    )
    spec = harness.run_specs(args)[0]
    command = harness.build_command(args, spec, "unit_full_long_short")

    assert "--portfolio-surface" in command
    assert command[command.index("--portfolio-surface") + 1] == "stock_score_qspread_ddqm2"
    assert command[command.index("--evaluation-mode") + 1] == "walk_forward"
    assert command[command.index("--walk-forward-test-periods") + 1] == "12"
    assert command[command.index("--walk-forward-validation-periods") + 1] == "12"
    assert command[command.index("--factor-score-chunk-dates") + 1] == "12"
    assert command[command.index("--feature-dir") + 1].endswith("features_full_chunked")


def test_long_short_sensitivity_charges_turnover_borrow_and_tax_proxy() -> None:
    portfolio = pd.DataFrame(
        {
            "formation_date": pd.date_range("2020-01-31", periods=3, freq="ME"),
            "split": ["holdout", "holdout", "holdout"],
            "portfolio_return": [0.02, -0.01, 0.03],
            "long_turnover": [1.0, 0.5, 0.25],
            "short_turnover": [1.0, 0.25, 0.25],
        }
    )

    zero = harness.long_short_sensitivity(portfolio, cost_bps_grid=[0.0], borrow_bps_grid=[0.0], slippage_bps_grid=[0.0], tax_proxy_grid=[0.0])
    costly = harness.long_short_sensitivity(portfolio, cost_bps_grid=[100.0], borrow_bps_grid=[120.0], slippage_bps_grid=[50.0], tax_proxy_grid=[0.0])
    taxed = harness.long_short_sensitivity(portfolio, cost_bps_grid=[100.0], borrow_bps_grid=[120.0], slippage_bps_grid=[50.0], tax_proxy_grid=[0.408])

    assert not zero.empty
    assert not costly.empty
    assert not taxed.empty
    assert costly["cumulative_return"].iloc[0] < zero["cumulative_return"].iloc[0]
    assert taxed["cumulative_return"].iloc[0] < costly["cumulative_return"].iloc[0]
    assert taxed["mean_tax_drag"].iloc[0] > 0.0


def test_full_long_short_dry_run_writes_additive_ledger_and_report(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    report = tmp_path / "report.md"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/eqr_run_full_long_short_matrix.py",
            "--ledger",
            str(ledger),
            "--report",
            str(report),
            "--output-dir",
            str(tmp_path / "runs"),
            "--models",
            "baseline_mean",
            "--quantiles",
            "0.30",
            "--dry-run",
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert "dry_run" in completed.stdout
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    assert payload["data_boundary"] == harness.DATA_BOUNDARY
    assert payload["guardrails"]["no_wrds_login"] is True
    assert payload["guardrails"]["single_heavy_experiment_at_a_time"] is True
    assert payload["matrix_runs"][0]["branch_decision"] == "dry_run_planned"
    assert "one heavy experiment at a time" in report.read_text(encoding="utf-8")
