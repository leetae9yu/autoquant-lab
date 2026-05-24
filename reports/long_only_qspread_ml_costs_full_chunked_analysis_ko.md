# Long-only QSpread ML 비용/세금 분석 리포트

작성일: 2026-05-24
저장소: `autoquant-lab`
주요 ledger: [`long_only_qspread_ml_costs_full_chunked_ledger.json`](long_only_qspread_ml_costs_full_chunked_ledger.json)
영문 원본: [`long_only_qspread_ml_costs_full_chunked_analysis_en.md`](long_only_qspread_ml_costs_full_chunked_analysis_en.md)

## 요약

이 리포트는 기존 DDQM2 long/short 결과를 보존한 상태에서, 더 보수적인 **long-only stock-score QSpread** surface를 추가로 평가한 결과를 정리한다. 실험은 기존 로컬 DDQM2/EQR 연구 하네스를 유지하되, 새로운 short-leg 최적화는 하지 않고 top-`q` equal-weight, fully-invested long portfolio를 여러 CPU-friendly ML 모델로 비교했다.

실험은 **로컬 parquet artifact만** 사용했다. WRDS 로그인, 외부 데이터 다운로드, 신규 raw data 취득은 수행하지 않았다.

핵심 결과는 다음과 같다.

1. **보수적 net 기준에서는 모든 모델에서 q=0.30이 우세했다.** 더 넓은 top basket이 turnover를 낮추고, 그 결과 거래비용/세금 proxy drag를 줄여 q=0.10과 q=0.20보다 좋은 결과를 냈다.
2. **net과 gross의 차이가 핵심 결과다.** q=0.10은 gross cumulative return이 매우 크지만 turnover가 높아 보수적 net 관점에서는 매력이 크게 줄어든다.
3. **이번 matrix의 net 기준 1위는 baseline-mean 모델이다.** 이것을 “ML이 쓸모없다”로 해석하면 안 된다. 첫 번째 net lens가 낮은 turnover와 안정적인 factor exposure를 강하게 보상한다는 증거이며, 모델 edge는 gross return만이 아니라 turnover, drawdown, factor concentration과 함께 봐야 한다는 뜻이다.
4. **Tree model의 진단 가치는 여전히 크다.** Extra Trees와 Random Forest가 q=0.30에서 baseline을 제외한 가장 강한 net 결과를 보였고, LightGBM은 ML 모델 중 q=0.30 gross가 가장 높다. 이 차이는 각 모델이 어떤 factor family를 잡는지 해석하는 데 유용하다.
5. **이 결과는 연구용 backtest이지 trading strategy가 아니다.** Slippage, tax, capacity는 단순화된 proxy로만 반영했으며, 투자/세무/법률 조언이 아니다.

## 범위와 보존 원칙

이번 실험은 additive이다.

- 기존 DDQM2 matrix report는 비교 기준으로 유지한다.
  - [`usa_ddqm2_matrix_report_en.md`](usa_ddqm2_matrix_report_en.md)
  - [`usa_ddqm2_matrix_report_ko.md`](usa_ddqm2_matrix_report_ko.md)
- 기존 generated experiment directory는 덮어쓰지 않았다.
- 새 run artifact는 `experiments/ddqm2_long_only_full_chunked/` 아래에 생성했고 git에서는 계속 ignore한다.
- source-controlled deliverable은 코드, ledger/report 요약, 문서로 제한했다.

## 데이터와 하네스

| 항목 | 값 |
|---|---:|
| 로컬 feature directory | `experiments/prepared/features_full_chunked` |
| Full label panel rows | 2,082,485 |
| Feature count | 159 |
| Feature partitions | 35 |
| 월별 커버리지 | 1990-01 ~ 2024-12 |
| Matrix portfolio periods | 383 |
| Models | LightGBM, ridge, elasticnet, random forest, extra trees, baseline mean |
| Quantiles | q=0.10, q=0.20, q=0.30 |
| Matrix runs | 18 |
| Failures | 0 |

메모리 안전 하네스는 feature와 factor-score 생성을 월/date chunk 단위로 수행한다. 전체 stock-factor score row를 한 번에 materialize하지 않기 때문에, 2 OCPU / 12 GB급 환경에서도 2.08M-row panel을 실행할 수 있다.

## 포트폴리오와 비용 가정

Portfolio construction은 다음과 같다.

- weighted DDQM2/EQR factor prediction으로 stock score를 만든다.
- 매월 top `q` stock을 선택한다.
- 선택된 long-only basket을 equal-weight한다.
- fully invested 상태를 유지한다.
- 매월 리밸런싱한다.
- 다음 달 forward return으로 평가한다.

Primary conservative net assumptions:

| 가정 | 값 |
|---|---:|
| One-way turnover transaction cost | 50 bps |
| Simplified tax drag | 40.8% |
| Tax proxy | positive monthly gain × turnover × tax rate |
| 해석 | 연구용 sensitivity일 뿐, 세무 조언 아님 |

## 모델별 best-q 요약

| 순위 | 모델 | Best q | Net cumulative | Gross cumulative | Max drawdown | Turnover | 해석 |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | baseline_mean | 0.30 | 51.322593 | 142.832212 | -0.599271 | 0.159131 | 가장 높은 net. 안정적인 low-turnover factor mix의 효과일 가능성. |
| 2 | extra_trees | 0.30 | 28.048746 | 269.394256 | -0.584286 | 0.352090 | baseline 제외 최고 net. quality/value 진단이 강함. |
| 3 | random_forest | 0.30 | 25.395444 | 289.516978 | -0.600565 | 0.370048 | Extra Trees와 유사하나 drawdown/turnover가 약간 높음. |
| 4 | lightgbm | 0.30 | 21.895557 | 299.617899 | -0.584324 | 0.415116 | ML 모델 중 gross가 강하지만 turnover drag도 큼. |
| 5 | elasticnet | 0.30 | 13.087143 | 180.803946 | -0.629269 | 0.421751 | Linear sparse/dense 구조 비교군으로 유용. |
| 6 | ridge | 0.30 | 7.595449 | 100.998272 | -0.614620 | 0.400174 | net은 낮지만 q=0.30 robustness는 확인. |

## Quantile robustness

q-axis가 가장 명확한 robustness 결과다. 보수적 net 정의에서는 여섯 모델 family 모두 q=0.30이 이겼다.

| Model | q=0.10 net | q=0.20 net | q=0.30 net | q=0.30 turnover |
|---|---:|---:|---:|---:|
| lightgbm | 6.034166 | 4.048132 | 21.895557 | 0.415116 |
| ridge | 2.726859 | 1.521176 | 7.595449 | 0.400174 |
| elasticnet | 4.859060 | 4.185112 | 13.087143 | 0.421751 |
| random_forest | 8.496163 | 5.410548 | 25.395444 | 0.370048 |
| extra_trees | 6.963795 | 5.032797 | 28.048746 | 0.352090 |
| baseline_mean | 2.135122 | 1.725806 | 51.322593 | 0.159131 |

이 결과는 q=0.30이 전역 최적이라는 증거가 아니다. 현재 로컬 artifact와 비용/세금 proxy에서는 더 넓은 basket이 좁고 turnover가 높은 basket보다 net-cost test를 더 잘 통과했다는 뜻이다.

## Factor/model diagnostics

상위 weighted factor 진단에는 다음 계열이 반복적으로 나타난다.

- size / small-size exposure
- short-horizon reversal 또는 moving-average gap factor
- net-income YoY 같은 quality factor
- forward price-to-book 및 relative price-to-book 같은 value factor

q=0.30에서 net이 강한 run들은 더 안정적인 quality/value mix와 낮은 turnover 쪽으로 이동하는 경향이 있다. 이는 비용/세금 결과와 일관된다. gross alpha가 커도 매월 selected basket을 과도하게 교체해야 한다면 net 관점에서는 불리하다.

## 기존 long/short DDQM2 결과와의 비교

기존 DDQM2 report는 long/short 비교 anchor로 유지한다. 이 리포트는 그것을 대체하는 것이 아니라 옆에 놓고 읽어야 한다.

이번 long-only matrix가 답하는 질문은 더 좁다.

> short optimization을 제거하고 long-only, fully invested, conservative cost/tax proxy net 기준으로 보면 어떤 q/model 조합이 여전히 흥미로운가?

이번 matrix의 답은 다음과 같다. q=0.30이 첫 번째 후속 surface이고, Extra Trees / Random Forest / LightGBM은 baseline-mean의 강한 low-turnover 결과와 비교할 만한 ML 후보이다.

## Reproducibility ledger

Source-controlled ledger:

- [`long_only_qspread_ml_costs_full_chunked_ledger.json`](long_only_qspread_ml_costs_full_chunked_ledger.json)
- [`long_only_qspread_ml_costs_full_chunked_report.csv`](long_only_qspread_ml_costs_full_chunked_report.csv)
- generated Korean matrix report: [`long_only_qspread_ml_costs_full_chunked_report.md`](long_only_qspread_ml_costs_full_chunked_report.md)

완료 run의 핵심 검증 증거:

```text
Matrix runs: 18
Failures: 0
Feature rows: 2,082,485
Feature chunks: 35
pytest: 153 passed, 54 warnings
Data boundary: local artifacts only; no WRDS login; no runtime external data
```

## 후속 해석을 위한 질문

사람이 판단해야 할 핵심 해석 여지는 다음과 같다.

1. baseline-mean q=0.30 결과는 진짜 low-turnover factor-allocation 결과인가, 아니면 ML objective에 turnover/cost-aware target을 명시적으로 넣어야 한다는 신호인가?
2. 다음 ML pass에서는 factor long/short return을 예측한 뒤 비용을 사후 적용하는 대신 net return을 직접 최적화해야 하는가?
3. q=0.30은 충분히 robust한가, 아니면 q=0.25/q=0.35와 sector/cap filter를 먼저 실험해야 하는가?
4. 경제적 스토리 관점에서 허용 가능한 factor family는 무엇인가: size/reversal, quality/value, 혹은 제한된 subset인가?
5. 더 엄격한 market impact, liquidity, tax-lot realism을 넣으면 높은 gross return 중 어느 정도가 사라질 가능성이 있는가?

## 한계

- 신규 raw data는 취득하지 않았다.
- Tax proxy는 의도적으로 단순화했고 보수적으로 둔 연구 가정이다. 세무 조언이 아니다.
- Slippage, market impact, borrow constraints, capacity, tax-lot accounting은 완전히 모델링하지 않았다.
- Generated experiment parquet artifact는 로컬에만 있고 git에서는 ignore한다.
- 이 실험은 research surface 평가이지 production trading system이 아니다.
