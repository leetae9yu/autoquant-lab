# autoquant-lab

[한국어](README_ko.md)

`autoquant-lab` is an offline research harness for adapting the DDQM2 idea to a U.S. equity setting. It builds point-in-time monthly equity panels from local research data, forecasts factor long-short returns from macro/market features, converts predictions into dynamic factor allocations, and evaluates walk-forward out-of-sample portfolios.

This repository is published as a **code and documentation scaffold only**. Raw WRDS-style datasets, credentials, local research notes, generated experiment artifacts, and vendor/reference PDFs are intentionally excluded.

## What this project does

The current harness supports a USA-version DDQM2 research loop:

1. Prepare a monthly `(date, security)` panel from local offline artifacts, without storing public/vendor source data in git.
2. Build feature families with point-in-time lag controls.
3. Compute stock-level factor scores from an EQR factor registry.
4. Convert factor scores into next-month factor long-short returns.
5. Train one CPU-friendly model per factor to forecast factor returns.
6. Convert predicted factor returns into non-negative factor weights.
7. Evaluate both:
   - weighted factor-return portfolios, and
   - DDQM2-style stock-level weighted factor score QSpread portfolios.
8. Record manifests, metrics, reports, and reproducible run metadata locally.

The project is inspired by Samsung Securities DDQM/DDQM2, but it is not a direct reproduction of their Korean-market production setup. It is a U.S. market adaptation with explicit differences in universe, data sources, macro features, factor definitions, and evaluation protocol.

## Current research track

The latest implementation promotes the previously planned USA-DDQM2 axes into executable runs:

- `selected_13_global_local`: DDQM2-inspired 13-factor selection from the available factor registry.
- `ddqm2_25x3_us_macro`: U.S. adaptation of the DDQM2 macro design with current, short-direction, and medium-direction style features where available.
- `expanded_us_macro`: an open macro expansion axis for additional U.S. market/macro variables supported by local artifacts.
- `stock_score_qspread_ddqm2`: stock-level weighted factor score QSpread portfolio surface.

Quantile `q` is intentionally left as a research axis:

- q=0.10 is the DDQM2-reference decile construction.
- q=0.20 and q=0.30 are U.S. adaptation settings for wider, more diversified legs.

See the final DDQM2 matrix reports:

- [Korean report](reports/usa_ddqm2_matrix_report_ko.md)
- [English report](reports/usa_ddqm2_matrix_report_en.md)

Latest additive long-only QSpread analysis:

- [English analysis report](reports/long_only_qspread_ml_costs_full_chunked_analysis_en.md)
- [Korean translation](reports/long_only_qspread_ml_costs_full_chunked_analysis_ko.md)
- [Reproducibility ledger](reports/long_only_qspread_ml_costs_full_chunked_ledger.json)

## Walk-forward timing and rebalancing

The portfolio surface is monthly. Each `formation_date` represents one monthly rebalance date, and labels use `ret_1m_fwd`, the next-month forward return.

In the default full-run configuration:

- portfolio weights are recomputed every month;
- the long/short stock baskets are rebuilt every month;
- each monthly portfolio is evaluated on the next one-month return;
- the forecasting model is refit once per 12-month walk-forward test fold.

For example, if a fold tests `2023-01` through `2023-12`, the model is fit only on dates before that test block, with the immediately preceding validation block kept out of training. It does **not** train on 2023 labels and then predict 2023.

The default setup is therefore:

```text
monthly portfolio rebalance
+ 1-month holding horizon
+ 12-month model refit cadence
```

For a stricter monthly-refit experiment, set the test fold to one month:

```bash
PYTHONPATH=src:. python scripts/eqr_run_ddqm2.py \
  --config configs/server_full.yaml \
  --evaluation-mode walk_forward \
  --walk-forward-test-periods 1 \
  --walk-forward-validation-periods 0
```

## Repository layout

```text
configs/                     Safe YAML configs and ablation plans
scripts/                     CLI entrypoints for preparation, validation, DDQM2 runs, and planning
src/autoquant_lab/eqr/       Main EQR package code
src/autoquant_lab/eqr/factors/DDQM2-style factor scoring, selection, allocation, and backtests
tests/                       Focused tests for config, panel, factors, models, and reporting
reports/                     Source-controlled final report only; generated local reports remain ignored
```

Runtime and private directories are ignored:

```text
data/                        raw/local research data, including WRDS/FRED-style exports, never committed
experiments/                 generated prepared panels and run artifacts
site/                        generated static reports
.env                         credentials/local settings
*.pdf, *.xlsx                local reference/data files
```

## What is intentionally not included

This repository does **not** include:

- WRDS/CRSP/Compustat/IBES data
- FRED/macro source exports or vendor macro files
- `.env` files or credentials
- private research notes such as `EQR.md`
- DDQM/DDQM2 PDF references
- generated parquet experiment artifacts
- generated static site output

Those files are required only in the private local/server environment and are excluded by `.gitignore`.

## Main CLI examples

Render runnable DDQM2 ablation commands without executing them:

```bash
PYTHONPATH=src:. python scripts/eqr_plan_ddqm2_ablations.py --format commands --limit 8
```

Run a DDQM2-style experiment from already-prepared local artifacts:

```bash
PYTHONPATH=src:. python scripts/eqr_run_ddqm2.py \
  --config configs/server_full.yaml \
  --run-id example_usa_ddqm2_q20 \
  --quantile 0.20 \
  --model lightgbm \
  --factor-universe selected_13_global_local \
  --macro-feature-design ddqm2_25x3_us_macro \
  --portfolio-surface stock_score_qspread_ddqm2 \
  --evaluation-mode walk_forward \
  --min-weight 0.03
```

Run the additive long-only QSpread matrix from already-prepared local chunked artifacts:

```bash
PYTHONPATH=src:. python scripts/eqr_run_long_only_matrix.py \
  --feature-dir experiments/prepared/features_full_chunked \
  --run-prefix longonly_full_chunked_YYYYMMDD \
  --output-dir experiments/ddqm2_long_only_full_chunked \
  --report reports/long_only_qspread_ml_costs_full_chunked_report.md \
  --ledger reports/long_only_qspread_ml_costs_full_chunked_ledger.json
```

Run focused tests:

```bash
PYTHONPATH=src:. python -m pytest tests/test_ddqm2_ablation_plan.py tests/test_factors.py -q
```

## Research status

The repository now has two source-controlled report families:

1. **Existing USA-DDQM2 long/short matrix**
   - q=0.10, q=0.20, and q=0.30 DDQM2-style stock-score QSpread runs.
   - Model sweeps covering LightGBM, ridge, elasticnet, random forest, extra trees, and baseline mean.
   - Reports: [`usa_ddqm2_matrix_report_en.md`](reports/usa_ddqm2_matrix_report_en.md), [`usa_ddqm2_matrix_report_ko.md`](reports/usa_ddqm2_matrix_report_ko.md).
2. **Additive long-only QSpread cost/tax matrix**
   - Full local chunked panel: 2,082,485 rows, 159 features, 35 feature partitions.
   - 18 successful runs: six model families across q=0.10, q=0.20, and q=0.30.
   - Long-only top-q equal-weight fully invested construction; no new short optimization.
   - Conservative primary net lens: 50 bps one-way turnover cost and a 40.8% simplified tax-drag proxy on positive monthly gains realized by turnover.
   - Reports: [`long_only_qspread_ml_costs_full_chunked_analysis_en.md`](reports/long_only_qspread_ml_costs_full_chunked_analysis_en.md), [`long_only_qspread_ml_costs_full_chunked_analysis_ko.md`](reports/long_only_qspread_ml_costs_full_chunked_analysis_ko.md).

Headline interpretation from the latest long-only report:

- q=0.30 is the strongest net-cost surface for every tested model family.
- The baseline-mean q=0.30 run has the highest primary net cumulative return, mostly because the conservative net lens strongly rewards lower turnover and stable factor exposure.
- Extra Trees and Random Forest are the strongest non-baseline ML runs at q=0.30; LightGBM has strong gross performance but higher turnover drag.
- The key research result is the gap between gross and conservative net outcomes, not the gross headline alone.

These are research backtests. They do not fully model slippage, market impact, capacity, tax-lot accounting, borrow constraints, or production tradability. The tax proxy is not tax advice.

## Verification

Recent checks used during the long-only QSpread completion:

```text
PYTHONPATH=src:. .venv/bin/python -m pytest -q
153 passed, 54 warnings

Full long-only matrix
18 runs, 0 failures
Data boundary: local artifacts only; no WRDS login; no runtime external data
```

The runner uses partitioned feature preparation and chunked factor-score generation to avoid rematerializing very large score tables during full-data runs.

## Safety and publication policy

Before publishing, verify that no private data is tracked:

```bash
git ls-files data experiments site .env EQR.md '*.pdf' '*.xlsx'
```

The expected output should be empty except for explicitly safe placeholders, if any.

## License / use

This is a research scaffold. It is not investment advice and not a deployable trading strategy.
