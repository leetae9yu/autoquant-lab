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
    assert "--drop-factor-scores-after-run" not in command


def test_full_long_short_command_can_enable_storage_light_child_run(tmp_path: Path) -> None:
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
            "--drop-factor-scores-after-run",
            "--dry-run",
        ]
    )
    spec = harness.run_specs(args)[0]
    command = harness.build_command(args, spec, "unit_storage_light")

    assert "--drop-factor-scores-after-run" in command


def test_factor_router_axes_expand_and_build_exact_runner_mapping(tmp_path: Path) -> None:
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
            "--factor-counts",
            "13",
            "--factor-selection-policies",
            "selected_13_global_local",
            "local_only",
            "global_only",
            "quota",
            "category_capped",
            "--global-local-quotas",
            "6:7",
            "--category-caps",
            "3",
            "--min-weights",
            "0.00",
            "0.01",
            "--dry-run",
        ]
    )

    specs = harness.run_specs(args)
    policies = {spec["factor_selection_policy"] for spec in specs}
    assert {"selected_13_global_local", "local_only", "global_only", "quota", "category_capped"}.issubset(policies)
    quota = next(spec for spec in specs if spec["factor_selection_policy"] == "quota")
    capped = next(spec for spec in specs if spec["factor_selection_policy"] == "category_capped")
    selected = next(spec for spec in specs if spec["factor_selection_policy"] == "selected_13_global_local")

    quota_command = harness.build_command(args, quota, "unit_quota")
    capped_command = harness.build_command(args, capped, "unit_cap")
    selected_command = harness.build_command(args, selected, "unit_selected")

    assert selected_command[selected_command.index("--factor-universe") + 1] == "selected_13_global_local"
    assert selected_command[selected_command.index("--factor-selection-policy") + 1] == "selected_13_global_local"
    assert quota_command[quota_command.index("--factor-selection-policy") + 1] == "quota"
    assert quota_command[quota_command.index("--global-local-quota") + 1] == "6:7"
    assert capped_command[capped_command.index("--factor-selection-policy") + 1] == "category_capped"
    assert capped_command[capped_command.index("--category-cap") + 1] == "3"


def test_factor_router_invalid_axes_are_rejected_before_subprocess(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(harness, "_run", lambda command: calls.append(command) or {"returncode": 0, "stdout": "", "stderr": ""})
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
            "--factor-counts",
            "7",
            "--factor-selection-policies",
            "quota",
            "--execute-heavy-experiments",
        ]
    )

    rows = harness.run_matrix(args, "unit")

    assert calls == []
    assert rows[0]["branch_decision"] == "rejected_invalid_axis_combination"
    assert rows[0]["invalid_axis_reason"] == "quota policy requires --global-local-quotas G:L"


def test_factor_router_dry_run_never_invokes_subprocess_and_ledgers_axes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(harness, "_run", lambda command: pytest.fail("dry-run must not invoke subprocess"))
    ledger = tmp_path / "ledger.json"
    report = tmp_path / "report.md"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/eqr_run_full_long_short_matrix.py",
            "--dry-run",
            "--models",
            "baseline_mean",
            "--quantiles",
            "0.30",
            "--factor-counts",
            "7",
            "13",
            "--factor-selection-policies",
            "selected_13_global_local",
            "local_only",
            "global_only",
            "quota",
            "category_capped",
            "--global-local-quotas",
            "6:7",
            "--category-caps",
            "3",
            "--macro-feature-designs",
            "ddqm2_25x3_us_macro",
            "--min-weights",
            "0.00",
            "0.01",
            "--max-runs",
            "10",
            "--ledger",
            str(ledger),
            "--report",
            str(report),
            "--output-dir",
            str(tmp_path / "runs"),
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert "dry_run" in completed.stdout
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    assert payload["matrix_runs"]
    first = payload["matrix_runs"][0]
    assert {"factor_selection_policy", "factor_universe_target_count", "optional_axis_state", "router_state"}.issubset(first)
    assert first["router_state"] == "planned_only"
    assert first["scorecard"]["dimensions"]["gross_oos_performance"]["available"] is False
    assert "Dry-run router state `planned_only` never uses observed OOS" in report.read_text(encoding="utf-8")


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


def test_heavy_execution_requires_single_run_gate(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/eqr_run_full_long_short_matrix.py",
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
            "--execute-heavy-experiments",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "pass --max-runs 1" in completed.stderr
    assert not (tmp_path / "ledger.json").exists()


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


def test_scorecard_reproducibility_requires_child_manifest_boundary() -> None:
    item = {
        "run_id": "unit_rf_q10",
        "run_dir": "/tmp/missing",
        "command": ["python", "scripts/eqr_run_ddqm2.py"],
        "data_boundary": harness.DATA_BOUNDARY,
        "interpretability_evidence": {key: True for key in harness.REQUIRED_INTERPRETABILITY_EVIDENCE},
    }
    row = {
        "status": "ok",
        "periods": 12,
        "cumulative_return": 1.0,
        "cagr": 0.10,
        "mdd": -0.2,
        "turnover": 0.5,
        "data_boundary": "different_child_boundary",
    }

    scorecard = harness.build_scorecard(item, row)

    assert scorecard["dimensions"]["reproducibility"]["available"] is False
    assert scorecard["dimensions"]["reproducibility"]["child_manifest_data_boundary"] == "different_child_boundary"


def test_runner_help_includes_factor_router_flags() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/eqr_run_ddqm2.py", "--help"],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert "--factor-selection-policy" in completed.stdout
    assert "--global-local-quota" in completed.stdout
    assert "--category-cap" in completed.stdout


def test_sequential_plan_artifact_contains_anchor_and_safety_language(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "anchor"
    run_dir.mkdir(parents=True)
    (run_dir / "manifest.json").write_text(
        json.dumps({"model": "baseline_mean", "quantile": 0.30, "portfolio_summary": {"periods": 12}}),
        encoding="utf-8",
    )
    args = harness.parse_args(
        [
            "--ledger",
            str(tmp_path / "ledger.json"),
            "--report",
            str(tmp_path / "report.md"),
            "--output-dir",
            str(tmp_path / "runs"),
            "--sequential-plan",
            str(tmp_path / "seq.md"),
        ]
    )
    ledger = {"matrix_runs": [{"run_id": "anchor", "run_dir": str(run_dir), "returncode": 0}]}

    path = harness.write_sequential_plan(args, ledger)

    assert path == tmp_path / "seq.md"
    text = path.read_text(encoding="utf-8")
    assert "Anchor run id: `anchor`" in text
    assert "--max-runs 1" in text
    assert "--factor-counts 7 --max-runs 1" in text
    assert "--factor-selection-policies local_only --factor-counts 13 --max-runs 1" in text
    assert "--factor-selection-policies global_only --factor-counts 13 --max-runs 1" in text
    assert "--factor-counts 7 13" not in text
    assert "--factor-selection-policies local_only global_only" not in text
    assert "No team, no swarm, no parallel heavy experiments" in text
    assert "Stop on failure, OOM, path collision" in text
    assert "Balanced-scorecard rationale" in text
    assert "Research diagnostics only" in text
