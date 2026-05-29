from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

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

    zero = harness.long_short_sensitivity(
        portfolio,
        cost_bps_grid=[0.0],
        borrow_bps_grid=[0.0],
        slippage_bps_grid=[0.0],
        tax_proxy_grid=[0.0],
    )
    costly = harness.long_short_sensitivity(
        portfolio,
        cost_bps_grid=[100.0],
        borrow_bps_grid=[120.0],
        slippage_bps_grid=[50.0],
        tax_proxy_grid=[0.0],
    )
    taxed = harness.long_short_sensitivity(
        portfolio,
        cost_bps_grid=[100.0],
        borrow_bps_grid=[120.0],
        slippage_bps_grid=[50.0],
        tax_proxy_grid=[0.408],
    )

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
    assert payload["artifact_no_overwrite_policy"]["per_run_manifest"] == "skip_existing_never_overwrite"
    assert payload["matrix_runs"][0]["branch_decision"] == "dry_run_planned"
    assert "one heavy experiment at a time" in report.read_text(encoding="utf-8")


def test_scorecard_defers_completed_branch_without_interpretability() -> None:
    item = {
        "run_id": "unit_rf_q10",
        "run_dir": "/tmp/missing",
        "command": ["python", "scripts/eqr_run_ddqm2.py"],
        "data_boundary": harness.DATA_BOUNDARY,
        "interpretability_evidence": {
            "model_factor_importance": False,
            "global_local_table": False,
            "leg_attribution": False,
            "worst_drawdown_explanation": False,
            "next_hypothesis": True,
            "limitations_or_defer_reason": True,
        },
    }
    row = {
        "status": "ok",
        "periods": 120,
        "cumulative_return": 10.0,
        "cagr": 0.25,
        "mdd": -0.30,
        "turnover": 0.70,
    }

    scorecard = harness.build_scorecard(item, row)

    assert scorecard["decision"] == "defer"
    assert scorecard["adoption_eligible"] is False
    assert "model_factor_importance" in scorecard["dimensions"]["interpretability"]["missing"]


def test_scorecard_can_adopt_only_with_all_interpretability_evidence() -> None:
    item = {
        "run_id": "unit_rf_q10",
        "run_dir": "/tmp/missing",
        "command": ["python", "scripts/eqr_run_ddqm2.py"],
        "data_boundary": harness.DATA_BOUNDARY,
        "interpretability_evidence": {key: True for key in harness.REQUIRED_INTERPRETABILITY_EVIDENCE},
    }
    row = {
        "status": "ok",
        "periods": 120,
        "cumulative_return": 10.0,
        "cagr": 0.25,
        "mdd": -0.50,
        "turnover": 1.20,
    }

    scorecard = harness.build_scorecard(item, row)

    assert scorecard["decision"] == "adopt"
    assert scorecard["adoption_eligible"] is True
    assert scorecard["dimensions"]["drawdown"]["mdd"] == -0.50
    assert scorecard["dimensions"]["turnover_resource_realism"]["turnover"] == 1.20


def test_full_long_short_dry_run_adds_scorecard_and_guardrails(tmp_path: Path) -> None:
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
    run = payload["matrix_runs"][0]
    assert payload["cloud_policy"] == harness.NO_CLOUD_POLICY
    assert payload["guardrails"]["no_cloud_or_oci_auto_provisioning"] is True
    assert payload["guardrails"]["not_investment_trading_legal_tax_or_production_advice"] is True
    assert run["autonomous_decision"] == "continue"
    assert run["scorecard"]["dimensions"]["interpretability"]["missing"]
    assert "Research diagnostics only" in report.read_text(encoding="utf-8")
    assert "no OCI/cloud auto-provisioning" in report.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "existing_name",
    ["ledger.json", "report.md", "report.csv", "report_sensitivity.csv"],
)
def test_full_long_short_refuses_existing_output_artifacts(tmp_path: Path, existing_name: str) -> None:
    ledger = tmp_path / "ledger.json"
    report = tmp_path / "report.md"
    existing = tmp_path / existing_name
    existing.write_text("keep", encoding="utf-8")

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
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "Refusing to overwrite" in completed.stderr
    assert existing.read_text(encoding="utf-8") == "keep"


def test_existing_run_dir_without_manifest_is_not_overwritten(tmp_path: Path) -> None:
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
            "--run-prefix",
            "unit",
        ]
    )
    run_dir = tmp_path / "runs" / "unit_baseline_mean_q30"
    run_dir.mkdir(parents=True)
    sentinel = run_dir / "sentinel.txt"
    sentinel.write_text("keep", encoding="utf-8")

    rows = harness.run_matrix(args, "unit")

    assert rows[0]["branch_decision"] == "failed_existing_run_dir_without_manifest"
    assert rows[0]["returncode"] == 2
    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_existing_manifest_is_skipped_and_preserved(tmp_path: Path) -> None:
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
            "--run-prefix",
            "unit",
        ]
    )
    run_dir = tmp_path / "runs" / "unit_baseline_mean_q30"
    run_dir.mkdir(parents=True)
    manifest = run_dir / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "model": "baseline_mean",
                "quantile": 0.30,
                "portfolio_summary": {"periods": 1},
            }
        ),
        encoding="utf-8",
    )

    rows = harness.run_matrix(args, "unit")

    assert rows[0]["branch_decision"] == "skipped_existing_manifest"
    assert rows[0]["returncode"] == 0
    assert json.loads(manifest.read_text(encoding="utf-8"))["model"] == "baseline_mean"


def test_heavy_execution_requires_explicit_opt_in(tmp_path: Path) -> None:
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
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    run = payload["matrix_runs"][0]
    assert run["branch_decision"] == "blocked_requires_execute_heavy_experiments"
    assert run["returncode"] == 3
    assert "requires --execute-heavy-experiments" in run["stderr"]


def test_scorecard_records_net_robustness_when_sensitivity_path_exists() -> None:
    item = {
        "run_id": "unit_rf_q10",
        "run_dir": "/tmp/missing",
        "command": ["python", "scripts/eqr_run_ddqm2.py"],
        "data_boundary": harness.DATA_BOUNDARY,
        "sensitivity_path": "/tmp/sensitivity.csv",
        "interpretability_evidence": {key: True for key in harness.REQUIRED_INTERPRETABILITY_EVIDENCE},
    }
    row = {"status": "ok", "periods": 12, "cumulative_return": 1.0, "cagr": 0.10, "mdd": -0.2, "turnover": 0.5}

    scorecard = harness.build_scorecard(item, row)

    assert scorecard["dimensions"]["net_robustness"]["available"] is True
