# V2 Final Paper: 1.25M DDQM2 Anchor에서 2.08M Full-Panel Factor-Router 연구까지

Date: 2026-05-30

**이 파일 하나를 보면 된다.** 이 문서는 기존 1.25M DDQM2 anchor, 2.08M full-panel long/short QSpread matrix, 그리고 factor-router 자율 연구 리포트를 하나로 합친 최종 V2 종합본이다.

근거 artifact:

- 1.25M anchor: [`usa_ddqm2_matrix_report_ko.md`](usa_ddqm2_matrix_report_ko.md), [`usa_ddqm2_matrix_report_en.md`](usa_ddqm2_matrix_report_en.md)
- 2.08M full-panel matrix: [`full_long_short_qspread_full_chunked_analysis_ko.md`](full_long_short_qspread_full_chunked_analysis_ko.md), [`full_long_short_qspread_full_chunked_analysis_en.md`](full_long_short_qspread_full_chunked_analysis_en.md)
- Full-panel ledger: [`full_long_short_qspread_full_chunked_ledger.json`](full_long_short_qspread_full_chunked_ledger.json)
- Factor-router final report: [`factor_router_autonomous_research_final_20260529_ko.md`](factor_router_autonomous_research_final_20260529_ko.md), [`factor_router_autonomous_research_final_20260529_en.md`](factor_router_autonomous_research_final_20260529_en.md)
- Factor-router autonomous ledger/log: [`factor_router_autonomous_research_20260529T111620Z.json`](factor_router_autonomous_research_20260529T111620Z.json), [`factor_router_autonomous_research_20260529T111620Z.md`](factor_router_autonomous_research_20260529T111620Z.md)
- V1 paper draft: [`full_run_research_paper_20260529_ko.md`](full_run_research_paper_20260529_ko.md), [`full_run_research_paper_20260529_en.md`](full_run_research_paper_20260529_en.md)

> **연구용 면책.** 본 문서는 source-controlled local report와 ledger를 종합한 연구 기록이다. Production trading guide, 투자 조언, 법률 조언, 세무 조언, 또는 backtest가 직접 tradable하다는 주장이 아니다. 이 V2 작성 과정에서 WRDS 로그인, 신규 raw data 수집, 외부 데이터 사용, cloud provisioning, 신규 실험 실행은 없었다.

## Abstract

본 연구는 DDQM/DDQM2 아이디어를 미국 주식 월별 패널에 이식하는 과정에서 나온 세 단계의 실험 기록을 종합한다. 첫째, 1.25M-row date-balanced DDQM2 anchor는 stock-level weighted factor-score QSpread long/short construction이 direct factor-return surface보다 훨씬 강하다는 초기 결을 만들었다. 둘째, 2,082,485-row full-panel long/short matrix는 이 결이 date-balanced cap에만 의존한 것이 아니라, 더 큰 local panel에서도 broad shape가 유지됨을 보였다. 셋째, factor-router 자율 연구 루프는 full-panel 결과를 바탕으로 local/global factor routing, q variation, quota policy, category cap, lightweight model variation을 순차적으로 탐색했다.

핵심 결과는 두 층으로 요약된다. Full-panel matrix에서는 Random Forest q=0.10이 cumulative return 6173.30, CAGR 31.45%, MDD -34.86%, turnover 75.90%로 가장 강한 gross row였다. Factor-router 루프에서는 ElasticNet quota 3:10 q=0.20이 cumulative return 235.43, CAGR 18.68%, MDD -21.20%, turnover 61.29%로 gross sparse-linear frontier를 형성했고, baseline quota 1:12 q=0.40은 MDD -17.14%, CAGR 7.08%, turnover 14.59%로 defensive frontier를 형성했다.

그러나 이 결과는 production strategy claim이 아니다. Full-panel 및 factor-router sensitivity는 transaction cost, slippage, borrow, simplified tax proxy를 반영하면 gross result가 크게 압축됨을 보여준다. 따라서 본 연구의 결론은 조심스럽다. 2.08M full data에서도 long/short factor construction의 gross research signal은 유지되었지만, 실전적 해석은 비용, turnover, borrow, capacity, tax treatment, factor-score attribution, robustness 검증에 의해 강하게 제약된다. AI agent 자율 연구 루프는 이 실험들을 더 체계적으로 반복하고 기록하게 해주었지만, 독립적인 방법론적 돌파구라기보다는 연구 하네스와 ledger discipline으로 이해해야 한다.

## 1. 연구 질문과 논문의 위치

이 논문은 하나의 새로운 실험 결과를 발표하기보다, 이미 완료된 full-run 연구 흐름을 하나의 읽을거리로 정리한다. 질문은 다음과 같다.

> 1.25M date-balanced DDQM2 실험에서 관찰된 stock-score QSpread long/short signal이 2.08M full-panel로 확장해도 유지되는가? 그리고 그 이후 factor-router 자율 연구는 어떤 return/drawdown/turnover frontier와 한계를 드러냈는가?

여기서 중요한 단어는 “유지”와 “확장”이다. 본 연구는 1.25M 실험과 2.08M 실험이 완전히 같은 표본, 같은 q, 같은 model ranking을 보였다고 주장하지 않는다. 대신 더 큰 local panel에서도 long/short stock-score QSpread라는 broad construction이 붕괴하지 않았고, 이후 routing 및 model variation을 통해 더 세분화된 frontier가 형성되었다고 본다.

본 문서의 서술 방식은 기존 리포트와 비슷한 report-style paper다. 형식적 학술 논문이라기보다, 실험 흐름, 수치, 해석, 한계, 다음 연구 방향을 한 문서에 모은 연구 기록에 가깝다.

## 2. Data Boundary와 Walk-Forward Protocol

모든 실험은 local artifact 경계 안에서 수행되었다. 공개 저장소에는 raw WRDS/CRSP/Compustat/IBES/FRED 데이터, credential, private note, generated parquet artifact, vendor/reference PDF가 포함되지 않는다. 본 V2 문서도 기존 source-controlled report와 ledger만 사용했다.

공통 원칙은 다음과 같다.

- WRDS 로그인 없음.
- 신규 raw data 없음.
- runtime external data 없음.
- 월별 formation date와 next-month forward return label 사용.
- Walk-forward OOS 평가 유지.
- Heavy run은 한 번에 하나씩만 실행.
- 기존 report/ledger를 덮어쓰지 않고 additive artifact로 남김.

실험 lineage는 다음과 같다.

| 단계 | 데이터/실험 | 목적 | 핵심 산출물 |
|---|---|---|---|
| 1 | 1.25M date-balanced DDQM2 anchor | U.S. adaptation에서 stock-score QSpread가 유효한지 확인 | `usa_ddqm2_matrix_report_*` |
| 2 | 2.08M full-panel long/short matrix | date-balanced cap을 넘어 full local chunked artifact에서도 결이 유지되는지 확인 | `full_long_short_qspread_full_chunked_analysis_*` |
| 3 | Factor-router autonomous loop | local/global quota, q, model, category cap 등 variation으로 frontier 탐색 | `factor_router_autonomous_research_final_*`, ledger/log |

## 3. 1.25M Date-Balanced DDQM2 Anchor

선행 1.25M 리포트는 DDQM2 아이디어의 U.S. adaptation을 만들었다. 핵심 chain은 다음과 같다.

```text
prepared monthly panel
→ factor score generation
→ factor long-short return labels
→ factor-return forecasting
→ dynamic factor allocation
→ stock-score QSpread long/short portfolio
```

여기서 date-balanced cap은 전체 row cap을 formation date별로 거의 균등하게 배분하는 방식이다. 따라서 연구 기간 전체는 유지하지만 full local artifact의 월별 cross-section을 그대로 쓰지는 않는다.

1.25M anchor의 핵심 결과는 stock-score QSpread surface가 direct factor-return surface보다 강했다는 점이다.

| 1.25M predecessor row | q | OOS months | Cumulative return | Approx. CAGR | MDD | Turnover |
|---|---:|---:|---:|---:|---:|---:|
| LightGBM stock-score QSpread | 0.20 | 383 | 5202.07 | 약 30.75% | -36.02% | 71.93% |
| LightGBM stock-score QSpread | 0.30 | 383 | 4366.44 | 약 30.03% | -35.71% | 71.39% |

이 결과의 초기 해석은 다음과 같았다.

1. q=0.20은 aggressive return candidate다.
2. q=0.30은 조금 더 balanced한 candidate다.
3. Stock-score QSpread가 DDQM2의 최종 portfolio construction에 더 가깝다.
4. 그러나 cost, slippage, borrow, tax, market impact, capacity는 반영되지 않았다.

즉 1.25M anchor의 결은 “바로 tradable하다”가 아니라 “long/short stock-score QSpread construction이 연구할 만하다”였다.

## 4. 2.08M Full-Panel 확장

다음 단계는 1.25M date-balanced cap을 넘어서 existing local full chunked artifact 전체를 쓰는 것이었다. Full-panel track은 `experiments/prepared/features_full_chunked/`의 2,082,485 prepared rows를 사용했다.

Full-panel matrix는 여섯 model family와 세 q 값을 조합했다.

- baseline mean;
- ridge;
- elasticnet;
- LightGBM;
- random forest;
- extra trees;
- q=0.10, q=0.20, q=0.30.

결과는 exact replication이 아니라 shape robustness에 가깝다. 1.25M에서는 q=0.20/q=0.30 LightGBM stock-score row가 중심이었지만, full-panel에서는 q=0.10 tree model이 gross leader로 올라왔다. 그럼에도 long/short stock-score QSpread signal 자체는 붕괴하지 않았다.

| 2.08M full-panel row | q | Cumulative return | CAGR | MDD | Turnover |
|---|---:|---:|---:|---:|---:|
| Random Forest | 0.10 | 6173.30 | 31.45% | -34.86% | 75.90% |
| LightGBM | 0.10 | 4932.48 | 30.53% | -32.68% | 76.86% |
| Extra Trees | 0.10 | 4605.15 | 30.25% | -36.42% | 76.25% |
| ElasticNet | 0.10 | 1942.77 | 26.78% | -36.46% | 73.81% |
| Ridge | 0.10 | 1107.01 | 24.56% | -45.68% | 73.99% |
| Baseline mean | 0.10 | 1002.89 | 24.18% | -36.51% | 77.44% |

Full-panel result의 해석은 두 가지다.

첫째, 2.08M full-panel 확장은 1.25M anchor의 broad story를 약화시키지 않았다. 오히려 best gross row 기준 CAGR은 1.25M q=0.20 anchor와 비슷하거나 조금 높다.

둘째, 내부 ranking은 바뀌었다. q=0.10과 tree model이 강해졌고, 이는 표본 확장 시 hyperparameter/model frontier가 달라질 수 있음을 뜻한다. 따라서 이 결과는 “같은 q와 같은 model이 재현됐다”가 아니라 “long/short factor construction의 결이 유지됐다”로 읽어야 한다.

## 5. Full-Panel 비용 민감도: Gross Signal의 압축

Full-panel matrix의 gross return은 매우 크지만, sensitivity layer는 해석을 크게 바꾼다. Conservative sensitivity는 25 bps transaction cost, 150 bps annual borrow, 10 bps slippage, 그리고 positive post-cost monthly return에 대한 40.8% simplified tax proxy를 적용한다.

Random Forest q=0.10 row는 gross 기준 leading candidate였지만, conservative row에서는 다음처럼 압축된다.

| Row | Mean monthly | Monthly vol | Conservative cumulative | Conservative MDD |
|---|---:|---:|---:|---:|
| Random Forest q=0.10 conservative proxy | 0.58% | 4.97% | 4.88 | -47.34% |

이 sensitivity는 tax-lot accounting이 아니며 세무 조언도 아니다. 하지만 연구 해석에는 중요하다. Gross result가 크더라도 turnover, short borrow, slippage, tax proxy를 넣으면 practical interpretation이 크게 약해진다. 따라서 이후 factor-router 연구는 단순히 gross return만 높이는 방향이 아니라 drawdown, turnover, q width, model stability를 함께 봐야 했다.

## 6. Factor-Router 자율 연구: 왜 필요했는가

Full-panel matrix는 long/short construction의 broad signal을 확인했지만, 여전히 질문이 남았다.

- q=0.10 tree gross leader가 진짜 최선인가?
- q=0.20/q=0.40에서는 return/drawdown/turnover trade-off가 어떻게 바뀌는가?
- local factor와 global factor를 분리하거나 quota로 섞으면 frontier가 달라지는가?
- Ridge/ElasticNet 같은 sparse-linear model은 더 안정적인 branch를 만들 수 있는가?
- 한계가 명확한 gross result를 비용-aware research program으로 어떻게 발전시킬 수 있는가?

Factor-router loop는 이 질문을 탐색하기 위해 만들어졌다. 핵심은 live trading router가 아니라 research router다. 즉 local/global factor universe, quota, q, factor count, model을 바꿔가며 gross return, MDD, turnover, factor concentration, cost sensitivity를 ledger로 남기는 하네스다.

실험은 항상 local 2,082,485-row prepared artifact만 사용했고, heavy run은 한 번에 하나씩 실행되었다. 이 점은 중요하다. AI agent가 여러 실험을 자율적으로 제안했지만, 하네스는 병렬 heavy execution을 하지 않았고, WRDS나 외부 데이터에 접근하지 않았다.

## 7. Factor-Router 실험 타임라인

Factor-router 연구는 다음 순서로 진행되었다.

1. **Anchor branch**: baseline-mean selected 13-factor q=0.30 branch.
2. **Factor selection branch**: selected factor count를 13에서 7로 줄여 concentration과 drawdown을 확인.
3. **Local/global isolation**: local-only와 global-only를 분리해 signal source를 진단.
4. **Quota branch**: global/local quota 6:7, 4:9, 3:10, 2:11, 1:12를 순차 확인.
5. **Category cap**: factor family concentration을 제한하는 category-cap=3 확인.
6. **q robustness**: q=0.20, q=0.30, q=0.40을 aggressive/defensive 축으로 비교.
7. **Model axis**: ridge와 ElasticNet을 주요 quota branch 위에서 테스트.
8. **ElasticNet robustness**: adjacent quota, q, category cap이 ElasticNet frontier를 개선하는지 확인.
9. **Stop rule**: run 25-29에서 completed non-progress hypothesis가 5개 연속 발생해 중단.

이 타임라인의 핵심은 “AI가 아무거나 돌렸다”가 아니라 “관찰된 frontier를 기준으로 다음 가설을 정하고, 실패/비개선도 ledger에 남겼다”는 점이다.

## 8. Local vs Global: Signal Source 진단

초기 factor-router loop에서 중요한 분기점은 local-only와 global-only 비교였다. Local-only는 gross return을 크게 높였지만 turnover와 drawdown 부담이 컸고, global-only는 return과 drawdown 모두 약했다. 이 결과는 이후 탐색을 local-heavy quota 방향으로 이동시켰다.

요지는 다음과 같다.

- local factors는 alpha source로 보였다.
- global factors는 standalone universe로는 약했다.
- 그러나 global factors를 완전히 제거하면 defensive profile이 나빠질 수 있었다.
- 따라서 “local-heavy but not local-only”가 핵심 탐색 방향이 되었다.

이 흐름은 최종 frontier에서도 나타난다. ElasticNet high-return branch는 local factor weight mass가 높지만 global factor를 일부 유지한다. Defensive q=0.40 branch도 global slot 하나가 stabilizer처럼 작동하는 모습을 보였다.

## 9. Gross Return Frontier: ElasticNet 3:10 q=0.20

Factor-router loop의 strongest gross branch는 ElasticNet quota 3:10 q=0.20이었다.

| Branch | Model | q | Policy | Quota | Cumulative | CAGR | MDD | Turnover |
|---|---|---:|---|---:|---:|---:|---:|---:|
| ElasticNet quota 3:10 q=0.20 | elasticnet | 0.20 | quota | 3:10 | 235.43 | 18.68% | -21.20% | 61.29% |
| ElasticNet quota 4:9 q=0.20 | elasticnet | 0.20 | quota | 4:9 | 234.44 | 18.66% | -21.55% | 61.08% |
| ElasticNet quota 2:11 q=0.20 | elasticnet | 0.20 | quota | 2:11 | 221.75 | 18.46% | -21.43% | 61.13% |
| ElasticNet category-cap=3 q=0.20 | elasticnet | 0.20 | category-capped | — | 193.66 | 17.96% | -23.09% | 61.57% |

이 결과는 흥미롭다. Full-panel matrix의 gross leader는 q=0.10 tree model이었지만, factor-router loop의 developed research frontier는 q=0.20 ElasticNet으로 이동했다. 이는 연구 질문이 달라졌기 때문이다. Full-panel matrix는 broad model/q matrix였고, factor-router loop는 local/global factor universe와 quota를 조정했다.

ElasticNet 3:10 q=0.20은 adjacent quota에서 거의 tie를 만들 정도로 robust했다. 4:9 q=0.20은 cumulative return 234.44로 매우 근접했고, 2:11 q=0.20도 221.75로 강했다. 하지만 어떤 adjacent branch도 3:10 q=0.20을 명확히 넘지 못했다.

## 10. Defensive Frontier: q=0.40과 1:12 Quota

Gross return만 보면 q=0.20이 강하지만, drawdown과 turnover를 보면 q=0.40 defensive branch가 별도의 의미를 갖는다.

| Branch | Model | q | Policy | Quota | Cumulative | CAGR | MDD | Turnover |
|---|---|---:|---|---:|---:|---:|---:|---:|
| baseline quota 1:12 q=0.40 | baseline_mean | 0.40 | quota | 1:12 | 7.88 | 7.08% | -17.14% | 14.59% |
| ElasticNet quota 1:12 q=0.40 | elasticnet | 0.40 | quota | 1:12 | 9.60 | 7.68% | -17.32% | 35.23% |
| ElasticNet quota 3:10 q=0.40 | elasticnet | 0.40 | quota | 3:10 | 10.85 | 8.05% | -18.09% | 34.56% |
| baseline quota 2:11 q=0.40 | baseline_mean | 0.40 | quota | 2:11 | 9.29 | 7.58% | -20.68% | 14.46% |

Baseline quota 1:12 q=0.40은 return은 낮지만 MDD -17.14%로 defensive frontier를 형성했다. 흥미로운 점은 pure local-only q=0.40보다 1개의 global slot을 유지하는 quota 1:12가 훨씬 더 나은 drawdown profile을 보였다는 것이다. 이는 global factor가 standalone alpha source로 약하더라도, constrained stabilizer로는 의미가 있을 수 있음을 시사한다.

따라서 최종 결론은 “ElasticNet q=0.20 하나만이 답”이 아니다. 연구 frontier는 최소 두 개다.

1. Gross return frontier: ElasticNet quota 3:10 q=0.20.
2. Defensive drawdown frontier: baseline quota 1:12 q=0.40.

## 11. Factor Diagnostics: Local-Heavy지만 Global을 버리지 않음

ElasticNet quota 3:10 q=0.20 branch의 top mean-weight factors는 다음과 같았다.

| Factor | Scope | Category | Mean weight | Holdout corr. |
|---|---|---|---:|---:|
| `size_local_small_size` | local | size_flow | 12.79% | 0.129 |
| `quality_global_net_income_yoy` | global | quality_growth | 12.74% | 0.033 |
| `reversal_local_ma_gap_1m` | local | reversal | 11.31% | 0.156 |
| `reversal_local_price_reversal_1m` | local | reversal | 11.31% | 0.156 |
| `val_global_pb_fwd` | global | valuation | 7.80% | 0.105 |
| `val_global_relative_pb_industry_fwd` | global | valuation | 7.80% | 0.105 |

Scope mass는 local 72.41%, global 28.35%였다. Category mass는 earnings 29.89%, reversal 22.62%, quality_growth 19.85%, valuation 15.61%, size_flow 12.79%였다.

이 결과는 다음처럼 해석할 수 있다.

- Signal의 중심은 local factor다.
- 하지만 global factor가 완전히 무의미하지는 않다.
- high-return branch는 local size/reversal/earnings/quality-value 조합 위에 일부 global quality/valuation factor를 결합한다.
- defensive branch에서는 global slot 하나가 drawdown stabilizer처럼 보인다.

이 때문에 factor-router 연구의 핵심은 local-only가 아니라 local-heavy quota다.

## 12. Drawdown Diagnostics: Strong Signal에도 Stress Window는 남음

ElasticNet quota 3:10 q=0.20은 high-return branch 중 MDD가 비교적 양호하지만, 월별 stress loss는 남아 있다.

| Formation date | Return | Turnover | Long turnover | Short turnover |
|---|---:|---:|---:|---:|
| 1999-11-30 | -12.68% | 67.34% | 72.53% | 62.14% |
| 2001-02-28 | -12.02% | 84.33% | 86.61% | 82.06% |
| 2000-10-31 | -9.17% | 76.33% | 74.69% | 77.97% |
| 2000-11-30 | -8.52% | 71.65% | 64.04% | 79.26% |
| 2015-06-30 | -8.29% | 61.82% | 57.14% | 66.49% |

Defensive q=0.40 branch도 손실을 제거하지는 않는다.

| Formation date | Return | Turnover | Long turnover | Short turnover |
|---|---:|---:|---:|---:|
| 2002-10-31 | -7.92% | 12.85% | 13.81% | 11.90% |
| 1999-11-30 | -6.10% | 12.56% | 12.63% | 12.48% |
| 2022-06-30 | -4.99% | 11.90% | 12.38% | 11.41% |
| 2020-12-31 | -4.93% | 16.94% | 16.53% | 17.34% |
| 2000-01-31 | -4.88% | 9.13% | 9.02% | 9.25% |

따라서 drawdown 관점의 결론은 “short leg와 quota tuning이 MDD를 낮출 수 있다”이지, “손실이 제거된다”가 아니다. 이 차이를 명확히 해야 한다.

## 13. Cost, Borrow, Slippage, Tax Proxy: Factor-Router에서도 같은 경고

Factor-router final report의 conservative sensitivity는 full-panel matrix와 같은 메시지를 반복한다. Gross frontier는 강하지만, friction proxy를 적용하면 해석이 크게 압축된다.

| Branch | Model | q | Quota | Gross cum | Pre-tax net cum | Conservative net cum | Conservative MDD | Mean tax drag |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| ElasticNet quota 3:10 q=0.20 | elasticnet | 0.20 | 3:10 | 235.43 | 27.94 | 0.420 | -41.75% | 0.84% |
| ElasticNet quota 3:10 q=0.40 | elasticnet | 0.40 | 3:10 | 10.85 | 1.92 | -0.519 | -56.90% | 0.49% |
| Baseline quota 1:12 q=0.40 | baseline_mean | 0.40 | 1:12 | 7.88 | 2.74 | -0.219 | -40.36% | 0.42% |
| Baseline quota 3:10 q=0.20 | baseline_mean | 0.20 | 3:10 | 95.02 | 9.68 | -0.299 | -61.03% | 0.76% |

ElasticNet q=0.20 branch는 conservative net cumulative가 양수로 남았지만, gross 235.43에서 0.420으로 크게 압축된다. 이는 매우 강한 경고다. Gross research signal은 존재하지만, execution-aware objective가 없으면 실전성 판단은 불가능하다.

따라서 다음 연구는 단순히 더 높은 gross cumulative를 찾는 것이 아니라 다음을 objective에 넣어야 한다.

- transaction cost;
- slippage;
- borrow;
- turnover;
- capacity;
- simplified tax proxy 또는 더 현실적인 tax-lot proxy;
- drawdown stress window;
- factor/leg attribution.

## 14. AI Agent 자율 연구 과정과 한계

이번 연구에서 AI agent는 독립적인 과학 방법론을 발명한 것이 아니다. 더 정확히는 실험 하네스 위에서 다음 역할을 수행했다.

1. 사용자가 설정한 제약을 유지했다.
2. 현재까지의 결과를 읽고 다음 hypothesis를 제안했다.
3. 한 번에 하나의 heavy run만 실행했다.
4. 각 run의 ledger/report를 남겼다.
5. 개선 여부를 scorecard로 판단했다.
6. non-progress가 연속되면 종료했다.

이 과정의 장점은 auditability다. 예를 들어 category-cap 첫 시도는 local disk pressure로 실패했고, 이 실패가 기록된 뒤 retry가 진행되었다. Local-only가 global-only보다 강하다는 결과가 나오자 이후 local-heavy quota branch로 이동했다. q=0.40이 MDD를 낮추자 defensive frontier를 따로 매핑했다. ElasticNet q=0.20이 강해지자 adjacent quota와 category cap으로 robustness를 확인했다.

하지만 한계도 분명하다.

- Agent의 다음 hypothesis는 이전 해석에 의존하므로 path-dependent하다.
- Scorecard에 없는 질문은 과소탐색될 수 있다.
- Local compute와 disk 제약이 실험 공간을 제한한다.
- Ledger는 재현성과 추적성을 높이지만, econometric identification이나 causal inference를 해결하지 않는다.
- Cost/tax sensitivity는 단순 proxy이며 세무 조언이 아니다.
- 최종 claim strength는 사람의 해석과 책임이 필요하다.

따라서 본 연구에서 AI agent의 의의는 “자율 연구자가 alpha를 발견했다”가 아니라 “엄격한 제약과 ledger 아래에서 반복 실험을 관리하고, 진행/비진행 판단을 기록했다”는 데 있다.

## 15. 최종 종합 해석

전체 흐름을 하나로 묶으면 다음과 같다.

1. **1.25M anchor의 결**: stock-score QSpread long/short construction이 U.S. DDQM2 adaptation에서 강한 gross signal을 만들었다.
2. **2.08M full-panel의 결**: 더 큰 local panel에서도 그 broad shape가 유지되었다. 다만 q/model ranking은 바뀌었다.
3. **Factor-router의 결**: local-heavy quota와 q/model variation을 통해 gross-return frontier와 defensive frontier가 분리되었다.
4. **비용 민감도의 결**: gross signal은 매우 크지만, friction proxy를 적용하면 실전적 해석은 크게 제한된다.
5. **AI-agent loop의 결**: 실험 반복과 기록을 체계화했지만, claim을 자동으로 강하게 만들어주지는 않는다.

이를 한 문장으로 쓰면 다음과 같다.

> 2.08M full-panel 확장은 1.25M date-balanced DDQM2 anchor의 long/short QSpread 연구 결을 약화시키지 않았고, factor-router 자율 연구는 local-heavy quota와 ElasticNet/q variation을 통해 새로운 gross 및 defensive frontier를 찾았지만, 비용·turnover·borrow·tax proxy 때문에 최종 해석은 여전히 연구용 frontier에 머문다.

## 16. Limitations

본 연구의 한계는 다음과 같다.

1. **Gross backtest 한계**: 가장 인상적인 수치는 gross research number다.
2. **Friction 한계**: transaction cost, slippage, borrow, tax proxy를 넣으면 결과가 크게 압축된다.
3. **Data boundary 한계**: local prepared artifact만 사용했고, 신규 WRDS validation은 하지 않았다.
4. **Comparison 한계**: 1.25M vs 2.08M은 shape robustness 비교이지 exact matched-sample replication이 아니다.
5. **Search 한계**: q/model/quota/factor universe를 많이 보았지만 exhaustive search는 아니다.
6. **Statistical 한계**: 본 문서는 p-value 중심의 formal inference보다 walk-forward backtest와 diagnostic ledger를 중심으로 한다.
7. **Execution 한계**: borrow availability, market impact, capacity, tax-lot accounting은 아직 production 수준으로 모델링되지 않았다.
8. **AI-agent 한계**: autonomous loop는 연구 과정을 기록하고 반복하게 해주지만, 연구 질문의 완전성이나 경제적 타당성을 보장하지 않는다.

## 17. Next Research Program

다음 단계는 gross return을 더 키우는 것보다 friction-aware robustness를 강화하는 쪽이어야 한다.

1. **Cost-aware objective**: transaction cost, slippage, borrow, turnover를 objective 또는 model selection score에 직접 넣는다.
2. **Turnover control**: q, min_weight, factor allocation smoothing, rebalance cadence를 통해 turnover를 낮춘다.
3. **Dashboard**: 보존된 `portfolio_returns`, `qspread_legs`, `factor_allocations`, `factor_diagnostics`, `factor_scores`를 연결해 월별/종목별/팩터별 drilldown을 만든다.
4. **Worst-month attribution**: ElasticNet q=0.20과 defensive q=0.40 branch의 worst month를 leg, factor family, scope 기준으로 분해한다.
5. **Router stability**: local-heavy quota가 다른 q, 다른 model, 다른 time split에서도 안정적인지 확인한다.
6. **Storage-aware score catalog**: exploratory run은 bulky intermediate를 pruning하고, 대표 run만 dashboard-grade artifact를 보존한다.

## 18. Conclusion

본 V2 종합본의 결론은 명확하지만 조심스럽다. 1.25M date-balanced DDQM2 anchor에서 관찰된 stock-score QSpread long/short signal은 2.08M full-panel 확장에서도 broad shape를 유지했다. 이후 factor-router 자율 연구는 local/global quota, q variation, ElasticNet model axis를 통해 gross-return frontier와 defensive drawdown frontier를 구분해냈다.

가장 강한 gross branch는 ElasticNet quota 3:10 q=0.20이다. 가장 방어적인 branch는 baseline quota 1:12 q=0.40이다. 그러나 어느 쪽도 production strategy라고 부르기에는 이르다. 비용, slippage, borrow, turnover, simplified tax proxy가 결과를 크게 압축하고, worst-month stress도 남아 있다.

따라서 이 연구가 보여주는 것은 “완성된 전략”이 아니라 “계속 연구할 가치가 있는 구조”다. Long/short factor construction은 full-panel에서도 유지되었고, local-heavy factor routing은 의미 있는 frontier를 만들었다. 다음 연구는 gross alpha 발견이 아니라, friction-aware robustness와 attribution을 중심에 두어야 한다.
