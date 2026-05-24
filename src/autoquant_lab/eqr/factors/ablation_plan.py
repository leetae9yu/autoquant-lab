# pyright: reportMissingImports=false, reportMissingTypeStubs=false, reportAny=false, reportExplicitAny=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportReturnType=false
"""DDQM2-style ablation planning helpers.

This module is intentionally non-executing. It gives Codex and operators a
machine-readable map of which DDQM2-inspired research degrees of freedom are
currently runnable and which are planned scaffolding for later implementation.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
import re
from typing import Any

import yaml


DEFAULT_ABLATION_PLAN = Path(__file__).resolve().parents[4] / "configs" / "ddqm2_ablation_plan.yaml"
_SAFE_TOKEN = re.compile(r"[^a-zA-Z0-9_.-]+")


@dataclass(frozen=True)
class AblationChoice:
    """One selectable value in an ablation axis."""

    name: str
    description: str
    cli_args: tuple[str, ...] = ()
    runnable: bool = True
    enabled: bool = True
    source_alignment: str = "adaptation"


@dataclass(frozen=True)
class AblationAxis:
    """A family of related ablation choices."""

    name: str
    description: str
    choices: tuple[AblationChoice, ...]

    def runnable_choices(self) -> tuple[AblationChoice, ...]:
        return tuple(choice for choice in self.choices if choice.enabled and choice.runnable)

    def planned_choices(self) -> tuple[AblationChoice, ...]:
        return tuple(choice for choice in self.choices if choice.enabled and not choice.runnable)


@dataclass(frozen=True)
class AblationPlan:
    """A DDQM2-style ablation plan loaded from YAML."""

    name: str
    objective: str
    base_command: tuple[str, ...]
    axes: tuple[AblationAxis, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def runnable_axes(self) -> tuple[AblationAxis, ...]:
        return tuple(axis for axis in self.axes if axis.runnable_choices())

    def planned_axes(self) -> tuple[AblationAxis, ...]:
        return tuple(axis for axis in self.axes if axis.planned_choices())


@dataclass(frozen=True)
class AblationVariant:
    """One runnable combination of ablation choices."""

    choices: tuple[AblationChoice, ...]

    @property
    def name(self) -> str:
        return "__".join(_safe_token(choice.name) for choice in self.choices)

    def cli_args(self) -> tuple[str, ...]:
        args: list[str] = []
        for choice in self.choices:
            args.extend(choice.cli_args)
        return tuple(args)

    def command(self, plan: AblationPlan, *, run_id_prefix: str = "ddqm2_ablation") -> tuple[str, ...]:
        run_id = _safe_token(f"{run_id_prefix}__{self.name}")
        return (*plan.base_command, "--run-id", run_id, *self.cli_args())

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "choices": [choice.name for choice in self.choices],
            "cli_args": list(self.cli_args()),
        }


def load_ablation_plan(path: str | Path = DEFAULT_ABLATION_PLAN) -> AblationPlan:
    """Load a DDQM2 ablation plan from YAML."""

    plan_path = Path(path)
    raw = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError("Ablation plan root must be a mapping")

    axes_raw = raw.get("axes")
    if not isinstance(axes_raw, Sequence) or isinstance(axes_raw, str):
        raise ValueError("Ablation plan must define a sequence of axes")

    axes = tuple(_parse_axis(axis_raw, index) for index, axis_raw in enumerate(axes_raw))
    base_command = _string_tuple(raw.get("base_command", ["python", "scripts/eqr_run_ddqm2.py"]), "base_command")
    return AblationPlan(
        name=str(raw.get("name", plan_path.stem)),
        objective=str(raw.get("objective", "")),
        base_command=base_command,
        axes=axes,
        notes=_string_tuple(raw.get("notes", []), "notes"),
    )


def runnable_variants(plan: AblationPlan, *, limit: int | None = None) -> tuple[AblationVariant, ...]:
    """Return runnable Cartesian-product variants from enabled runnable choices."""

    choice_groups = [axis.runnable_choices() for axis in plan.runnable_axes()]
    if not choice_groups:
        return ()

    variants: list[AblationVariant] = []
    for choices in product(*choice_groups):
        variants.append(AblationVariant(tuple(choices)))
        if limit is not None and len(variants) >= limit:
            break
    return tuple(variants)


def planned_backlog(plan: AblationPlan) -> tuple[dict[str, str], ...]:
    """Return enabled-but-not-runnable choices as explicit implementation backlog."""

    items: list[dict[str, str]] = []
    for axis in plan.axes:
        for choice in axis.planned_choices():
            items.append(
                {
                    "axis": axis.name,
                    "choice": choice.name,
                    "description": choice.description,
                    "source_alignment": choice.source_alignment,
                }
            )
    return tuple(items)


def _parse_axis(raw: Any, index: int) -> AblationAxis:
    if not isinstance(raw, Mapping):
        raise ValueError(f"axes[{index}] must be a mapping")
    choices_raw = raw.get("choices")
    if not isinstance(choices_raw, Sequence) or isinstance(choices_raw, str):
        raise ValueError(f"axes[{index}].choices must be a sequence")
    return AblationAxis(
        name=str(raw.get("name", f"axis_{index}")),
        description=str(raw.get("description", "")),
        choices=tuple(_parse_choice(choice_raw, index, choice_index) for choice_index, choice_raw in enumerate(choices_raw)),
    )


def _parse_choice(raw: Any, axis_index: int, choice_index: int) -> AblationChoice:
    if not isinstance(raw, Mapping):
        raise ValueError(f"axes[{axis_index}].choices[{choice_index}] must be a mapping")
    return AblationChoice(
        name=str(raw.get("name", f"choice_{choice_index}")),
        description=str(raw.get("description", "")),
        cli_args=_string_tuple(raw.get("cli_args", []), f"axes[{axis_index}].choices[{choice_index}].cli_args"),
        runnable=bool(raw.get("runnable", True)),
        enabled=bool(raw.get("enabled", True)),
        source_alignment=str(raw.get("source_alignment", "adaptation")),
    )


def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence")
    return tuple(str(item) for item in value)


def _safe_token(value: str) -> str:
    token = _SAFE_TOKEN.sub("_", value.strip()).strip("_")
    return token or "variant"
