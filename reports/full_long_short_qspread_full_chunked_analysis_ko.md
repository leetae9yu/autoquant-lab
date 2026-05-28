# Full-panel Long/Short QSpread ML 분석 리포트

작성일: 2026-05-28

영문 리포트: [`full_long_short_qspread_full_chunked_analysis_en.md`](full_long_short_qspread_full_chunked_analysis_en.md)

## 초록

이 리포트는 **2,082,485-row full-panel** DDQM2/EQR long/short QSpread 실행 결과를 정리한다. 기존 walk-forward OOS protocol을 유지했고, 로컬 prepared parquet artifact만 사용했으며, WRDS 접속이나 신규 raw data 수집은 하지 않았다. 실행 방식도 의도적으로 보수적이었다. Heavy experiment는 한 번에 하나씩만 돌렸고, OMX team/swarm 방식의 병렬 실험 실행은 사용하지 않았다.

핵심 결과는 full-panel long/short surface가 기존 DDQM2/EQR의 큰 결을 유지하면서 model ranking을 바꾼다는 점이다. Gross 기준 best row는 **Random Forest q=0.10**이며 CAGR 31.45%, MDD -34.86%, turnover 75.90%를 기록했다. LightGBM q=0.10과 Extra Trees q=0.10이 그 뒤를 따른다. 기존 1.25M date-balanced anchor와 비교해도 best full-panel row는 약해지지 않았고, 기존 q=0.20 CAGR(30.75%)보다 약간 높다.

다만 보수적인 cost/borrow/slippage/tax proxy를 넣으면 해석은 크게 달라진다. Transaction cost 25 bps, annual borrow 150 bps, slippage 10 bps, positive post-cost monthly return에 대한 40.8% 단순 tax proxy를 적용하면 Random Forest q=0.10이 여전히 tested candidate 중 1위지만 누적수익은 크게 압축된다. 이는 research diagnostic이지 production execution model, 투자 조언, 세무 조언이 아니다.

## 1. 연구 질문

직전 long-only branch는 short leg의 중요성을 보여주었다. Long-only version은 informative했지만 drawdown과 strategy-quality 측면에서 더 약했다. 따라서 다음 질문은 다음과 같다.

> 기존 long/short QSpread construction을 복원하고, 로컬 2.08M-row full panel을 쓰면 여러 ML model family가 DDQM2/EQR 결과의 큰 결을 유지하는가, 아니면 바꾸는가?

이 리포트는 baseline mean, ridge, elasticnet, LightGBM, random forest, extra trees의 여섯 CPU-friendly model family에 대해 답한다.

## 2. 데이터 경계와 protocol

- Data boundary: `local_artifacts_only_no_wrds_login_no_runtime_external_data`.
- Input feature directory: `experiments/prepared/features_full_chunked/`.
- Prepared rows: 2,082,485.
- Portfolio surface: `stock_score_qspread_ddqm2`.
- Evaluation mode: `walk_forward`.
- Walk-forward test block: 12개월.
- Walk-forward validation block: 12개월.
- Factor-score chunking: 12 formation dates per part.
- Execution policy: heavy run은 한 번에 하나씩; team/swarm 병렬 실험 실행 없음.

이번 run은 additive이다. 기존 DDQM/DDQM2/EQR report나 long-only report를 덮어쓰지 않는다.

## 3. 실험 타임라인

1. 기존 1.25M date-balanced DDQM2 report가 long/short comparison anchor를 제공했다.
2. Long-only full-panel branch를 통해 short leg를 제거했을 때 무엇이 남는지 확인했다.
3. Long/short stock-score QSpread backtest가 factor-score chunk를 streaming 방식으로 처리하도록 하네스를 확장했다.
4. 여섯 model family × q=0.10, q=0.20, q=0.30으로 총 18개 full-panel matrix run을 순차 실행했다.
5. 18개 run 모두 ledger failure 없이 완료했다.
6. 완료된 local artifact에서 compact report, CSV matrix, sensitivity CSV, 본 narrative report를 생성했다.

## 4. Gross matrix evidence

### 4.1 Gross 기준 top rows

| Model | q | Gross cumulative | Gross CAGR | MDD | Turnover |
| --- | --- | --- | --- | --- | --- |
| random_forest | 0.100 | 6173.304 | 31.45% | -34.86% | 75.90% |
| lightgbm | 0.100 | 4932.484 | 30.53% | -32.68% | 76.86% |
| extra_trees | 0.100 | 4605.148 | 30.25% | -36.42% | 76.25% |
| elasticnet | 0.100 | 1942.770 | 26.78% | -36.46% | 73.81% |
| ridge | 0.100 | 1107.005 | 24.56% | -45.68% | 73.99% |
| baseline_mean | 0.100 | 1002.888 | 24.18% | -36.51% | 77.44% |

### 4.2 Model별 best q

| Model | Best q | Gross CAGR | MDD | Turnover |
| --- | --- | --- | --- | --- |
| random_forest | 0.100 | 31.45% | -34.86% | 75.90% |
| lightgbm | 0.100 | 30.53% | -32.68% | 76.86% |
| extra_trees | 0.100 | 30.25% | -36.42% | 76.25% |
| elasticnet | 0.100 | 26.78% | -36.46% | 73.81% |
| ridge | 0.100 | 24.56% | -45.68% | 73.99% |
| baseline_mean | 0.100 | 24.18% | -36.51% | 77.44% |

### 4.3 Quantile robustness

| q | Best model | Mean CAGR | Max CAGR | Mean MDD | Mean turnover |
| --- | --- | --- | --- | --- | --- |
| 0.100 | random_forest | 27.96% | 31.45% | -37.10% | 75.71% |
| 0.200 | random_forest | 18.58% | 23.52% | -36.95% | 63.01% |
| 0.300 | random_forest | 11.31% | 14.74% | -35.18% | 33.36% |

해석: long/short를 복원하면 q=0.10이 gross-return leader가 된다. q=0.20과 q=0.30은 일부 row에서 turnover와 drawdown을 낮추지만 gross CAGR도 크게 낮춘다. 따라서 long-only branch와 달리, short leg가 있는 decile-style QSpread가 다시 가장 강한 gross research surface로 나타난다.

## 5. Cost, borrow, slippage, tax-proxy sensitivity

Sensitivity layer는 단순화된 proxy이다. Transaction cost와 slippage는 long turnover + short turnover에 부과하고, borrow는 monthly short-notional drag로 처리하며, tax는 positive post-cost monthly return에 대한 단순 proxy로 처리한다. 이는 tax-lot accounting이 아니며 세무 조언도 아니다.

### 5.1 Conservative proxy: cost 25 bps, borrow 150 bps, slippage 10 bps, tax proxy 40.8%

| Model | q | Net cumulative | Mean monthly net | MDD | Mean tax proxy drag |
| --- | --- | --- | --- | --- | --- |
| random_forest | 0.100 | 4.880 | 0.58% | -47.34% | 1.29% |
| lightgbm | 0.100 | 3.482 | 0.52% | -54.48% | 1.30% |
| extra_trees | 0.100 | 3.349 | 0.51% | -60.28% | 1.29% |
| random_forest | 0.200 | 2.410 | 0.38% | -40.37% | 0.93% |
| elasticnet | 0.100 | 1.759 | 0.37% | -44.54% | 1.19% |
| extra_trees | 0.200 | 0.914 | 0.24% | -48.38% | 0.92% |
| lightgbm | 0.200 | 0.909 | 0.24% | -42.31% | 0.92% |
| ridge | 0.100 | 0.679 | 0.25% | -71.59% | 1.17% |

### 5.2 같은 trading assumption에서 tax proxy 제외

| Model | q | Pre-tax net cumulative | Mean monthly net | MDD |
| --- | --- | --- | --- | --- |
| random_forest | 0.100 | 521.418 | 1.88% | -38.03% |
| lightgbm | 0.100 | 404.721 | 1.83% | -35.87% |
| extra_trees | 0.100 | 384.032 | 1.80% | -39.59% |
| elasticnet | 0.100 | 171.409 | 1.57% | -42.38% |
| random_forest | 0.200 | 96.817 | 1.31% | -38.25% |
| ridge | 0.100 | 96.591 | 1.42% | -55.95% |

### 5.3 Severe proxy: cost 50 bps, borrow 300 bps, slippage 25 bps, tax proxy 40.8%

| Model | q | Severe net cumulative | Mean monthly net | MDD |
| --- | --- | --- | --- | --- |
| random_forest | 0.100 | -0.328 | 0.02% | -74.95% |
| random_forest | 0.200 | -0.483 | -0.11% | -61.38% |
| lightgbm | 0.100 | -0.512 | -0.05% | -78.71% |
| extra_trees | 0.100 | -0.515 | -0.06% | -81.31% |
| random_forest | 0.300 | -0.627 | -0.20% | -66.94% |
| elasticnet | 0.100 | -0.680 | -0.18% | -84.91% |

해석: long/short surface는 moderate friction에서도 여전히 흥미롭지만, gross와 conservative proxy return의 차이는 매우 크다. 따라서 DDQM/EQR식 결론은 유지된다. 이 결과는 research backtest이며, 경제적 해석은 execution, borrow, capacity, tax assumption에 크게 의존한다.

## 6. Model/factor diagnostics

### 6.1 Leading rows의 top factors

| Model | q | Top mean-weight factors |
| --- | --- | --- |
| random_forest | 0.100 | size_local_small_size, reversal_local_ma_gap_1m, reversal_local_price_reversal_1m |
| lightgbm | 0.100 | size_local_small_size, reversal_local_ma_gap_1m, reversal_local_price_reversal_1m |
| extra_trees | 0.100 | size_local_small_size, reversal_local_ma_gap_1m, reversal_local_price_reversal_1m |
| elasticnet | 0.100 | size_local_small_size, reversal_local_ma_gap_1m, reversal_local_price_reversal_1m |
| ridge | 0.100 | size_local_small_size, reversal_local_ma_gap_1m, reversal_local_price_reversal_1m |
| baseline_mean | 0.100 | reversal_local_ma_gap_1m, reversal_local_price_reversal_1m, size_local_small_size |

### 6.2 q=0.10 factor-family weight mass by model

| Model | Earn | Quality | Reversal | Size | Value |
| --- | --- | --- | --- | --- | --- |
| baseline_mean | 0.154 | 0.177 | 0.349 | 0.149 | 0.193 |
| elasticnet | 0.278 | 0.176 | 0.266 | 0.157 | 0.163 |
| extra_trees | 0.208 | 0.191 | 0.289 | 0.147 | 0.191 |
| lightgbm | 0.231 | 0.189 | 0.297 | 0.153 | 0.154 |
| random_forest | 0.209 | 0.183 | 0.285 | 0.162 | 0.188 |
| ridge | 0.275 | 0.157 | 0.285 | 0.149 | 0.171 |

모델들이 완전히 서로 다른 factor world를 발견한 것은 아니다. High-gross q=0.10 row 전반에서 size, reversal, value, quality, earnings 계열 factor가 반복된다. Tree model들은 size/reversal core를 유지하면서 realized ranking을 더 잘 잡아 linear model보다 gross 기준 우위에 선 것으로 보인다. 다만 이는 model-dependent factor emphasis의 증거이지, 특정 factor family의 영구적 우월성에 대한 causal proof는 아니다.

## 7. Drawdown과 stress-window diagnosis

Gross 기준 best run인 Random Forest q=0.10도 MDD가 -34.86%로 작지 않다. Worst month와 annual profile은 누적성과가 강해도 stress-window loss가 사라지는 것은 아님을 보여준다.

### 7.1 Random Forest q=0.10 worst months

| Formation date | Return | Turnover | Long turnover | Short turnover |
| --- | --- | --- | --- | --- |
| 2000-01-31 00:00:00 | -27.72% | 74.96% | 77.40% | 72.52% |
| 1999-11-30 00:00:00 | -18.24% | 77.09% | 78.45% | 75.72% |
| 2000-10-31 00:00:00 | -10.35% | 82.81% | 79.53% | 86.09% |
| 2001-02-28 00:00:00 | -10.32% | 92.05% | 91.07% | 93.02% |
| 1997-11-28 00:00:00 | -9.13% | 77.24% | 74.25% | 80.22% |

### 7.2 약한 연도

| Year | Annual return | Mean turnover |
| --- | --- | --- |
| 2014 | -17.99% | 66.83% |
| 2023 | -11.99% | 78.18% |
| 2017 | -7.95% | 67.84% |
| 2011 | 8.62% | 63.78% |
| 2007 | 9.92% | 75.82% |

### 7.3 강한 연도

| Year | Annual return | Mean turnover |
| --- | --- | --- |
| 2020 | 151.11% | 62.62% |
| 2009 | 141.15% | 72.16% |
| 2001 | 106.12% | 82.42% |
| 1998 | 83.04% | 79.72% |
| 2002 | 76.32% | 84.15% |

해석: long/short construction은 일부 설정에서 long-only branch보다 drawdown 방어에 도움이 되지만, free hedge는 아니다. Full-panel best row 역시 큰 월간 손실과 높은 turnover를 가진다.

## 8. 1.25M date-balanced anchor와의 관계

기존 source-controlled 1.25M date-balanced anchor는 다음을 기록했다.

- q=0.20: cumulative 5202.0665, implied CAGR 30.75%, MDD -36.02%.
- q=0.30: cumulative 4366.4377, implied CAGR 30.03%, MDD -35.71%.

Full-panel best row는 cumulative 6173.3037, CAGR 31.45%, MDD -34.86%이다. 따라서 local full panel로 확장해도 기존 연구 결과가 크게 붕괴하지 않았다. 오히려 기존 DDQM/EQR long/short shape가 1.25M date-balanced cap의 산물만은 아니었다는 쪽의 evidence가 된다.

단, full-panel best row는 q=0.10이고 prior anchor는 q=0.20/q=0.30을 강조했다. 따라서 apples-to-apples 비교는 best hyperparameter의 완전한 일치가 아니라, broad shape의 robustness로 해석해야 한다.

## 9. Reproducibility ledger

- Matrix report: [`full_long_short_qspread_full_chunked_report.md`](full_long_short_qspread_full_chunked_report.md).
- Matrix CSV: [`full_long_short_qspread_full_chunked_report.csv`](full_long_short_qspread_full_chunked_report.csv).
- Sensitivity CSV: [`full_long_short_qspread_full_chunked_report_sensitivity.csv`](full_long_short_qspread_full_chunked_report_sensitivity.csv).
- Ledger: [`full_long_short_qspread_full_chunked_ledger.json`](full_long_short_qspread_full_chunked_ledger.json).
- Local run root: `experiments/ddqm2_full_long_short/`.
- Run count: 18.
- Failures: 0.

## 10. 한계와 다음 실험

1. Cost/borrow/slippage/tax sensitivity는 proxy이며 production execution model이 아니다.
2. Tax proxy는 특정 국가/개인의 세무 조언이 아니고 tax-lot accounting도 아니다.
3. Capacity, liquidity, short availability, financing, market impact는 아직 완전하게 모델링하지 않았다.
4. Full anchor grid가 완료되었고 failure가 없으며 model/q evidence가 충분했기 때문에 hyperparameter probe는 이번 stop trigger 이후로 미뤘다.
5. Model objective는 factor return forecast이며, net-after-cost utility를 직접 최적화하지 않는다.

다음 작업은 additive하게 분리하는 것이 좋다. q=0.10/q=0.20 주변 q-neighborhood probe, conservative tree hyperparameter probe, drawdown-focused diagnostics, equal-turnover comparison layer가 우선 후보이다.

## 11. 결론

완료된 full-panel long/short run은 long-only branch보다 기존 DDQM/DDQM2/EQR 방향을 더 강하게 지지한다. Short leg는 연구 결과의 핵심으로 보인다. Gross 기준 best tested row는 Random Forest q=0.10이고, LightGBM 및 Extra Trees가 tree-model confirmation을 제공한다. 그러나 conservative proxy friction을 넣으면 결과는 크게 압축된다. 따라서 방어 가능한 결론은 production strategy가 준비되었다는 것이 아니라, full local panel에서도 의미 있는 long/short QSpread research signal이 남아 있으며 cost-aware/drawdown-aware 후속 연구 가치가 있다는 것이다.
