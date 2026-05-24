# Long-only QSpread ML Cost/Tax Analysis Report v2

Date: 2026-05-24

Companion Korean report: [`long_only_qspread_ml_costs_full_chunked_analysis_v2_ko.md`](long_only_qspread_ml_costs_full_chunked_analysis_v2_ko.md)

## Abstract

This v2 report upgrades the previous long-only QSpread summary into an experiment-report-style narrative. It documents the path from the existing USA-DDQM2 long/short work to a long-only, fully invested stock-score QSpread matrix; records what was produced by the completed local runs; and offers a cautious interpretation of the final results. The report does not add new experiments, does not contact WRDS, and does not acquire new raw data. It is written from existing local artifacts: the completed matrix CSV/ledger and the already-generated run directories.

The central empirical result is that **q=0.30 is the strongest conservative-net surface across all six tested model families**. The result is not simply “larger basket is better”; rather, it says that under a 50 bps one-way turnover cost and a 40.8% simplified tax-drag proxy, the wider basket reduces turnover enough to dominate narrower high-gross, high-turnover variants. The baseline-mean q=0.30 run has the highest primary net cumulative return, while Extra Trees, Random Forest, and LightGBM form the strongest ML comparison set.

## 1. Background and problem definition

The previous DDQM2 adaptation tested a U.S. equity version of a macro-to-factor-return idea: predict factor returns from macro/market information, convert those predictions into factor allocations, and evaluate stock-level QSpread portfolios. That work kept the DDQM2-style long/short surface as the comparison anchor.

The new question is narrower and more operationally conservative:

> What remains interesting if the short leg is discarded, the portfolio is forced to be long-only and fully invested, and the result is evaluated through a conservative net-of-cost lens?

This matters because a long/short research backtest and a long-only constrained portfolio answer different questions. The former can show directional spread efficacy; the latter tests whether the ranking signal still gives a plausible long-only selection surface after turnover-driven frictions are acknowledged.

## 2. Relationship to the existing DDQM2 reports

This report is additive. It does not replace the existing DDQM2 reports:

- [`usa_ddqm2_matrix_report_en.md`](usa_ddqm2_matrix_report_en.md)
- [`usa_ddqm2_matrix_report_ko.md`](usa_ddqm2_matrix_report_ko.md)

Those reports remain the long/short benchmark and methodological backdrop. This v2 report adds a long-only branch of the experiment tree: same local research environment, same preservation policy, but a different portfolio constraint and a stronger emphasis on net interpretation.

## 3. Experiment timeline

1. **Baseline DDQM2/EQR adaptation.** The repository first established local panel preparation, PIT feature construction, factor scoring, factor-return modeling, and DDQM2-style QSpread reports.
2. **Long-only reframing.** The short strategy was intentionally not optimized further. The new surface uses top-q stock scores only, equal-weighted and fully invested.
3. **Memory-safe full-panel path.** The full local panel has 2,082,485 rows and 159 features. Feature preparation was partitioned into 35 parts, and factor-score generation/backtesting were made chunk-aware.
4. **Completed matrix.** The matrix ran 18 model/q combinations with 0 failures: six model families across q=0.10, q=0.20, and q=0.30.
5. **Report layer.** The first bilingual report summarized the result. This v2 report turns that summary into a fuller experiment narrative with appendices for interpretability and reproducibility.

## 4. Data boundary and publication policy

The data boundary is explicit: `local_artifacts_only_no_wrds_login_no_runtime_external_data`. The run reads local parquet artifacts only. No WRDS login, external service call, or new raw data acquisition is part of this report pass.

Source-controlled files are documentation and compact report artifacts. Large generated parquet outputs remain local under `experiments/` and are intentionally ignored by git.

## 5. Portfolio construction and net assumptions

For each month, the harness combines predicted factor returns with selected factor scores to form a stock score. The long-only surface then selects the top q fraction of stocks, equal-weights that long basket, remains fully invested, and evaluates the next-month forward return.

Primary net assumptions:

- Transaction cost: 50.0 bps per one-way turnover.
- Tax proxy: 40.8% applied to positive monthly gains realized by turnover.
- Interpretation: simplified research sensitivity, not tax advice.

## 6. Main model/q matrix evidence

The matrix itself is the core evidence for the report. Every model family prefers q=0.30 under the conservative net definition.

### 6.1 Model-by-model best-q summary

| Rank | Model | Best q | Net cumulative | Gross cumulative | MDD | Turnover | Run ID |
|---|---|---|---|---|---|---|---|
| 1 | baseline_mean | 0.30 | 51.323 | 142.832 | -0.599 | 0.159 | longonly_full_chunked_20260524_baseline_mean_q30 |
| 2 | extra_trees | 0.30 | 28.049 | 269.394 | -0.584 | 0.352 | longonly_full_chunked_20260524_extra_trees_q30 |
| 3 | random_forest | 0.30 | 25.395 | 289.517 | -0.601 | 0.370 | longonly_full_chunked_20260524_random_forest_q30 |
| 4 | lightgbm | 0.30 | 21.896 | 299.618 | -0.584 | 0.415 | longonly_full_chunked_20260524_lightgbm_q30 |
| 5 | elasticnet | 0.30 | 13.087 | 180.804 | -0.629 | 0.422 | longonly_full_chunked_20260524_elasticnet_q30 |
| 6 | ridge | 0.30 | 7.595 | 100.998 | -0.615 | 0.400 | longonly_full_chunked_20260524_ridge_q30 |

### 6.2 Quantile-level summary

| q | Mean net | Median net | Max net | Mean gross | Mean turnover | Mean MDD | Mean tax drag | Mean trading drag |
|---|---|---|---|---|---|---|---|---|
| 0.10 | 5.203 | 5.447 | 8.496 | 3757.760 | 0.744 | -0.672 | 0.0146 | 0.0037 |
| 0.20 | 3.654 | 4.117 | 5.411 | 549.280 | 0.636 | -0.648 | 0.0101 | 0.0032 |
| 0.30 | 24.557 | 23.646 | 51.323 | 213.861 | 0.353 | -0.602 | 0.0043 | 0.0018 |

### 6.3 Full model/q matrix

| Model | q | Net cum | Gross cum | MDD | Turnover | Avg tax drag | Avg trading drag |
|---|---|---|---|---|---|---|---|
| lightgbm | 0.10 | 6.034 | 4425.7 | -0.663 | 0.757 | 0.0148 | 0.0038 |
| lightgbm | 0.20 | 4.048 | 616.4 | -0.642 | 0.649 | 0.0102 | 0.0032 |
| lightgbm | 0.30 | 21.896 | 299.6 | -0.584 | 0.415 | 0.0050 | 0.0021 |
| ridge | 0.10 | 2.727 | 1861.7 | -0.726 | 0.736 | 0.0142 | 0.0037 |
| ridge | 0.20 | 1.521 | 252.4 | -0.668 | 0.621 | 0.0098 | 0.0031 |
| ridge | 0.30 | 7.595 | 101.0 | -0.615 | 0.400 | 0.0048 | 0.0020 |
| elasticnet | 0.10 | 4.859 | 2830.4 | -0.660 | 0.736 | 0.0141 | 0.0037 |
| elasticnet | 0.20 | 4.185 | 516.6 | -0.648 | 0.624 | 0.0098 | 0.0031 |
| elasticnet | 0.30 | 13.087 | 180.8 | -0.629 | 0.422 | 0.0049 | 0.0021 |
| random_forest | 0.10 | 8.496 | 6332.0 | -0.644 | 0.742 | 0.0150 | 0.0037 |
| random_forest | 0.20 | 5.411 | 864.8 | -0.658 | 0.642 | 0.0105 | 0.0032 |
| random_forest | 0.30 | 25.395 | 289.5 | -0.601 | 0.370 | 0.0047 | 0.0019 |
| extra_trees | 0.10 | 6.964 | 5075.6 | -0.637 | 0.748 | 0.0149 | 0.0037 |
| extra_trees | 0.20 | 5.033 | 712.9 | -0.630 | 0.636 | 0.0102 | 0.0032 |
| extra_trees | 0.30 | 28.049 | 269.4 | -0.584 | 0.352 | 0.0044 | 0.0018 |
| baseline_mean | 0.10 | 2.135 | 2021.1 | -0.702 | 0.745 | 0.0149 | 0.0037 |
| baseline_mean | 0.20 | 1.726 | 332.7 | -0.642 | 0.643 | 0.0103 | 0.0032 |
| baseline_mean | 0.30 | 51.323 | 142.8 | -0.599 | 0.159 | 0.0020 | 0.0008 |

## 7. Interpretation of the cost/tax net transition

The cost/tax lens changes the apparent ranking of the experiment. Narrower q=0.10 portfolios often produce enormous gross cumulative returns, but they also require much more monthly replacement of the selected basket. At q=0.10, mean turnover is 0.744; at q=0.30 it falls to 0.353. That turnover reduction is the reason q=0.30 survives the conservative net test.

For the best net run (`longonly_full_chunked_20260524_baseline_mean_q30`), the primary sensitivity row records cumulative return 51.323 under 50 bps and 40.8% tax proxy. With the same 50 bps cost and zero tax proxy, the sensitivity table records 105.412. Evidence: the tax proxy matters materially, but does not fully explain the q=0.30 result.

Interpretation: the experiment is less a proof of production alpha than a demonstration that the ranking surface must be judged jointly with turnover, drawdown, and friction assumptions. A high-gross model is not automatically the best research candidate if it churns the basket too aggressively.

## 8. Factor/model interpretation

The top weighted factor strings in the run diagnostics repeatedly point to a small set of factor families:

| Factor family | Top-factor appearances |
|---|---|
| quality | 25 |
| reversal | 24 |
| val | 19 |
| size | 18 |
| earn | 4 |

Evidence: quality, reversal, value, and size exposures appear repeatedly in the top weighted factors. Interpretation: the long-only surface is not a pure black-box model contest; the strongest runs tend to be explainable as mixes of quality/value stability, size exposure, and short-horizon reversal. This is economically plausible but not yet a causal proof.

## 9. Annual profile and stress months

The annual profile below uses the best primary net run, baseline_mean q=0.30, as a concrete lens. This is not a claim that it should be deployed; it is the run that best illustrates the low-turnover net result.

### 9.1 Strongest years in the best net run

| Year | Annual net | Mean turnover |
|---|---|---|
| 2003 | 93.1% | 0.166 |
| 2009 | 82.6% | 0.179 |
| 2020 | 44.5% | 0.194 |
| 2013 | 37.9% | 0.152 |
| 2016 | 35.7% | 0.136 |

### 9.2 Weakest years in the best net run

| Year | Annual net | Mean turnover |
|---|---|---|
| 2008 | -43.7% | 0.143 |
| 2023 | -16.1% | 0.213 |
| 2007 | -14.7% | 0.128 |
| 2015 | -9.0% | 0.136 |
| 2022 | -8.8% | 0.175 |

### 9.3 Worst monthly observations in the best net run

| Formation date | Net return | Gross return | Turnover | Tax drag | Trading drag |
|---|---|---|---|---|---|
| 2020-02-28 00:00:00 | -25.8% | -25.7% | 0.138 | 0.0000 | 0.0007 |
| 2008-09-30 00:00:00 | -20.9% | -20.9% | 0.157 | 0.0000 | 0.0008 |
| 1998-07-31 00:00:00 | -18.8% | -18.7% | 0.135 | 0.0000 | 0.0007 |

The worst months include recognizable stress windows such as 2008-09 and 2020-02. The drawdown evidence matters because the long-only surface remains exposed to broad equity-market selloffs; removing the short leg does not remove market risk.

## 10. Reproducibility and harness appendix

- Feature directory: `experiments/prepared/features_full_chunked`.
- Output directory: `experiments/ddqm2_long_only_full_chunked`.
- Feature rows: 2,082,485.
- Feature count: 159.
- Feature partitions: 35.
- Matrix runs: 18.
- Matrix failures: 0.
- Ledger: [`long_only_qspread_ml_costs_full_chunked_ledger.json`](long_only_qspread_ml_costs_full_chunked_ledger.json).
- Matrix CSV: [`long_only_qspread_ml_costs_full_chunked_report.csv`](long_only_qspread_ml_costs_full_chunked_report.csv).

The harness detail belongs in the appendix because it is not the primary research conclusion, but it is essential for understanding why the full 2.08M-row run was feasible in a small-memory environment. The report pass did not rerun experiments; it only read the completed artifacts.

## 11. Limitations and next experiments

1. **No new robustness runs in this pass.** q=0.25/q=0.35, alternative cost grids, and additional model profiles remain future work.
2. **Simplified tax proxy.** The 40.8% assumption is a conservative research proxy, not tax advice and not tax-lot accounting.
3. **No capacity model.** Slippage, market impact, liquidity constraints, and capacity are not fully modeled.
4. **Model objective mismatch.** Models forecast factor returns; they do not directly optimize net-after-cost portfolio outcomes.
5. **Baseline-mean surprise.** The best net run being baseline_mean may reflect the value of stable low-turnover factor exposure, but it could also indicate that ML objectives need cost-aware reformulation.

Follow-up experiments should be separated into a new plan: cost-aware objectives, q-neighborhood robustness, liquidity/capacity filters, and model comparison under equal turnover constraints.

## 12. Conclusion

This experiment adds a long-only branch to the DDQM2/EQR research story. The main result is not that a deployable strategy has been found. The defensible conclusion is narrower: when the short leg is removed and conservative frictions are imposed, q=0.30 becomes the most robust tested long-only surface, and model interpretation shifts from gross return chasing toward turnover-aware factor stability.
