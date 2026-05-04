# autoquant-lab

<p align="center">
  <a href="#english-guide"><img src="https://img.shields.io/badge/README-English-blue?style=for-the-badge" alt="English README" /></a>
  <a href="#korean-guide"><img src="https://img.shields.io/badge/README-한국어-green?style=for-the-badge" alt="한국어 README" /></a>
</p>

<a id="english-guide"></a>

## English Guide

Credential-safe research scaffold for adapting the Samsung Securities DDQM2 LightGBM workflow to a U.S. S&P 500 setting.

This repository currently focuses on two tracks:

1. Prepare the WRDS/CRSP/Compustat/IBES data map for the final research path.
2. Provide a WRDS-free prototype path using yfinance and the existing macro workbook, clearly marked as prototype-only.

## What is in this repo

| Area | Files |
|---|---|
| Config and secrets | `.env.example`, `src/autoquant_lab/config.py` |
| Macro feature pipeline | `scripts/build_macro_features.py`, `scripts/validate_macro_workbook.py`, `scripts/diagnose_macro_feature_quality.py` |
| WRDS readiness | `scripts/probe_wrds.py`, `docs/wrds_manual_export_guide.md` |
| Data requirements | `docs/crsp_requirements.md`, `docs/compustat_requirements.md`, `docs/ibes_requirements.md`, `docs/ddqm2_sp500_data_inventory.md` |
| Legacy stock-return prototype | `scripts/build_yfinance_sp500_labels.py`, `scripts/assemble_yfinance_macro_dataset.py`, `scripts/train_yfinance_macro_lgbm_baseline.py` |
| DDQM2-lite factor MVP | `scripts/build_yfinance_price_panel.py`, `scripts/build_yfinance_factor_scores.py`, `scripts/build_factor_long_short_returns.py`, `scripts/assemble_macro_factor_dataset.py`, `scripts/train_macro_factor_lgbm_baseline.py` |
| DDQM2-lite validation | `scripts/validate_yfinance_price_panel.py`, `scripts/validate_factor_scores.py`, `scripts/validate_factor_long_short_returns.py`, `scripts/validate_macro_factor_dataset.py`, `scripts/validate_macro_factor_experiment.py` |
| DDQM2-lite dashboard | `apps/ddqm2_lite_dashboard.py` |
| Safety check | `scripts/scan_secrets.py` |

## Implementation status and roadmap

This section summarizes what is already implemented and what remains to build for a DDQM-style S&P 500 research pipeline. The repository currently covers the credential-safe scaffold, macro feature workflow, WRDS data requirements, and a WRDS-free prototype path; the final WRDS loaders and factor database still need to be implemented.

### Implemented so far

| Area | Status | Technical detail |
|---|---|---|
| Credential-safe setup | Implemented | `.env.example` and `src/autoquant_lab/config.py` keep FRED and WRDS credentials outside committed code. |
| Macro features | Implemented | `scripts/build_macro_features.py` builds FRED/ALFRED/yfinance macro-market features; validation and diagnostics scripts check workbook quality. |
| WRDS readiness docs | Implemented | CRSP, Compustat, IBES, CCM, and manual export requirements are documented under `docs/`. |
| WRDS access probe | Implemented | `scripts/probe_wrds.py` checks whether WRDS schemas and representative tables are accessible. |
| Legacy prototype equity path | Implemented | yfinance S&P 500 stock-level labels, macro join, validation, and LightGBM smoke-test scripts are available for simple pipeline testing only. |
| DDQM2-lite factor path | Implemented | FRED/ALFRED macro features plus yfinance price/volume data now produce canonical price panels, factor scores, factor long-short labels, macro-factor model data, persisted LightGBM artifacts, and a read-only Streamlit dashboard. |
| Research-grade WRDS factor path | Not yet implemented | CRSP/Compustat/IBES loaders, point-in-time joins, and research-grade survivorship-bias controls still need WRDS access. |

### What needs to be built next

| Priority | Deliverable | Why it matters |
|---|---|---|
| 1 | WRDS extraction scripts for `crsp.msf`/`crsp.dsf`, `comp.funda`, `comp.fundq`, `comp.ccmxpf_lnkhist`, IBES Summary History, and `wrdsapps.ibcrsphist` | Moves the project from prototype data to research-grade source data. |
| 2 | Database/staging schema for WRDS data | Keeps CRSP `PERMNO`, Compustat `GVKEY`, CCM links, IBES links, macro features, factor scores, and labels separated but joinable. |
| 3 | Point-in-time fundamental pipeline | Prevents lookahead bias by using `rdq` or conservative release lags instead of raw `datadate`. |
| 4 | Research-grade WRDS factor score builders | Extends the DDQM2-lite public-data factors with CRSP/Compustat/IBES point-in-time signals. |
| 5 | Research-grade WRDS factor long-short return labels | Replaces prototype yfinance/current-membership labels with CRSP-backed factor-level targets. |
| 6 | Research-grade rolling LightGBM loop | Runs macro-to-factor-return experiments on WRDS-backed labels with baselines, feature importance, and out-of-sample evaluation. |

### Proposed WRDS database structure

| Table | Main keys | Purpose |
|---|---|---|
| `security_master` | `permno`, `permco`, `gvkey` | Stable security/company mapping with historical links. |
| `sp500_membership` | `permno`, `start_date`, `end_date` | Point-in-time S&P 500 universe membership. |
| `crsp_monthly_returns` | `permno`, `date` | Returns, delisting returns, prices, volume, shares, and market cap. |
| `compustat_fundamentals` | `gvkey`, `permno`, `available_date` | PIT annual/quarterly fundamentals for value, profitability, investment, leverage, and cash-flow factors. |
| `ibes_estimates` | `permno`, `estimate_date`, `fiscal_period` | Consensus, dispersion, coverage, and revision features. |
| `macro_features` | `date` | FRED/ALFRED macro and market-state features. |
| `factor_scores` | `permno`, `date`, `factor_name` | Cross-sectional factor values before portfolio construction. |
| `factor_long_short_returns` | `date`, `factor_name` | DDQM-style long-short factor return labels. |
| `model_dataset` | `date`, `factor_name` | Final LightGBM-ready macro features and target factor returns. |

Implementation note: the final research path should not join by ticker. It should use CRSP `PERMNO`, Compustat `GVKEY`, CCM link history, IBES-CRSP link history, and explicit availability dates to keep the S&P 500 panel point-in-time safe.

## Important caveats

- WRDS/CRSP/Compustat/IBES should be treated as the final research data path.
- yfinance uses public, current-membership data and is only for pipeline testing.
- Prototype outputs include `prototype_only=True` and should not be described as research-grade or survivorship-bias-free.
- Keep `.env` local. Do not commit API keys, WRDS credentials, raw licensed data, or generated prototype outputs.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` locally:

```bash
FRED_API_KEY=your_fred_key_here
WRDS_USERNAME=your_wrds_username_here
```

Use `PYTHONPATH=src` when running scripts that import project modules.

## Safety check before commits or pushes

Run this before sharing or pushing changes:

```bash
python scripts/scan_secrets.py
```

Expected safe output:

```text
No potential secrets found in .py/.txt files under ...
```

## Macro workbook checks

Validate the existing macro feature workbook:

```bash
python scripts/validate_macro_workbook.py expanded_macro_market_features.xlsx
```

Run deeper quality diagnostics:

```bash
python scripts/diagnose_macro_feature_quality.py --top-n 5
```

This prints coverage, missing values, constant columns, duplicate columns, high correlations, robust outliers, and largest one-day changes to stdout. It does not create report files by default.

## Rebuilding macro features

If you need to rebuild the macro/market feature workbook from APIs:

```bash
PYTHONPATH=src python scripts/build_macro_features.py --output expanded_macro_market_features.xlsx
```

Requirements:

- `.env` must contain `FRED_API_KEY`.
- The script may call FRED/ALFRED and yfinance.
- Do not print or commit the API key.

## WRDS readiness

WRDS is not required for the prototype path, but it is needed for the final research-grade path.

Check WRDS access when the `wrds` package and credentials are available:

```bash
PYTHONPATH=src python scripts/probe_wrds.py
```

If Python WRDS access is blocked, follow:

```text
docs/wrds_manual_export_guide.md
```

The main data inventory is here:

```text
docs/ddqm2_sp500_data_inventory.md
```

## WRDS-free prototype path

Use this path only to verify that the pipeline works end to end before WRDS is available.

### DDQM2-lite factor MVP

This is the preferred WRDS-free prototype path. It uses FRED/ALFRED macro features and yfinance price/volume data to imitate the DDQM-style flow:

```text
yfinance canonical price panel
→ price/volume factor scores
→ factor long-short return labels
→ FRED/ALFRED macro-factor dataset
→ LightGBM baseline and experiment artifacts
→ read-only Streamlit dashboard
```

Build a canonical yfinance price panel:

```bash
PYTHONPATH=src python scripts/build_yfinance_price_panel.py \
  --tickers AAPL MSFT SPY \
  --start-date 2020-01-01 \
  --end-date 2020-06-30 \
  --output prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet
```

Validate it:

```bash
PYTHONPATH=src python scripts/validate_yfinance_price_panel.py \
  prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet
```

Build wide price/volume factor scores:

```bash
PYTHONPATH=src python scripts/build_yfinance_factor_scores.py \
  --price-panel prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet \
  --output prototypes/yfinance_sp500/factor_scores_smoke.parquet \
  --smoke
```

Validate factor scores:

```bash
PYTHONPATH=src python scripts/validate_factor_scores.py \
  prototypes/yfinance_sp500/factor_scores_smoke.parquet \
  --smoke
```

Build factor long-short return labels:

```bash
PYTHONPATH=src python scripts/build_factor_long_short_returns.py \
  --factor-scores prototypes/yfinance_sp500/factor_scores_smoke.parquet \
  --price-panel prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet \
  --output prototypes/yfinance_sp500/factor_long_short_returns_smoke.parquet \
  --horizon-trading-days 21 \
  --smoke
```

Validate factor labels:

```bash
PYTHONPATH=src python scripts/validate_factor_long_short_returns.py \
  prototypes/yfinance_sp500/factor_long_short_returns_smoke.parquet \
  --smoke
```

Assemble the macro-factor model-ready dataset:

```bash
PYTHONPATH=src python scripts/assemble_macro_factor_dataset.py \
  --factor-returns prototypes/yfinance_sp500/factor_long_short_returns_smoke.parquet \
  --macro-workbook expanded_macro_market_features.xlsx \
  --output prototypes/yfinance_sp500/macro_factor_model_ready_smoke.parquet
```

Validate the model-ready dataset:

```bash
PYTHONPATH=src python scripts/validate_macro_factor_dataset.py \
  prototypes/yfinance_sp500/macro_factor_model_ready_smoke.parquet
```

Train the macro-factor LightGBM baseline and write experiment artifacts:

```bash
PYTHONPATH=src python scripts/train_macro_factor_lgbm_baseline.py \
  --input prototypes/yfinance_sp500/macro_factor_model_ready_smoke.parquet \
  --output-dir prototypes/yfinance_sp500/experiments/smoke_lgbm \
  --smoke
```

Validate the experiment artifacts:

```bash
PYTHONPATH=src python scripts/validate_macro_factor_experiment.py \
  prototypes/yfinance_sp500/experiments/smoke_lgbm
```

Open the read-only dashboard:

```bash
PYTHONPATH=src streamlit run apps/ddqm2_lite_dashboard.py
```

The dashboard reads generated artifacts only. It does not download data, rebuild labels, retrain models, or mutate experiment files.

### DDQM2-lite artifacts

| Artifact | Purpose |
|---|---|
| `canonical_price_panel_smoke.parquet` | yfinance price/volume data in a WRDS-ready canonical schema. |
| `factor_scores_smoke.parquet` | Raw price/volume factor scores with factor metadata. |
| `factor_long_short_returns_smoke.parquet` | Monthly equal-weight factor long-short return labels. |
| `macro_factor_model_ready_smoke.parquet` | Macro features joined to factor return targets. |
| `experiments/smoke_lgbm/` | LightGBM config, metrics, predictions, feature importance, and manifest. |

### WRDS expansion path

The MVP is intentionally source-adapter based. Downstream factor, label, model, and dashboard logic should read canonical artifacts rather than yfinance-specific raw columns.

Future WRDS adapters should replace only the source layer:

```text
CRSP adapter → canonical price/return panel with PERMNO/PERMCO and delisting returns
Compustat adapter → PIT fundamental features through GVKEY/CCM links
IBES adapter → analyst revision/dispersion features through IBES-CRSP links
```

After that replacement, the factor-score, factor-label, macro-factor, LightGBM, and dashboard layers should be reused where their inputs overlap.

### Legacy stock-level prototype

The older stock-return prototype remains available for simple plumbing checks. It predicts individual stock forward returns, so it is less DDQM-like than the factor long-short MVP.

#### 1. Build yfinance S&P 500 labels

Small smoke test:

```bash
PYTHONPATH=src python scripts/build_yfinance_sp500_labels.py \
  --start-date 2020-01-01 \
  --end-date 2020-03-31 \
  --max-tickers 10 \
  --horizon-days 5 \
  --output prototypes/yfinance_sp500/sp500_yfinance_labels_sample.csv
```

Validate the labels:

```bash
PYTHONPATH=src python scripts/validate_yfinance_sp500_labels.py \
  prototypes/yfinance_sp500/sp500_yfinance_labels_sample.csv \
  --label-column forward_return_5d
```

#### 2. Join labels with macro features

```bash
PYTHONPATH=src python scripts/assemble_yfinance_macro_dataset.py \
  --labels prototypes/yfinance_sp500/sp500_yfinance_labels_sample.csv \
  --macro-workbook expanded_macro_market_features.xlsx \
  --output prototypes/yfinance_sp500/sp500_yfinance_macro_model_ready_sample.csv
```

Validate the assembled model-ready table:

```bash
PYTHONPATH=src python scripts/validate_yfinance_macro_dataset.py \
  prototypes/yfinance_sp500/sp500_yfinance_macro_model_ready_sample.csv \
  --label-column forward_return_5d
```

#### 3. Run the LightGBM prototype baseline

```bash
PYTHONPATH=src python scripts/train_yfinance_macro_lgbm_baseline.py \
  --input prototypes/yfinance_sp500/sp500_yfinance_macro_model_ready_sample.csv \
  --label-column forward_return_5d \
  --valid-fraction 0.25 \
  --min-train-rows 20 \
  --min-valid-rows 5 \
  --n-estimators 50 \
  --early-stopping-rounds 10
```

The script prints LightGBM metrics and two simple comparisons:

- `zero_return`: always predicts 0% return.
- `train_mean_return`: always predicts the average return from the train split.

These metrics are for smoke testing only, not for research conclusions.

## Generated files and git

Generated prototype CSV/Parquet files under `prototypes/yfinance_sp500/` are ignored by git.

Before pushing:

```bash
git status --short
python scripts/scan_secrets.py
```

Do not commit:

- `.env`
- raw WRDS data
- API keys or credentials
- generated prototype datasets
- large PDFs/XLSX files unless intentionally approved

---

<a id="korean-guide"></a>

# 한국어 사용 가이드

<p align="center">
  <a href="#english-guide"><img src="https://img.shields.io/badge/README-English-blue?style=for-the-badge" alt="English README" /></a>
  <a href="#korean-guide"><img src="https://img.shields.io/badge/README-한국어-green?style=for-the-badge" alt="한국어 README" /></a>
</p>

이 레포는 삼성증권 DDQM2 방식의 LightGBM 아이디어를 미국 S&P 500 기준으로 옮기기 위한 작업 공간입니다.

현재 목적은 두 가지입니다.

1. WRDS, CRSP, Compustat, IBES 같은 최종 연구용 데이터 경로를 정리합니다.
2. WRDS 접속 전까지 yfinance와 기존 매크로 엑셀로 임시 실험 파이프라인을 돌립니다.

## 먼저 알아둘 점

- 최종 연구용 데이터는 WRDS/CRSP/Compustat/IBES 쪽입니다.
- yfinance 경로는 임시 테스트용입니다.
- yfinance는 현재 S&P 500 구성종목 기반이라 생존편향 문제가 있습니다.
- 그래서 prototype 결과를 최종 성과나 논문용 결과처럼 해석하면 안 됩니다.
- API 키는 `.env`에만 두고 커밋하지 않습니다.

## 현재 구현 상태와 로드맵

이 섹션은 DDQM 스타일 S&P 500 연구 파이프라인에서 이미 구현된 부분과 앞으로 구현해야 할 부분을 정리합니다. 현재 레포에는 보안 설정, 매크로 피처 workflow, WRDS 데이터 요구사항, WRDS 없는 prototype 경로가 준비되어 있고, 최종 WRDS loader와 factor database는 아직 구현해야 합니다.

### 지금 구현된 부분

| 영역 | 상태 | 기술적 내용 |
|---|---|---|
| 보안 설정 | 구현됨 | `.env.example`과 `src/autoquant_lab/config.py`로 FRED/WRDS credential을 코드 밖에서 관리합니다. |
| 매크로 피처 | 구현됨 | `scripts/build_macro_features.py`가 FRED/ALFRED/yfinance 기반 macro-market feature를 만들고, 검증/진단 스크립트가 품질을 확인합니다. |
| WRDS 준비 문서 | 구현됨 | `docs/` 아래에 CRSP, Compustat, IBES, CCM, manual export 요구사항이 정리되어 있습니다. |
| WRDS 접근 확인 | 구현됨 | `scripts/probe_wrds.py`로 WRDS schema와 대표 table 접근 가능 여부를 확인합니다. |
| 기존 임시 주식 데이터 경로 | 구현됨 | yfinance S&P 500 stock-level label, macro join, 검증, LightGBM smoke test 스크립트가 있습니다. 단순 연결 확인용이며 연구용이 아니라 prototype 전용입니다. |
| DDQM2-lite factor 경로 | 구현됨 | FRED/ALFRED macro feature와 yfinance 가격/거래량 데이터로 canonical price panel, factor score, factor long-short label, macro-factor model dataset, LightGBM artifact, 읽기 전용 Streamlit dashboard를 생성합니다. |
| 연구용 WRDS factor 경로 | 미구현 | CRSP/Compustat/IBES loader, point-in-time join, 연구용 생존편향 통제는 WRDS 접근 확보 후 구현해야 합니다. |

### 앞으로 구현해야 할 부분

| 우선순위 | 산출물 | 필요한 이유 |
|---|---|---|
| 1 | `crsp.msf`/`crsp.dsf`, `comp.funda`, `comp.fundq`, `comp.ccmxpf_lnkhist`, IBES Summary History, `wrdsapps.ibcrsphist` 추출 스크립트 | prototype 데이터를 WRDS 연구용 원천 데이터로 교체합니다. |
| 2 | WRDS 데이터베이스/staging schema | CRSP `PERMNO`, Compustat `GVKEY`, CCM link, IBES link, macro, factor, label을 분리하되 안전하게 join할 수 있게 합니다. |
| 3 | point-in-time 펀더멘털 파이프라인 | `datadate`만 쓰면 미래정보가 섞일 수 있으므로 `rdq` 또는 보수적 lag 기준으로 사용 가능일을 관리합니다. |
| 4 | 연구용 WRDS factor score builder | DDQM2-lite 공개 데이터 factor를 CRSP/Compustat/IBES point-in-time signal로 확장합니다. |
| 5 | 연구용 WRDS factor long-short return label | prototype yfinance/current-membership label을 CRSP 기반 factor-level target으로 교체합니다. |
| 6 | 연구용 rolling LightGBM 루프 | WRDS 기반 label로 macro-to-factor-return 실험, baseline, feature importance, out-of-sample 평가를 수행합니다. |

### 제안하는 WRDS 데이터베이스 구조

| 테이블 | 주요 키 | 역할 |
|---|---|---|
| `security_master` | `permno`, `permco`, `gvkey` | 종목/기업의 안정적인 historical mapping을 관리합니다. |
| `sp500_membership` | `permno`, `start_date`, `end_date` | 특정 시점의 S&P 500 universe를 관리합니다. |
| `crsp_monthly_returns` | `permno`, `date` | 수익률, 상장폐지 수익률, 가격, 거래량, 주식수, 시가총액을 저장합니다. |
| `compustat_fundamentals` | `gvkey`, `permno`, `available_date` | value, profitability, investment, leverage, cash-flow factor용 PIT 재무 데이터를 저장합니다. |
| `ibes_estimates` | `permno`, `estimate_date`, `fiscal_period` | consensus, dispersion, coverage, revision feature를 저장합니다. |
| `macro_features` | `date` | FRED/ALFRED macro 및 market-state feature를 저장합니다. |
| `factor_scores` | `permno`, `date`, `factor_name` | 포트폴리오 구성 전 cross-sectional factor 값을 저장합니다. |
| `factor_long_short_returns` | `date`, `factor_name` | DDQM식 long-short factor return label을 저장합니다. |
| `model_dataset` | `date`, `factor_name` | LightGBM 학습용 macro feature와 target factor return을 결합합니다. |

구현상 중요한 원칙은 ticker join을 피하는 것입니다. 최종 연구 경로는 CRSP `PERMNO`, Compustat `GVKEY`, CCM link history, IBES-CRSP link history, 그리고 명시적인 `available_date`를 기준으로 S&P 500 패널을 point-in-time 안전하게 만들어야 합니다.

## 설치 방법

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` 파일을 열어서 아래처럼 채웁니다.

```bash
FRED_API_KEY=본인_FRED_KEY
WRDS_USERNAME=본인_WRDS_ID
```

## 커밋/푸시 전 보안 확인

```bash
python scripts/scan_secrets.py
```

정상이라면 `.py` 또는 `.txt` 파일 안에 키가 없다고 나옵니다.

## 매크로 엑셀 확인

기본 검증:

```bash
python scripts/validate_macro_workbook.py expanded_macro_market_features.xlsx
```

품질 진단:

```bash
python scripts/diagnose_macro_feature_quality.py --top-n 5
```

여기서는 결측치, 중복 컬럼, 상관관계가 너무 높은 컬럼, 이상치, 하루 변화가 큰 구간 등을 확인합니다.

## 매크로 피처 다시 만들기

FRED 키가 `.env`에 들어있다면 아래 명령으로 매크로 피처를 다시 만들 수 있습니다.

```bash
PYTHONPATH=src python scripts/build_macro_features.py --output expanded_macro_market_features.xlsx
```

## WRDS 확인

WRDS 패키지와 계정이 준비되면 아래 명령으로 접근 가능 여부를 확인합니다.

```bash
PYTHONPATH=src python scripts/probe_wrds.py
```

WRDS 접속이 안 되면 아래 문서를 보면 됩니다.

```text
docs/wrds_manual_export_guide.md
```

전체 데이터 설명은 아래 문서에 있습니다.

```text
docs/ddqm2_sp500_data_inventory.md
```

## WRDS 없이 임시 파이프라인 돌리기

이 경로는 WRDS 접근 전까지 전체 흐름을 확인하기 위한 prototype 전용입니다.

### DDQM2-lite factor MVP

권장하는 WRDS-free prototype 경로입니다. FRED/ALFRED macro feature와 yfinance 가격/거래량 데이터를 사용해 DDQM 스타일 흐름을 최대한 비슷하게 구성합니다.

```text
yfinance canonical price panel
→ price/volume factor score
→ factor long-short return label
→ FRED/ALFRED macro-factor dataset
→ LightGBM baseline 및 experiment artifact
→ 읽기 전용 Streamlit dashboard
```

canonical yfinance price panel을 만듭니다.

```bash
PYTHONPATH=src python scripts/build_yfinance_price_panel.py \
  --tickers AAPL MSFT SPY \
  --start-date 2020-01-01 \
  --end-date 2020-06-30 \
  --output prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet
```

검증합니다.

```bash
PYTHONPATH=src python scripts/validate_yfinance_price_panel.py \
  prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet
```

가격/거래량 기반 factor score를 만듭니다.

```bash
PYTHONPATH=src python scripts/build_yfinance_factor_scores.py \
  --price-panel prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet \
  --output prototypes/yfinance_sp500/factor_scores_smoke.parquet \
  --smoke
```

factor score를 검증합니다.

```bash
PYTHONPATH=src python scripts/validate_factor_scores.py \
  prototypes/yfinance_sp500/factor_scores_smoke.parquet \
  --smoke
```

factor long-short return label을 만듭니다.

```bash
PYTHONPATH=src python scripts/build_factor_long_short_returns.py \
  --factor-scores prototypes/yfinance_sp500/factor_scores_smoke.parquet \
  --price-panel prototypes/yfinance_sp500/canonical_price_panel_smoke.parquet \
  --output prototypes/yfinance_sp500/factor_long_short_returns_smoke.parquet \
  --horizon-trading-days 21 \
  --smoke
```

factor label을 검증합니다.

```bash
PYTHONPATH=src python scripts/validate_factor_long_short_returns.py \
  prototypes/yfinance_sp500/factor_long_short_returns_smoke.parquet \
  --smoke
```

macro-factor model-ready dataset을 만듭니다.

```bash
PYTHONPATH=src python scripts/assemble_macro_factor_dataset.py \
  --factor-returns prototypes/yfinance_sp500/factor_long_short_returns_smoke.parquet \
  --macro-workbook expanded_macro_market_features.xlsx \
  --output prototypes/yfinance_sp500/macro_factor_model_ready_smoke.parquet
```

model-ready dataset을 검증합니다.

```bash
PYTHONPATH=src python scripts/validate_macro_factor_dataset.py \
  prototypes/yfinance_sp500/macro_factor_model_ready_smoke.parquet
```

macro-factor LightGBM baseline을 학습하고 experiment artifact를 저장합니다.

```bash
PYTHONPATH=src python scripts/train_macro_factor_lgbm_baseline.py \
  --input prototypes/yfinance_sp500/macro_factor_model_ready_smoke.parquet \
  --output-dir prototypes/yfinance_sp500/experiments/smoke_lgbm \
  --smoke
```

experiment artifact를 검증합니다.

```bash
PYTHONPATH=src python scripts/validate_macro_factor_experiment.py \
  prototypes/yfinance_sp500/experiments/smoke_lgbm
```

읽기 전용 dashboard를 엽니다.

```bash
PYTHONPATH=src streamlit run apps/ddqm2_lite_dashboard.py
```

dashboard는 생성된 artifact만 읽습니다. 데이터를 다운로드하거나, label을 다시 만들거나, 모델을 재학습하거나, experiment 파일을 수정하지 않습니다.

### DDQM2-lite artifact

| Artifact | 역할 |
|---|---|
| `canonical_price_panel_smoke.parquet` | WRDS 확장에 맞춘 canonical schema의 yfinance 가격/거래량 데이터입니다. |
| `factor_scores_smoke.parquet` | factor metadata를 포함한 가격/거래량 factor score입니다. |
| `factor_long_short_returns_smoke.parquet` | 월별 equal-weight factor long-short return label입니다. |
| `macro_factor_model_ready_smoke.parquet` | macro feature와 factor return target을 결합한 model-ready dataset입니다. |
| `experiments/smoke_lgbm/` | LightGBM config, metrics, prediction, feature importance, manifest를 저장합니다. |

### WRDS 확장 경로

이 MVP는 source adapter를 교체할 수 있도록 구성했습니다. 하위 factor, label, model, dashboard 로직은 yfinance raw column이 아니라 canonical artifact를 읽는 방식으로 유지합니다.

앞으로 WRDS adapter는 source layer만 교체하는 방향이 좋습니다.

```text
CRSP adapter → PERMNO/PERMCO와 delisting return을 포함한 canonical price/return panel
Compustat adapter → GVKEY/CCM link 기반 point-in-time fundamental feature
IBES adapter → IBES-CRSP link 기반 analyst revision/dispersion feature
```

이 교체 이후에도 입력 schema가 겹치는 factor-score, factor-label, macro-factor, LightGBM, dashboard layer는 재사용하는 것이 목표입니다.

### 기존 stock-level prototype

기존 stock-return prototype도 단순 연결 확인용으로 남겨두었습니다. 개별 종목 forward return을 예측하므로 factor long-short MVP보다 DDQM 구조와는 거리가 있습니다.

#### 1. yfinance로 S&P 500 라벨 만들기

```bash
PYTHONPATH=src python scripts/build_yfinance_sp500_labels.py \
  --start-date 2020-01-01 \
  --end-date 2020-03-31 \
  --max-tickers 10 \
  --horizon-days 5 \
  --output prototypes/yfinance_sp500/sp500_yfinance_labels_sample.csv
```

검증:

```bash
PYTHONPATH=src python scripts/validate_yfinance_sp500_labels.py \
  prototypes/yfinance_sp500/sp500_yfinance_labels_sample.csv \
  --label-column forward_return_5d
```

#### 2. yfinance 라벨에 매크로 피처 붙이기

```bash
PYTHONPATH=src python scripts/assemble_yfinance_macro_dataset.py \
  --labels prototypes/yfinance_sp500/sp500_yfinance_labels_sample.csv \
  --macro-workbook expanded_macro_market_features.xlsx \
  --output prototypes/yfinance_sp500/sp500_yfinance_macro_model_ready_sample.csv
```

검증:

```bash
PYTHONPATH=src python scripts/validate_yfinance_macro_dataset.py \
  prototypes/yfinance_sp500/sp500_yfinance_macro_model_ready_sample.csv \
  --label-column forward_return_5d
```

#### 3. LightGBM baseline 돌리기

```bash
PYTHONPATH=src python scripts/train_yfinance_macro_lgbm_baseline.py \
  --input prototypes/yfinance_sp500/sp500_yfinance_macro_model_ready_sample.csv \
  --label-column forward_return_5d \
  --valid-fraction 0.25 \
  --min-train-rows 20 \
  --min-valid-rows 5 \
  --n-estimators 50 \
  --early-stopping-rounds 10
```

이 스크립트는 LightGBM 결과를 두 가지 단순 기준과 비교합니다.

- `zero_return`: 항상 0% 수익률이라고 예측
- `train_mean_return`: 학습 구간 평균 수익률로 예측

이 결과는 모델 성능 결론이 아니라, 전체 파이프라인이 제대로 연결됐는지 확인하는 용도입니다.

## git 주의사항

커밋 전에 항상 확인합니다.

```bash
git status --short
python scripts/scan_secrets.py
```

커밋하지 말아야 할 것:

- `.env`
- API 키
- WRDS 원천 데이터
- 자동 생성된 prototype CSV/Parquet
- 승인되지 않은 큰 PDF/XLSX 파일
