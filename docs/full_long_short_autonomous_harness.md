# Sequential Full-Panel Long/Short QSpread Harness Runbook

This runbook is for a single Ralph-style execution loop. Do not use OMX
team/swarm for compute-heavy experiment execution on the current resource
budget.


## Phase boundary

### Current phase: factor-router harness build + one anchor gate

This phase refines the autonomous harness and then permits exactly one
explicitly gated full-panel anchor. It may update selector policy support,
scorecard, ledger, report, runbook, and test behavior, but it must not launch
broad q/model/factor grids or more than one heavy backtest. Validation before
the anchor is limited to:

- unit tests and synthetic/minimal fixtures;
- `--dry-run` ledger/report generation;
- existing already-completed local artifacts;
- command construction checks that do not invoke `scripts/eqr_run_ddqm2.py`.

Harness validation must use unique temporary output paths and must not
overwrite existing reports, ledgers, CSV sidecars, manifests, run directories,
or experiment outputs.

After those validation gates pass, the only allowed heavy run in this phase is
the fixed anchor:

```text
model=baseline_mean
q=0.30
factor_universe=selected_13_global_local
factor_selection_policy=selected_13_global_local
factor_universe_target_count=13
macro_feature_design=ddqm2_25x3_us_macro
portfolio_surface=stock_score_qspread_ddqm2
evaluation_mode=walk_forward
walk_forward_test_periods=12
walk_forward_validation_periods=12
factor_score_chunk_dates=12
min_weight=0.0
```

If the anchor fails, stop and ledger the blocker. If it succeeds, write an
additive sequential full-run plan; do not start broad follow-up runs in the
same command.

### Later phase: experiment execution

A separate later phase may use the improved harness to run real experiments.
That later phase still inherits all guardrails in this document: local artifacts
only, no WRDS, no external data, no cloud auto-provisioning, no parallel heavy
runs, no overwrite, and no investment/trading/legal/tax advice. Real execution
must pass the explicit `--execute-heavy-experiments` opt-in; omitting it keeps
the harness in a blocked/planned safety state rather than launching the runner.

## Hard guardrails

- Use local artifacts only.
- Never log in to WRDS.
- Never acquire new raw data.
- Never overwrite existing reports, results, or ledgers.
- Never auto-provision OCI or other cloud resources.
- Never delete or move existing local experiment artifacts as part of this
  harness.
- Treat all outputs as research diagnostics, not investment, trading, legal, or
  tax advice.

## Default local artifacts

- Panel: `experiments/prepared/panel/monthly_labels.parquet`
- Full chunked features: `experiments/prepared/features_full_chunked/`
- Harness: `scripts/eqr_run_full_long_short_matrix.py`
- Underlying runner: `scripts/eqr_run_ddqm2.py`

## Required evaluation protocol

Full-panel long/short anchor runs must preserve the existing DDQM2
walk-forward OOS protocol:

```text
--portfolio-surface stock_score_qspread_ddqm2
--factor-universe selected_13_global_local
--factor-selection-policy selected_13_global_local
--factor-universe-target-count 13
--macro-feature-design ddqm2_25x3_us_macro
--evaluation-mode walk_forward
--walk-forward-test-periods 12
--walk-forward-validation-periods 12
--factor-score-chunk-dates 12
--min-weight 0.0000
```

## Factor-router axes

The harness can now describe a broader DDQM/EQR-aligned research surface while
keeping the underlying runner local-data-only and walk-forward OOS:

- `--factor-selection-policies selected_13_global_local`: reference selected-13
  DDQM2 global/local screen.
- `--factor-selection-policies local_only`: select from factor definitions with
  `scope == "local"` only.
- `--factor-selection-policies global_only`: select from factor definitions with
  `scope == "global"` only.
- `--factor-selection-policies quota --global-local-quotas G:L`: prioritize up
  to `G` global factors and up to `L` local factors, then deterministically fill
  any remaining slots up to the factor-count target. Selection metadata labels
  quota buckets and fill rows separately.
- `--factor-selection-policies category_capped --category-caps N`: cap selected
  factors per category/family.
- `--factor-counts`: sweep the requested number of selected factors.
- `--macro-feature-designs`: sweep macro-design families supported by
  `scripts/eqr_run_ddqm2.py`.
- `--min-weights`: sweep minimum non-negative DDQM2 factor allocation weights.

The word `category` in reports and ledgers is an alias for
`FactorDefinition.family`; tests require `category == family`. Quotas apply only
to quota policies, and category caps apply only to category-capped policies.
Invalid quota/cap combinations are rejected before subprocess execution.
Ignored optional axes are still recorded in the ledger.

## Later experiment-execution Single-Ralph loop

1. State the next hypothesis.
2. Build one run or one small sequential batch.
3. Check local artifact paths and memory.
4. Execute one heavy run at a time.
5. Record the command, environment, status, and paths in the ledger.
6. Parse `manifest.json`, `portfolio_summary.json`, and
   `portfolio_returns.parquet`.
7. Compare against prior 1.25M date-balanced anchors.
8. Decide one of:
   - continue the current q/model grid;
   - run cost/borrow/slippage/tax-proxy sensitivity for Pareto candidates;
   - shrink model size or serialize execution after memory pressure;
   - stop a failed branch and ledger the reason;
   - write the paper-style report.

Native child agents may help inspect code, review results, or draft/report
text, but they must not launch parallel heavy experiments.


## Autonomous control-layer scorecard

Each autonomous branch record should preserve:

- branch/run id;
- hypothesis and changed axes;
- planned command/config and local data boundary;
- status and artifact paths;
- balanced scorecard dimensions;
- autonomous decision: `adopt`, `defer`, `continue`, `stop`, `failed`, or `skipped`;
- next hypothesis or next-branch recommendation;
- limitations or defer reason.

The rule router uses research states, not production approval states:

- `planned_only`: dry-run branch; observed OOS, MDD, turnover, and net
  sensitivity are unavailable and must not be implied.
- `insufficient_evidence`: branch lacks enough manifest/metric evidence.
- `candidate`: completed branch with some balanced-scorecard evidence but
  remaining interpretation or net/cost gaps.
- `preferred_research_branch`: completed research branch with enough balanced
  scorecard evidence; still not a live trading recommendation.
- `stop_or_defer`: failed, unsafe, OOM, collision-blocked, or out-of-scope
  branch.

Performance alone is not enough to adopt a branch. If the branch lacks required
interpretation evidence, mark it `defer`, not `adopt`. Required interpretation
evidence is:

1. model factor importance or coefficients;
2. global/local factor classification table;
3. long/short leg attribution;
4. worst-drawdown explanation;
5. next experiment hypothesis;
6. limitations or explicit defer reason.

All outputs are research diagnostics only, not investment, trading, legal, tax,
production, or deployment advice.

## Stop trigger

Do not stop because one run has a high return. Stop only after the mandatory
evidence gates pass and one of the convergence conditions is met.

Mandatory evidence gates:

1. Full 2.08M long/short OOS anchor grid completed or failures ledgered.
2. Gross comparison to prior 1.25M date-balanced long/short results completed.
3. Cost/borrow/slippage/tax-proxy sensitivity completed for Pareto candidates when
   feasible.
4. Drawdown and stress-month diagnostics completed.
5. Robust q/model map generated.

Convergence stop conditions:

- Two consecutive hypothesis batches produce no material Pareto improvement.
- Memory/time budget is exhausted or repeated OOM/fallback failures make more
  runs unproductive.
- Remaining plausible variations would leave the DDQM/DDQM2/EQR research shape.

## First safe harness-only validation command

Use this command in the current harness/control-layer phase. It only builds the
planned ledger/report in a unique temporary directory and must not invoke the
underlying DDQM2 runner:

```bash
SMOKE_DIR="$(mktemp -d)"
PYTHONPATH=src:. .venv/bin/python scripts/eqr_run_full_long_short_matrix.py \
  --dry-run \
  --models baseline_mean \
  --quantiles 0.30 \
  --factor-counts 7 13 \
  --factor-selection-policies selected_13_global_local local_only global_only quota category_capped \
  --global-local-quotas 6:7 \
  --category-caps 3 \
  --macro-feature-designs ddqm2_25x3_us_macro \
  --min-weights 0.00 0.01 \
  --max-runs 10 \
  --run-prefix "harness_dry_run_$(date -u +%Y%m%dT%H%M%SZ)" \
  --output-dir "$SMOKE_DIR/runs" \
  --report "$SMOKE_DIR/full_long_short_qspread_harness_report.md" \
  --ledger "$SMOKE_DIR/full_long_short_qspread_harness_ledger.json"
```

A successful harness-only validation proves command construction, additive
ledger/report writing, scorecard rendering, and no-heavy-execution behavior. It
does not count as a completed experiment.

## Current one-anchor command

Use this only after tests and dry-run validation pass. Keep outputs unique and
pass the heavy-execution opt-in:

```bash
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PYTHONPATH=src:. .venv/bin/python scripts/eqr_run_full_long_short_matrix.py \
  --execute-heavy-experiments \
  --models baseline_mean \
  --quantiles 0.30 \
  --factor-selection-policies selected_13_global_local \
  --factor-universes selected_13_global_local \
  --factor-counts 13 \
  --macro-feature-designs ddqm2_25x3_us_macro \
  --portfolio-surfaces stock_score_qspread_ddqm2 \
  --evaluation-modes walk_forward \
  --walk-forward-test-periods 12 \
  --walk-forward-validation-periods 12 \
  --factor-score-chunk-dates 12 \
  --min-weights 0.00 \
  --max-runs 1 \
  --run-prefix "factor_router_anchor_${STAMP}" \
  --output-dir "experiments/ddqm2_factor_router_anchor_${STAMP}" \
  --report "reports/factor_router_anchor_${STAMP}.md" \
  --ledger "reports/factor_router_anchor_${STAMP}.json"
```

After this anchor succeeds, read the generated
`reports/factor_router_anchor_<STAMP>_sequential_plan.md`. Follow it one command
at a time only: no team, no swarm, no parallel heavy experiments, and stop on
failure/OOM/path collision before attempting the next branch.
