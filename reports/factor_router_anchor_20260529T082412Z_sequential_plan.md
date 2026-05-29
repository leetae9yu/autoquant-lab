# Factor Router Sequential Full-Run Plan

Created: 2026-05-29T08:35:01.085781+00:00

## Anchor evidence

- Anchor run id: `factor_router_anchor_20260529T082412Z_baseline_mean_q30`
- Anchor run dir: `experiments/ddqm2_factor_router_anchor_20260529T082412Z/factor_router_anchor_20260529T082412Z_baseline_mean_q30`
- Anchor ledger: `reports/factor_router_anchor_20260529T082412Z.json`
- Anchor report: `reports/factor_router_anchor_20260529T082412Z.md`

## Execution boundaries

- Data boundary: `local_artifacts_only_no_wrds_login_no_runtime_external_data`.
- Use local prepared parquet artifacts only; no WRDS login, no external/new raw data.
- No team, no swarm, no parallel heavy experiments. Run exactly one command at a time.
- Stop on failure, OOM, path collision, missing manifest, or scope drift; ledger the blocker before the next run.
- Advice boundary: Research diagnostics only; not investment, trading, legal, tax, production, or deployment advice.

## Ordered one-run command templates

Each command must use a fresh UTC stamp and unique output/report/ledger paths.

### 1. selected-factor-count-7

Balanced-scorecard rationale: Check whether a narrower selected-factor set changes the balanced scorecard after the N=13 anchor.

```bash
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PYTHONPATH=src:. .venv/bin/python scripts/eqr_run_full_long_short_matrix.py \
  --execute-heavy-experiments \
  --models baseline_mean --quantiles 0.30 --factor-selection-policies selected_13_global_local --factor-counts 7 --max-runs 1 \
  --factor-universes selected_13_global_local \
  --macro-feature-designs ddqm2_25x3_us_macro \
  --portfolio-surfaces stock_score_qspread_ddqm2 \
  --evaluation-modes walk_forward \
  --walk-forward-test-periods 12 \
  --walk-forward-validation-periods 12 \
  --factor-score-chunk-dates 12 \
  --min-weights 0.00 \
  --run-prefix "factor_router_seq_1_selected-factor-count-7_${STAMP}" \
  --output-dir "experiments/ddqm2_factor_router_seq_1_selected-factor-count-7_${STAMP}" \
  --report "reports/factor_router_seq_1_selected-factor-count-7_${STAMP}.md" \
  --ledger "reports/factor_router_seq_1_selected-factor-count-7_${STAMP}.json"
```

### 2. local-only

Balanced-scorecard rationale: Isolate local-state factor families under the same OOS protocol.

```bash
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PYTHONPATH=src:. .venv/bin/python scripts/eqr_run_full_long_short_matrix.py \
  --execute-heavy-experiments \
  --models baseline_mean --quantiles 0.30 --factor-selection-policies local_only --factor-counts 13 --max-runs 1 \
  --factor-universes selected_13_global_local \
  --macro-feature-designs ddqm2_25x3_us_macro \
  --portfolio-surfaces stock_score_qspread_ddqm2 \
  --evaluation-modes walk_forward \
  --walk-forward-test-periods 12 \
  --walk-forward-validation-periods 12 \
  --factor-score-chunk-dates 12 \
  --min-weights 0.00 \
  --run-prefix "factor_router_seq_2_local-only_${STAMP}" \
  --output-dir "experiments/ddqm2_factor_router_seq_2_local-only_${STAMP}" \
  --report "reports/factor_router_seq_2_local-only_${STAMP}.md" \
  --ledger "reports/factor_router_seq_2_local-only_${STAMP}.json"
```

### 3. global-only

Balanced-scorecard rationale: Isolate global-return factor families under the same OOS protocol.

```bash
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PYTHONPATH=src:. .venv/bin/python scripts/eqr_run_full_long_short_matrix.py \
  --execute-heavy-experiments \
  --models baseline_mean --quantiles 0.30 --factor-selection-policies global_only --factor-counts 13 --max-runs 1 \
  --factor-universes selected_13_global_local \
  --macro-feature-designs ddqm2_25x3_us_macro \
  --portfolio-surfaces stock_score_qspread_ddqm2 \
  --evaluation-modes walk_forward \
  --walk-forward-test-periods 12 \
  --walk-forward-validation-periods 12 \
  --factor-score-chunk-dates 12 \
  --min-weights 0.00 \
  --run-prefix "factor_router_seq_3_global-only_${STAMP}" \
  --output-dir "experiments/ddqm2_factor_router_seq_3_global-only_${STAMP}" \
  --report "reports/factor_router_seq_3_global-only_${STAMP}.md" \
  --ledger "reports/factor_router_seq_3_global-only_${STAMP}.json"
```

### 4. quota-policy

Balanced-scorecard rationale: Force explicit global/local allocation and inspect selection metadata coverage.

```bash
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PYTHONPATH=src:. .venv/bin/python scripts/eqr_run_full_long_short_matrix.py \
  --execute-heavy-experiments \
  --models baseline_mean --quantiles 0.30 --factor-selection-policies quota --global-local-quotas 6:7 --factor-counts 13 --max-runs 1 \
  --factor-universes selected_13_global_local \
  --macro-feature-designs ddqm2_25x3_us_macro \
  --portfolio-surfaces stock_score_qspread_ddqm2 \
  --evaluation-modes walk_forward \
  --walk-forward-test-periods 12 \
  --walk-forward-validation-periods 12 \
  --factor-score-chunk-dates 12 \
  --min-weights 0.00 \
  --run-prefix "factor_router_seq_4_quota-policy_${STAMP}" \
  --output-dir "experiments/ddqm2_factor_router_seq_4_quota-policy_${STAMP}" \
  --report "reports/factor_router_seq_4_quota-policy_${STAMP}.md" \
  --ledger "reports/factor_router_seq_4_quota-policy_${STAMP}.json"
```

### 5. family-cap-policy

Balanced-scorecard rationale: Reduce family concentration and compare drawdown/turnover diagnostics.

```bash
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PYTHONPATH=src:. .venv/bin/python scripts/eqr_run_full_long_short_matrix.py \
  --execute-heavy-experiments \
  --models baseline_mean --quantiles 0.30 --factor-selection-policies category_capped --category-caps 3 --factor-counts 13 --max-runs 1 \
  --factor-universes selected_13_global_local \
  --macro-feature-designs ddqm2_25x3_us_macro \
  --portfolio-surfaces stock_score_qspread_ddqm2 \
  --evaluation-modes walk_forward \
  --walk-forward-test-periods 12 \
  --walk-forward-validation-periods 12 \
  --factor-score-chunk-dates 12 \
  --min-weights 0.00 \
  --run-prefix "factor_router_seq_5_family-cap-policy_${STAMP}" \
  --output-dir "experiments/ddqm2_factor_router_seq_5_family-cap-policy_${STAMP}" \
  --report "reports/factor_router_seq_5_family-cap-policy_${STAMP}.md" \
  --ledger "reports/factor_router_seq_5_family-cap-policy_${STAMP}.json"
```

## Router interpretation rule

Prefer branches only when the balanced scorecard improves or explains gross OOS, drawdown, turnover/resource realism, net/cost sensitivity when available, interpretability metadata, novelty coverage, and reproducibility. A preferred branch remains a research diagnostic, not production approval.

Research diagnostics only; not investment, trading, legal, tax, production, or deployment advice.
The tax-proxy sensitivity is not tax-lot accounting or tax advice.
