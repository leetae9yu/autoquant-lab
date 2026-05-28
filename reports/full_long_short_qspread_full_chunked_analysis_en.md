# Full-panel Long/Short QSpread ML Analysis Report

Date: 2026-05-28

Companion Korean report: [`full_long_short_qspread_full_chunked_analysis_ko.md`](full_long_short_qspread_full_chunked_analysis_ko.md)

## Abstract

This report documents the completed **2,082,485-row full-panel** DDQM2/EQR long/short QSpread run. It preserves the existing walk-forward OOS protocol, uses only local prepared parquet artifacts, does not contact WRDS, and does not acquire new raw data. The execution path is intentionally sequential: one heavy experiment at a time, no OMX team/swarm experiment execution.

The empirical headline is that the full-panel long/short surface keeps the broad shape of the earlier DDQM2/EQR story while changing the model ranking. The best gross row is **Random Forest q=0.10** with CAGR 31.45%, MDD -34.86%, and turnover 75.90%. LightGBM q=0.10 and Extra Trees q=0.10 follow closely. Compared with the prior 1.25M date-balanced anchors, the best full-panel row is not directionally weaker; it is slightly above the prior q=0.20 CAGR (30.75%) while using the larger local panel.

The conservative cost/borrow/slippage/tax proxy changes the interpretation. Under 25 bps transaction cost, 150 bps annual borrow, 10 bps slippage, and a 40.8% simplified tax proxy on positive post-cost monthly returns, the same Random Forest q=0.10 row remains the leading tested candidate, but cumulative return compresses sharply. This is a research diagnostic, not production execution modeling, investment advice, or tax advice.

## 1. Research question

The preceding long-only branch showed why the short leg matters: long-only versions had weaker drawdown behavior and their best net interpretation depended strongly on turnover control. The next question is therefore:

> If the original long/short QSpread construction is restored and the full local 2.08M-row panel is used, do multiple ML model families preserve or change the DDQM2/EQR result shape?

This report answers that question for six CPU-friendly model families: baseline mean, ridge, elasticnet, LightGBM, random forest, and extra trees.

## 2. Data boundary and protocol

- Data boundary: `local_artifacts_only_no_wrds_login_no_runtime_external_data`.
- Input feature directory: `experiments/prepared/features_full_chunked/`.
- Prepared rows: 2,082,485.
- Portfolio surface: `stock_score_qspread_ddqm2`.
- Evaluation mode: `walk_forward`.
- Walk-forward test block: 12 monthly periods.
- Walk-forward validation block: 12 monthly periods.
- Factor-score chunking: 12 formation dates per part.
- Execution policy: one heavy run at a time; no team/swarm parallel experiment execution.

The run is additive. It does not overwrite existing DDQM/DDQM2/EQR reports or previous long-only reports.

## 3. Experiment timeline

1. The existing 1.25M date-balanced DDQM2 reports established the long/short comparison anchor.
2. A long-only full-panel branch tested whether abandoning the short leg was sufficient. It was informative but weaker as a strategy-quality candidate.
3. The harness was extended so long/short stock-score QSpread backtests can stream factor-score chunks instead of loading all score parts at once.
4. A sequential full-panel matrix ran 18 model/q combinations: six model families times q=0.10, q=0.20, q=0.30.
5. All 18 runs completed with zero ledger failures.
6. The compact report, CSV matrix, sensitivity CSV, and this narrative report were generated from the completed local artifacts.

## 4. Gross matrix evidence

### 4.1 Top gross rows

| Model | q | Gross cumulative | Gross CAGR | MDD | Turnover |
| --- | --- | --- | --- | --- | --- |
| random_forest | 0.100 | 6173.304 | 31.45% | -34.86% | 75.90% |
| lightgbm | 0.100 | 4932.484 | 30.53% | -32.68% | 76.86% |
| extra_trees | 0.100 | 4605.148 | 30.25% | -36.42% | 76.25% |
| elasticnet | 0.100 | 1942.770 | 26.78% | -36.46% | 73.81% |
| ridge | 0.100 | 1107.005 | 24.56% | -45.68% | 73.99% |
| baseline_mean | 0.100 | 1002.888 | 24.18% | -36.51% | 77.44% |

### 4.2 Best q by model

| Model | Best q | Gross CAGR | MDD | Turnover |
| --- | --- | --- | --- | --- |
| random_forest | 0.100 | 31.45% | -34.86% | 75.90% |
| lightgbm | 0.100 | 30.53% | -32.68% | 76.86% |
| extra_trees | 0.100 | 30.25% | -36.42% | 76.25% |
| elasticnet | 0.100 | 26.78% | -36.46% | 73.81% |
| ridge | 0.100 | 24.56% | -45.68% | 73.99% |
| baseline_mean | 0.100 | 24.18% | -36.51% | 77.44% |

### 4.3 Quantile robustness

| q | Best model | Mean CAGR | Max CAGR | Mean MDD | Mean turnover |
| --- | --- | --- | --- | --- | --- |
| 0.100 | random_forest | 27.96% | 31.45% | -37.10% | 75.71% |
| 0.200 | random_forest | 18.58% | 23.52% | -36.95% | 63.01% |
| 0.300 | random_forest | 11.31% | 14.74% | -35.18% | 33.36% |

Interpretation: q=0.10 is the gross-return leader across the tested model families. q=0.20 and q=0.30 lower turnover and drawdown in some rows, but they also reduce gross CAGR materially. The q result is therefore different from the long-only branch: with the short leg restored, the narrower decile-style QSpread surface is again the strongest gross research surface.

## 5. Cost, borrow, slippage, and tax-proxy sensitivity

The sensitivity layer is deliberately simple. Transaction cost and slippage are charged on long plus short turnover, borrow is charged as a monthly short-notional drag, and tax is a simplified proxy on positive post-cost monthly returns. This is not tax-lot accounting and not tax advice.

### 5.1 Conservative proxy: 25 bps cost, 150 bps borrow, 10 bps slippage, 40.8% tax proxy

| Model | q | Net cumulative | Mean monthly net | MDD | Mean tax proxy drag |
| --- | --- | --- | --- | --- | --- |
| random_forest | 0.100 | 4.880 | 0.58% | -47.34% | 1.29% |
| lightgbm | 0.100 | 3.482 | 0.52% | -54.48% | 1.30% |
| extra_trees | 0.100 | 3.349 | 0.51% | -60.28% | 1.29% |
| random_forest | 0.200 | 2.410 | 0.38% | -40.37% | 0.93% |
| elasticnet | 0.100 | 1.759 | 0.37% | -44.54% | 1.19% |
| extra_trees | 0.200 | 0.914 | 0.24% | -48.38% | 0.92% |
| lightgbm | 0.200 | 0.909 | 0.24% | -42.31% | 0.92% |
| ridge | 0.100 | 0.679 | 0.25% | -71.59% | 1.17% |

### 5.2 Same trading assumptions before tax proxy

| Model | q | Pre-tax net cumulative | Mean monthly net | MDD |
| --- | --- | --- | --- | --- |
| random_forest | 0.100 | 521.418 | 1.88% | -38.03% |
| lightgbm | 0.100 | 404.721 | 1.83% | -35.87% |
| extra_trees | 0.100 | 384.032 | 1.80% | -39.59% |
| elasticnet | 0.100 | 171.409 | 1.57% | -42.38% |
| random_forest | 0.200 | 96.817 | 1.31% | -38.25% |
| ridge | 0.100 | 96.591 | 1.42% | -55.95% |

### 5.3 Severe proxy: 50 bps cost, 300 bps borrow, 25 bps slippage, 40.8% tax proxy

| Model | q | Severe net cumulative | Mean monthly net | MDD |
| --- | --- | --- | --- | --- |
| random_forest | 0.100 | -0.328 | 0.02% | -74.95% |
| random_forest | 0.200 | -0.483 | -0.11% | -61.38% |
| lightgbm | 0.100 | -0.512 | -0.05% | -78.71% |
| extra_trees | 0.100 | -0.515 | -0.06% | -81.31% |
| random_forest | 0.300 | -0.627 | -0.20% | -66.94% |
| elasticnet | 0.100 | -0.680 | -0.18% | -84.91% |

Interpretation: the long/short surface remains interesting under moderate frictions, but the gap between gross and conservative proxy returns is large. This supports the DDQM/EQR report style conclusion: these are research backtests whose economic interpretation depends on execution, borrow, capacity, and tax assumptions.

## 6. Model/factor diagnostics

### 6.1 Top factors in leading rows

| Model | q | Top mean-weight factors |
| --- | --- | --- |
| random_forest | 0.100 | size_local_small_size, reversal_local_ma_gap_1m, reversal_local_price_reversal_1m |
| lightgbm | 0.100 | size_local_small_size, reversal_local_ma_gap_1m, reversal_local_price_reversal_1m |
| extra_trees | 0.100 | size_local_small_size, reversal_local_ma_gap_1m, reversal_local_price_reversal_1m |
| elasticnet | 0.100 | size_local_small_size, reversal_local_ma_gap_1m, reversal_local_price_reversal_1m |
| ridge | 0.100 | size_local_small_size, reversal_local_ma_gap_1m, reversal_local_price_reversal_1m |
| baseline_mean | 0.100 | reversal_local_ma_gap_1m, reversal_local_price_reversal_1m, size_local_small_size |

### 6.2 q=0.10 factor-family weight mass by model

| Model | Earn | Quality | Reversal | Size | Value |
| --- | --- | --- | --- | --- | --- |
| baseline_mean | 0.154 | 0.177 | 0.349 | 0.149 | 0.193 |
| elasticnet | 0.278 | 0.176 | 0.266 | 0.157 | 0.163 |
| extra_trees | 0.208 | 0.191 | 0.289 | 0.147 | 0.191 |
| lightgbm | 0.231 | 0.189 | 0.297 | 0.153 | 0.154 |
| random_forest | 0.209 | 0.183 | 0.285 | 0.162 | 0.188 |
| ridge | 0.275 | 0.157 | 0.285 | 0.149 | 0.171 |

The models are not discovering completely unrelated factor worlds. Across the high-gross q=0.10 rows, size, reversal, value, quality, and earnings-related factors all appear. The tree models tend to keep the size/reversal core but improve the realized ranking enough to dominate the linear models in gross terms. This is evidence for model-dependent factor emphasis, not a causal proof that any factor family is permanently superior.

## 7. Drawdown and stress-window diagnosis

The best gross run, Random Forest q=0.10, still has a material MDD of -34.86%. Its worst months and annual profile show that strong cumulative performance does not eliminate stress-window losses.

### 7.1 Worst months in Random Forest q=0.10

| Formation date | Return | Turnover | Long turnover | Short turnover |
| --- | --- | --- | --- | --- |
| 2000-01-31 00:00:00 | -27.72% | 74.96% | 77.40% | 72.52% |
| 1999-11-30 00:00:00 | -18.24% | 77.09% | 78.45% | 75.72% |
| 2000-10-31 00:00:00 | -10.35% | 82.81% | 79.53% | 86.09% |
| 2001-02-28 00:00:00 | -10.32% | 92.05% | 91.07% | 93.02% |
| 1997-11-28 00:00:00 | -9.13% | 77.24% | 74.25% | 80.22% |

### 7.2 Weakest years

| Year | Annual return | Mean turnover |
| --- | --- | --- |
| 2014 | -17.99% | 66.83% |
| 2023 | -11.99% | 78.18% |
| 2017 | -7.95% | 67.84% |
| 2011 | 8.62% | 63.78% |
| 2007 | 9.92% | 75.82% |

### 7.3 Strongest years

| Year | Annual return | Mean turnover |
| --- | --- | --- |
| 2020 | 151.11% | 62.62% |
| 2009 | 141.15% | 72.16% |
| 2001 | 106.12% | 82.42% |
| 1998 | 83.04% | 79.72% |
| 2002 | 76.32% | 84.15% |

Interpretation: the long/short construction can defend drawdown better than the long-only branch in some settings, but it is not a free hedge. The full-panel best row still has large monthly losses and high turnover.

## 8. Relationship to the 1.25M date-balanced anchors

The prior source-controlled 1.25M date-balanced anchors reported:

- q=0.20: cumulative 5202.0665, implied CAGR 30.75%, MDD -36.02%.
- q=0.30: cumulative 4366.4377, implied CAGR 30.03%, MDD -35.71%.

The full-panel best row reports cumulative 6173.3037, CAGR 31.45%, and MDD -34.86%. The larger panel therefore does not produce a dramatic collapse of the original research result. Instead, it strengthens the case that the main DDQM/EQR long/short shape was not solely an artifact of the 1.25M date-balanced cap.

The caveat is that the best full-panel row uses q=0.10, while the prior anchors highlighted q=0.20/q=0.30. The most apples-to-apples comparison should therefore be read as evidence of robustness in broad shape, not exact identity of the best hyperparameter.

## 9. Reproducibility ledger

- Matrix report: [`full_long_short_qspread_full_chunked_report.md`](full_long_short_qspread_full_chunked_report.md).
- Matrix CSV: [`full_long_short_qspread_full_chunked_report.csv`](full_long_short_qspread_full_chunked_report.csv).
- Sensitivity CSV: [`full_long_short_qspread_full_chunked_report_sensitivity.csv`](full_long_short_qspread_full_chunked_report_sensitivity.csv).
- Ledger: [`full_long_short_qspread_full_chunked_ledger.json`](full_long_short_qspread_full_chunked_ledger.json).
- Local run root: `experiments/ddqm2_full_long_short/`.
- Run count: 18.
- Failures: 0.

## 10. Limitations and next steps

1. The cost/borrow/slippage/tax sensitivity is a proxy, not production execution modeling.
2. The tax proxy is not jurisdiction-specific tax advice and does not implement tax-lot accounting.
3. Capacity, liquidity, short availability, financing, and market impact remain outside this completed run.
4. Hyperparameter probes were intentionally deferred after the full anchor grid because the stop trigger was satisfied: complete full-panel anchor grid, zero failures, and sufficient model/q evidence.
5. The model objective forecasts factor returns; it does not directly optimize net-after-cost utility.

Next work should be additive: q-neighborhood probes around q=0.10/q=0.20, conservative tree hyperparameter probes, drawdown-focused diagnostics, and an equal-turnover comparison layer.

## 11. Conclusion

The completed full-panel long/short run supports the existing DDQM/DDQM2/EQR direction more strongly than the long-only branch. The short leg appears central to the research result. The best tested gross row is Random Forest q=0.10, while LightGBM and Extra Trees provide close tree-model confirmations. However, conservative proxy frictions materially compress the result, so the defensible conclusion is not that a production strategy is ready. The defensible conclusion is that the full local panel preserves a meaningful long/short QSpread research signal worth further cost-aware and drawdown-aware study.
