"""Tests for the EQR autoresearch skill document and validator."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO_ROOT / "skills" / "eqr-autoresearch" / "SKILL.md"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "eqr_validate_skill.py"

REQUIRED_SECTIONS: tuple[str, ...] = (
    "## Overview",
    "## Inspection",
    "## Stage Map",
    "## Delegation Rules",
    "## Config-Only Mutation Rules",
    "## Experiment Proposal",
    "## Batch Execution",
    "## Evaluation",
    "## Promotion",
    "## Reporting",
    "## Recovery",
    "## Stop Conditions",
    "## Forbidden Actions",
    "## Example Session",
)

FORBIDDEN_ACTIONS: tuple[str, ...] = (
    "Edit harness code",
    "Delete data",
    "WRDS login",
    "Unlimited trials",
    "Shell injection",
    "Path escape",
    "Future leakage",
    "Holdout training",
    "Override evaluation",
    "Network downloads",
    "Delete ledger",
    "Bypass validation",
)


def test_skill_md_exists() -> None:
    assert SKILL_PATH.exists(), f"SKILL.md not found at {SKILL_PATH}"


def test_skill_md_is_parseable() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert len(text) > 1000, "SKILL.md seems too short"
    assert "# EQR Autoresearch Skill" in text, "Missing title"


def test_skill_md_has_overview() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Overview" in text
    assert "Configs-only autonomy" in text


def test_skill_md_has_inspection() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Inspection" in text
    assert "configs/golden_path.yaml" in text


def test_skill_md_has_stage_map() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Stage Map" in text
    assert "PREPARE" in text and "PROPOSE" in text and "QUEUE" in text


def test_skill_md_has_delegation_rules() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Delegation Rules" in text
    assert "researcher" in text and "implementer" in text and "reviewer" in text


def test_skill_md_has_config_mutation_rules() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Config-Only Mutation Rules" in text
    assert "Allowed Mutable Paths" in text
    assert "Frozen Paths" in text


def test_skill_md_has_experiment_proposal() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Experiment Proposal" in text
    assert "eqr_validate_config.py" in text


def test_skill_md_has_batch_execution() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Batch Execution" in text
    assert "run-batch" in text


def test_skill_md_has_evaluation() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Evaluation" in text
    assert "metrics.json" in text


def test_skill_md_has_promotion() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Promotion" in text
    assert "validation" in text and "holdout" in text


def test_skill_md_has_reporting() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Reporting" in text
    assert "eqr_build_links.py" in text


def test_skill_md_has_recovery() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Recovery" in text
    assert "dead-letter" in text


def test_skill_md_has_stop_conditions() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Stop Conditions" in text
    assert "Budget exhausted" in text


def test_skill_md_has_forbidden_actions() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Forbidden Actions" in text
    for action in FORBIDDEN_ACTIONS:
        assert action in text, f"Forbidden action '{action}' not documented"


def test_skill_md_has_example_session() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Example Session" in text
    assert "Step 1" in text and "Step 2" in text


def test_skill_md_has_prompt_templates() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Prompt Templates" in text
    assert "Template: Propose a Batch" in text
    assert "Template: Evaluate and Promote" in text


def test_skill_md_has_metric_reference() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "## Appendix: Metric Reference" in text
    assert "rank_ic" in text
    assert "decile_long_short_return" in text


def test_validator_exists() -> None:
    assert VALIDATOR_PATH.exists(), f"Validator not found at {VALIDATOR_PATH}"


def test_validator_runs_and_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"Validator failed: {result.stderr}"
    assert "VALIDATION PASSED" in result.stdout
