# Full-panel Long/Short QSpread Sequential Harness Report

Date: 2026-05-28

## Data boundary and execution policy

- Data boundary: `local_artifacts_only_no_wrds_login_no_runtime_external_data`.
- No WRDS login, no external API, no new raw data.
- Execution policy: one heavy experiment at a time; no OMX team/swarm experiment execution.
- Feature dir: `/home/opc/projects/autoquant-lab/experiments/prepared/features_full_chunked`.
- Output dir: `experiments/ddqm2_full_long_short`.

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
| ok | full_long_short_core_q | baseline_mean | 0.10 | 383 | 1002.888382 | 24.18% | -36.51% | 77.44% | 74.50% | 80.37% | `full_long_short_full_chunked_20260528_anchor_baseline_mean_q10` |
| ok | full_long_short_core_q | baseline_mean | 0.20 | 383 | 82.647758 | 14.88% | -42.27% | 65.29% | 64.32% | 66.26% | `full_long_short_full_chunked_20260528_anchor_baseline_mean_q20` |
| ok | full_long_short_core_q | baseline_mean | 0.30 | 383 | 12.555739 | 8.51% | -43.07% | 15.24% | 15.91% | 14.57% | `full_long_short_full_chunked_20260528_anchor_baseline_mean_q30` |
| ok | full_long_short_core_q | ridge | 0.10 | 383 | 1107.005334 | 24.56% | -45.68% | 73.99% | 73.58% | 74.39% | `full_long_short_full_chunked_20260528_anchor_ridge_q10` |
| ok | full_long_short_core_q | ridge | 0.20 | 383 | 59.000352 | 13.69% | -38.66% | 61.16% | 62.14% | 60.18% | `full_long_short_full_chunked_20260528_anchor_ridge_q20` |
| ok | full_long_short_core_q | ridge | 0.30 | 383 | 7.091283 | 6.77% | -44.69% | 38.40% | 40.02% | 36.78% | `full_long_short_full_chunked_20260528_anchor_ridge_q30` |
| ok | full_long_short_core_q | elasticnet | 0.10 | 383 | 1942.770173 | 26.78% | -36.46% | 73.81% | 73.65% | 73.97% | `full_long_short_full_chunked_20260528_anchor_elasticnet_q10` |
| ok | full_long_short_core_q | elasticnet | 0.20 | 383 | 160.793554 | 17.28% | -23.57% | 60.99% | 62.38% | 59.60% | `full_long_short_full_chunked_20260528_anchor_elasticnet_q20` |
| ok | full_long_short_core_q | elasticnet | 0.30 | 383 | 19.921324 | 10.00% | -27.57% | 40.02% | 42.18% | 37.87% | `full_long_short_full_chunked_20260528_anchor_elasticnet_q30` |
| ok | full_long_short_core_q | lightgbm | 0.10 | 383 | 4932.484099 | 30.53% | -32.68% | 76.86% | 75.68% | 78.04% | `full_long_short_full_chunked_20260528_anchor_lightgbm_q10` |
| ok | full_long_short_core_q | lightgbm | 0.20 | 383 | 448.046057 | 21.09% | -38.99% | 64.01% | 64.87% | 63.16% | `full_long_short_full_chunked_20260528_anchor_lightgbm_q20` |
| ok | full_long_short_core_q | lightgbm | 0.30 | 383 | 69.767065 | 14.28% | -27.39% | 38.72% | 41.51% | 35.92% | `full_long_short_full_chunked_20260528_anchor_lightgbm_q30` |
| ok | full_long_short_core_q | random_forest | 0.10 | 383 | 6173.303664 | 31.45% | -34.86% | 75.90% | 74.22% | 77.57% | `full_long_short_full_chunked_20260528_anchor_random_forest_q10` |
| ok | full_long_short_core_q | random_forest | 0.20 | 383 | 846.151418 | 23.52% | -35.42% | 63.70% | 64.15% | 63.24% | `full_long_short_full_chunked_20260528_anchor_random_forest_q20` |
| ok | full_long_short_core_q | random_forest | 0.30 | 383 | 79.585295 | 14.74% | -27.04% | 34.98% | 37.00% | 32.96% | `full_long_short_full_chunked_20260528_anchor_random_forest_q30` |
| ok | full_long_short_core_q | extra_trees | 0.10 | 383 | 4605.148479 | 30.25% | -36.42% | 76.25% | 74.81% | 77.69% | `full_long_short_full_chunked_20260528_anchor_extra_trees_q10` |
| ok | full_long_short_core_q | extra_trees | 0.20 | 383 | 443.417533 | 21.05% | -42.79% | 62.90% | 63.61% | 62.19% | `full_long_short_full_chunked_20260528_anchor_extra_trees_q20` |
| ok | full_long_short_core_q | extra_trees | 0.30 | 383 | 57.075048 | 13.57% | -41.32% | 32.79% | 35.21% | 30.38% | `full_long_short_full_chunked_20260528_anchor_extra_trees_q30` |

## Best completed rows

- `full_long_short_full_chunked_20260528_anchor_random_forest_q10`: cumulative 6173.303664, CAGR 31.45%, MDD -34.86%.
- `full_long_short_full_chunked_20260528_anchor_lightgbm_q10`: cumulative 4932.484099, CAGR 30.53%, MDD -32.68%.
- `full_long_short_full_chunked_20260528_anchor_extra_trees_q10`: cumulative 4605.148479, CAGR 30.25%, MDD -36.42%.
- `full_long_short_full_chunked_20260528_anchor_elasticnet_q10`: cumulative 1942.770173, CAGR 26.78%, MDD -36.46%.
- `full_long_short_full_chunked_20260528_anchor_ridge_q10`: cumulative 1107.005334, CAGR 24.56%, MDD -45.68%.

## Stop trigger policy

- Complete the full-panel long/short walk-forward OOS anchor grid or ledger failures.
- Run cost/borrow/slippage/tax-proxy sensitivity for Pareto candidates when feasible.
- Diagnose drawdowns and stress months before declaring a strategy-quality conclusion.
- Stop after two consecutive hypothesis batches without material Pareto improvement, repeated memory failures, or scope drift outside DDQM/DDQM2/EQR.

## Artifacts

- Matrix CSV: `reports/full_long_short_qspread_full_chunked_report.csv`
- Ledger: `reports/full_long_short_qspread_full_chunked_ledger.json`
- Sensitivity CSV: `reports/full_long_short_qspread_full_chunked_report_sensitivity.csv`

All figures are research backtest diagnostics, not investment, trading, legal, or tax advice. The tax-proxy sensitivity is not tax-lot accounting.
