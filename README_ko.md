# autoquant-lab

[English](README.md)

`autoquant-lab`는 DDQM2 아이디어를 미국 주식시장에 맞게 이식하기 위한 오프라인 리서치 하네스입니다. 로컬 연구 데이터에서 point-in-time 월별 주식 패널을 만들고, macro/market feature로 factor long-short return을 예측한 뒤, 예측값을 동적 factor allocation으로 바꿔 walk-forward OOS 포트폴리오를 평가합니다.

이 저장소는 **코드와 문서 스캐폴드만** 공개합니다. Raw WRDS-style dataset, credential, private research note, generated experiment artifact, vendor/reference PDF는 의도적으로 제외합니다.

## 무엇을 하는가

현재 하네스는 USA-version DDQM2 연구 루프를 지원합니다.

1. 로컬 offline artifact에서 월별 `(date, security)` 패널을 준비합니다.
2. point-in-time lag control이 적용된 feature family를 만듭니다.
3. EQR factor registry에서 stock-level factor score를 계산합니다.
4. factor score를 다음 달 factor long-short return으로 변환합니다.
5. factor return 예측을 위해 factor별 CPU-friendly model을 학습합니다.
6. 예측 factor return을 non-negative factor weight로 변환합니다.
7. 두 가지 surface를 평가합니다.
   - weighted factor-return portfolio
   - DDQM2-style stock-level weighted factor score QSpread portfolio
8. manifest, metric, report, reproducible run metadata를 로컬에 저장합니다.

이 프로젝트는 삼성증권 DDQM/DDQM2에서 영감을 받았지만, 한국시장 production setup의 직접 복제는 아닙니다. Universe, data source, macro feature, factor definition, evaluation protocol이 모두 미국시장 adaptation에 맞게 다릅니다.

## 현재 연구 축

현재 구현은 USA-DDQM2 축을 실제 실행 가능한 run으로 올려두었습니다.

- `selected_13_global_local`: 사용 가능한 factor registry에서 DDQM2-inspired 13-factor selection을 구성합니다.
- `ddqm2_25x3_us_macro`: current, short-direction, medium-direction style feature를 포함한 DDQM2 macro design의 U.S. adaptation입니다.
- `expanded_us_macro`: 로컬 artifact가 지원하는 추가 U.S. macro/market variable 확장 축입니다.
- `stock_score_qspread_ddqm2`: stock-level weighted factor score QSpread portfolio surface입니다.

Quantile `q`는 고정 default가 아니라 연구 축으로 둡니다.

- q=0.10은 DDQM2-reference decile construction입니다.
- q=0.20과 q=0.30은 더 넓고 분산된 leg를 보기 위한 U.S. adaptation 설정입니다.

## Panel cap과 full-panel run

기존 1.25M-row DDQM2 report는 `date-balanced` prepared-panel cap을
사용했습니다. 이 저장소에서 `date-balanced`는 **formation-date 기준 균등
row cap**을 의미합니다. 전체 cap을 월별 `formation_date`에 거의 균등하게
나누고, 남는 row는 date별 round-robin으로 배분합니다. 같은 월 안에서는
결정론적으로 `formation_date, permno` 순서를 따릅니다.

따라서 이 cap은 1990-2024 전체 연구 기간을 보존하지만,
sector-balanced, liquidity-balanced, market-cap-balanced는 아닙니다. Full
local artifact와 비교하면 월별 cross-section 구성이 달라질 수 있습니다.

Full-panel track은 기존 로컬 chunked artifact인
`experiments/prepared/features_full_chunked/`를 사용하며, prepared row 수는
2,082,485개입니다. Full-panel 실험도 별도로 다른 protocol이라고 명시하지
않는 한 source-controlled DDQM2 report와 같은 walk-forward OOS protocol을
유지해야 합니다.

최종 DDQM2 matrix report:

- [한국어 리포트](reports/usa_ddqm2_matrix_report_ko.md)
- [English report](reports/usa_ddqm2_matrix_report_en.md)

최신 additive long-only QSpread 분석:

- [English v2 analysis report](reports/long_only_qspread_ml_costs_full_chunked_analysis_v2_en.md)
- [한국어 v2 번역본](reports/long_only_qspread_ml_costs_full_chunked_analysis_v2_ko.md)
- 기존 v1 리포트: [English](reports/long_only_qspread_ml_costs_full_chunked_analysis_en.md), [한국어](reports/long_only_qspread_ml_costs_full_chunked_analysis_ko.md)
- [Reproducibility ledger](reports/long_only_qspread_ml_costs_full_chunked_ledger.json)

최신 additive full-panel long/short QSpread 분석:

- [English analysis report](reports/full_long_short_qspread_full_chunked_analysis_en.md)
- [한국어 번역본](reports/full_long_short_qspread_full_chunked_analysis_ko.md)
- [Matrix report](reports/full_long_short_qspread_full_chunked_report.md)
- [Reproducibility ledger](reports/full_long_short_qspread_full_chunked_ledger.json)

## Walk-forward timing과 리밸런싱

Portfolio surface는 월별입니다. 각 `formation_date`는 월별 리밸런싱 날짜이고, label은 `ret_1m_fwd`, 즉 다음 1개월 forward return입니다.

기본 full-run 설정에서는 다음처럼 동작합니다.

- portfolio weight는 매월 다시 계산합니다.
- long/short stock basket도 매월 다시 구성합니다.
- 각 월별 portfolio는 다음 1개월 수익률로 평가합니다.
- forecasting model은 12개월 walk-forward test fold마다 한 번 재학습합니다.

예를 들어 어떤 fold가 `2023-01`부터 `2023-12`까지를 test한다면, 모델은 그 test block 이전 날짜만 사용해 학습하고, 직전 validation block은 training에서 제외합니다. 즉 2023년 label로 학습한 뒤 2023년을 예측하는 구조가 아닙니다.

기본 구조는 다음과 같습니다.

```text
월별 포트폴리오 리밸런싱
+ 1개월 holding horizon
+ 12개월 단위 모델 재학습 cadence
```

더 엄격한 monthly-refit 실험을 원하면 test fold를 1개월로 설정합니다.

```bash
PYTHONPATH=src:. python scripts/eqr_run_ddqm2.py \
  --config configs/server_full.yaml \
  --evaluation-mode walk_forward \
  --walk-forward-test-periods 1 \
  --walk-forward-validation-periods 0
```

## Repository layout

```text
configs/                     안전한 YAML config와 ablation plan
scripts/                     preparation, validation, DDQM2 run, planning CLI
src/autoquant_lab/eqr/       메인 EQR package code
src/autoquant_lab/eqr/factors/DDQM2-style factor scoring, selection, allocation, backtest
tests/                       config, panel, factor, model, reporting 중심 테스트
reports/                     source-controlled final report only
```

Runtime/private directory는 ignore합니다.

```text
data/                        raw/local research data, WRDS/FRED-style export 포함, never committed
experiments/                 generated prepared panel과 run artifact
site/                        generated static report
.env                         credential/local setting
*.pdf, *.xlsx                local reference/data file
```

## 의도적으로 포함하지 않는 것

이 저장소에는 다음을 포함하지 않습니다.

- WRDS/CRSP/Compustat/IBES data
- FRED/macro source export 또는 vendor macro file
- `.env` file 또는 credential
- `EQR.md` 같은 private research note
- DDQM/DDQM2 PDF reference
- generated parquet experiment artifact
- generated static site output

이 파일들은 private local/server environment에서만 필요하며 `.gitignore`로 제외합니다.

## 주요 CLI 예시

DDQM2 ablation command를 실행하지 않고 렌더링만 합니다.

```bash
PYTHONPATH=src:. python scripts/eqr_plan_ddqm2_ablations.py --format commands --limit 8
```

이미 준비된 로컬 artifact에서 DDQM2-style experiment를 실행합니다.

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

이미 준비된 로컬 chunked artifact에서 additive long-only QSpread matrix를 실행합니다.

```bash
PYTHONPATH=src:. python scripts/eqr_run_long_only_matrix.py \
  --feature-dir experiments/prepared/features_full_chunked \
  --run-prefix longonly_full_chunked_YYYYMMDD \
  --output-dir experiments/ddqm2_long_only_full_chunked \
  --report reports/long_only_qspread_ml_costs_full_chunked_report.md \
  --ledger reports/long_only_qspread_ml_costs_full_chunked_ledger.json
```

이미 준비된 로컬 chunked artifact에서 additive full-panel long/short QSpread
matrix를 순차 실행합니다. 이 하네스는 메모리가 작은 환경을 위해
single-heavy-run-at-a-time으로 설계되어 있으며, 기존 manifest는 skip하고
로컬 run directory에서 compact report artifact를 다시 생성합니다.

```bash
PYTHONPATH=src:. python scripts/eqr_run_full_long_short_matrix.py \
  --run-prefix full_long_short_full_chunked_YYYYMMDD \
  --output-dir experiments/ddqm2_full_long_short \
  --report reports/full_long_short_qspread_full_chunked_report.md \
  --ledger reports/full_long_short_qspread_full_chunked_ledger.json
```

Focused test:

```bash
PYTHONPATH=src:. python -m pytest tests/test_ddqm2_ablation_plan.py tests/test_factors.py -q
```

## Research status

현재 저장소에는 세 계열의 source-controlled report가 있습니다.

1. **기존 USA-DDQM2 long/short matrix**
   - q=0.10, q=0.20, q=0.30 DDQM2-style stock-score QSpread run.
   - LightGBM, ridge, elasticnet, random forest, extra trees, baseline mean 모델 sweep.
   - Reports: [`usa_ddqm2_matrix_report_en.md`](reports/usa_ddqm2_matrix_report_en.md), [`usa_ddqm2_matrix_report_ko.md`](reports/usa_ddqm2_matrix_report_ko.md).
2. **Additive long-only QSpread cost/tax matrix**
   - Full local chunked panel: 2,082,485 rows, 159 features, 35 feature partitions.
   - 18개 run 성공: 여섯 model family × q=0.10, q=0.20, q=0.30.
   - Long-only top-q equal-weight fully invested construction이며, 신규 short optimization은 하지 않았습니다.
   - 보수적 primary net lens: one-way turnover cost 50 bps, positive monthly gain × turnover × 40.8% 단순 tax-drag proxy.
   - Reports: [`long_only_qspread_ml_costs_full_chunked_analysis_v2_en.md`](reports/long_only_qspread_ml_costs_full_chunked_analysis_v2_en.md), [`long_only_qspread_ml_costs_full_chunked_analysis_v2_ko.md`](reports/long_only_qspread_ml_costs_full_chunked_analysis_v2_ko.md). 기존 v1 리포트도 [`long_only_qspread_ml_costs_full_chunked_analysis_en.md`](reports/long_only_qspread_ml_costs_full_chunked_analysis_en.md), [`long_only_qspread_ml_costs_full_chunked_analysis_ko.md`](reports/long_only_qspread_ml_costs_full_chunked_analysis_ko.md)에 보존합니다.

최신 long-only v2 report의 headline 해석은 다음과 같습니다.

- q=0.30은 테스트한 모든 model family에서 net-cost 기준 가장 강한 surface입니다.
- baseline-mean q=0.30 run이 primary net cumulative return 기준 1위인데, 이는 보수적 net lens가 낮은 turnover와 안정적인 factor exposure를 강하게 보상하기 때문으로 해석해야 합니다.
- Extra Trees와 Random Forest는 q=0.30에서 baseline을 제외한 가장 강한 ML run이고, LightGBM은 gross 성과가 강하지만 turnover drag도 큽니다.
- 핵심 연구 결과는 gross headline 자체가 아니라 gross와 conservative net outcome 사이의 차이입니다.

3. **Additive full-panel long/short QSpread ML matrix**
   - Full local chunked panel: 2,082,485 prepared rows.
   - 18개 run 성공: 여섯 model family × q=0.10, q=0.20, q=0.30.
   - 순차 실행 정책: heavy run은 한 번에 하나씩; OMX team/swarm 병렬 실험 실행 없음.
   - DDQM2 report와 같은 walk-forward OOS protocol 유지.
   - Reports: [`full_long_short_qspread_full_chunked_analysis_en.md`](reports/full_long_short_qspread_full_chunked_analysis_en.md), [`full_long_short_qspread_full_chunked_analysis_ko.md`](reports/full_long_short_qspread_full_chunked_analysis_ko.md).

최신 full-panel long/short report의 headline 해석은 다음과 같습니다.

- Gross 기준 best row는 Random Forest q=0.10이며 CAGR 31.45%, MDD -34.86%, turnover 75.90%입니다.
- LightGBM q=0.10과 Extra Trees q=0.10이 tree-model 결과를 가깝게 확인합니다.
- 2.08M-row panel로 확장해도 기존 1.25M date-balanced DDQM2 shape가 붕괴하지 않았고, best full-panel row는 기존 q=0.20 CAGR anchor보다 약간 높습니다.
- Conservative cost/borrow/slippage/tax-proxy sensitivity를 넣으면 결과는 크게 압축되므로, 결론은 “production strategy 준비 완료”가 아니라 “후속 연구 가치가 있는 research signal이 남아 있다”입니다.

모든 결과는 research backtest입니다. Slippage, market impact, capacity, tax-lot accounting, borrow constraints, production tradability는 완전히 모델링하지 않았습니다. Tax proxy는 세무 조언이 아닙니다.

## Verification

Long-only QSpread completion에서 사용한 최근 검증:

```text
PYTHONPATH=src:. .venv/bin/python -m pytest -q
157 passed, 54 warnings

Full long-only matrix
18 runs, 0 failures
Data boundary: local artifacts only; no WRDS login; no runtime external data

Full long/short matrix
18 runs, 0 failures
Data boundary: local artifacts only; no WRDS login; no runtime external data
```

Full-data run에서는 partitioned feature preparation과 chunked factor-score generation을 사용해 매우 큰 score table을 한 번에 materialize하지 않습니다.

## Safety and publication policy

공개 전에는 private data가 tracked file에 들어가지 않았는지 확인합니다.

```bash
git ls-files data experiments site .env EQR.md '*.pdf' '*.xlsx'
```

예상 출력은 명시적으로 안전한 placeholder를 제외하면 비어 있어야 합니다.

## License / use

이 저장소는 research scaffold입니다. 투자 조언이 아니며, 바로 배포 가능한 trading strategy도 아닙니다.
