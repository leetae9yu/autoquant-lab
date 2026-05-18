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

## 8. Conclusion

autoquant-lab shows that the DDQM2 idea can be expressed as a reproducible U.S. equity research harness: factor-return labels, CPU-friendly model forecasts, dynamic factor allocation, and stock-score QSpread portfolios. The strongest current interpretation is not that this is a finished strategy, but that the stock-score QSpread surface and q=0.20/q=0.30 settings are meaningful candidates for deeper robustness testing.

The comparison with DDQM/DDQM2 should be read as a methodological comparison, not a direct return contest. The next step is to net transaction costs and slippage, test ridge/elasticnet under the same selected13 stock-score walk-forward setup, and run regime/year robustness checks.
