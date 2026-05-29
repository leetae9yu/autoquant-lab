# Factor-Router Autonomous Research Report

Date: 2026-05-29

Companion Korean report: [`factor_router_autonomous_research_final_20260529_ko.md`](factor_router_autonomous_research_final_20260529_ko.md)

Source ledger: [`factor_router_autonomous_research_20260529T111620Z.json`](factor_router_autonomous_research_20260529T111620Z.json)

## Abstract

This report documents an additive, autonomous full-panel factor-router experiment loop over the existing DDQM2/EQR long/short QSpread harness. The loop used the local 2,082,485-row prepared parquet artifact, preserved the walk-forward out-of-sample protocol, ran one heavy experiment at a time, and never contacted WRDS or any new raw-data source. Existing reports were not overwritten.

The main empirical result is that the factor-router extension found two useful frontiers. First, baseline-mean local/global quota tuning produced a defensive branch: **quota 1:12, q=0.40** reached MDD **-17.14%** with gross CAGR **7.08%**. Second, model variation found a much stronger sparse-linear branch: **ElasticNet, quota 3:10, q=0.20** reached gross cumulative **235.43**, CAGR **18.68%**, MDD **-21.20%**, and turnover **61.29%**. Subsequent adjacent-quota, category-cap, and q=0.40 ElasticNet checks did not improve that frontier. The loop stopped after five consecutive completed non-progress hypotheses, per the user-defined rule.

All figures are research backtest diagnostics. They are not production-trading, investment, legal, or tax advice.

## 1. Research question

The previous full-panel long/short QSpread report established that restoring the short leg matters. This run asked a narrower follow-up question:

> Given the existing DDQM2/EQR walk-forward OOS harness, can local/global factor routing, q variation, and lightweight model variation improve the return/drawdown/turnover frontier without new data or WRDS access?

## 2. Data boundary and protocol

- Data boundary: local artifacts only; no WRDS login; no runtime external data.
- Input feature directory: `experiments/prepared/features_full_chunked/`.
- Prepared rows: 2,082,485.
- Portfolio surface: `stock_score_qspread_ddqm2`.
- Evaluation mode: walk-forward OOS.
- Walk-forward cadence: 12-month test block, 12-month validation block.
- Factor-score chunking: 12 formation dates per part.
- Execution policy: one heavy run at a time; no team/swarm parallel heavy runs.
- Stop rules: explicit user stop, five consecutive completed non-progress hypotheses, or available disk <= 2GB.

The disk rule did not trigger; the heavy loop stopped on the five-non-progress rule after run 29 with 7.6GB still available.

## 3. Experiment timeline

1. Anchor run: baseline-mean selected 13-factor q=0.30 branch.
2. Selection surface: N=7, local-only, global-only, quota 6:7, category-cap=3.
3. q robustness: q=0.20 and q=0.40 variants around local-only and quota branches.
4. Quota sweep: local-heavy q=0.30 and q=0.40 branches, including 4:9, 3:10, 2:11, and 1:12.
5. Aggressive q=0.20 quota sweep: 3:10 became the baseline-mean high-return quota frontier.
6. Model-axis tests: ridge and ElasticNet on the strongest q=0.20 branch.
7. ElasticNet robustness: q=0.20/0.30/0.40 and adjacent quota/category-cap checks.
8. Stop: runs 25-29 produced five consecutive completed non-progress hypotheses.

## 4. Gross evidence

### 4.1 Top gross rows

| branch | model | q | policy | quota | cum | CAGR | MDD | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| elasticnet-quota-3-10-q20-preserve-scores | elasticnet | 0.20 | quota | 3:10 | 235.434 | 18.68% | -21.20% | 61.29% |
| elasticnet-quota-4-9-q20-preserve-scores | elasticnet | 0.20 | quota | 4:9 | 234.435 | 18.66% | -21.55% | 61.08% |
| elasticnet-quota-2-11-q20-preserve-scores | elasticnet | 0.20 | quota | 2:11 | 221.749 | 18.46% | -21.43% | 61.13% |
| elasticnet-category-cap3-q20-preserve-scores | elasticnet | 0.20 | category_capped |  | 193.657 | 17.96% | -23.09% | 61.57% |
| quota-3-10-q20-preserve-scores | baseline_mean | 0.20 | quota | 3:10 | 95.020 | 15.37% | -39.27% | 64.72% |
| quota-4-9-q20-preserve-scores | baseline_mean | 0.20 | quota | 4:9 | 93.271 | 15.31% | -40.08% | 64.84% |
| quota-q20-min-weight-001-storage-light | baseline_mean | 0.20 | quota | 6:7 | 87.727 | 15.09% | -41.16% | 65.10% |
| quota-2-11-q20-preserve-scores | baseline_mean | 0.20 | quota | 2:11 | 87.516 | 15.08% | -40.79% | 64.52% |

### 4.2 Lowest drawdown rows

| branch | model | q | policy | quota | cum | CAGR | MDD | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| quota-1-12-q40-preserve-scores | baseline_mean | 0.40 | quota | 1:12 | 7.883 | 7.08% | -17.14% | 14.59% |
| elasticnet-quota-1-12-q40-preserve-scores | elasticnet | 0.40 | quota | 1:12 | 9.602 | 7.68% | -17.32% | 35.23% |
| elasticnet-quota-3-10-q40-preserve-scores | elasticnet | 0.40 | quota | 3:10 | 10.848 | 8.05% | -18.09% | 34.56% |
| elasticnet-quota-2-11-q40-preserve-scores | elasticnet | 0.40 | quota | 2:11 | 10.424 | 7.93% | -18.20% | 34.90% |
| quota-2-11-q40-preserve-scores | baseline_mean | 0.40 | quota | 2:11 | 9.290 | 7.58% | -20.68% | 14.46% |
| elasticnet-quota-3-10-q20-preserve-scores | elasticnet | 0.20 | quota | 3:10 | 235.434 | 18.68% | -21.20% | 61.29% |
| elasticnet-quota-3-10-q30-preserve-scores | elasticnet | 0.30 | quota | 3:10 | 27.100 | 11.02% | -21.33% | 40.79% |
| elasticnet-quota-2-11-q20-preserve-scores | elasticnet | 0.20 | quota | 2:11 | 221.749 | 18.46% | -21.43% | 61.13% |

### 4.3 Main frontier branches

| branch | model | q | policy | quota | cum | CAGR | MDD | turnover | HHI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| elasticnet-quota-3-10-q20-preserve-scores | elasticnet | 0.20 | quota | 3:10 | 235.434 | 18.68% | -21.20% | 61.29% | 0.199 |
| elasticnet-quota-4-9-q20-preserve-scores | elasticnet | 0.20 | quota | 4:9 | 234.435 | 18.66% | -21.55% | 61.08% | 0.200 |
| elasticnet-quota-3-10-q30-preserve-scores | elasticnet | 0.30 | quota | 3:10 | 27.100 | 11.02% | -21.33% | 40.79% | 0.242 |
| elasticnet-quota-3-10-q40-preserve-scores | elasticnet | 0.40 | quota | 3:10 | 10.848 | 8.05% | -18.09% | 34.56% | 0.242 |
| quota-1-12-q40-preserve-scores | baseline_mean | 0.40 | quota | 1:12 | 7.883 | 7.08% | -17.14% | 14.59% | 0.143 |
| quota-3-10-q20-preserve-scores | baseline_mean | 0.20 | quota | 3:10 | 95.020 | 15.37% | -39.27% | 64.72% | 0.096 |
| ridge-quota-3-10-q20-preserve-scores | ridge | 0.20 | quota | 3:10 | 78.040 | 14.67% | -38.36% | 60.61% | 0.196 |

Interpretation: the search did not produce a single universal winner. The ElasticNet q=0.20 branch dominates gross return and still has a moderate MDD relative to other high-return branches. The baseline q=0.40 1:12 branch dominates defensive drawdown but at much lower return. Ridge is useful as a lower-turnover/lower-risk model diagnostic, not as the gross leader.

## 5. Cost, slippage, borrow, and tax-proxy sensitivity

The sensitivity layer is simple by design: transaction cost and slippage are charged against turnover, borrow is charged on short exposure, and a 40.8% simplified tax proxy is applied to positive post-cost monthly returns. This is not tax-lot accounting and not tax advice.

The conservative row below uses 25 bps transaction cost, 150 bps annual borrow, 10 bps slippage, and the 40.8% simplified tax proxy.

| branch | model | q | quota | gross cum | pre-tax net cum | conservative net cum | conservative MDD | mean tax drag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| elasticnet-quota-3-10-q20-preserve-scores | elasticnet | 0.20 | 3:10 | 235.434 | 27.940 | 0.420 | -41.75% | 0.84% |
| elasticnet-quota-3-10-q40-preserve-scores | elasticnet | 0.40 | 3:10 | 10.848 | 1.922 | -0.519 | -56.90% | 0.49% |
| quota-1-12-q40-preserve-scores | baseline_mean | 0.40 | 1:12 | 7.883 | 2.737 | -0.219 | -40.36% | 0.42% |
| quota-3-10-q20-preserve-scores | baseline_mean | 0.20 | 3:10 | 95.020 | 9.677 | -0.299 | -61.03% | 0.76% |

Interpretation: gross ElasticNet q=0.20 is very strong, but conservative net results compress sharply. The branch remains research-relevant because it still has a positive conservative net cumulative result in the generated sensitivity table, but the economic story depends heavily on execution, borrow, turnover, capacity, and tax assumptions.

## 6. Model/factor diagnostics

### ElasticNet quota 3:10 q=0.20

Top mean-weight factors:

| factor | scope | category | mean weight | holdout corr |
| --- | --- | --- | --- | --- |
| size_local_small_size | local | size_flow | 12.79% | 0.129 |
| quality_global_net_income_yoy | global | quality_growth | 12.74% | 0.033 |
| reversal_local_ma_gap_1m | local | reversal | 11.31% | 0.156 |
| reversal_local_price_reversal_1m | local | reversal | 11.31% | 0.156 |
| val_global_pb_fwd | global | valuation | 7.80% | 0.105 |
| val_global_relative_pb_industry_fwd | global | valuation | 7.80% | 0.105 |

Scope weight mass:

| scope | weight mass |
| --- | --- |
| local | 72.41% |
| global | 28.35% |

Category weight mass:

| category | weight mass |
| --- | --- |
| earnings | 29.89% |
| reversal | 22.62% |
| quality_growth | 19.85% |
| valuation | 15.61% |
| size_flow | 12.79% |


### Baseline quota 1:12 q=0.40

Top mean-weight factors:

| factor | scope | category | mean weight | holdout corr |
| --- | --- | --- | --- | --- |
| quality_global_net_income_yoy | global | quality_growth | 26.76% | 0.157 |
| quality_local_net_income_yoy | local | quality_growth | 19.94% | 0.146 |
| size_local_small_size | local | size_flow | 12.68% | -0.041 |
| earn_local_eps_fast_fy1_1m | local | earnings | 4.22% | -0.139 |
| earn_local_eps_fast_fy1_1m_voladj | local | earnings | 4.22% | -0.139 |
| earn_local_eps_fq1_1m | local | earnings | 4.22% | -0.139 |

Scope weight mass:

| scope | weight mass |
| --- | --- |
| local | 74.86% |
| global | 26.76% |

Category weight mass:

| category | weight mass |
| --- | --- |
| quality_growth | 46.70% |
| earnings | 42.25% |
| size_flow | 12.68% |


Interpretation: the ElasticNet high-return branch is not simply a generic “local only” bet. Its selected 3:10 quota keeps three global factors while emphasizing local size, reversal, earnings, and quality/value families. The defensive baseline 1:12 branch uses one global slot as a stabilizer; pure local-only q=0.40 had much worse drawdown, so the single global slot appears diagnostically meaningful.

## 7. Drawdown diagnosis

### Worst months: ElasticNet quota 3:10 q=0.20

| formation date | return | turnover | long turnover | short turnover |
| --- | --- | --- | --- | --- |
| 1999-11-30 00:00:00 | -12.68% | 67.34% | 72.53% | 62.14% |
| 2001-02-28 00:00:00 | -12.02% | 84.33% | 86.61% | 82.06% |
| 2000-10-31 00:00:00 | -9.17% | 76.33% | 74.69% | 77.97% |
| 2000-11-30 00:00:00 | -8.52% | 71.65% | 64.04% | 79.26% |
| 2015-06-30 00:00:00 | -8.29% | 61.82% | 57.14% | 66.49% |


### Worst months: baseline quota 1:12 q=0.40

| formation date | return | turnover | long turnover | short turnover |
| --- | --- | --- | --- | --- |
| 2002-10-31 00:00:00 | -7.92% | 12.85% | 13.81% | 11.90% |
| 1999-11-30 00:00:00 | -6.10% | 12.56% | 12.63% | 12.48% |
| 2022-06-30 00:00:00 | -4.99% | 11.90% | 12.38% | 11.41% |
| 2020-12-31 00:00:00 | -4.93% | 16.94% | 16.53% | 17.34% |
| 2000-01-31 00:00:00 | -4.88% | 9.13% | 9.02% | 9.25% |


The high-return ElasticNet branch still has stress-window losses. The defensive branch lowers MDD but does not remove month-level losses. This supports reporting the result as a research frontier rather than a strategy-quality claim.

## 8. Stop-rule audit

The autonomous loop stopped after five consecutive completed non-progress hypotheses:

- Run 25: ElasticNet 1:12 q=0.40 did not improve the sparse-linear defensive frontier.
- Run 26: ElasticNet 2:11 q=0.40 did not improve the sparse-linear defensive frontier.
- Run 27: ElasticNet 4:9 q=0.20 nearly tied but did not beat ElasticNet 3:10 q=0.20.
- Run 28: ElasticNet 2:11 q=0.20 did not beat ElasticNet 3:10 q=0.20.
- Run 29: ElasticNet category-cap=3 q=0.20 did not beat ElasticNet 3:10 q=0.20.

Disk stop did not trigger: 7.6GB remained after run 29, above the 2GB threshold.

## 9. Limitations

- Backtest only; no production execution, no live portfolio router, and no investment advice.
- Local prepared data only; no new raw data and no WRDS validation in this loop.
- Cost/tax proxy is simplified and not tax advice.
- Factor-score artifacts are preserved for the main representative runs, enabling later dashboard drilldowns, but storage pressure remains a constraint.
- The ElasticNet q=0.20 result is large enough to require further robustness review before any stronger claim.

## 10. Next research steps

1. Build a dashboard over preserved `portfolio_returns`, `qspread_legs`, `factor_allocations`, `factor_diagnostics`, and `factor_scores` for the representative runs.
2. Compare worst months by leg and factor family for ElasticNet q=0.20 versus the defensive q=0.40 branches.
3. Add a storage-aware raw score catalog so exploratory runs can prune bulky intermediates while preserving dashboard-grade finalists.
4. If more disk is available, test ElasticNet hyperparameter profiles through the harness rather than expanding more quota points.
