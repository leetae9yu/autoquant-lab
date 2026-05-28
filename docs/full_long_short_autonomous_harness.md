# Sequential Full-Panel Long/Short QSpread Harness Runbook

This runbook is for a single Ralph-style execution loop. Do not use OMX
team/swarm for compute-heavy experiment execution on the current resource
budget.

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
--macro-feature-design ddqm2_25x3_us_macro
--evaluation-mode walk_forward
--walk-forward-test-periods 12
--walk-forward-validation-periods 12
--factor-score-chunk-dates 12
```

## Single-Ralph loop

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

## First safe anchor command

Use this as the first full-panel smoke/anchor when resources are uncertain:

```bash
PYTHONPATH=src:. .venv/bin/python scripts/eqr_run_full_long_short_matrix.py \
  --models baseline_mean \
  --quantiles 0.30 \
  --run-prefix full_long_short_full_chunked_$(date -u +%Y%m%d)_anchor \
  --report reports/full_long_short_qspread_full_chunked_report.md \
  --ledger reports/full_long_short_qspread_full_chunked_ledger.json
```

After it succeeds, continue sequentially through the remaining q/model grid.
