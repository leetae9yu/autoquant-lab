# Long-only QSpread ML 비용/세금 분석 리포트 v2

작성일: 2026-05-24

영문 리포트: [`long_only_qspread_ml_costs_full_chunked_analysis_v2_en.md`](long_only_qspread_ml_costs_full_chunked_analysis_v2_en.md)

## 초록

이 v2 리포트는 기존 long-only QSpread 요약을 실험 리포트 수준의 서사로 확장한다. 기존 USA-DDQM2 long/short 작업에서 long-only, fully-invested stock-score QSpread matrix로 이어진 흐름을 기록하고, 완료된 로컬 run에서 어떤 산출물이 나왔는지 정리하며, 최종 결과에 대한 보수적 해석을 제시한다. 이 리포트는 새 실험을 추가하지 않고, WRDS에 접속하지 않으며, 신규 raw data를 취득하지 않는다. 사용한 근거는 이미 완료된 matrix CSV/ledger와 로컬 run directory이다.

핵심 경험적 결과는 **여섯 model family 모두에서 q=0.30이 conservative net 기준 가장 강한 surface**라는 점이다. 이것은 단순히 “basket을 넓히면 좋다”는 말이 아니다. 50 bps one-way turnover cost와 40.8% 단순 tax-drag proxy를 적용하면, 넓은 basket이 turnover를 낮추어 좁고 gross가 큰 q=0.10 variant보다 net 기준 우위에 선다는 뜻이다. baseline_mean q=0.30 run이 primary net cumulative return 기준 1위이고, Extra Trees, Random Forest, LightGBM이 주요 ML 비교군을 형성한다.

## 1. 배경과 문제 정의

기존 DDQM2 adaptation은 미국 주식시장 버전의 macro-to-factor-return 아이디어를 테스트했다. Macro/market information으로 factor return을 예측하고, 그 예측을 factor allocation으로 바꾼 뒤, stock-level QSpread portfolio를 평가하는 구조였다. 그 작업에서는 DDQM2-style long/short surface가 비교 기준이었다.

이번 질문은 더 좁고 보수적이다.

> Short leg를 제거하고, portfolio를 long-only fully invested로 강제하며, conservative net-of-cost lens로 평가하면 무엇이 여전히 흥미로운가?

Long/short research backtest와 long-only constrained portfolio는 다른 질문에 답한다. 전자는 directional spread efficacy를 보여줄 수 있고, 후자는 turnover friction을 인정한 뒤에도 ranking signal이 long-only selection surface로 남는지 본다.

## 2. 기존 DDQM2 리포트와의 관계

이 리포트는 additive이다. 기존 DDQM2 report를 대체하지 않는다.

- [`usa_ddqm2_matrix_report_en.md`](usa_ddqm2_matrix_report_en.md)
- [`usa_ddqm2_matrix_report_ko.md`](usa_ddqm2_matrix_report_ko.md)

기존 리포트는 long/short benchmark와 방법론적 배경으로 남는다. 이 v2 리포트는 같은 로컬 연구 환경과 보존 원칙 위에 long-only branch를 추가한다. Portfolio constraint가 다르고, net interpretation을 더 강조한다.

## 3. 실험 타임라인

1. **Baseline DDQM2/EQR adaptation.** 로컬 panel preparation, PIT feature construction, factor scoring, factor-return modeling, DDQM2-style QSpread report를 먼저 확립했다.
2. **Long-only reframing.** Short strategy를 추가 최적화하지 않고, top-q stock score만 사용해 equal-weight fully-invested long portfolio를 만들었다.
3. **Memory-safe full-panel path.** Full local panel은 2,082,485 rows와 159 features를 가진다. Feature preparation은 35개 partition으로 나누었고, factor-score generation/backtest는 chunk-aware하게 처리했다.
4. **Completed matrix.** 여섯 model family와 q=0.10, q=0.20, q=0.30 조합으로 18개 run을 돌렸고 failure는 0개였다.
5. **Report layer.** 첫 bilingual report는 결과를 요약했다. 이 v2 report는 그 요약을 interpretability/reproducibility appendix가 있는 실험 서사로 확장한다.

## 4. 데이터 경계와 공개 원칙

데이터 경계는 명시적이다: `local_artifacts_only_no_wrds_login_no_runtime_external_data`. Run은 local parquet artifact만 읽는다. WRDS login, external service call, 신규 raw data acquisition은 이 리포트 pass에 포함되지 않는다.

Source-controlled file은 문서와 compact report artifact로 제한한다. 대형 generated parquet output은 `experiments/` 아래 로컬에 남고 git에서는 계속 ignore한다.

## 5. Portfolio construction과 net assumptions

각 월마다 하네스는 predicted factor return과 selected factor score를 결합해 stock score를 만든다. Long-only surface는 top q fraction을 선택하고, 그 long basket을 equal-weight하며, fully invested 상태로 다음 달 forward return을 평가한다.

Primary net assumptions:

- Transaction cost: one-way turnover당 50.0 bps.
- Tax proxy: positive monthly gain × turnover에 40.8% 적용.
- Interpretation: 단순화된 research sensitivity이며 세무 조언이 아니다.

## 6. 주요 model/q matrix evidence

Matrix 자체가 이 리포트의 핵심 근거다. Conservative net 정의에서는 모든 model family가 q=0.30을 선호한다.

### 6.1 Model별 best-q 요약

| Rank | Model | Best q | Net cumulative | Gross cumulative | MDD | Turnover | Run ID |
|---|---|---|---|---|---|---|---|
| 1 | baseline_mean | 0.30 | 51.323 | 142.832 | -0.599 | 0.159 | longonly_full_chunked_20260524_baseline_mean_q30 |
| 2 | extra_trees | 0.30 | 28.049 | 269.394 | -0.584 | 0.352 | longonly_full_chunked_20260524_extra_trees_q30 |
| 3 | random_forest | 0.30 | 25.395 | 289.517 | -0.601 | 0.370 | longonly_full_chunked_20260524_random_forest_q30 |
| 4 | lightgbm | 0.30 | 21.896 | 299.618 | -0.584 | 0.415 | longonly_full_chunked_20260524_lightgbm_q30 |
| 5 | elasticnet | 0.30 | 13.087 | 180.804 | -0.629 | 0.422 | longonly_full_chunked_20260524_elasticnet_q30 |
| 6 | ridge | 0.30 | 7.595 | 100.998 | -0.615 | 0.400 | longonly_full_chunked_20260524_ridge_q30 |

### 6.2 Quantile-level summary

| q | Mean net | Median net | Max net | Mean gross | Mean turnover | Mean MDD | Mean tax drag | Mean trading drag |
|---|---|---|---|---|---|---|---|---|
| 0.10 | 5.203 | 5.447 | 8.496 | 3757.760 | 0.744 | -0.672 | 0.0146 | 0.0037 |
| 0.20 | 3.654 | 4.117 | 5.411 | 549.280 | 0.636 | -0.648 | 0.0101 | 0.0032 |
| 0.30 | 24.557 | 23.646 | 51.323 | 213.861 | 0.353 | -0.602 | 0.0043 | 0.0018 |

### 6.3 Full model/q matrix

| Model | q | Net cum | Gross cum | MDD | Turnover | Avg tax drag | Avg trading drag |
|---|---|---|---|---|---|---|---|
| lightgbm | 0.10 | 6.034 | 4425.7 | -0.663 | 0.757 | 0.0148 | 0.0038 |
| lightgbm | 0.20 | 4.048 | 616.4 | -0.642 | 0.649 | 0.0102 | 0.0032 |
| lightgbm | 0.30 | 21.896 | 299.6 | -0.584 | 0.415 | 0.0050 | 0.0021 |
| ridge | 0.10 | 2.727 | 1861.7 | -0.726 | 0.736 | 0.0142 | 0.0037 |
| ridge | 0.20 | 1.521 | 252.4 | -0.668 | 0.621 | 0.0098 | 0.0031 |
| ridge | 0.30 | 7.595 | 101.0 | -0.615 | 0.400 | 0.0048 | 0.0020 |
| elasticnet | 0.10 | 4.859 | 2830.4 | -0.660 | 0.736 | 0.0141 | 0.0037 |
| elasticnet | 0.20 | 4.185 | 516.6 | -0.648 | 0.624 | 0.0098 | 0.0031 |
| elasticnet | 0.30 | 13.087 | 180.8 | -0.629 | 0.422 | 0.0049 | 0.0021 |
| random_forest | 0.10 | 8.496 | 6332.0 | -0.644 | 0.742 | 0.0150 | 0.0037 |
| random_forest | 0.20 | 5.411 | 864.8 | -0.658 | 0.642 | 0.0105 | 0.0032 |
| random_forest | 0.30 | 25.395 | 289.5 | -0.601 | 0.370 | 0.0047 | 0.0019 |
| extra_trees | 0.10 | 6.964 | 5075.6 | -0.637 | 0.748 | 0.0149 | 0.0037 |
| extra_trees | 0.20 | 5.033 | 712.9 | -0.630 | 0.636 | 0.0102 | 0.0032 |
| extra_trees | 0.30 | 28.049 | 269.4 | -0.584 | 0.352 | 0.0044 | 0.0018 |
| baseline_mean | 0.10 | 2.135 | 2021.1 | -0.702 | 0.745 | 0.0149 | 0.0037 |
| baseline_mean | 0.20 | 1.726 | 332.7 | -0.642 | 0.643 | 0.0103 | 0.0032 |
| baseline_mean | 0.30 | 51.323 | 142.8 | -0.599 | 0.159 | 0.0020 | 0.0008 |

## 7. Cost/tax net 전환의 해석

Cost/tax lens는 실험 해석을 바꾼다. q=0.10 portfolio는 gross cumulative return이 매우 큰 경우가 많지만, 매월 selected basket을 더 많이 교체해야 한다. q=0.10의 mean turnover는 0.744이고, q=0.30에서는 0.353까지 내려간다. 이 turnover 감소가 q=0.30이 conservative net test를 통과하는 핵심 이유다.

Best net run인 `longonly_full_chunked_20260524_baseline_mean_q30`에서 primary sensitivity row는 50 bps 및 40.8% tax proxy 기준 cumulative return 51.323을 기록한다. 같은 50 bps cost에 tax proxy를 0으로 두면 sensitivity table의 cumulative return은 105.412이다. Tax proxy는 결과에 중요하지만, q=0.30 결과 전체를 설명하는 유일한 요인은 아니다.

해석은 다음과 같다. 이 실험은 production alpha의 증명이 아니라, ranking surface를 turnover, drawdown, friction assumption과 함께 평가해야 한다는 증거다. Gross가 높은 model도 basket churn이 과도하면 최고의 research candidate가 아닐 수 있다.

## 8. Factor/model interpretation

Run diagnostics의 top weighted factor string은 반복적으로 소수의 factor family를 가리킨다.

| Factor family | Top-factor appearances |
|---|---|
| quality | 25 |
| reversal | 24 |
| val | 19 |
| size | 18 |
| earn | 4 |

Evidence: quality, reversal, value, size exposure가 top weighted factors에 반복적으로 나타난다. Interpretation: long-only surface는 순수 black-box model contest가 아니다. 강한 run들은 quality/value stability, size exposure, short-horizon reversal의 혼합으로 설명될 여지가 있다. 이는 경제적으로 그럴듯하지만 아직 causal proof는 아니다.

## 9. Annual profile과 stress months

아래 annual profile은 primary net 기준 best run인 baseline_mean q=0.30을 구체적인 lens로 사용한다. Deployable strategy라고 주장하는 것이 아니라, low-turnover net result를 가장 잘 보여주는 run으로 보는 것이다.

### 9.1 Best net run의 강한 연도

| Year | Annual net | Mean turnover |
|---|---|---|
| 2003 | 93.1% | 0.166 |
| 2009 | 82.6% | 0.179 |
| 2020 | 44.5% | 0.194 |
| 2013 | 37.9% | 0.152 |
| 2016 | 35.7% | 0.136 |

### 9.2 Best net run의 약한 연도

| Year | Annual net | Mean turnover |
|---|---|---|
| 2008 | -43.7% | 0.143 |
| 2023 | -16.1% | 0.213 |
| 2007 | -14.7% | 0.128 |
| 2015 | -9.0% | 0.136 |
| 2022 | -8.8% | 0.175 |

### 9.3 Best net run의 worst monthly observations

| Formation date | Net return | Gross return | Turnover | Tax drag | Trading drag |
|---|---|---|---|---|---|
| 2020-02-28 00:00:00 | -25.8% | -25.7% | 0.138 | 0.0000 | 0.0007 |
| 2008-09-30 00:00:00 | -20.9% | -20.9% | 0.157 | 0.0000 | 0.0008 |
| 1998-07-31 00:00:00 | -18.8% | -18.7% | 0.135 | 0.0000 | 0.0007 |

Worst months에는 2008-09와 2020-02 같은 stress window가 포함된다. Long-only surface는 broad equity-market selloff에 노출되어 있으며, short leg 제거는 market risk 제거를 의미하지 않는다.

## 10. Reproducibility and harness appendix

- Feature directory: `experiments/prepared/features_full_chunked`.
- Output directory: `experiments/ddqm2_long_only_full_chunked`.
- Feature rows: 2,082,485.
- Feature count: 159.
- Feature partitions: 35.
- Matrix runs: 18.
- Matrix failures: 0.
- Ledger: [`long_only_qspread_ml_costs_full_chunked_ledger.json`](long_only_qspread_ml_costs_full_chunked_ledger.json).
- Matrix CSV: [`long_only_qspread_ml_costs_full_chunked_report.csv`](long_only_qspread_ml_costs_full_chunked_report.csv).

Harness detail은 primary research conclusion은 아니지만 full 2.08M-row run이 작은 메모리 환경에서 가능했던 이유를 설명한다. 이번 report pass는 실험을 다시 돌리지 않았고, 이미 완료된 artifact만 읽었다.

## 11. 한계와 다음 실험

1. **이번 pass에서는 새 robustness run을 하지 않았다.** q=0.25/q=0.35, alternative cost grids, additional model profiles는 future work이다.
2. **Tax proxy는 단순화되어 있다.** 40.8% 가정은 보수적 research proxy이지 세무 조언이나 tax-lot accounting이 아니다.
3. **Capacity model이 없다.** Slippage, market impact, liquidity constraints, capacity는 완전히 모델링하지 않았다.
4. **Model objective mismatch.** 모델은 factor return을 예측할 뿐 net-after-cost portfolio outcome을 직접 최적화하지 않는다.
5. **Baseline-mean surprise.** Best net run이 baseline_mean이라는 점은 stable low-turnover factor exposure의 가치를 보여줄 수 있지만, 동시에 ML objective를 cost-aware하게 바꿔야 한다는 신호일 수도 있다.

후속 실험은 별도 plan으로 분리하는 것이 맞다. Cost-aware objective, q-neighborhood robustness, liquidity/capacity filter, equal-turnover 조건의 model comparison이 자연스러운 다음 단계다.

## 12. 결론

이 실험은 DDQM2/EQR research story에 long-only branch를 추가한다. 핵심 결과는 deployable strategy를 찾았다는 것이 아니다. 더 좁고 방어 가능한 결론은 다음이다. Short leg를 제거하고 conservative friction을 부과하면 q=0.30이 테스트된 long-only surface 중 가장 robust하며, model 해석은 gross return 추격이 아니라 turnover-aware factor stability 중심으로 이동한다.
