#!/usr/bin/env python3
"""Validate the structure and content of skills/eqr-autoresearch/SKILL.md."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO_ROOT / "skills" / "eqr-autoresearch" / "SKILL.md"

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

FORBIDDEN_ACTIONS_KEYWORDS: tuple[str, ...] = (
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

ALLOWED_PATHS_KEYWORDS: tuple[str, ...] = (
    "configs/*.yaml",
    "experiments/runs",
    "reports/",
    "site/",
)

FROZEN_PATHS_KEYWORDS: tuple[str, ...] = (
    "src/autoquant_lab/eqr/",
    "scripts/eqr_autoresearch.py",
    "scripts/eqr_train.py",
    "data/",
    "experiments/prepared/",
)


def _read_skill_text() -> str:
    if not SKILL_PATH.exists():
        print(f"ERROR: SKILL.md not found at {SKILL_PATH}", file=sys.stderr)
        sys.exit(1)
    return SKILL_PATH.read_text(encoding="utf-8")


def validate_required_sections(text: str) -> list[str]:
    missing: list[str] = []
    for section in REQUIRED_SECTIONS:
        if section not in text:
            missing.append(section)
    return missing


def validate_forbidden_actions(text: str) -> list[str]:
    missing: list[str] = []
    for keyword in FORBIDDEN_ACTIONS_KEYWORDS:
        if keyword not in text:
            missing.append(keyword)
    return missing


def validate_allowed_paths(text: str) -> list[str]:
    missing: list[str] = []
    for keyword in ALLOWED_PATHS_KEYWORDS:
        if keyword not in text:
            missing.append(keyword)
    return missing


def validate_frozen_paths(text: str) -> list[str]:
    missing: list[str] = []
    for keyword in FROZEN_PATHS_KEYWORDS:
        if keyword not in text:
            missing.append(keyword)
    return missing


def validate_has_code_blocks(text: str) -> list[str]:
    errors: list[str] = []
    if "```bash" not in text:
        errors.append("No bash code blocks found")
    if "```yaml" not in text:
        errors.append("No yaml code blocks found")
    if "```json" not in text:
        errors.append("No json code blocks found")
    return errors


def validate_has_prompt_templates(text: str) -> list[str]:
    errors: list[str] = []
    if "## Prompt Templates" not in text:
        errors.append("Missing Prompt Templates section")
    template_count = text.count("### Template:")
    if template_count < 3:
        errors.append(f"Only {template_count} prompt templates found (expected at least 3)")
    return errors


def validate_has_metric_reference(text: str) -> list[str]:
    errors: list[str] = []
    if "## Appendix: Metric Reference" not in text:
        errors.append("Missing Appendix: Metric Reference section")
    for metric in ("rank_ic", "decile_long_short_return", "feature_coverage"):
        if metric not in text:
            errors.append(f"Metric '{metric}' not mentioned")
    return errors


def main() -> int:
    text = _read_skill_text()
    all_errors: list[str] = []

    missing_sections = validate_required_sections(text)
    if missing_sections:
        all_errors.append(f"Missing required sections: {missing_sections}")

    missing_forbidden = validate_forbidden_actions(text)
    if missing_forbidden:
        all_errors.append(f"Missing forbidden actions: {missing_forbidden}")

    missing_allowed = validate_allowed_paths(text)
    if missing_allowed:
        all_errors.append(f"Missing allowed paths: {missing_allowed}")

    missing_frozen = validate_frozen_paths(text)
    if missing_frozen:
        all_errors.append(f"Missing frozen paths: {missing_frozen}")

    code_errors = validate_has_code_blocks(text)
    if code_errors:
        all_errors.append(f"Code block issues: {code_errors}")

    template_errors = validate_has_prompt_templates(text)
    if template_errors:
        all_errors.append(f"Prompt template issues: {template_errors}")

    metric_errors = validate_has_metric_reference(text)
    if metric_errors:
        all_errors.append(f"Metric reference issues: {metric_errors}")

    if all_errors:
        print("VALIDATION FAILED", file=sys.stderr)
        for error in all_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("VALIDATION PASSED")
    print(f"  Skill document: {SKILL_PATH}")
    print(f"  All {len(REQUIRED_SECTIONS)} required sections present")
    print(f"  All {len(FORBIDDEN_ACTIONS_KEYWORDS)} forbidden actions documented")
    print(f"  All {len(ALLOWED_PATHS_KEYWORDS)} allowed paths documented")
    print(f"  All {len(FROZEN_PATHS_KEYWORDS)} frozen paths documented")
    print(f"  Code blocks (bash/yaml/json) present")
    print(f"  Prompt templates present")
    print(f"  Metric reference appendix present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
