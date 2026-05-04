# DDQM2-lite MVP: WRDS-Ready Public-Data Factor Pipeline

## TL;DR
> **Summary**: Build a WRDS-free DDQM2-lite MVP using FRED/ALFRED macro features and yfinance price/volume data, while enforcing canonical schemas that future CRSP/Compustat/IBES adapters can reuse. The MVP produces wide price/volume factor scores, factor long-short labels, macro-factor model data, LightGBM experiment artifacts, and a read-only Streamlit dashboard.
> **Deliverables**:
> - Canonical yfinance price/return panel with WRDS-ready identifiers and provenance flags
> - Wide public-data price/volume factor score artifact
> - Factor long-short return labels with leakage checks
> - Macro-factor model-ready artifact using as-of macro joins
> - LightGBM baseline + small grid option + naive baseline comparison
> - Autoresearch-inspired experiment artifacts and ledger
> - Read-only Streamlit dashboard for metrics, factor returns, feature importance, and data coverage
> - README/docs smoke commands and prototype caveats
> **Effort**: Large
> **Parallel**: YES - 4 waves
> **Critical Path**: Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7

## Context

### Original Request
- Plan a DDQM2-lite MVP before WRDS access is available.
- Use FRED/ALFRED + yfinance as the MVP data sources.
- Do not make the MVP artificially tiny; imitate DDQM2 structure as much as public data allows.
- Consider Karpathy `autoresearch`, but only if it fits.
- Add Streamlit visualizations for model performance tables and charts.
- Ensure later WRDS expansion can preserve the factor/label/model/dashboard logic as much as possible.

### Interview Summary
- MVP v1 uses **FRED/ALFRED** for macro features and **yfinance** for temporary price/volume/equity return data.
- WRDS is not part of MVP implementation, but the design must be WRDS-ready via canonical schemas and source adapters.
- yfinance outputs remain `prototype_only=True`; future WRDS outputs become `prototype_only=False` after validation.
- DDQM2-lite label target is **factor long-short return**, not individual stock forward return.
- Karpathy `autoresearch` is **conceptually reused** as an operating model: frozen prep/eval, constrained mutable experiment surface, metric ledger. Its LLM/CUDA code is not integrated.
- Streamlit is a read-only dashboard over artifacts; it must not download data, rebuild labels, retrain models, or mutate outputs.

### Metis Review (gaps addressed)
- Added fixed defaults for rebalance frequency, portfolio construction, minimum basket sizes, factor direction metadata, label horizon, model unit, macro as-of join, and dashboard boundaries.
- Added leakage guardrails: `formation_date`, `forward_return_start`, `forward_return_end`, time split only, and embargo around label horizon.
- Added canonical artifact paths and validator-first smoke commands.
- Added directive that MVP is factor-label plumbing, not final DDQM2 replication or alpha-quality research output.
- Added explicit no-random-split policy and no-dashboard-recomputation policy.

## Work Objectives

### Core Objective
Create a public-data DDQM2-lite pipeline that validates the DDQM-style structure `macro state → factor long-short return prediction`, while preserving a clean path to future WRDS adapters.

### Deliverables
- `scripts/build_yfinance_price_panel.py`
- `scripts/validate_yfinance_price_panel.py`
- `scripts/build_yfinance_factor_scores.py`
- `scripts/validate_factor_scores.py`
- `scripts/build_factor_long_short_returns.py`
- `scripts/validate_factor_long_short_returns.py`
- `scripts/assemble_macro_factor_dataset.py`
- `scripts/validate_macro_factor_dataset.py`
- `scripts/train_macro_factor_lgbm_baseline.py`
- `scripts/validate_macro_factor_experiment.py`
- `apps/ddqm2_lite_dashboard.py`
- README/docs updates with smoke commands, artifact contracts, and caveats

### Definition of Done (verifiable conditions with commands)
- Secret scan passes: `python scripts/scan_secrets.py`
- Smoke price panel builds and validates.
- Smoke factor scores build and validate.
- Smoke factor long-short labels build and validate.
- Smoke macro-factor dataset assembles and validates.
- Smoke LightGBM experiment runs and validates.
- Streamlit app imports and displays missing-artifact instructions without crashing.
- Generated prototype outputs are under `prototypes/yfinance_sp500/` and are not committed.

### Must Have
- Canonical schema boundaries between source-specific adapters and downstream factor/model/dashboard logic.
- `source`, `prototype_only`, and `asset_id_type` retained in major artifacts.
- Time-based or rolling validation only; no random train/validation split.
- As-of macro join using latest macro row on or before `formation_date`.
- Date-local factor ranking/winsorization; no future cross-sectional leakage.
- Equal-weight top/bottom quintile long-short labels by default.
- Full-run default minimum basket size `25`; smoke mode minimum basket size `2`.
- LightGBM and naive baseline metrics persisted to artifacts.
- Dashboard reads artifacts only.

### Must NOT Have
- No WRDS/CRSP/Compustat/IBES access or loaders in this MVP.
- No public fundamentals/analyst proxies in MVP v1.
- No yfinance raw columns leaking into final model-ready artifact except provenance fields.
- No claims that prototype results are research-grade, survivorship-bias-free, or tradable.
- No direct import, clone, or integration of Karpathy `autoresearch` code.
- No mutation of generated experiment artifacts from Streamlit.

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: validator-first / smoke-command-first; no pytest framework exists in repo.
- QA policy: Every task has agent-executed scenarios.
- Evidence: `.sisyphus/evidence/task-{N}-{slug}.{ext}`
- Required common checks:
  - `python scripts/scan_secrets.py`
  - Relevant `validate_*` scripts exit `0` on valid artifacts and nonzero on schema failures.
  - Smoke commands use small ticker lists and short date windows for speed.

## Execution Strategy

### Parallel Execution Waves
> Target: 5-8 tasks per wave. This plan has dependency-heavy data layers; later waves parallelize docs/dashboard after artifact contracts exist.

Wave 1: Task 1 canonical contracts and shared IO helpers.
Wave 2: Tasks 2-4 data/factor/label builders and validators.
Wave 3: Tasks 5-6 model-ready assembly and LightGBM experiment runner.
Wave 4: Tasks 7-8 dashboard and documentation.

### Dependency Matrix (full, all tasks)
| Task | Blocks | Blocked By |
|---|---|---|
| 1. Canonical contracts | 2,3,4,5,6,7,8 | none |
| 2. yfinance canonical price panel | 3,4 | 1 |
| 3. factor score builder | 4 | 1,2 |
| 4. long-short label builder | 5 | 1,2,3 |
| 5. macro-factor assembler | 6,7 | 1,4 |
| 6. LightGBM experiment runner | 7,8 | 1,5 |
| 7. Streamlit dashboard | 8 | 1,5,6 |
| 8. README/docs | final verification | 1,6,7 |

### Agent Dispatch Summary (wave → task count → categories)
| Wave | Task count | Recommended categories |
|---|---:|---|
| 1 | 1 | deep |
| 2 | 3 | deep, quick |
| 3 | 2 | deep |
| 4 | 2 | visual-engineering, writing |

## TODOs
> Implementation + Test = ONE task. Never separate.
> EVERY task MUST have: Agent Profile + Parallelization + QA Scenarios.

- [ ] 1. Define canonical schemas and shared prototype IO helpers

  **What to do**: Add a small schema/helper layer under `src/autoquant_lab/` for canonical column constants, required-column validation, CSV/Parquet IO, prototype flag checks, duplicate-key checks, and deterministic summary helpers. The canonical contracts must cover price panel, factor scores, factor long-short labels, macro-factor model data, and experiment artifacts. Include nullable future WRDS columns (`permno`, `permco`, `gvkey`) in schemas even when MVP values are null.
  **Must NOT do**: Do not add WRDS loaders. Do not add a database dependency. Do not move existing scripts.

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: establishes downstream contracts and migration boundaries.
  - Skills: [] - No specialized skill needed.
  - Omitted: [`git-master`] - Commit is handled outside implementation unless explicitly requested.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 2,3,4,5,6,7,8 | Blocked By: none

  **References**:
  - Pattern: `scripts/build_yfinance_sp500_labels.py:221-228` - existing CSV/Parquet write convention.
  - Pattern: `scripts/assemble_yfinance_macro_dataset.py` - existing macro prefix/provenance convention from exploration.
  - Pattern: `scripts/validate_yfinance_macro_dataset.py` - existing validator style for required columns, macro columns, and provenance.
  - Pattern: `src/autoquant_lab/config.py` - current project module style and import root.
  - Docs: `README.md` - current implementation roadmap and caveats.

  **Acceptance Criteria**:
  - [ ] `python scripts/scan_secrets.py` exits `0`.
  - [ ] A Python one-liner can import the new schema/helper module: `PYTHONPATH=src python -c "import autoquant_lab; import autoquant_lab.schemas"`.
  - [ ] Schema constants include required columns for price panel, factor scores, factor labels, macro-factor model data, and experiment manifest.
  - [ ] Helper validation raises nonzero/exception on missing required columns and duplicate key rows.

  **QA Scenarios**:
  ```
  Scenario: Import and validate a minimal valid schema frame
    Tool: Bash
    Steps: Run `PYTHONPATH=src python - <<'PY'
import pandas as pd
from autoquant_lab import schemas
df = pd.DataFrame([{c: None for c in schemas.PRICE_PANEL_REQUIRED_COLUMNS}])
print(sorted(schemas.PRICE_PANEL_REQUIRED_COLUMNS))
PY`
    Expected: Command exits 0 and prints required price panel columns including date, asset_id, asset_id_type, source, prototype_only.
    Evidence: .sisyphus/evidence/task-1-schemas-import.txt

  Scenario: Missing required column fails
    Tool: Bash
    Steps: Run a helper validation on a frame missing `date`.
    Expected: Command exits nonzero or prints a deterministic missing-column error containing `date`.
    Evidence: .sisyphus/evidence/task-1-schemas-missing-column.txt
  ```

  **Commit**: YES | Message: `feat: add canonical artifact schemas` | Files: `src/autoquant_lab/*`

- [ ] 2. Build and validate canonical yfinance price panel

  **What to do**: Add `scripts/build_yfinance_price_panel.py` and `scripts/validate_yfinance_price_panel.py`. Reuse current yfinance universe/download logic where practical, but emit canonical price/return schema rather than stock-level label schema. Required output default: `prototypes/yfinance_sp500/canonical_price_panel.parquet`. Include `asset_id=ticker`, `asset_id_type='ticker'`, nullable `permno/permco/gvkey`, `price_adjusted`, `close`, `volume`, `return_1d`, `delisting_return=None`, `total_return=return_1d`, `source='yfinance'`, `prototype_only=True`, universe metadata, and generated timestamp. Support `--tickers` for deterministic smoke runs and `--universe-csv`/Wikipedia for full runs.
  **Must NOT do**: Do not emit model labels here. Do not add factor calculations here. Do not rely on exact current S&P membership for research claims.

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: adapts existing data builder into canonical WRDS-ready artifact.
  - Skills: [] - No specialized skill needed.
  - Omitted: [`recipe-apply-autoresearch-pipeline`] - external repo already assessed; no direct integration.

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: 3,4 | Blocked By: 1

  **References**:
  - Pattern: `scripts/build_yfinance_sp500_labels.py:77-108` - universe loading and ticker normalization.
  - Pattern: `scripts/build_yfinance_sp500_labels.py:136-188` - chunked yfinance download and failure handling.
  - Pattern: `scripts/build_yfinance_sp500_labels.py:191-204` - price frame normalization.
  - Pattern: `scripts/build_yfinance_sp500_labels.py:232-237` - failed ticker sidecar file convention.
  - Test: `scripts/validate_yfinance_sp500_labels.py` - validator CLI/summary pattern.

  **Acceptance Criteria**:
  - [ ] Smoke build command exits `0`: `PYTHONPATH=src python scripts/build_yfinance_price_panel.py --tickers AAPL MSFT SPY --start-date 2020-01-01 --end-date 2020-06-30 --output prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet`.
  - [ ] Validator exits `0`: `PYTHONPATH=src python scripts/validate_yfinance_price_panel.py prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet`.
  - [ ] Output has no duplicate `(date, asset_id)` rows.
  - [ ] All rows have `prototype_only=True`, `source='yfinance'`, and `asset_id_type='ticker'`.
  - [ ] `return_1d` and `total_return` are finite for rows after each asset's first valid price observation.

  **QA Scenarios**:
  ```
  Scenario: Build smoke canonical price panel
    Tool: Bash
    Steps: Run the smoke build and validator commands above.
    Expected: Both commands exit 0; validator summary reports 3 assets, date range, and prototype-only row count equal to total rows.
    Evidence: .sisyphus/evidence/task-2-price-panel-smoke.txt

  Scenario: Validator rejects duplicate key rows
    Tool: Bash
    Steps: Create a temporary copied parquet/csv with a duplicated first row, then run validator on that temp file.
    Expected: Validator exits nonzero and error mentions duplicate `(date, asset_id)`.
    Evidence: .sisyphus/evidence/task-2-price-panel-duplicate.txt
  ```

  **Commit**: YES | Message: `feat: add yfinance canonical price panel` | Files: `scripts/build_yfinance_price_panel.py`, `scripts/validate_yfinance_price_panel.py`, `src/autoquant_lab/*`

- [ ] 3. Build and validate wide price/volume factor scores

  **What to do**: Add `scripts/build_yfinance_factor_scores.py` and `scripts/validate_factor_scores.py`. Input canonical price panel, compute date-local factor scores for the wide public-data factor zoo, and emit `prototypes/yfinance_sp500/factor_scores.parquet`. Required factors: `mom_1m`, `mom_3m`, `mom_6m`, `mom_12m`, `rev_1w`, `rev_1m`, `vol_1m`, `vol_3m`, `vol_6m`, `max_dd_1m`, `max_dd_3m`, `max_dd_6m`, `dollar_volume_1m`, `volume_z_1m`, `amihud_illiq_1m`, `beta_spy_6m`, `corr_spy_6m`. Add `vix_sensitivity_6m` only if VIX/market proxy data is present in the input or explicitly supplied; otherwise skip with metadata, not failure. Include factor metadata columns: `factor_family`, `lookback_days`, `direction`, `source_columns`, `rank_method`, `winsorization_method`, `source`, `prototype_only`.
  **Must NOT do**: Do not use future returns in factor values. Do not calculate factor rankings across all dates. Do not add public fundamentals.

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: factor math and leakage constraints require careful implementation.
  - Skills: [] - No specialized skill needed.
  - Omitted: [`frontend-ui-ux`] - no UI work in this task.

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: 4 | Blocked By: 1,2

  **References**:
  - API/Type: canonical price panel schema from Task 1.
  - Pattern: `scripts/validate_yfinance_macro_dataset.py` - deterministic validation summary pattern.
  - Pattern: `scripts/build_yfinance_sp500_labels.py:207-218` - grouped per-asset time series transformation style.
  - External concept: Karpathy `autoresearch` frozen metric pattern; keep factor definitions frozen after implementation.

  **Acceptance Criteria**:
  - [ ] Smoke factor build exits `0`: `PYTHONPATH=src python scripts/build_yfinance_factor_scores.py --price-panel prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet --output prototypes/yfinance_sp500/factor_scores_smoke.parquet --smoke`.
  - [ ] Validator exits `0`: `PYTHONPATH=src python scripts/validate_factor_scores.py prototypes/yfinance_sp500/factor_scores_smoke.parquet --smoke`.
  - [ ] Unique key is `(date, asset_id, factor_name)`.
  - [ ] Factor values are finite after each factor's lookback coverage requirement.
  - [ ] Every row has `prototype_only=True`, `source`, `factor_family`, `lookback_days`, and `direction`.
  - [ ] Validator prints coverage by factor and date range.

  **QA Scenarios**:
  ```
  Scenario: Build wide factor scores from smoke panel
    Tool: Bash
    Steps: Run the factor build and validator commands above.
    Expected: Commands exit 0; validator lists at least momentum, reversal, volatility, drawdown, liquidity, and market sensitivity factor families.
    Evidence: .sisyphus/evidence/task-3-factor-scores-smoke.txt

  Scenario: Validator catches non-finite factor value
    Tool: Bash
    Steps: Copy smoke factor scores to temp CSV, set one `factor_value` to `inf` or blank for a covered row, run validator.
    Expected: Validator exits nonzero and identifies non-finite factor values.
    Evidence: .sisyphus/evidence/task-3-factor-scores-nonfinite.txt
  ```

  **Commit**: YES | Message: `feat: add yfinance factor score builder` | Files: `scripts/build_yfinance_factor_scores.py`, `scripts/validate_factor_scores.py`, `src/autoquant_lab/*`

- [ ] 4. Build and validate factor long-short return labels

  **What to do**: Add `scripts/build_factor_long_short_returns.py` and `scripts/validate_factor_long_short_returns.py`. Use factor scores and canonical price panel to form equal-weight long/short baskets by factor on monthly formation dates. Default: last available trading day per calendar month, horizon `21` trading days, top/bottom quintile, `min_basket_size=25`, `--smoke` minimum basket size `2`. Output `prototypes/yfinance_sp500/factor_long_short_returns.parquet`. Include `formation_date`, `factor_name`, `horizon_trading_days`, `long_quantile`, `short_quantile`, `long_count`, `short_count`, `long_return`, `short_return`, `long_short_return`, `forward_return_start`, `forward_return_end`, `return_source`, `prototype_only`.
  **Must NOT do**: Do not use same-period returns. Do not allow `forward_return_start <= formation_date`. Do not silently create baskets below min size except in explicit `--smoke` mode.

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: label construction is the core DDQM-style target and must avoid leakage.
  - Skills: [] - No specialized skill needed.
  - Omitted: [`visual-engineering`] - no UI work in this task.

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: 5 | Blocked By: 1,2,3

  **References**:
  - API/Type: canonical factor score and price panel schemas from Tasks 1-3.
  - Pattern: `scripts/build_yfinance_sp500_labels.py:207-218` - forward return horizon concept; replace stock-level label with factor portfolio label.
  - Docs: `docs/crsp_requirements.md:22-39` - forward return label concepts and future CRSP `dlret` migration note.

  **Acceptance Criteria**:
  - [ ] Smoke label build exits `0`: `PYTHONPATH=src python scripts/build_factor_long_short_returns.py --factor-scores prototypes/yfinance_sp500/factor_scores_smoke.parquet --price-panel prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet --output prototypes/yfinance_sp500/factor_long_short_returns_smoke.parquet --horizon-trading-days 21 --smoke`.
  - [ ] Validator exits `0`: `PYTHONPATH=src python scripts/validate_factor_long_short_returns.py prototypes/yfinance_sp500/factor_long_short_returns_smoke.parquet --smoke`.
  - [ ] Unique key is `(formation_date, factor_name, horizon_trading_days)`.
  - [ ] Every `forward_return_start` is strictly after `formation_date`.
  - [ ] `long_short_return = long_return - short_return` within floating tolerance.
  - [ ] Validator reports basket counts and skipped factor/date combinations.

  **QA Scenarios**:
  ```
  Scenario: Build monthly factor long-short labels
    Tool: Bash
    Steps: Run the smoke long-short build and validator commands above.
    Expected: Commands exit 0; output includes multiple `factor_name` values and strictly future return windows.
    Evidence: .sisyphus/evidence/task-4-long-short-smoke.txt

  Scenario: Validator catches leakage window
    Tool: Bash
    Steps: Modify a temp copy so `forward_return_start == formation_date`, then run validator.
    Expected: Validator exits nonzero and reports leakage/date-order failure.
    Evidence: .sisyphus/evidence/task-4-long-short-leakage.txt
  ```

  **Commit**: YES | Message: `feat: add factor long-short labels` | Files: `scripts/build_factor_long_short_returns.py`, `scripts/validate_factor_long_short_returns.py`, `src/autoquant_lab/*`

- [ ] 5. Assemble and validate macro-factor model-ready dataset

  **What to do**: Add `scripts/assemble_macro_factor_dataset.py` and `scripts/validate_macro_factor_dataset.py`. Join `factor_long_short_returns` to `expanded_macro_market_features.xlsx` using as-of join: latest macro date on or before `formation_date`. Prefix macro columns as `macro__`. Output `prototypes/yfinance_sp500/macro_factor_model_ready.parquet`. Required columns: `formation_date`, `factor_name`, `horizon_trading_days`, `target_long_short_return`, `macro__*`, `label_source`, `macro_source`, `prototype_only`. Preserve factor metadata needed for modeling, but do not leak raw yfinance staging fields.
  **Must NOT do**: Do not exact-date-only join if macro feature date is prior business day. Do not include `asset_id`, ticker-level fields, or basket constituents in model-ready rows.

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: model data contract and as-of join are critical for WRDS reuse.
  - Skills: [] - No specialized skill needed.
  - Omitted: [`frontend-ui-ux`] - no UI work in this task.

  **Parallelization**: Can Parallel: NO | Wave 3 | Blocks: 6,7 | Blocked By: 1,4

  **References**:
  - Pattern: `scripts/assemble_yfinance_macro_dataset.py:51-63` - macro workbook read, date index normalization, `macro__` prefix.
  - Pattern: `scripts/assemble_yfinance_macro_dataset.py:89-103` - join/provenance pattern.
  - Test: `scripts/validate_yfinance_macro_dataset.py:53-64` - required provenance and macro column checks.
  - Data: `expanded_macro_market_features.xlsx` - existing macro workbook used by current prototype.

  **Acceptance Criteria**:
  - [ ] Smoke assemble exits `0`: `PYTHONPATH=src python scripts/assemble_macro_factor_dataset.py --factor-returns prototypes/yfinance_sp500/factor_long_short_returns_smoke.parquet --macro-workbook expanded_macro_market_features.xlsx --output prototypes/yfinance_sp500/macro_factor_model_ready_smoke.parquet`.
  - [ ] Validator exits `0`: `PYTHONPATH=src python scripts/validate_macro_factor_dataset.py prototypes/yfinance_sp500/macro_factor_model_ready_smoke.parquet`.
  - [ ] Unique key is `(formation_date, factor_name, horizon_trading_days)`.
  - [ ] At least one `macro__*` column exists and no macro feature rows are missing after as-of join.
  - [ ] `target_long_short_return` equals source `long_short_return`.
  - [ ] No ticker/asset-level staging columns are present in final model-ready artifact.

  **QA Scenarios**:
  ```
  Scenario: Assemble macro-factor model-ready dataset
    Tool: Bash
    Steps: Run smoke assemble and validator commands above.
    Expected: Commands exit 0; validator reports macro feature count, factor count, date range, and prototype-only row count.
    Evidence: .sisyphus/evidence/task-5-macro-factor-smoke.txt

  Scenario: Validator catches missing macro columns
    Tool: Bash
    Steps: Write temp copy with all `macro__*` columns removed, run validator.
    Expected: Validator exits nonzero and reports no macro feature columns.
    Evidence: .sisyphus/evidence/task-5-macro-factor-no-macro.txt
  ```

  **Commit**: YES | Message: `feat: assemble macro factor dataset` | Files: `scripts/assemble_macro_factor_dataset.py`, `scripts/validate_macro_factor_dataset.py`, `src/autoquant_lab/*`

- [ ] 6. Add LightGBM macro-factor experiment runner and validators

  **What to do**: Add `scripts/train_macro_factor_lgbm_baseline.py` and `scripts/validate_macro_factor_experiment.py`. Train pooled LightGBM model on macro-factor rows using time holdout or rolling split only. Encode `factor_name` deterministically as categorical/one-hot. Default fixed params: `learning_rate=0.05`, `num_leaves=31`, `n_estimators=500`, `early_stopping_rounds=50`, `seed=42`. Add optional small grid search over `learning_rate`, `num_leaves`, `min_child_samples`, `feature_fraction`, and `bagging_fraction`. Persist artifacts under `prototypes/yfinance_sp500/experiments/<run_id>/`: `config.json`, `metrics.json`, `predictions.parquet`, `feature_importance.csv`, `manifest.json`, `run.log` if available. Metrics must include LightGBM and naive baselines: `zero_return`, `train_mean_return`, and `last_factor_return` when computable.
  **Must NOT do**: Do not use random split. Do not tune on validation and claim final performance. Do not omit baseline comparison. Do not write artifacts outside experiment output dir.

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: model training, rolling/time split, artifacts, and validation gates are central.
  - Skills: [] - No specialized skill needed.
  - Omitted: [`recipe-apply-autoresearch-pipeline`] - use concept only, no direct code.

  **Parallelization**: Can Parallel: NO | Wave 3 | Blocks: 7,8 | Blocked By: 1,5

  **References**:
  - Pattern: `scripts/train_yfinance_macro_lgbm_baseline.py:23-37` - existing CLI params.
  - Pattern: `scripts/train_yfinance_macro_lgbm_baseline.py:90-115` - time holdout split.
  - Pattern: `scripts/train_yfinance_macro_lgbm_baseline.py:118-150` - metrics and naive baselines.
  - Pattern: `scripts/train_yfinance_macro_lgbm_baseline.py:167-186` - LightGBM regressor and early stopping.
  - External concept: Karpathy `autoresearch` `results.tsv`/metric ledger pattern, adapted to quant artifacts.

  **Acceptance Criteria**:
  - [ ] Smoke train exits `0`: `PYTHONPATH=src python scripts/train_macro_factor_lgbm_baseline.py --input prototypes/yfinance_sp500/macro_factor_model_ready_smoke.parquet --output-dir prototypes/yfinance_sp500/experiments/smoke_lgbm --smoke`.
  - [ ] Experiment validator exits `0`: `PYTHONPATH=src python scripts/validate_macro_factor_experiment.py prototypes/yfinance_sp500/experiments/smoke_lgbm`.
  - [ ] Output dir contains `config.json`, `metrics.json`, `predictions.parquet`, `feature_importance.csv`, and `manifest.json`.
  - [ ] `metrics.json` contains LightGBM metrics and naive baseline metrics.
  - [ ] Manifest contains train/validation date ranges, split method, input artifact path, run id, git commit if available, and prototype warning.
  - [ ] Validation start date is after train max date, with embargo if configured.

  **QA Scenarios**:
  ```
  Scenario: Train smoke macro-factor LightGBM experiment
    Tool: Bash
    Steps: Run smoke train and experiment validator commands above.
    Expected: Commands exit 0; metrics include RMSE, MAE, R2, Pearson IC, and baseline metrics.
    Evidence: .sisyphus/evidence/task-6-lgbm-smoke.txt

  Scenario: Validator catches missing metrics artifact
    Tool: Bash
    Steps: Copy experiment dir to temp, remove `metrics.json`, run validator.
    Expected: Validator exits nonzero and reports missing metrics artifact.
    Evidence: .sisyphus/evidence/task-6-lgbm-missing-metrics.txt
  ```

  **Commit**: YES | Message: `feat: train macro factor LightGBM baseline` | Files: `scripts/train_macro_factor_lgbm_baseline.py`, `scripts/validate_macro_factor_experiment.py`, `src/autoquant_lab/*`

- [ ] 7. Add read-only Streamlit dashboard for DDQM2-lite artifacts

  **What to do**: Add `apps/ddqm2_lite_dashboard.py` and update dependencies if `streamlit`/plotting libraries are absent. Dashboard reads existing artifacts only. Required views: overview/prototype warning, run summary table, LightGBM vs naive baseline table, RMSE/MAE/R2/IC charts, factor-level metric breakdown, long-short return time series and cumulative return, predicted-vs-actual scatter, residual distribution, feature importance chart, and data coverage/missingness/basket count table. It must fail gracefully with clear instructions when artifacts are missing.
  **Must NOT do**: Do not trigger downloads, rebuild datasets, retrain models, mutate experiment files, or present results as research-grade.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: dashboard layout, readable tables/charts, and user-facing warning design.
  - Skills: [`frontend-ui-ux`] - Useful for clear visualization and dashboard hierarchy.
  - Omitted: [`dev-browser`] - only needed if user requests browser verification beyond CLI import/smoke.

  **Parallelization**: Can Parallel: YES | Wave 4 | Blocks: 8 | Blocked By: 1,5,6

  **References**:
  - Artifact contracts from Task 6.
  - README caveats: `README.md` - prototype-only and WRDS limitations.
  - Pattern: existing scripts print warnings; dashboard must display persistent warning.

  **Acceptance Criteria**:
  - [ ] Import check exits `0`: `PYTHONPATH=src python -c "import apps.ddqm2_lite_dashboard"`.
  - [ ] Streamlit smoke command starts without import errors: `PYTHONPATH=src streamlit run apps/ddqm2_lite_dashboard.py --server.headless true --server.port 8501` run with timeout/capture.
  - [ ] Missing artifact state displays instructions and does not raise uncaught exception.
  - [ ] When smoke artifacts exist, dashboard can read metrics, predictions, feature importance, and factor returns.
  - [ ] Dashboard source contains no calls to training/build scripts or write methods for experiment artifacts.

  **QA Scenarios**:
  ```
  Scenario: Dashboard imports with no artifacts
    Tool: Bash
    Steps: Run `PYTHONPATH=src python -c "import apps.ddqm2_lite_dashboard"`.
    Expected: Command exits 0 with no artifact access side effects.
    Evidence: .sisyphus/evidence/task-7-dashboard-import.txt

  Scenario: Dashboard starts headless against smoke artifacts
    Tool: Bash
    Steps: Run Streamlit headless command with a bounded timeout after Task 6 smoke artifacts exist.
    Expected: Process starts without import/runtime error; captured output includes local URL or Streamlit startup line.
    Evidence: .sisyphus/evidence/task-7-dashboard-headless.txt
  ```

  **Commit**: YES | Message: `feat: add DDQM2-lite dashboard` | Files: `apps/ddqm2_lite_dashboard.py`, `requirements.txt`, `README.md` if command docs needed

- [ ] 8. Update README/docs with MVP workflow, caveats, and WRDS expansion path

  **What to do**: Update README in English and Korean with public-facing DDQM2-lite MVP workflow. Include source roles: FRED/ALFRED = macro, yfinance = MVP price/volume, future WRDS CRSP/Compustat/IBES = research-grade expansion. Document canonical artifacts, smoke commands, validation commands, experiment artifact structure, Streamlit command, prototype-only caveats, and WRDS expansion phases. Keep tone public and avoid internal-study wording.
  **Must NOT do**: Do not claim prototype results prove performance. Do not document generated files as committed artifacts. Do not remove existing WRDS readiness docs.

  **Recommended Agent Profile**:
  - Category: `writing` - Reason: bilingual technical documentation and public-facing caveats.
  - Skills: [] - No specialized skill needed.
  - Omitted: [`git-master`] - commit handled outside implementation unless requested.

  **Parallelization**: Can Parallel: YES | Wave 4 | Blocks: final verification | Blocked By: 1,6,7

  **References**:
  - Pattern: `README.md` - existing bilingual README structure and language switch links.
  - Docs: `docs/ddqm2_sp500_data_inventory.md` - WRDS source chain and fallback separation.
  - Docs: `docs/crsp_requirements.md`, `docs/compustat_requirements.md`, `docs/ibes_requirements.md` - future expansion references.
  - Tool: `scripts/scan_secrets.py` - safety check documented in README.

  **Acceptance Criteria**:
  - [ ] README contains English and Korean sections for DDQM2-lite MVP workflow.
  - [ ] README includes smoke commands for all new builder/validator/trainer/dashboard entrypoints.
  - [ ] README explicitly states yfinance outputs are `prototype_only=True` and not research-grade.
  - [ ] README describes WRDS expansion as adapter replacement preserving canonical factor/model/dashboard logic.
  - [ ] `python scripts/scan_secrets.py` exits `0`.
  - [ ] Grep for internal wording exits no matches: `grep -n "study lead\|스터디장\|스터디용" README.md` should return no matches.

  **QA Scenarios**:
  ```
  Scenario: README documents complete smoke workflow
    Tool: Bash
    Steps: Search README for each new script name and for `prototype_only=True`.
    Expected: Every new script name appears; caveat appears in English and Korean.
    Evidence: .sisyphus/evidence/task-8-readme-script-coverage.txt

  Scenario: README remains public-facing and secret-safe
    Tool: Bash
    Steps: Run internal wording grep and `python scripts/scan_secrets.py`.
    Expected: Grep returns no internal wording matches; secret scan exits 0.
    Evidence: .sisyphus/evidence/task-8-readme-public-safe.txt
  ```

  **Commit**: YES | Message: `docs: document DDQM2-lite MVP workflow` | Files: `README.md`, optional `docs/*.md`

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**
> **Never mark F1-F4 as checked before getting user's okay.** Rejection or user feedback -> fix -> re-run -> present again -> wait for okay.
- [ ] F1. Plan Compliance Audit — oracle
  - Verify all planned artifacts/scripts exist, match canonical schema decisions, and all tasks' acceptance criteria were run with evidence.
- [ ] F2. Code Quality Review — unspecified-high
  - Review Python script structure, schema helper design, CLI consistency, error messages, and artifact contracts.
- [ ] F3. Real Manual QA — unspecified-high (+ playwright/browser only if UI verification requested)
  - Execute full smoke chain from price panel through dashboard headless startup and inspect generated summaries.
- [ ] F4. Scope Fidelity Check — deep
  - Confirm no WRDS loader, no public fundamentals/analyst proxy scope creep, no research-grade performance claims, and no dashboard recomputation.

## Commit Strategy
- Use atomic commits in task order.
- Generated artifacts under `prototypes/yfinance_sp500/` must remain untracked unless user explicitly approves otherwise.
- Do not commit `.env`, raw WRDS data, PDFs, XLSX workbooks, or prototype outputs.
- Suggested commits:
  1. `feat: add canonical artifact schemas`
  2. `feat: add yfinance canonical price panel`
  3. `feat: add yfinance factor score builder`
  4. `feat: add factor long-short labels`
  5. `feat: assemble macro factor dataset`
  6. `feat: train macro factor LightGBM baseline`
  7. `feat: add DDQM2-lite dashboard`
  8. `docs: document DDQM2-lite MVP workflow`

## Success Criteria
- End-to-end smoke pipeline produces validated artifacts:
  - `prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet`
  - `prototypes/yfinance_sp500/factor_scores_smoke.parquet`
  - `prototypes/yfinance_sp500/factor_long_short_returns_smoke.parquet`
  - `prototypes/yfinance_sp500/macro_factor_model_ready_smoke.parquet`
  - `prototypes/yfinance_sp500/experiments/smoke_lgbm/{config.json,metrics.json,predictions.parquet,feature_importance.csv,manifest.json}`
- LightGBM metrics are compared against naive baselines in `metrics.json`.
- Streamlit dashboard starts headless and reads smoke artifacts.
- All validators and secret scan pass.
- README explains FRED/ALFRED, yfinance, and future WRDS roles in both English and Korean.
- User receives final verification results and explicitly approves completion.
