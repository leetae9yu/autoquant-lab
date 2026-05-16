#!/usr/bin/env python3
"""Render runnable and planned DDQM2 ablation candidates."""
# pyright: reportMissingImports=false, reportMissingTypeStubs=false, reportAny=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnusedCallResult=false

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if SRC_DIR.is_dir():
    src_path = str(SRC_DIR)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

from autoquant_lab.eqr.factors.ablation_plan import load_ablation_plan, planned_backlog, runnable_variants  # noqa: E402


DEFAULT_PLAN = Path(__file__).resolve().parents[1] / "configs" / "ddqm2_ablation_plan.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan DDQM2-style ablation commands without executing them.")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN, help="YAML ablation plan to render.")
    parser.add_argument("--format", choices=("markdown", "json", "commands"), default="markdown", help="Output format.")
    parser.add_argument("--limit", type=int, default=24, help="Maximum runnable variants to render; <=0 means all.")
    parser.add_argument("--run-id-prefix", default="ddqm2_ablation", help="Prefix for rendered run ids.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    limit = None if args.limit <= 0 else args.limit
    plan = load_ablation_plan(args.plan)
    variants = runnable_variants(plan, limit=limit)
    backlog = planned_backlog(plan)

    if args.format == "json":
        print(
            json.dumps(
                {
                    "name": plan.name,
                    "objective": plan.objective,
                    "runnable_variant_count": len(variants),
                    "runnable_variants": [
                        {
                            **variant.summary(),
                            "command": list(variant.command(plan, run_id_prefix=args.run_id_prefix)),
                        }
                        for variant in variants
                    ],
                    "planned_backlog": list(backlog),
                    "notes": list(plan.notes),
                },
                indent=2,
            )
        )
        return 0

    if args.format == "commands":
        for variant in variants:
            print(" ".join(variant.command(plan, run_id_prefix=args.run_id_prefix)))
        return 0

    print(f"# {plan.name}")
    print()
    if plan.objective:
        print(plan.objective)
        print()
    print("## Runnable variants")
    print()
    print("These commands only cover axes already supported by the current harness.")
    print()
    for variant in variants:
        print(f"- `{variant.name}`")
        print(f"  - command: `{' '.join(variant.command(plan, run_id_prefix=args.run_id_prefix))}`")
    print()
    print("## Planned backlog")
    print()
    print("These choices preserve research freedom but require implementation before Codex should execute them.")
    print()
    for item in backlog:
        print(f"- `{item['axis']}.{item['choice']}`: {item['description']} ({item['source_alignment']})")
    if plan.notes:
        print()
        print("## Notes")
        print()
        for note in plan.notes:
            print(f"- {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
