# DDQM2 S&P500 WRDS Data Setup

## TL;DR
> **Summary**: 이번 주 목표는 삼성 DDQM2를 S&P500으로 옮기기 위한 데이터 세팅을 거의 완료하는 것이다. 모델 학습은 제외하고, 매크로 피처 정리, WRDS/CRSP/Compustat/CCM/IBES 접근 확인, 데이터베이스 구조 조사, fallback 경로, 공유문서 초안을 실행 가능한 산출물로 만든다.
> **Deliverables**:
> - credential-safe Python project scaffold
> - validated macro/market feature workbook and sanitized macro script
> - WRDS connection/schema probe scripts
> - CRSP/Compustat/CCM/IBES dataset inventory and extraction manifests
> - fallback/manual export guide
> - shared-document-ready report for next study meeting
> **Effort**: Medium
> **Parallel**: YES - 3 waves
> **Critical Path**: Task 1 → Task 2 → Task 3/4/5 → Task 7 → Task 8

## Execution Status Update — 2026-05-04

> **Status**: This plan is now a historical/stale execution plan. The original TODO checkboxes below were not updated during execution, and several acceptance criteria were superseded by practical constraints discovered during implementation. Use this section as the current source of truth.

### Completed in repo

- Credential-safe Python scaffold and config loader were created.
- Macro feature pipeline was modularized and sanitized into `scripts/build_macro_features.py`.
- Macro workbook validation and deeper quality diagnostics were added:
  - `scripts/validate_macro_workbook.py`
  - `scripts/diagnose_macro_feature_quality.py`
- Secret scanning was added in `scripts/scan_secrets.py`.
- WRDS probe script was added in `scripts/probe_wrds.py`, but live WRDS access remains blocked until the `wrds` package/auth is available.
- CRSP, Compustat, and IBES requirement docs were created under `docs/`.
- WRDS manual export guide and consolidated DDQM2 S&P500 inventory report were created:
  - `docs/wrds_manual_export_guide.md`
  - `docs/ddqm2_sp500_data_inventory.md`
- WRDS-free prototype path was added:
  - yfinance S&P500 label builder and validator
  - yfinance labels + macro feature assembly and validator
  - prototype LightGBM macro baseline with naive baseline comparison

### Key commits produced

- `4167e30` — initial credential-safe scaffold
- `a954436`, `8acf47b` — macro feature pipeline, validation, and secret scan
- `406e1b6` — WRDS connection probe
- `4d399dc` — CRSP, Compustat, and IBES requirement mappings
- `4785a35` — WRDS manual export guide and DDQM2 data inventory
- `c02fce7` — yfinance S&P500 prototype labels
- `282bd75` — macro feature diagnostics
- `bbc40ed` — yfinance + macro model-ready prototype assembly
- `759b748` — prototype LightGBM macro baseline
- `2acbfa2` — naive baseline comparison for LightGBM baseline

### Known deviations from original plan

- Momus plan review rejected the original plan as an active execution plan because it references missing QA helper scripts, a missing draft file, and contradictory wave/dependency ordering.
- The original plan said not to begin model training before data setup gates, but we later added a clearly marked **prototype-only** LightGBM baseline after WRDS access was deferred.
- The original manifest/validator targets under `data/manifests/` were not implemented.
- Original QA references to `scripts/check_doc_requirements.py`, `scripts/check_no_ticker_only_join.py`, and `scripts/validate_manifest.py` remain unimplemented.
- Original Task 8 reference `.sisyphus/drafts/ddqm-lightgbm-quant-study.md` does not exist in the repo.
- Some planned document names differ from actual files. Actual docs use:
  - `docs/crsp_requirements.md`
  - `docs/compustat_requirements.md`
  - `docs/ibes_requirements.md`
- `python scripts/scan_secrets.py` still flags the pre-existing untracked `macro code.txt` FRED key. That file remains sensitive and must not be committed or shared as-is.
- WRDS live probing is blocked until the `wrds` package and credentials/subscription access are available.

### Remaining next actions

1. Decide whether to archive this plan or rewrite it into a new active plan.
2. If WRDS becomes available, install dependencies and run `scripts/probe_wrds.py` against CRSP/Compustat/IBES.
3. Remove, sanitize, or quarantine `macro code.txt` before any repo sharing.
4. Optionally implement manifest generation/validation if the study group needs formal data inventory artifacts.

## Context
### Original Request
- User is using two Samsung Securities DDQM reports as the main quant study track.
- User will follow the LightGBM direction from DDQM2.
- Current repo contains two PDFs, one XLSX macro/market dataset, and one TXT code file.
- Target universe is likely U.S. S&P500, not KOSPI200.
- This week’s study instruction is to organize required fundamental data, investigate WRDS data acquisition and database structure, and summarize in a shared document.
- User clarified this is not just planning: actual setup should be nearly complete.

### Interview Summary
- DDQM2 uses separate LightGBM regressors to predict each factor’s future 1-month L/S return.
- The factor-level future L/S returns are computed historical labels from stock-level factor scores and subsequent returns, not raw inputs already present in the repo.
- CRSP may be available, but WRDS authentication is uncertain.
- Compustat also generally requires WRDS access.
- Default scope because user left scope question unanswered: **WRDS core databases + fallback/manual/public prototype routes**.

### Metis Review (gaps addressed)
- Added strict secret handling because `macro code.txt:9` contains a hard-coded FRED key.
- Added no ticker-only join guardrail for CRSP/Compustat/IBES.
- Added WRDS auth failure paths instead of assuming Python WRDS works.
- Added survivorship-bias guardrail: current S&P500 tickers/yfinance are prototype-only.
- Added point-in-time guardrails for macro vintages, Compustat filing dates, and IBES announcement dates.

## Work Objectives
### Core Objective
Prepare a reproducible S&P500 DDQM2 data foundation: macro/market features, WRDS database access mapping, required table/field inventory, extraction stubs/manifests, fallback paths, and meeting-ready documentation.

### Deliverables
- `README.md` project overview and this-week checklist.
- `requirements.txt` or `pyproject.toml` dependency specification.
- `.env.example` without secrets.
- `src/autoquant_lab/config.py` credential/config loader.
- `scripts/validate_macro_workbook.py` validation script.
- `scripts/scan_secrets.py` secret scanner.
- `scripts/probe_wrds.py` WRDS connection/schema probe.
- `docs/ddqm2_sp500_data_inventory.md` shared-document-ready report.
- `docs/wrds_manual_export_guide.md` fallback guide.
- `data/manifests/*.json` source manifests for every checked/extracted dataset.
- `.sisyphus/evidence/*.txt|json|md` verification evidence.

### Definition of Done (verifiable conditions with commands)
- `python scripts/scan_secrets.py .` exits 0 and reports `secret_findings=0`.
- `python scripts/validate_macro_workbook.py expanded_macro_market_features.xlsx` exits 0 and reports `feature_columns=75`, `data_rows=6024`, `min_date=2003-04-01`, `max_date=2026-05-01`, `duplicate_dates=0`.
- `python scripts/probe_wrds.py --dry-run` exits 0 without credentials and prints which environment variables are required.
- `python scripts/probe_wrds.py --list-libraries --output data/manifests/wrds_probe_manifest.json` either records accessible WRDS libraries or records an explicit auth failure with remediation.
- `python scripts/validate_manifest.py data/manifests/wrds_probe_manifest.json` exits 0.
- `docs/ddqm2_sp500_data_inventory.md` contains status rows for FRED/ALFRED, yfinance, CRSP stock, CRSP index/S&P500 membership, Compustat, CCM, and IBES.

### Must Have
- Credential-safe config; no hard-coded API keys.
- Authoritative data path separated from fallback/prototype path.
- CRSP as canonical return/delisting layer if accessible.
- Compustat/CCM/IBES documented as required for DDQM2-like fundamentals/revisions/target-price factors.
- All datasets have manifest fields: source, access path, extraction timestamp, date range, row count, column count, identifiers, status, blocker.

### Must NOT Have
- Do not train LightGBM models this week unless all data setup gates pass.
- Do not use yfinance/current S&P500 tickers as final research-grade historical universe.
- Do not join CRSP/Compustat/IBES by ticker alone.
- Do not share or commit hard-coded credentials.
- Do not claim public-data fallback is equivalent to WRDS/CRSP/Compustat/IBES.

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: tests-after + lightweight Python validation scripts because no test infra exists yet.
- QA policy: Every task has agent-executed scenarios.
- Evidence: `.sisyphus/evidence/task-{N}-{slug}.{ext}`

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks for max parallelism.

Wave 1: Task 1 scaffold/config, Task 2 macro validation/sanitization, Task 3 WRDS auth probe foundation
Wave 2: Task 4 CRSP inventory, Task 5 Compustat/CCM inventory, Task 6 IBES/analyst inventory, Task 7 fallback/manual guide
Wave 3: Task 8 shared report consolidation

### Dependency Matrix (full, all tasks)
- Task 1 blocks Tasks 2-8.
- Task 2 blocks Task 8.
- Task 3 blocks Tasks 4-7.
- Tasks 4-7 block Task 8.
- Final Verification Wave blocked by all Tasks 1-8.

### Agent Dispatch Summary (wave → task count → categories)
- Wave 1 → 3 tasks → quick, unspecified-high
- Wave 2 → 4 tasks → deep, unspecified-high, writing
- Wave 3 → 1 task → writing

## TODOs
> Implementation + Test = ONE task. Never separate.
> EVERY task MUST have: Agent Profile + Parallelization + QA Scenarios.

- [ ] 1. Initialize credential-safe project scaffold

  **What to do**: Create minimal Python research project layout without moving existing files: `src/autoquant_lab/`, `scripts/`, `docs/`, `data/raw/`, `data/processed/`, `data/manifests/`, `.sisyphus/evidence/`. Add dependency file including `pandas`, `numpy`, `requests`, `pandas-datareader`, `yfinance`, `python-dotenv`, `wrds`, `openpyxl`, `pyarrow`. Add `.env.example` with `FRED_API_KEY=`, `WRDS_USERNAME=`, and no real values. Add `.gitignore` for `.env`, raw data, credentials, and large extracts. Add `src/autoquant_lab/config.py` to load env vars and fail with actionable messages.
  **Must NOT do**: Do not delete existing PDFs/XLSX/TXT. Do not put any real API key in `.env.example` or code.

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: bounded scaffold and config setup.
  - Skills: [] - no special skill required.
  - Omitted: [`git-master`] - no commit requested by user.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: Tasks 2-8 | Blocked By: none

  **References**:
  - Existing artifact list: `/root/projects/autoquant-lab` - contains only two PDFs, one XLSX, one TXT.
  - Sensitive pattern: `macro code.txt:9` - hard-coded FRED key must be removed from shareable code.

  **Acceptance Criteria**:
  - [ ] `python -c "from autoquant_lab.config import load_config; print(load_config(require_secrets=False).mode)"` runs with `PYTHONPATH=src` and exits 0.
  - [ ] `.env.example` contains placeholders only and no value longer than 20 alphanumeric characters.
  - [ ] Required directories exist.

  **QA Scenarios**:
  ```
  Scenario: Config loads without secrets in dry-run mode
    Tool: Bash
    Steps: PYTHONPATH=src python -c "from autoquant_lab.config import load_config; c=load_config(require_secrets=False); print(c.mode)"
    Expected: Exit 0 and stdout includes `dry-run`.
    Evidence: .sisyphus/evidence/task-1-scaffold.txt

  Scenario: Missing required secret fails clearly
    Tool: Bash
    Steps: env -u FRED_API_KEY PYTHONPATH=src python -c "from autoquant_lab.config import load_config; load_config(require_secrets=True)"
    Expected: Non-zero exit or raised error mentioning `FRED_API_KEY` and `.env.example`.
    Evidence: .sisyphus/evidence/task-1-scaffold-error.txt
  ```

  **Commit**: NO | Message: `chore: initialize quant data scaffold` | Files: [new scaffold files]

- [ ] 2. Sanitize and validate macro/market feature dataset

  **What to do**: Convert `macro code.txt` into `scripts/build_macro_features.py` or `src/autoquant_lab/macro_features.py` while preserving current output semantics. Replace hard-coded FRED key with config/env loading. Add `scripts/validate_macro_workbook.py` that validates existing `expanded_macro_market_features.xlsx`: one sheet, 75 feature columns, 6024 rows, no duplicate dates, date range 2003-04-01 to 2026-05-01, required columns present. Add `scripts/scan_secrets.py` and run it over repo.
  **Must NOT do**: Do not expose existing FRED key in logs/evidence. Do not overwrite `expanded_macro_market_features.xlsx` unless validation passes first.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: credential cleanup plus validation script with exact workbook expectations.
  - Skills: [] - no special skill required.
  - Omitted: [`ai-slop-remover`] - single-file cleanup is not the primary task.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: Task 8 | Blocked By: Task 1

  **References**:
  - Pattern: `macro code.txt:1-245` - current macro generation logic.
  - Output: `expanded_macro_market_features.xlsx` - workbook to validate.
  - XLSX facts: one sheet `Sheet1`, range `A1:BX6025`, 75 features.

  **Acceptance Criteria**:
  - [ ] `python scripts/scan_secrets.py .` exits 0 with `secret_findings=0`.
  - [ ] `python scripts/validate_macro_workbook.py expanded_macro_market_features.xlsx` exits 0 with exact expected shape/date report.
  - [ ] Sanitized macro script contains no literal FRED API key and reads from env/config.

  **QA Scenarios**:
  ```
  Scenario: Existing workbook validates
    Tool: Bash
    Steps: python scripts/validate_macro_workbook.py expanded_macro_market_features.xlsx
    Expected: Exit 0; output includes `data_rows=6024`, `feature_columns=75`, `min_date=2003-04-01`, `max_date=2026-05-01`, `duplicate_dates=0`.
    Evidence: .sisyphus/evidence/task-2-macro-validation.txt

  Scenario: Hard-coded API key detection fails
    Tool: Bash
    Steps: python scripts/scan_secrets.py . --fail-on-secrets
    Expected: Exit 0 only after `macro code.txt` is either sanitized, quarantined from sharing, or documented as sensitive; output `secret_findings=0` for shareable files.
    Evidence: .sisyphus/evidence/task-2-secret-scan.txt
  ```

  **Commit**: NO | Message: `fix(data): sanitize macro feature generation` | Files: [scripts/build_macro_features.py, scripts/validate_macro_workbook.py, scripts/scan_secrets.py]

- [ ] 3. Implement WRDS authentication and schema probe path

  **What to do**: Add `scripts/probe_wrds.py` with modes: `--dry-run`, `--list-libraries`, `--describe-table LIB TABLE`, and `--output PATH`. In dry-run, no network login occurs; it verifies env/config and prints required variables. In live mode, use `wrds.Connection(wrds_username=...)`, `list_libraries()`, `list_tables(library=...)`, `describe_table(library=..., table=...)`. Always write a manifest JSON with status `accessible`, `auth_failed`, or `not_subscribed`.
  **Must NOT do**: Do not run large extraction queries. Do not prompt interactively for passwords; fail with manual export fallback instructions.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: external auth behavior and robust failure handling.
  - Skills: [] - no special skill required.
  - Omitted: [`playwright`] - no browser automation required unless manual WRDS UI guide is later tested.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: Tasks 4-7 | Blocked By: Task 1

  **References**:
  - External: WRDS Python `wrds.Connection`, `list_libraries`, `list_tables`, `describe_table` conventions.
  - Metis guardrail: WRDS auth may fail; failure must be recorded, not silently skipped.

  **Acceptance Criteria**:
  - [ ] `python scripts/probe_wrds.py --dry-run` exits 0 without WRDS credentials and lists required variables.
  - [ ] `python scripts/probe_wrds.py --list-libraries --output data/manifests/wrds_probe_manifest.json` creates a manifest whether login succeeds or fails.
  - [ ] `python scripts/validate_manifest.py data/manifests/wrds_probe_manifest.json` exits 0.

  **QA Scenarios**:
  ```
  Scenario: Dry-run does not require WRDS login
    Tool: Bash
    Steps: env -u WRDS_USERNAME python scripts/probe_wrds.py --dry-run
    Expected: Exit 0; output includes `WRDS_USERNAME required for live mode`.
    Evidence: .sisyphus/evidence/task-3-wrds-dry-run.txt

  Scenario: Live auth failure creates manifest
    Tool: Bash
    Steps: env WRDS_USERNAME=invalid python scripts/probe_wrds.py --list-libraries --output data/manifests/wrds_probe_manifest.json || true; python scripts/validate_manifest.py data/manifests/wrds_probe_manifest.json
    Expected: Manifest exists with `status=auth_failed` and `next_action=manual_export_or_fix_credentials`.
    Evidence: .sisyphus/evidence/task-3-wrds-auth-failure.json
  ```

  **Commit**: NO | Message: `feat(data): add wrds schema probe` | Files: [scripts/probe_wrds.py, scripts/validate_manifest.py]

- [ ] 4. Map CRSP market/return/S&P500 universe data requirements

  **What to do**: Create `docs/crsp_data_requirements.md` and update `docs/ddqm2_sp500_data_inventory.md` with CRSP requirements: daily/monthly stock prices and returns, delisting returns, share codes, exchange codes, PERMNO/PERMCO, company names, distribution/corporate-action fields, and S&P500 historical membership via CRSP Index Files if subscribed. Add small bounded extraction probe definitions for CRSP tables only if accessible; otherwise document manual export fields. Add validation expectations for `permno,date` uniqueness and delisting return handling.
  **Must NOT do**: Do not build universe from today’s tickers. Do not ignore delisting returns.

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: requires careful data-model and bias-control reasoning.
  - Skills: [] - no special skill required.
  - Omitted: [`librarian`] - prior CRSP research already completed.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: Task 8 | Blocked By: Task 3

  **References**:
  - External: CRSP US Stock Databases - prices, returns, active/inactive securities, PERMNO/PERMCO.
  - External: WRDS S&P500 constituents guide - historical constituents require relevant CRSP subscription.
  - Guardrail: yfinance/current constituents are prototype-only.

  **Acceptance Criteria**:
  - [ ] `docs/crsp_data_requirements.md` contains table: purpose, WRDS library/table candidate, fields, identifiers, date filters, status, fallback.
  - [ ] `python scripts/validate_manifest.py data/manifests/crsp_requirements_manifest.json` exits 0.
  - [ ] Document explicitly says final joins use `permno`/`permco`, not ticker.

  **QA Scenarios**:
  ```
  Scenario: CRSP inventory contains required return fields
    Tool: Bash
    Steps: python scripts/check_doc_requirements.py docs/crsp_data_requirements.md --must-contain permno permco ret dlret date "S&P500 historical membership" survivorship
    Expected: Exit 0; all tokens present.
    Evidence: .sisyphus/evidence/task-4-crsp-doc-check.txt

  Scenario: Ticker-only join is rejected
    Tool: Bash
    Steps: python scripts/check_no_ticker_only_join.py docs/crsp_data_requirements.md
    Expected: Exit 0; document includes explicit prohibition against ticker-only final joins.
    Evidence: .sisyphus/evidence/task-4-crsp-join-guardrail.txt
  ```

  **Commit**: NO | Message: `docs(data): map crsp requirements` | Files: [docs/crsp_data_requirements.md]

- [ ] 5. Map Compustat and CCM fundamentals/linking requirements

  **What to do**: Create `docs/compustat_ccm_data_requirements.md`. Map DDQM2-like U.S. fundamental/valuation factors to Compustat fields and CCM links: book equity, market equity linkage, earnings, cash flow, sales, operating income, assets, liabilities, shares, fiscal dates, report dates (`rdq` where applicable), `gvkey`, `iid`, `datadate`, `linktype`, `linkprim`, `linkdt`, `linkenddt`, `permno`. Specify point-in-time lags and no future filing data. Include WRDS libraries/table candidates and manual export route.
  **Must NOT do**: Do not imply Compustat data is available unless probe confirms subscription. Do not join by ticker.

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: fundamental data and identifier timing are high-risk.
  - Skills: [] - no special skill required.
  - Omitted: [] - none.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: Task 8 | Blocked By: Task 3

  **References**:
  - External: CRSP/Compustat Merged database maps CRSP and Compustat identifiers over time.
  - Samsung DDQM2 factor groups: valuation, earnings momentum, surprise, growth, quality/sentiment equivalents.

  **Acceptance Criteria**:
  - [ ] `docs/compustat_ccm_data_requirements.md` contains fields `gvkey`, `permno`, `linkdt`, `linkenddt`, `datadate`, `rdq`.
  - [ ] Each proposed fundamental factor states required source table, identifiers, and point-in-time availability rule.
  - [ ] `data/manifests/compustat_ccm_requirements_manifest.json` validates.

  **QA Scenarios**:
  ```
  Scenario: CCM temporal link fields documented
    Tool: Bash
    Steps: python scripts/check_doc_requirements.py docs/compustat_ccm_data_requirements.md --must-contain gvkey permno linkdt linkenddt linktype linkprim datadate rdq
    Expected: Exit 0; all fields present.
    Evidence: .sisyphus/evidence/task-5-ccm-doc-check.txt

  Scenario: Future-data guardrail documented
    Tool: Bash
    Steps: python scripts/check_doc_requirements.py docs/compustat_ccm_data_requirements.md --must-contain "point-in-time" "no future" "filing" "availability"
    Expected: Exit 0; document explicitly prevents using future filings.
    Evidence: .sisyphus/evidence/task-5-point-in-time.txt
  ```

  **Commit**: NO | Message: `docs(data): map compustat ccm requirements` | Files: [docs/compustat_ccm_data_requirements.md]

- [ ] 6. Map IBES/analyst estimate requirements and feasible substitutes

  **What to do**: Create `docs/ibes_data_requirements.md`. Map DDQM2 analyst-driven factors to U.S. equivalents: EPS revisions, estimate dispersion, earnings surprise, target-price upside, recommendation changes. Identify IBES/FactSet/Bloomberg/Refinitiv/Capital IQ as authoritative sources. For WRDS IBES, specify required identifiers and dates: ticker/CUSIP link caveat, `anndats`, `fpedats`, estimate period, actual EPS announcement timing, target price date. If no IBES access, mark analyst factors as `required_but_blocked` and propose non-authoritative prototype substitutes separately.
  **Must NOT do**: Do not fabricate analyst data from yfinance as research-grade. Do not use estimates announced after rebalance date.

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: analyst data has high lookahead and identifier risk.
  - Skills: [] - no special skill required.
  - Omitted: [] - none.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: Task 8 | Blocked By: Task 3

  **References**:
  - Samsung DDQM2 selected factors include EPS changes, operating-profit changes, net-income surprise, target-price upside.
  - Metis guardrail: IBES/analyst estimates must use announcement dates and no future information.

  **Acceptance Criteria**:
  - [ ] `docs/ibes_data_requirements.md` distinguishes authoritative IBES/FactSet/Bloomberg/Refinitiv from prototype substitutes.
  - [ ] Document includes `anndats`, `fpedats`, target price date, and identifier-link caveats.
  - [ ] Blocked status is explicit if access is unavailable.

  **QA Scenarios**:
  ```
  Scenario: IBES timing fields documented
    Tool: Bash
    Steps: python scripts/check_doc_requirements.py docs/ibes_data_requirements.md --must-contain anndats fpedats "target price" "announcement" "no future"
    Expected: Exit 0; all timing guardrails present.
    Evidence: .sisyphus/evidence/task-6-ibes-doc-check.txt

  Scenario: Prototype substitutes are labeled non-authoritative
    Tool: Bash
    Steps: python scripts/check_doc_requirements.py docs/ibes_data_requirements.md --must-contain prototype non-authoritative "not research-grade"
    Expected: Exit 0; fallback language prevents overstating validity.
    Evidence: .sisyphus/evidence/task-6-ibes-fallback.txt
  ```

  **Commit**: NO | Message: `docs(data): map ibes analyst requirements` | Files: [docs/ibes_data_requirements.md]

- [ ] 7. Create WRDS manual export and fallback guide

  **What to do**: Create `docs/wrds_manual_export_guide.md` covering three routes: Python WRDS, WRDS web/manual CSV export, and WRDS-hosted Jupyter/SAS export. Include exact datasets to request/export: CRSP stock returns/delistings, CRSP S&P500 historical constituents/index files, Compustat annual/quarterly fundamentals, CCM link table, IBES estimates/actuals/target prices. Include fallback table: Norgate for survivorship-aware equities, Sharadar/Nasdaq Data Link/FMP/EODHD/Polygon/Tiingo for prototypes with caveats. Add blocker checklist for the study team.
  **Must NOT do**: Do not instruct storing WRDS passwords in code. Do not recommend public APIs as final replacement.

  **Recommended Agent Profile**:
  - Category: `writing` - Reason: shared instruction document.
  - Skills: [] - no special skill required.
  - Omitted: [] - none.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: Task 8 | Blocked By: Task 3

  **References**:
  - User issue: WRDS authentication may be difficult.
  - Metis directive: manual export path required for every auth failure.

  **Acceptance Criteria**:
  - [ ] Guide includes Python, web/manual, and hosted WRDS routes.
  - [ ] Guide includes exact export checklist for CRSP, Compustat, CCM, IBES.
  - [ ] Guide labels public-data route as prototype-only.

  **QA Scenarios**:
  ```
  Scenario: Manual export guide covers all required databases
    Tool: Bash
    Steps: python scripts/check_doc_requirements.py docs/wrds_manual_export_guide.md --must-contain CRSP Compustat CCM IBES "manual export" "prototype-only"
    Expected: Exit 0; all required routes and caveats present.
    Evidence: .sisyphus/evidence/task-7-manual-guide.txt

  Scenario: No password storage instructions
    Tool: Bash
    Steps: python scripts/check_doc_requirements.py docs/wrds_manual_export_guide.md --must-not-contain "password=" "WRDS_PASSWORD=" "hard-code"
    Expected: Exit 0; no unsafe password guidance.
    Evidence: .sisyphus/evidence/task-7-password-guardrail.txt
  ```

  **Commit**: NO | Message: `docs(data): add wrds fallback guide` | Files: [docs/wrds_manual_export_guide.md]

- [ ] 8. Produce shared-document-ready DDQM2 S&P500 data setup report

  **What to do**: Consolidate Tasks 2-7 into `docs/ddqm2_sp500_data_inventory.md`. Use tables that can be copied into a shared document: Required Dataset, DDQM2 Role, U.S. Source, WRDS Library/Table Candidate, Key Identifiers, Point-in-Time Rule, Current Status, Blocker, Fallback, Next Action. Include macro/market data status from FRED/ALFRED/yfinance and explicitly state macro Excel/code can be shared only after secret scan passes. Include a short Korean executive summary for the study group.
  **Must NOT do**: Do not include raw API keys, WRDS credentials, or large raw data dumps. Do not present blocked datasets as completed.

  **Recommended Agent Profile**:
  - Category: `writing` - Reason: consolidation into meeting-ready documentation.
  - Skills: [] - no special skill required.
  - Omitted: [] - none.

  **Parallelization**: Can Parallel: NO | Wave 3 | Blocks: Final Verification | Blocked By: Tasks 2-7

  **References**:
  - Draft: `.sisyphus/drafts/ddqm-lightgbm-quant-study.md` - planning baseline.
  - Docs from Tasks 4-7.
  - Existing workbook validation evidence from Task 2.

  **Acceptance Criteria**:
  - [ ] `docs/ddqm2_sp500_data_inventory.md` contains rows for FRED/ALFRED, yfinance, CRSP stock, CRSP index/S&P500 membership, Compustat, CCM, IBES.
  - [ ] Report includes Korean summary and blocker table.
  - [ ] Report includes clear next-week action list.
  - [ ] `python scripts/check_doc_requirements.py docs/ddqm2_sp500_data_inventory.md --must-contain FRED ALFRED yfinance CRSP Compustat CCM IBES LightGBM S\&P500` exits 0.

  **QA Scenarios**:
  ```
  Scenario: Shared report is complete
    Tool: Bash
    Steps: python scripts/check_doc_requirements.py docs/ddqm2_sp500_data_inventory.md --must-contain FRED ALFRED yfinance CRSP Compustat CCM IBES "Point-in-Time" "Fallback" "Next Action"
    Expected: Exit 0; report contains all required sections and datasets.
    Evidence: .sisyphus/evidence/task-8-report-complete.txt

  Scenario: Shared report contains no secrets
    Tool: Bash
    Steps: python scripts/scan_secrets.py docs/ddqm2_sp500_data_inventory.md
    Expected: Exit 0; output `secret_findings=0`.
    Evidence: .sisyphus/evidence/task-8-report-secret-scan.txt
  ```

  **Commit**: NO | Message: `docs: add ddqm2 sp500 data setup report` | Files: [docs/ddqm2_sp500_data_inventory.md]

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**
> **Never mark F1-F4 as checked before getting user's okay.** Rejection or user feedback -> fix -> re-run -> present again -> wait for okay.
- [ ] F1. Plan Compliance Audit — oracle
- [ ] F2. Code Quality Review — unspecified-high
- [ ] F3. Real Manual QA — unspecified-high
- [ ] F4. Scope Fidelity Check — deep

## Commit Strategy
- User did not request commits; do not commit by default.
- If user later requests commits, use small commits in this order: scaffold/config, macro sanitization/validation, WRDS probe, CRSP docs, Compustat/CCM docs, IBES docs, fallback guide, shared report, final QA evidence.
- Never commit `.env`, raw licensed WRDS data, credentials, or large extracts unless user explicitly instructs and license permits.

## Success Criteria
- The study group can open one shared report and see exactly what data is needed, which databases provide it, what is accessible/blocked, and what to do next.
- The repo can safely share macro Excel/code after secret scan passes.
- WRDS path is either working with manifests or blocked with manual export instructions.
- CRSP/Compustat/CCM/IBES roles are unambiguous for S&P500 DDQM2 adaptation.
- No model-training work begins before data setup, identifier linkage, and point-in-time rules are established.
