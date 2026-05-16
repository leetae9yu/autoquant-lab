from __future__ import annotations
# pyright: reportMissingImports=false, reportMissingTypeStubs=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

import subprocess
import sys
from pathlib import Path

from autoquant_lab.eqr.factors.ablation_plan import load_ablation_plan, planned_backlog, runnable_variants


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = REPO_ROOT / "configs" / "ddqm2_ablation_plan.yaml"


def test_ddqm2_ablation_plan_keeps_quantile_freedom() -> None:
    plan = load_ablation_plan(PLAN_PATH)
    variants = runnable_variants(plan, limit=1000)
    names = {variant.name for variant in variants}

    assert any("q10_ddqm2_reference" in name for name in names)
    assert any("q20_current_practical" in name for name in names)
    assert any("q30_diversified_stress" in name for name in names)


def test_ddqm2_ablation_plan_marks_remaining_unimplemented_axes_as_backlog() -> None:
    plan = load_ablation_plan(PLAN_PATH)
    backlog = planned_backlog(plan)
    backlog_keys = {(item["axis"], item["choice"]) for item in backlog}

    assert ("factor_universe", "selected_13_plus_us_overrides") in backlog_keys
    assert ("factor_universe", "selected_13_global_local") not in backlog_keys
    assert ("macro_feature_design", "ddqm2_25x3_us_macro") not in backlog_keys
    assert ("portfolio_surface", "stock_score_qspread_ddqm2") not in backlog_keys


def test_ddqm2_ablation_command_renderer_smoke() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/eqr_plan_ddqm2_ablations.py",
            "--plan",
            str(PLAN_PATH),
            "--format",
            "commands",
            "--limit",
            "2",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 2
    assert all("scripts/eqr_run_ddqm2.py" in line for line in lines)
    assert any("--quantile 0.10" in line for line in lines)
