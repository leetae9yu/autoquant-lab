# Full-panel Long/Short QSpread Sequential Harness Report

Date: 2026-05-29

## Data boundary and execution policy

- Data boundary: `local_artifacts_only_no_wrds_login_no_runtime_external_data`.
- No WRDS login, no external API, no new raw data.
- Cloud policy: `no_cloud_or_oci_auto_provisioning`; no OCI/cloud auto-provisioning.
- Execution policy: one heavy experiment at a time; no OMX team/swarm experiment execution.
- Advice boundary: Research diagnostics only; not investment, trading, legal, tax, production, or deployment advice.
- Feature dir: `/home/opc/projects/autoquant-lab/experiments/prepared/features_full_chunked`.
- Output dir: `experiments/ddqm2_factor_router_anchor_20260529T082412Z`.

## Walk-forward OOS protocol

- Portfolio surface: `stock_score_qspread_ddqm2`.
- Evaluation mode: `walk_forward`.
- Test periods per fold: 12.
- Validation periods per fold: 12.
- Headline metrics come from holdout/OOS rows when available.

## Prior 1.25M date-balanced anchors

| Label | q | Cumulative return | Implied CAGR | MDD | Turnover |
|---|---:|---:|---:|---:|---:|
| prior_125m_q20 | 0.20 | 5202.0665 | 30.75% | -36.02% | 71.93% |
| prior_125m_q30 | 0.30 | 4366.4377 | 30.03% | -35.71% | 71.39% |

## Current full-panel matrix rows

| Status | Family | Model | q | Periods | Cumulative | CAGR | MDD | Turnover | Long turnover | Short turnover | Run ID |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ok | full_long_short_factor_router | baseline_mean | 0.30 | 383 | 12.555739 | 8.51% | -43.07% | 15.24% | 15.91% | 14.57% | `factor_router_anchor_20260529T082412Z_baseline_mean_q30` |

## Autonomous branch scorecard

| Router state | Decision | Changed axes | Factor policy | Hypothesis / next hypothesis | Missing interpretation evidence | Rationale | Run ID |
|---|---|---|---|---|---|---|---|
| candidate | defer | q_grid, model_subset | selected_13_global_local | Full-panel long/short QSpread branch under existing walk-forward OOS protocol with factor-router axes. | model_factor_importance, global_local_table, leg_attribution, worst_drawdown_explanation | Missing required interpretation evidence: model_factor_importance, global_local_table, leg_attribution, worst_drawdown_explanation | `factor_router_anchor_20260529T082412Z_baseline_mean_q30` |

## Factor-router axis semantics

- `category` is a report alias for `FactorDefinition.family`; category caps limit selections per family.
- `selected_13_global_local`, `local_only`, and `global_only` ignore quota/cap axes unless a capped policy is selected.
- `quota` requires one `G:L` global/local quota; invalid combinations are rejected before subprocess execution.
- `category_capped` requires one positive family cap; invalid values are rejected before subprocess execution.
- Dry-run router state `planned_only` never uses observed OOS, MDD, turnover, or net performance.

## Post-run artifact note

This anchor was executed before the runner manifest data-boundary string was harmonized with the harness boundary. The performance artifacts are unchanged; future runs now write `local_artifacts_only_no_wrds_login_no_runtime_external_data` directly in the child manifest, and the ledger records the pre-fix child boundary transparently.

## Best completed rows

- `factor_router_anchor_20260529T082412Z_baseline_mean_q30`: cumulative 12.555739, CAGR 8.51%, MDD -43.07%.

## Stop trigger policy

- Complete the full-panel long/short walk-forward OOS anchor grid or ledger failures.
- Run cost/borrow/slippage/tax-proxy sensitivity for Pareto candidates when feasible.
- Diagnose drawdowns and stress months before declaring a strategy-quality conclusion.
- Stop after two consecutive hypothesis batches without material Pareto improvement, repeated memory failures, or scope drift outside DDQM/DDQM2/EQR.

## Artifacts

- Matrix CSV: `reports/factor_router_anchor_20260529T082412Z.csv`
- Ledger: `reports/factor_router_anchor_20260529T082412Z.json`
- Artifact no-overwrite policy: `{'control_ledger': 'fail_if_exists_unique_path_required', 'control_report_md': 'fail_if_exists_unique_path_required', 'matrix_csv_sidecar': 'fail_if_exists_unique_path_required', 'sensitivity_csv': 'fail_if_exists_unique_path_required', 'per_run_manifest': 'skip_existing_never_overwrite', 'existing_run_dir_without_manifest': 'do_not_write_mark_failed', 'temporary_test_outputs': 'unique_tmp_path_or_mktemp_required'}`
- Sensitivity CSV: `reports/factor_router_anchor_20260529T082412Z_sensitivity.csv`

Research diagnostics only; not investment, trading, legal, tax, production, or deployment advice.
The tax-proxy sensitivity is not tax-lot accounting.
