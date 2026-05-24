# Long-only QSpread ML Cost/Tax Analysis Report

Date: 2026-05-24
Repository: `autoquant-lab`
Primary ledger: [`long_only_qspread_ml_costs_full_chunked_ledger.json`](long_only_qspread_ml_costs_full_chunked_ledger.json)
Companion Korean translation: [`long_only_qspread_ml_costs_full_chunked_analysis_ko.md`](long_only_qspread_ml_costs_full_chunked_analysis_ko.md)

## Executive summary

This report documents an additive research experiment that keeps the previous DDQM2 long/short results intact while testing a more conservative **long-only stock-score QSpread** surface. The experiment uses the same local DDQM2/EQR research harness, but discards any new short-leg optimization and evaluates top-`q` equal-weight, fully invested long portfolios across several CPU-friendly ML models.

The experiment uses **local parquet artifacts only**. No WRDS login, external data download, or new raw data acquisition was performed.

Main findings:

1. **q=0.30 dominates the primary net lens for every model.** Wider top baskets reduce turnover and therefore reduce the conservative transaction-cost/tax drag enough to beat narrower q=0.10 and q=0.20 variants.
2. **The net-vs-gross gap is the central result.** Narrow q=0.10 variants show extremely large gross cumulative returns, but high turnover makes the conservative net result much less attractive.
3. **The baseline-mean model is the best net performer in this matrix.** That should not be read as “ML is useless.” It is evidence that this first-pass net lens heavily rewards lower turnover and stable factor exposure; it also means model edge must be judged jointly with turnover, drawdown, and factor concentration rather than gross return alone.
4. **Tree models still show useful diagnostics.** Extra Trees and Random Forest have the strongest non-baseline net results at q=0.30, while LightGBM has the largest q=0.30 gross return among the ML models. These differences are useful for interpreting which factor families each model emphasizes.
5. **This is a research backtest, not a trading strategy.** Slippage, tax, and capacity are proxied with simplified assumptions; the report is not investment, tax, or legal advice.

## Scope and preservation policy

The experiment is additive:

- Existing DDQM2 matrix reports remain the baseline comparison:
  - [`usa_ddqm2_matrix_report_en.md`](usa_ddqm2_matrix_report_en.md)
  - [`usa_ddqm2_matrix_report_ko.md`](usa_ddqm2_matrix_report_ko.md)
- Existing generated experiment directories were not overwritten.
- New run artifacts were written under `experiments/ddqm2_long_only_full_chunked/` and remain ignored by git.
- Source-controlled deliverables are limited to code, ledger/report summaries, and documentation.

## Data and harness

| Item | Value |
|---|---:|
| Local feature directory | `experiments/prepared/features_full_chunked` |
| Full label panel rows | 2,082,485 |
| Feature count | 159 |
| Feature partitions | 35 |
| Monthly coverage | 1990-01 to 2024-12 |
| Portfolio periods in matrix | 383 |
| Models | LightGBM, ridge, elasticnet, random forest, extra trees, baseline mean |
| Quantiles | q=0.10, q=0.20, q=0.30 |
| Matrix runs | 18 |
| Failures | 0 |

The memory-safe harness uses monthly/date chunking for feature and factor-score construction. It avoids materializing all stock-factor score rows at once, which is essential for running the 2.08M-row panel on a 2 OCPU / 12 GB-class environment.

## Portfolio and cost assumptions

Portfolio construction:

- score stocks by weighted DDQM2/EQR factor predictions;
- select the top `q` stocks each month;
- equal-weight the selected long-only basket;
- keep the portfolio fully invested;
- rebalance monthly;
- evaluate using next-month forward returns.

Primary conservative net assumptions:

| Assumption | Value |
|---|---:|
| One-way turnover transaction cost | 50 bps |
| Simplified tax drag | 40.8% |
| Tax proxy | positive monthly gain × turnover × tax rate |
| Interpretation | research sensitivity only; not tax advice |

## Model-by-model best-q summary

| Rank | Model | Best q | Net cumulative | Gross cumulative | Max drawdown | Turnover | Interpretation |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | baseline_mean | 0.30 | 51.322593 | 142.832212 | -0.599271 | 0.159131 | Highest net; likely benefits from stable low-turnover factor mix. |
| 2 | extra_trees | 0.30 | 28.048746 | 269.394256 | -0.584286 | 0.352090 | Best non-baseline net; quality/value-heavy diagnostics. |
| 3 | random_forest | 0.30 | 25.395444 | 289.516978 | -0.600565 | 0.370048 | Similar to Extra Trees, slightly higher drawdown/turnover. |
| 4 | lightgbm | 0.30 | 21.895557 | 299.617899 | -0.584324 | 0.415116 | Strong gross among ML models, but higher turnover drag. |
| 5 | elasticnet | 0.30 | 13.087143 | 180.803946 | -0.629269 | 0.421751 | Linear sparse/dense structure remains a useful comparator. |
| 6 | ridge | 0.30 | 7.595449 | 100.998272 | -0.614620 | 0.400174 | Lower net but still confirms q=0.30 robustness. |

## Quantile robustness

The q-axis is the clearest robustness result. q=0.30 wins under the conservative net definition for all six model families.

| Model | q=0.10 net | q=0.20 net | q=0.30 net | q=0.30 turnover |
|---|---:|---:|---:|---:|
| lightgbm | 6.034166 | 4.048132 | 21.895557 | 0.415116 |
| ridge | 2.726859 | 1.521176 | 7.595449 | 0.400174 |
| elasticnet | 4.859060 | 4.185112 | 13.087143 | 0.421751 |
| random_forest | 8.496163 | 5.410548 | 25.395444 | 0.370048 |
| extra_trees | 6.963795 | 5.032797 | 28.048746 | 0.352090 |
| baseline_mean | 2.135122 | 1.725806 | 51.322593 | 0.159131 |

Interpretation: the result does **not** prove that q=0.30 is globally optimal. It says that, in this local artifact set and this cost/tax proxy, wider baskets survive the net-cost test better than narrower, higher-turnover baskets.

## Factor and model diagnostics

The top weighted factor diagnostics repeatedly surface:

- size / small-size exposure;
- short-horizon reversal or moving-average gap factors;
- quality factors such as net-income year-over-year behavior;
- value factors such as forward price-to-book and relative price-to-book.

At q=0.30, the strongest net runs tend to shift toward more stable quality/value mixtures and lower turnover. This is consistent with the cost/tax result: gross alpha is not enough if it requires excessive monthly replacement of the selected basket.

## Comparison to existing long/short DDQM2 results

The existing DDQM2 report remains the long/short comparison anchor. This report should be read beside it rather than as a replacement.

The new long-only matrix answers a narrower question:

> If short optimization is removed and the strategy is forced to be long-only, fully invested, and evaluated net of conservative costs/tax proxy, which q/model combinations remain interesting?

The answer from this matrix is: q=0.30 is the first follow-up surface, and Extra Trees / Random Forest / LightGBM are useful ML comparators against the surprisingly strong baseline-mean low-turnover result.

## Reproducibility ledger

Source-controlled ledger:

- [`long_only_qspread_ml_costs_full_chunked_ledger.json`](long_only_qspread_ml_costs_full_chunked_ledger.json)
- [`long_only_qspread_ml_costs_full_chunked_report.csv`](long_only_qspread_ml_costs_full_chunked_report.csv)
- generated Korean matrix report: [`long_only_qspread_ml_costs_full_chunked_report.md`](long_only_qspread_ml_costs_full_chunked_report.md)

Key verification evidence from the completion run:

```text
Matrix runs: 18
Failures: 0
Feature rows: 2,082,485
Feature chunks: 35
pytest: 153 passed, 54 warnings
Data boundary: local artifacts only; no WRDS login; no runtime external data
```

## Interpretation hooks for follow-up discussion

These are the main judgment calls left for human interpretation:

1. Is the baseline-mean q=0.30 result a genuine low-turnover factor-allocation result, or a sign that the ML objective needs an explicit turnover/cost-aware target?
2. Should the next ML pass optimize for net return directly rather than forecast factor long/short returns and then apply costs downstream?
3. Is q=0.30 robust enough, or should q=0.25/q=0.35 and sector/cap filters be tested before drawing stronger conclusions?
4. Which factor families are acceptable from an economic-story perspective: size/reversal, quality/value, or a constrained subset?
5. How much of the high gross return is likely non-tradable once market impact, liquidity, and tax-lot realism are made stricter?

## Limitations

- No new raw data was acquired.
- The tax proxy is intentionally simplified and conservative; it is not tax advice.
- Slippage, market impact, borrow constraints, capacity, and tax-lot accounting are not fully modeled.
- Generated experiment parquet artifacts remain local and ignored by git.
- The experiment evaluates a research surface, not a production trading system.
