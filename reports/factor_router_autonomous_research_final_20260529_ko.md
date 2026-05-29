# 팩터 라우터 자율 연구 리포트

일자: 2026-05-29

영문 원본: [`factor_router_autonomous_research_final_20260529_en.md`](factor_router_autonomous_research_final_20260529_en.md)

소스 ledger: [`factor_router_autonomous_research_20260529T111620Z.json`](factor_router_autonomous_research_20260529T111620Z.json)

## 초록

이 리포트는 기존 DDQM2/EQR long/short QSpread 하네스 위에서 수행한 additive 자율 full-panel factor-router 실험 루프를 기록한다. 루프는 로컬 2,082,485-row prepared parquet artifact만 사용했고, walk-forward OOS 프로토콜을 유지했으며, heavy experiment는 항상 한 번에 하나씩만 실행했다. WRDS나 신규 raw data source에는 접속하지 않았고 기존 리포트도 덮어쓰지 않았다.

핵심 실증 결과는 factor-router 확장이 두 개의 유용한 frontier를 찾았다는 점이다. 첫째, baseline-mean local/global quota tuning에서는 defensive branch가 나왔다. **quota 1:12, q=0.40**은 gross CAGR **7.08%**와 함께 MDD **-17.14%**를 기록했다. 둘째, 모델 축을 바꾸자 훨씬 강한 sparse-linear branch가 나왔다. **ElasticNet, quota 3:10, q=0.20**은 gross cumulative **235.43**, CAGR **18.68%**, MDD **-21.20%**, turnover **61.29%**를 기록했다. 이후 인접 quota, category-cap, q=0.40 ElasticNet 확인 실험들은 이 frontier를 개선하지 못했다. 루프는 사용자가 정의한 규칙에 따라 완료된 non-progress hypothesis가 5개 연속 발생한 시점에서 중단했다.

모든 수치는 연구용 백테스트 진단이다. production trading, 투자, 법률, 세무 조언이 아니다.

## 1. 연구 질문

이전 full-panel long/short QSpread 리포트는 short leg를 복원하는 것이 중요하다는 점을 확인했다. 이번 루프의 후속 질문은 더 좁다:

> 기존 DDQM2/EQR walk-forward OOS 하네스 안에서, 신규 데이터나 WRDS 접속 없이 local/global factor routing, q variation, lightweight model variation만으로 return/drawdown/turnover frontier를 개선할 수 있는가?

## 2. 데이터 경계와 프로토콜

- 데이터 경계: 로컬 artifact만 사용; WRDS 로그인 없음; runtime external data 없음.
- 입력 feature directory: `experiments/prepared/features_full_chunked/`.
- Prepared rows: 2,082,485.
- Portfolio surface: `stock_score_qspread_ddqm2`.
- 평가 모드: walk-forward OOS.
- Walk-forward cadence: 12개월 test block, 12개월 validation block.
- Factor-score chunking: part당 12 formation dates.
- 실행 정책: heavy run은 한 번에 하나만; team/swarm 병렬 heavy run 없음.
- 종료 규칙: 명시적 사용자 stop, 완료된 non-progress hypothesis 5개 연속, 또는 디스크 여유 <= 2GB.

디스크 규칙은 발동하지 않았다. run 29 이후에도 7.6GB가 남아 있었고, heavy loop는 5개 연속 non-progress 규칙으로 중단됐다.

## 3. 실험 타임라인

1. Anchor run: baseline-mean selected 13-factor q=0.30 branch.
2. Selection surface: N=7, local-only, global-only, quota 6:7, category-cap=3.
3. q robustness: local-only 및 quota branch 주변에서 q=0.20, q=0.40 variant를 확인했다.
4. Quota sweep: local-heavy q=0.30 및 q=0.40 branch에서 4:9, 3:10, 2:11, 1:12를 확인했다.
5. Aggressive q=0.20 quota sweep: 3:10이 baseline-mean high-return quota frontier가 됐다.
6. Model-axis tests: 가장 강한 q=0.20 branch 위에서 ridge와 ElasticNet을 확인했다.
7. ElasticNet robustness: q=0.20/0.30/0.40 및 인접 quota/category-cap을 확인했다.
8. Stop: run 25-29에서 완료된 non-progress hypothesis가 5개 연속 발생했다.

## 4. Gross 기준 근거

### 4.1 Gross 상위 행

| branch | model | q | policy | quota | cum | CAGR | MDD | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| elasticnet-quota-3-10-q20-preserve-scores | elasticnet | 0.20 | quota | 3:10 | 235.434 | 18.68% | -21.20% | 61.29% |
| elasticnet-quota-4-9-q20-preserve-scores | elasticnet | 0.20 | quota | 4:9 | 234.435 | 18.66% | -21.55% | 61.08% |
| elasticnet-quota-2-11-q20-preserve-scores | elasticnet | 0.20 | quota | 2:11 | 221.749 | 18.46% | -21.43% | 61.13% |
| elasticnet-category-cap3-q20-preserve-scores | elasticnet | 0.20 | category_capped |  | 193.657 | 17.96% | -23.09% | 61.57% |
| quota-3-10-q20-preserve-scores | baseline_mean | 0.20 | quota | 3:10 | 95.020 | 15.37% | -39.27% | 64.72% |
| quota-4-9-q20-preserve-scores | baseline_mean | 0.20 | quota | 4:9 | 93.271 | 15.31% | -40.08% | 64.84% |
| quota-q20-min-weight-001-storage-light | baseline_mean | 0.20 | quota | 6:7 | 87.727 | 15.09% | -41.16% | 65.10% |
| quota-2-11-q20-preserve-scores | baseline_mean | 0.20 | quota | 2:11 | 87.516 | 15.08% | -40.79% | 64.52% |

### 4.2 최저 MDD 행

| branch | model | q | policy | quota | cum | CAGR | MDD | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| quota-1-12-q40-preserve-scores | baseline_mean | 0.40 | quota | 1:12 | 7.883 | 7.08% | -17.14% | 14.59% |
| elasticnet-quota-1-12-q40-preserve-scores | elasticnet | 0.40 | quota | 1:12 | 9.602 | 7.68% | -17.32% | 35.23% |
| elasticnet-quota-3-10-q40-preserve-scores | elasticnet | 0.40 | quota | 3:10 | 10.848 | 8.05% | -18.09% | 34.56% |
| elasticnet-quota-2-11-q40-preserve-scores | elasticnet | 0.40 | quota | 2:11 | 10.424 | 7.93% | -18.20% | 34.90% |
| quota-2-11-q40-preserve-scores | baseline_mean | 0.40 | quota | 2:11 | 9.290 | 7.58% | -20.68% | 14.46% |
| elasticnet-quota-3-10-q20-preserve-scores | elasticnet | 0.20 | quota | 3:10 | 235.434 | 18.68% | -21.20% | 61.29% |
| elasticnet-quota-3-10-q30-preserve-scores | elasticnet | 0.30 | quota | 3:10 | 27.100 | 11.02% | -21.33% | 40.79% |
| elasticnet-quota-2-11-q20-preserve-scores | elasticnet | 0.20 | quota | 2:11 | 221.749 | 18.46% | -21.43% | 61.13% |

### 4.3 주요 frontier branch

| branch | model | q | policy | quota | cum | CAGR | MDD | turnover | HHI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| elasticnet-quota-3-10-q20-preserve-scores | elasticnet | 0.20 | quota | 3:10 | 235.434 | 18.68% | -21.20% | 61.29% | 0.199 |
| elasticnet-quota-4-9-q20-preserve-scores | elasticnet | 0.20 | quota | 4:9 | 234.435 | 18.66% | -21.55% | 61.08% | 0.200 |
| elasticnet-quota-3-10-q30-preserve-scores | elasticnet | 0.30 | quota | 3:10 | 27.100 | 11.02% | -21.33% | 40.79% | 0.242 |
| elasticnet-quota-3-10-q40-preserve-scores | elasticnet | 0.40 | quota | 3:10 | 10.848 | 8.05% | -18.09% | 34.56% | 0.242 |
| quota-1-12-q40-preserve-scores | baseline_mean | 0.40 | quota | 1:12 | 7.883 | 7.08% | -17.14% | 14.59% | 0.143 |
| quota-3-10-q20-preserve-scores | baseline_mean | 0.20 | quota | 3:10 | 95.020 | 15.37% | -39.27% | 64.72% | 0.096 |
| ridge-quota-3-10-q20-preserve-scores | ridge | 0.20 | quota | 3:10 | 78.040 | 14.67% | -38.36% | 60.61% | 0.196 |

해석: 탐색 결과 하나의 보편적 winner가 나온 것은 아니다. ElasticNet q=0.20 branch는 gross return을 지배하면서도 high-return branch 중에서는 비교적 완만한 MDD를 보인다. baseline q=0.40 1:12 branch는 defensive drawdown 측면에서 가장 강하지만 return은 낮다. Ridge는 gross leader라기보다 lower-turnover/lower-risk 모델 진단으로 유용하다.

## 5. 비용, 슬리피지, 대차비용, 세금 proxy 민감도

민감도 레이어는 의도적으로 단순하다. transaction cost와 slippage는 turnover에 부과하고, borrow는 short exposure에 월별 drag로 부과하며, 40.8% 단순 tax proxy는 비용 차감 후 양의 월별 수익에 적용한다. 이는 tax-lot accounting이 아니며 세무 조언도 아니다.

아래 conservative row는 25 bps transaction cost, 연 150 bps borrow, 10 bps slippage, 40.8% 단순 tax proxy를 사용한다.

| branch | model | q | quota | gross cum | pre-tax net cum | conservative net cum | conservative MDD | mean tax drag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| elasticnet-quota-3-10-q20-preserve-scores | elasticnet | 0.20 | 3:10 | 235.434 | 27.940 | 0.420 | -41.75% | 0.84% |
| elasticnet-quota-3-10-q40-preserve-scores | elasticnet | 0.40 | 3:10 | 10.848 | 1.922 | -0.519 | -56.90% | 0.49% |
| quota-1-12-q40-preserve-scores | baseline_mean | 0.40 | 1:12 | 7.883 | 2.737 | -0.219 | -40.36% | 0.42% |
| quota-3-10-q20-preserve-scores | baseline_mean | 0.20 | 3:10 | 95.020 | 9.677 | -0.299 | -61.03% | 0.76% |

해석: gross 기준 ElasticNet q=0.20은 매우 강하지만 conservative net 결과는 크게 압축된다. 생성된 sensitivity table에서 여전히 양의 conservative net cumulative를 보이므로 연구적으로는 중요하지만, 경제적 해석은 execution, borrow, turnover, capacity, tax assumption에 크게 의존한다.

## 6. 모델/팩터 진단

### ElasticNet quota 3:10 q=0.20

Top mean-weight factors:

| factor | scope | category | mean weight | holdout corr |
| --- | --- | --- | --- | --- |
| size_local_small_size | local | size_flow | 12.79% | 0.129 |
| quality_global_net_income_yoy | global | quality_growth | 12.74% | 0.033 |
| reversal_local_ma_gap_1m | local | reversal | 11.31% | 0.156 |
| reversal_local_price_reversal_1m | local | reversal | 11.31% | 0.156 |
| val_global_pb_fwd | global | valuation | 7.80% | 0.105 |
| val_global_relative_pb_industry_fwd | global | valuation | 7.80% | 0.105 |

Scope weight mass:

| scope | weight mass |
| --- | --- |
| local | 72.41% |
| global | 28.35% |

Category weight mass:

| category | weight mass |
| --- | --- |
| earnings | 29.89% |
| reversal | 22.62% |
| quality_growth | 19.85% |
| valuation | 15.61% |
| size_flow | 12.79% |


### Baseline quota 1:12 q=0.40

Top mean-weight factors:

| factor | scope | category | mean weight | holdout corr |
| --- | --- | --- | --- | --- |
| quality_global_net_income_yoy | global | quality_growth | 26.76% | 0.157 |
| quality_local_net_income_yoy | local | quality_growth | 19.94% | 0.146 |
| size_local_small_size | local | size_flow | 12.68% | -0.041 |
| earn_local_eps_fast_fy1_1m | local | earnings | 4.22% | -0.139 |
| earn_local_eps_fast_fy1_1m_voladj | local | earnings | 4.22% | -0.139 |
| earn_local_eps_fq1_1m | local | earnings | 4.22% | -0.139 |

Scope weight mass:

| scope | weight mass |
| --- | --- |
| local | 74.86% |
| global | 26.76% |

Category weight mass:

| category | weight mass |
| --- | --- |
| quality_growth | 46.70% |
| earnings | 42.25% |
| size_flow | 12.68% |


해석: ElasticNet high-return branch는 단순한 generic “local only” bet가 아니다. 선택된 3:10 quota는 global factor 3개를 유지하면서 local size, reversal, earnings, quality/value family를 강조한다. defensive baseline 1:12 branch는 global slot 1개를 stabilizer처럼 사용한다. pure local-only q=0.40의 drawdown이 훨씬 나빴기 때문에 이 global slot 1개는 진단적으로 의미가 있어 보인다.

## 7. Drawdown 진단

### Worst months: ElasticNet quota 3:10 q=0.20

| formation date | return | turnover | long turnover | short turnover |
| --- | --- | --- | --- | --- |
| 1999-11-30 00:00:00 | -12.68% | 67.34% | 72.53% | 62.14% |
| 2001-02-28 00:00:00 | -12.02% | 84.33% | 86.61% | 82.06% |
| 2000-10-31 00:00:00 | -9.17% | 76.33% | 74.69% | 77.97% |
| 2000-11-30 00:00:00 | -8.52% | 71.65% | 64.04% | 79.26% |
| 2015-06-30 00:00:00 | -8.29% | 61.82% | 57.14% | 66.49% |


### Worst months: baseline quota 1:12 q=0.40

| formation date | return | turnover | long turnover | short turnover |
| --- | --- | --- | --- | --- |
| 2002-10-31 00:00:00 | -7.92% | 12.85% | 13.81% | 11.90% |
| 1999-11-30 00:00:00 | -6.10% | 12.56% | 12.63% | 12.48% |
| 2022-06-30 00:00:00 | -4.99% | 11.90% | 12.38% | 11.41% |
| 2020-12-31 00:00:00 | -4.93% | 16.94% | 16.53% | 17.34% |
| 2000-01-31 00:00:00 | -4.88% | 9.13% | 9.02% | 9.25% |


high-return ElasticNet branch에도 stress-window 손실은 남아 있다. defensive branch는 MDD를 낮추지만 월별 손실 자체를 제거하지는 못한다. 따라서 이 결과는 strategy-quality claim이 아니라 research frontier로 보고하는 것이 적절하다.

## 8. 종료 규칙 감사

자율 루프는 완료된 non-progress hypothesis가 5개 연속 발생한 뒤 중단됐다:

- Run 25: ElasticNet 1:12 q=0.40 did not improve the sparse-linear defensive frontier.
- Run 26: ElasticNet 2:11 q=0.40 did not improve the sparse-linear defensive frontier.
- Run 27: ElasticNet 4:9 q=0.20 nearly tied but did not beat ElasticNet 3:10 q=0.20.
- Run 28: ElasticNet 2:11 q=0.20 did not beat ElasticNet 3:10 q=0.20.
- Run 29: ElasticNet category-cap=3 q=0.20 did not beat ElasticNet 3:10 q=0.20.

디스크 stop 조건은 발동하지 않았다. run 29 이후 7.6GB가 남아 있어 2GB threshold보다 높았다.

## 9. 한계

- 백테스트 전용이다. production execution, live portfolio router, 투자 조언이 아니다.
- 로컬 prepared data만 사용했다. 신규 raw data도 없고 WRDS validation도 수행하지 않았다.
- 비용/세금 proxy는 단순화된 것이며 세무 조언이 아니다.
- 주요 representative run의 factor-score artifact는 보존되어 이후 dashboard drilldown이 가능하지만, storage pressure는 계속 제약이다.
- ElasticNet q=0.20 결과는 매우 크기 때문에 더 강한 주장을 하기 전에 추가 robustness review가 필요하다.

## 10. 다음 연구 단계

1. representative run에 대해 보존된 `portfolio_returns`, `qspread_legs`, `factor_allocations`, `factor_diagnostics`, `factor_scores` 기반 dashboard를 구축한다.
2. ElasticNet q=0.20과 defensive q=0.40 branch의 worst month를 leg 및 factor family 단위로 비교한다.
3. storage-aware raw score catalog를 추가해 exploratory run은 bulky intermediate를 pruning하면서 dashboard-grade finalist는 보존한다.
4. 디스크가 더 확보되면 quota point를 더 늘리기보다 harness를 통해 ElasticNet hyperparameter profile을 테스트한다.
