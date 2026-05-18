# autoquant-lab Experiment Report

Date: 2026-05-16

Korean version: [`reports/usa_ddqm2_matrix_report_ko.md`](usa_ddqm2_matrix_report_ko.md)

Report index: [`reports/usa_ddqm2_matrix_report.md`](usa_ddqm2_matrix_report.md)

## Abstract

This project builds an offline CPU-only research harness for adapting the core DDQM/DDQM2 idea to a U.S. equity setting. It preserves the high-level structure of the original approach: forecast factor returns from macro/market variables, convert predicted factor returns into dynamic factor allocations, and evaluate long-short or QSpread-style portfolios. The implementation uses local CRSP/Compustat/IBES/FRED-style artifacts and excludes raw data, credentials, private notes, generated experiment artifacts, and vendor/reference PDFs from public GitHub publication.

The final implementation includes a selected 13-factor universe, DDQM2-style U.S. macro feature design, CPU-friendly factor-return forecasting, stock-level weighted factor score QSpread, expanding walk-forward OOS evaluation, and an ablation planner. The 1,250,000 rows used in the reported matrix are not the full raw universe; they are a date-balanced prepared panel cap. On that prepared panel, the LightGBM matrix covered q=0.10, q=0.20, and q=0.30 over 383 OOS months. A separate chunked model sweep compared ridge, elasticnet, random forest, extra trees, and baseline mean. q=0.20 stock-score QSpread produced the highest cumulative return, while q=0.30 stock-score QSpread looked more balanced across mean/vol, turnover, and drawdown. All results remain gross research backtests without transaction costs, slippage, borrow, tax, market impact, capacity, or final tradability review.

## 1. Background and Problem Definition

DDQM2 forecasts next-period factor long-short returns rather than individual stock returns, then dynamically changes factor weights based on those predictions. The goal of this project was to implement that structure for U.S. equities and create a repeatable harness for long-running server experiments.

Initial constraints were:

1. Use only already-prepared local WRDS/FRED-style artifacts.
2. Avoid runtime login, credential prompts, or external downloads.
3. Do not publish CRSP/Compustat/IBES/FRED source data or private notes.
4. Exclude GPU-heavy models such as LSTM or Transformer models.
5. Evaluate with repeatable walk-forward OOS runs rather than simple return ranking.

The result should be interpreted as a research harness and early empirical study, not as a production trading strategy.

## 2. Relationship to DDQM/DDQM2

### 2.1 What follows DDQM/DDQM2

- The target is factor return, not direct stock return.
- Factor returns are constructed as top/bottom bucket long-short returns.
- Macro/market variables forecast each factor's next-period return.
- One regression model is trained per factor.
- Predicted factor returns are converted into non-negative factor weights.
- Final performance is evaluated through long-short or QSpread-style portfolios.
- q=0.10 is retained as the DDQM2-reference decile construction.

### 2.2 What changed in the U.S. adaptation

- Universe: U.S. equity monthly panel instead of KOSPI200-style Korean universe.
- Data: CRSP/Compustat/IBES/FRED-style local artifacts instead of original Korean-market data.
- Factor universe: selected 13-factor universe from the EQR factor registry instead of a direct 1:1 copy of the original 13 factors.
- Macro design: U.S. proxy adaptation of the 25 x 3 DDQM2 macro structure.
- Evaluation: expanding walk-forward OOS is the main protocol.
- Quantile: q=0.10 is a reference setting, while q=0.20 and q=0.30 remain U.S. adaptation axes.

### 2.3 Comparing DDQM/DDQM2 results with this study

The original DDQM/DDQM2 results and the autoquant-lab results should not be compared as direct return numbers. The original studies use Korean-market data, original universe definitions, original factors, and original evaluation assumptions. This project uses a U.S. equity monthly panel, U.S. macro proxies, a date-balanced prepared panel cap, and a different evaluation stack. The comparison is therefore methodological: whether the same direction of improvement appears when the idea is adapted to U.S. data.

| Item | DDQM | DDQM2 | autoquant-lab U.S. adaptation |
|---|---|---|---|
| Market / universe | Korean market / KOSPI200-style universe | Korean market / KOSPI200-style universe | U.S. equity monthly panel, 1.25M-row date-balanced prepared panel |
| Prediction target | Factor regime or style state | Next-period factor long-short return | Next-1M factor long-short return |
| Main model | Random Forest-style classifier | LightGBM-style regression | LightGBM-centered matrix plus ridge, elasticnet, tree ensembles, baseline mean |
| Portfolio construction | Factor rotation by predicted regime | Dynamic allocation from predicted factor returns | Weighted factor-return surface and stock-score QSpread surface |
| Result interpretation | Dynamic rotation improves over static factor use inside the original setup | Factor-return regression improves the DDQM direction inside the original setup | Stock-score QSpread looked closer to DDQM2 final construction and produced stronger results than the factor-return surface |
| Direct comparability | Internal comparison only | Internal comparison only | Not directly comparable by raw return level because market, data, period, costs, and universe differ |


From a return perspective, the original DDQM and DDQM2 reports both argue that dynamic factor rotation improves over static style/factor portfolios. The table below places the original reported summary statistics next to the strongest U.S. adaptation candidates. It should still be read as context, not a direct contest: markets, universes, periods, cost assumptions, volatility definitions, and data vendors differ.

| Strategy / experiment | Market / period | Portfolio construction | Reported return | Risk / turnover notes | Interpretation |
|---|---|---|---:|---|---|
| Original DDQM | Korea, early 2011-Aug 2022 | Top 20% long / bottom 20% short | +704% cumulative, 20.0% CAGR | Sharpe 1.4, MDD -22%, turnover 57% | Dynamic regime/factor rotation improved over static styles in the original setup |
| Original DDQM2 | Korea, early 2011-Jun 2023 | Top 10% long / bottom 10% short | +1,357% cumulative, 23.9% CAGR | Sharpe 1.3, MDD -30%, turnover 65.1% | Factor-return regression improved the DDQM direction in the original setup |
| autoquant q=0.20 stock-score | U.S. panel, Jan 1993-Nov 2024 | Top 20% long / bottom 20% short | cumulative return ratio 5202.0665, implied CAGR about 30.7% | monthly vol 5.73%, MDD -36.02%, turnover 71.93% | Aggressive return candidate, gross-only and not cost adjusted |
| autoquant q=0.30 stock-score | U.S. panel, Jan 1993-Nov 2024 | Top 30% long / bottom 30% short | cumulative return ratio 4366.4377, implied CAGR about 30.0% | monthly vol 5.41%, MDD -35.71%, turnover 71.39% | More balanced candidate with lower volatility and turnover than q=0.20 |

The useful comparison is directional: DDQM2 moved from discrete regime classification toward direct factor-return forecasting, and this U.S. adaptation also became much stronger when factor-return forecasts were translated into a stock-level QSpread surface. The claim is not that the U.S. run beat the Korean-market original, but that the same methodological chain, factor-return forecast to dynamic allocation to QSpread construction, produced a strong gross research signal in a different market.

Three directional similarities were observed:

1. Factor-return forecasting is easier to audit than direct stock-return prediction because labels, predictions, allocations, and portfolio returns can be separated.
2. Dynamic factor allocation is central; the portfolio changes factor weights with macro/market state rather than holding one fixed factor mix.
3. Portfolio construction matters. In this study, the stock-level weighted factor score QSpread surface was closer to the DDQM2 final portfolio idea and stronger than the weighted factor-return surface.

Important differences remain:

- This is an adaptation, not a replication of the Korean-market experiments.
- The selected 13-factor universe is not a 1:1 copy of the original factor set.
- Costs, taxes, borrow, slippage, and capacity are not yet netted out.
- A direct numeric comparison would require matched periods, matched universe rules, and matched cost assumptions.

## 3. Data and Publication Boundary

This report does not include source data values or private file contents. It only describes broad data categories:

- CRSP-style monthly equity data
- Compustat-style accounting features
- IBES-style estimate/revision features
- FRED-style macro/market features

Excluded from public GitHub:

- WRDS/CRSP/Compustat/IBES raw parquet or raw exports
- FRED/macro source exports
- `.env` and credentials
- private notes such as `EQR.md`
- DDQM/DDQM2 PDF references
- generated parquet/csv experiment artifacts
- generated static site output

## 4. Harness Structure

```text
prepared panel/features
→ factor score generation
→ factor long-short return labeling
→ per-factor CPU-friendly regression
→ predicted factor return
→ factor allocation
→ weighted factor-return or stock-score QSpread backtest
→ manifest/report
```

The implementation also added memory-safe chunking, date-balanced panel caps, manifest-based parsing, and secret/publication checks.

## 5. Final USA-DDQM2 Matrix

Common setup:

- Model: LightGBM
- Evaluation: expanding walk-forward OOS
- Prepared panel rows: 1,250,000 (date-balanced cap, not full raw universe)
- OOS periods: 383
- Factor universe: selected 13 global/local factors
- q values: 0.10, 0.20, 0.30

| Run | q | Macro | Surface | Periods | Cum. Return | Max DD | Mean Monthly | Vol Monthly | Turnover |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| `usa_ddqm2_lightgbm_q010_selected13_currentmacro_factorret` | 0.10 | current | factor-return | 383 | 386.8638 | -0.2708 | 0.0165 | 0.0408 |  |
| `usa_ddqm2_lightgbm_q010_selected13_ddqm2macro_stockscore` | 0.10 | DDQM2 25x3 | stock-score QSpread | 383 | 5094.4375 | -0.3076 | 0.0243 | 0.0627 | 0.7319 |
| `usa_ddqm2_lightgbm_q020_selected13_currentmacro_factorret` | 0.20 | current | factor-return | 383 | 53.1742 | -0.2198 | 0.0109 | 0.0304 |  |
| `usa_ddqm2_lightgbm_q020_selected13_ddqm2macro_stockscore` | 0.20 | DDQM2 25x3 | stock-score QSpread | 383 | 5202.0665 | -0.3602 | 0.0241 | 0.0572 | 0.7193 |
| `usa_ddqm2_lightgbm_q030_selected13_currentmacro_factorret` | 0.30 | current | factor-return | 383 | 30.4420 | -0.1826 | 0.0093 | 0.0228 |  |
| `usa_ddqm2_lightgbm_q030_selected13_ddqm2macro_stockscore` | 0.30 | DDQM2 25x3 | stock-score QSpread | 383 | 4366.4377 | -0.3571 | 0.0235 | 0.0540 | 0.7139 |

Interpretation:

- The stock-score QSpread surface was much stronger than the factor-return surface.
- q=0.20 stock-score produced the highest cumulative return.
- q=0.30 stock-score had a more balanced practical profile across mean/vol, turnover, and drawdown.
- q=0.10 remains a DDQM2-reference benchmark, not a forced default.

## 6. CPU-Friendly Model Sweep

The model sweep is diagnostic rather than the final headline matrix because it used a broader factor-return surface and a different evaluation setup.

1.0M-row q=0.10 chunked sweep:

| Run | Model | q | Periods | Cum. Return | Max DD |
|---|---|---:|---:|---:|---:|
| `chunked_1000000_lightgbm_q10` | lightgbm | 0.10 | 197 | 178.9471 | -0.2281 |
| `chunked_1000000_ridge_q10` | ridge | 0.10 | 197 | 130.4248 | -0.2206 |
| `chunked_1000000_elasticnet_q10` | elasticnet | 0.10 | 197 | 130.4764 | -0.2423 |
| `chunked_1000000_random_forest_q10` | random_forest | 0.10 | 197 | 76.6173 | -0.2528 |
| `chunked_1000000_extra_trees_q10` | extra_trees | 0.10 | 197 | 64.2307 | -0.2498 |
| `chunked_1000000_baseline_mean_q10` | baseline_mean | 0.10 | 197 | 22.7204 | -0.2683 |

1.25M-row date-balanced prepared panel, q=0.10 fixed-holdout family:

| Run | Model | q | Periods | Cum. Return | Max DD |
|---|---|---:|---:|---:|---:|
| `chunked_1250000_ridge_q10` | ridge | 0.10 | 257 | 5565.9987 | -0.4179 |
| `chunked_1250000_elasticnet_q10` | elasticnet | 0.10 | 257 | 4213.1459 | -0.4732 |
| `chunked_1250000_lightgbm_q10` | lightgbm | 0.10 | 257 | 1112.2701 | -0.6871 |
| `chunked_1250000_lightgbm_q10_minw01` | lightgbm | 0.10 | 257 | 195.3615 | -0.6949 |
| `chunked_1250000_baseline_mean_q10` | baseline_mean | 0.10 | 257 | 13.5862 | -0.7570 |

Ridge and elasticnet should remain core follow-up models. Random forest and extra trees improved on baseline mean but were weaker than LightGBM/ridge/elasticnet in the available sweeps.

## 7. Limitations

- Transaction cost, slippage, borrow, taxes, market impact, and capacity are not reflected.
- Turnover for stock-score runs is high, around 0.71 to 0.73.
- The selected 13-factor universe needs an overlap and economic interpretation audit.
- The U.S. macro design is a proxy adaptation, not a one-to-one copy of the original DDQM2 macro variables.
- Ridge/elasticnet have not yet been rerun under the final selected13 stock-score walk-forward matrix.
- Annual/regime breakdown and statistical significance tests remain incomplete.
- The interpretability appendix is aggregate-only and does not publish stock-level attribution.

## 8. Conclusion

autoquant-lab shows that the DDQM2 idea can be expressed as a reproducible U.S. equity research harness: factor-return labels, CPU-friendly model forecasts, dynamic factor allocation, and stock-score QSpread portfolios. The strongest current interpretation is not that this is a finished strategy, but that the stock-score QSpread surface and q=0.20/q=0.30 settings are meaningful candidates for deeper robustness testing.

The comparison with DDQM/DDQM2 should be read as a methodological comparison, not a direct return contest. The existing-artifact interpretability appendix supports the same q=0.20 aggressive versus q=0.30 balanced reading, but it does not turn the gross backtest into a tradable strategy. The next step is to net transaction costs and slippage, test ridge/elasticnet under the same selected13 stock-score walk-forward setup, and run regime/year robustness checks.


## 9. Existing-Artifact Interpretability Appendix

This section uses only generated q=0.20 and q=0.30 stock-score QSpread artifacts that already existed on the server. No new WRDS login, new data download, or new model training was used. The supporting artifacts were `portfolio_returns.parquet`, `factor_allocations.parquet`, `factor_model_metrics.csv`, and `qspread_legs.parquet`. All summaries are aggregate-only; no stock-level rows or names are published.

### 9.1 Aggregate q=0.20 versus q=0.30 profile

| Item | q=0.20 stock-score | q=0.30 stock-score | Interpretation |
|---|---:|---:|---|
| OOS periods | 383 | 383 | Same Jan 1993-Nov 2024 window |
| Mean monthly return | 0.0241 | 0.0235 | q=0.20 is slightly higher |
| Monthly volatility | 0.0573 | 0.0541 | q=0.30 is lower |
| Average turnover | 0.7193 | 0.7139 | q=0.30 is slightly lower |
| Gross cost break-even per turnover | about 335.6 bps | about 329.5 bps | Simple cost stress reference, before borrow and impact |
| Mean score gap | 1.3432 | 1.3044 | q=0.20 has slightly wider long/short score separation |
| Score gap vs monthly return corr. | 0.005 | -0.008 | Simple score dispersion is not a useful timing signal |

q=0.20 remains the aggressive return candidate. q=0.30 uses wider baskets and gives up a small amount of mean return in exchange for lower volatility and turnover. Both variants still require transaction cost, borrow, and liquidity testing because turnover is around 0.71.

### 9.2 Annual strength and weakness

| Run | Best years | Weakest years |
|---|---|---|
| q=0.20 stock-score | 2009 +106.73%, 2020 +100.71%, 2001 +76.17%, 2021 +64.93%, 1998 +63.89% | 2014 -4.48%, 2023 +1.49%, 2017 +2.60%, 2019 +4.67%, 2005 +10.81% |
| q=0.30 stock-score | 2009 +101.88%, 2020 +83.26%, 2001 +81.73%, 1998 +67.03%, 2000 +64.98% | 2014 -11.98%, 2017 +2.37%, 2008 +4.41%, 2019 +7.19%, 2007 +7.49% |

The weakest common year is 2014 rather than 2008. The strongest periods include 2009 and 2020, which suggests the strategy may have captured large factor dispersion around regime-transition and rebound windows rather than simply following calm bull markets.

### 9.3 Worst-month attribution

| Run | Month | Return | Turnover | Max factor weight | HHI |
|---|---|---:|---:|---:|---:|
| q=0.20 | 2000-01 | -28.70% | 0.672 | 0.158 | 0.114 |
| q=0.20 | 1999-11 | -14.91% | 0.769 | 0.248 | 0.136 |
| q=0.20 | 2020-02 | -10.77% | 0.729 | 0.173 | 0.105 |
| q=0.20 | 2023-07 | -10.05% | 0.953 | 0.732 | 0.540 |
| q=0.30 | 2000-01 | -25.82% | 0.655 | 0.168 | 0.121 |
| q=0.30 | 1999-11 | -15.07% | 0.772 | 0.240 | 0.137 |
| q=0.30 | 2020-02 | -10.44% | 0.547 | 0.160 | 0.101 |
| q=0.30 | 2003-12 | -9.06% | 0.760 | 0.124 | 0.084 |

January 2000 and November 1999 are the largest common loss months. July 2023 in q=0.20 is different: it combines a large loss with very high factor concentration, max factor weight 0.732 and HHI 0.540. That is a useful case for testing concentration caps or entropy regularization.

### 9.4 Average factor allocation

| Factor | q=0.20 mean weight | q=0.20 max | q=0.30 mean weight | q=0.30 max | Interpretation |
|---|---:|---:|---:|---:|---|
| `reversal_local_ma_gap_1m` | 0.132 | 0.373 | 0.123 | 0.373 | Local reversal axis |
| `reversal_local_price_reversal_1m` | 0.132 | 0.373 | 0.123 | 0.373 | Local reversal axis; overlap audit needed |
| `size_local_small_size` | 0.119 | 0.732 | 0.113 | 0.470 | Size/local alpha axis |
| `quality_global_net_income_yoy` | 0.097 | 0.545 | 0.110 | 0.735 | Quality/profitability axis |
| `val_global_pb_fwd` | 0.080 | 0.333 | 0.078 | 0.300 | Value axis |
| `val_global_relative_pb_industry_fwd` | 0.080 | 0.333 | 0.078 | 0.300 | Industry-relative value axis |
| `quality_local_net_income_yoy` | 0.078 | 0.504 | 0.090 | 0.409 | Local quality axis |
| `earn_global_eps_fast_fy1_1m` | 0.048 | 0.136 | 0.049 | 0.137 | Earnings revision axis |

The allocator leaned most heavily on local reversal, size, quality, and value. The two local reversal factors moved almost identically in average and max weight, which makes factor-overlap and duplicate-exposure review important before promoting the result.

### 9.5 Long/short contribution and concentration

| Item | q=0.20 | q=0.30 | Interpretation |
|---|---:|---:|---|
| Long leg mean forward return | 2.5955% | 2.5580% | Long basket selection is the main source of return |
| Short leg mean forward return | 0.1821% | 0.2067% | The short basket also had positive average forward return |
| Long-short forward spread | 2.41% | 2.35% | Close to the monthly portfolio return |
| High concentration months mean return | 2.47% | 1.22% | Higher factor concentration did not improve returns |
| Low concentration months mean return | 3.01% | 2.28% | More diversified months had higher average returns |
| Avg weight vs holdout correlation corr. | -0.247 | -0.298 | Heavily weighted factors were not necessarily the factors with higher holdout correlation |

The strategy appears to be driven more by long-side selection than by successful short-side collapse. Concentration also looks like a risk rather than a benefit in these aggregates. Follow-up work should test factor caps, entropy penalties, and removal or merging of duplicate reversal signals.

### 9.6 Author interpretation note

The strongest message is not that a single model produced a large return number. The stronger research point is that the DDQM2 chain, factor-return forecasting to dynamic allocation to stock-level QSpread construction, produced an interpretable gross alpha structure in U.S. data. The result should remain a research signal until it survives cost, liquidity, borrow, and capacity tests.
