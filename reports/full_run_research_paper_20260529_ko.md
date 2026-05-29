# Date-Balanced DDQM2 Anchor에서 Full-Panel 자율 Factor-Router 연구까지

Date: 2026-05-29

영문 원문: [`full_run_research_paper_20260529_en.md`](full_run_research_paper_20260529_en.md)

주요 근거 artifact:

- 1.25M 선행 리포트: [`usa_ddqm2_matrix_report_ko.md`](usa_ddqm2_matrix_report_ko.md), [`usa_ddqm2_matrix_report_en.md`](usa_ddqm2_matrix_report_en.md)
- 2.08M full-panel long/short 리포트: [`full_long_short_qspread_full_chunked_analysis_ko.md`](full_long_short_qspread_full_chunked_analysis_ko.md), [`full_long_short_qspread_full_chunked_analysis_en.md`](full_long_short_qspread_full_chunked_analysis_en.md)
- Full-panel matrix ledger: [`full_long_short_qspread_full_chunked_ledger.json`](full_long_short_qspread_full_chunked_ledger.json)
- 자율 factor-router 리포트: [`factor_router_autonomous_research_final_20260529_ko.md`](factor_router_autonomous_research_final_20260529_ko.md), [`factor_router_autonomous_research_final_20260529_en.md`](factor_router_autonomous_research_final_20260529_en.md)
- 자율 연구 ledger: [`factor_router_autonomous_research_20260529T111620Z.json`](factor_router_autonomous_research_20260529T111620Z.json)
- 자율 연구 log: [`factor_router_autonomous_research_20260529T111620Z.md`](factor_router_autonomous_research_20260529T111620Z.md)

> **연구용 면책.** 이 문서는 기존 로컬 artifact를 바탕으로 작성한 report-style research manuscript입니다. Production trading guide, 투자 조언, 법률 조언, 세무 조언, 또는 backtest가 직접 tradable하다는 주장이 아닙니다. 이 문서를 작성하는 과정에서 WRDS 로그인, 외부 raw data 수집, cloud provisioning, 신규 실험 실행은 없었습니다.

## 초록

이 문서는 기존 1.25M-row date-balanced USA-DDQM2 실험에서 시작해, 2,082,485-row full-panel long/short QSpread 및 factor-router 연구 루프까지 이어진 과정을 정리한다. 선행 1.25M 실험은 formation-date-balanced panel cap에서 강한 gross stock-score QSpread signal을 보였다. q=0.20과 q=0.30 stock-score long/short portfolio는 383개 OOS 월에서 높은 cumulative return을 냈지만, 해당 리포트는 이 결과가 transaction cost, slippage, borrow, tax, market impact, capacity를 반영하지 않은 gross 결과임을 명시했다. 이후 full-panel 실험은 같은 연구 방향을 기존 로컬 chunked artifact 전체로 확장했고, walk-forward OOS protocol과 no-WRDS/no-new-data boundary를 유지했다.

Full-panel 결과는 선행 연구의 결을 무너뜨리지 않았다. 18개 full-panel model/q matrix에서 가장 강한 gross row는 Random Forest q=0.10이었고, cumulative return 6173.30, CAGR 31.45%, MDD -34.86%, turnover 75.90%를 기록했다. LightGBM q=0.10과 Extra Trees q=0.10도 근접했다. 핵심은 특정 q나 model이 완전히 동일하게 재현되었다는 것이 아니라, 더 큰 local panel에서도 long/short stock-score QSpread의 broad shape가 유지되었다는 점이다.

그 후 자율 factor-router loop는 같은 2.08M-row local artifact를 사용해 factor-count, local/global universe routing, q variation, quota policy, category cap, lightweight model variation을 탐색했다. 그 결과 두 가지 연구 frontier가 발견되었다. 첫째, defensive baseline branch인 quota 1:12 q=0.40은 MDD -17.14%, CAGR 7.08%를 기록했다. 둘째, stronger gross sparse-linear branch인 ElasticNet quota 3:10 q=0.20은 cumulative return 235.43, CAGR 18.68%, MDD -21.20%, turnover 61.29%를 기록했다. 그러나 cost, borrow, slippage, simplified tax-proxy sensitivity를 적용하면 gross 해석은 크게 압축된다. 따라서 결론은 조심스럽다. Full-data 확장에서도 gross long/short factor-construction signal은 유지되었지만, 실제 활용 가능성은 turnover, cost, borrow, capacity, tax treatment, 추가 robustness 분석에 크게 의존한다.

## 1. Introduction

이 저장소의 첫 source-controlled USA-DDQM2 리포트는 1,250,000-row date-balanced prepared-panel cap을 사용했다. 여기서 date-balanced는 cap을 월별 formation date에 거의 균등하게 배분한다는 뜻이다. 이 방식은 1990-2024 연구 기간 전체를 유지하지만, full local monthly cross-section을 그대로 유지하지는 않는다. 해당 선행 실험은 초기 empirical shape를 만들었다. Stock-level weighted factor-score QSpread surface가 direct weighted factor-return surface보다 훨씬 강했고, q=0.20/q=0.30은 aggressive-versus-balanced 해석 축이 되었다.

자연스러운 다음 질문은 이 결이 1.25M date-balanced cap의 산물인지 여부였다. Full-panel branch는 기존 local chunked feature artifact인 `experiments/prepared/features_full_chunked/` 전체, 즉 2,082,485 prepared rows로 확장해 이 질문에 답했다. 월별 formation date, next-month forward-return label, 12개월 walk-forward test block, runtime external data 금지 등 DDQM2/EQR walk-forward OOS 정신은 유지했다.

이 문서는 그 전체 과정을 하나의 report-style narrative로 정리한다. 신규 실험을 제시하는 것이 아니라, 기존 리포트와 ledger를 하나의 연구 기록으로 묶는다.

1. 1.25M date-balanced DDQM2 anchor;
2. 2.08M full-panel long/short QSpread matrix;
3. 이후 자율 factor-router research loop;
4. cost, turnover, simplified tax proxy, storage constraint, AI-agent experiment-path dependence가 만드는 한계.

중심 주장은 의도적으로 절제한다. Full-data 확장은 broad gross research signal을 유지했지만, 이를 production strategy로 해석해서는 안 된다. 이는 cost-aware objective, 추가 robustness check, 더 자세한 attribution이 필요한 research frontier다.

## 2. Research Design and Data Boundary

이 문서의 모든 근거는 저장소 안의 기존 local artifact에서 나온다. 작성 과정에서 WRDS에 로그인하지 않았고, 새 데이터를 다운로드하지 않았으며, cloud resource를 만들거나 신규 heavy experiment를 실행하지 않았다.

실험 lineage는 세 단계로 정리할 수 있다.

| Stage | Main source | Rows / runs | Purpose |
|---|---|---:|---|
| 1.25M date-balanced anchor | `usa_ddqm2_matrix_report_en.md` / `_ko.md` | 1,250,000 prepared rows | DDQM2-style U.S. adaptation과 stock-score QSpread surface 설정 |
| 2.08M full-panel matrix | `full_long_short_qspread_full_chunked_analysis_en.md` / `_ko.md` | 2,082,485 prepared rows; 18 model/q rows | Long/short shape가 full-panel expansion에서도 유지되는지 확인 |
| Autonomous factor-router loop | `factor_router_autonomous_research_final_20260529_en.md` / `_ko.md` 및 ledger | anchor 이후 29개 연구 단계 | Local/global routing, q variation, factor-count, model frontier 탐색 |

이 protocol은 단일 final strategy backtest라기보다 walk-forward research harness에 가깝다. 각 월별 portfolio는 평가 대상 next-month return 이전에 관측 가능한 정보를 사용한다. Model은 future label을 보고 학습하지 않고 walk-forward block에 따라 재학습된다. 또한 저장소 리포트는 private local data 및 generated artifact와 source-controlled summary를 분리한다.

## 3. 1.25M Date-Balanced 선행 실험

선행 리포트는 autoquant-lab을 DDQM/DDQM2 아이디어의 U.S. adaptation으로 정의했다. 핵심 method chain은 factor long-short return을 macro/market variable로 예측하고, 예측 factor return을 non-negative factor allocation으로 바꾼 뒤, long/short 또는 QSpread-style portfolio를 평가하는 것이다.

핵심 empirical observation은 stock-score QSpread surface가 weighted factor-return surface보다 DDQM2 final portfolio construction에 더 가깝고 강했다는 점이다. 1.25M date-balanced panel에서 LightGBM stock-score QSpread row는 다음과 같았다.

| Predecessor run | q | OOS periods | Cumulative return | Approx. CAGR | MDD | Turnover |
|---|---:|---:|---:|---:|---:|---:|
| 1.25M stock-score QSpread | 0.20 | 383 | 5202.07 | 약 30.75% | -36.02% | 71.93% |
| 1.25M stock-score QSpread | 0.30 | 383 | 4366.44 | 약 30.03% | -35.71% | 71.39% |

선행 리포트의 해석도 이미 조심스러웠다. q=0.20은 aggressive return candidate, q=0.30은 조금 더 balanced한 candidate로 보되, 둘 다 transaction cost, slippage, borrow, tax, market impact, capacity, final tradability review가 빠진 gross backtest라고 명시했다.

따라서 이 논문에서 1.25M 결과는 기계적으로 이겨야 할 benchmark가 아니다. 그것은 선행 연구의 결이다. Long/short stock-score QSpread가 중요해 보였고, q는 연구 축이며, cost/turnover는 아직 풀리지 않은 문제였다는 점이 중요하다.

## 4. 2.08M Full-Panel 확장

2.08M full-panel long/short 리포트는 기존 local full chunked artifact로 선행 연구를 확장했다. Full-panel matrix는 여섯 model family와 세 q 값을 조합했다.

- baseline mean;
- ridge;
- elasticnet;
- LightGBM;
- random forest;
- extra trees;
- q=0.10, q=0.20, q=0.30.

Headline은 같은 model/q 조합이 그대로 지배했다는 것이 아니다. Expanded sample에서도 broad long/short QSpread shape가 유지되었고, model ranking은 바뀌었다. 가장 강한 gross row는 다음과 같았다.

| Full-panel row | q | Cumulative return | CAGR | MDD | Turnover |
|---|---:|---:|---:|---:|---:|
| Random Forest | 0.10 | 6173.30 | 31.45% | -34.86% | 75.90% |
| LightGBM | 0.10 | 4932.48 | 30.53% | -32.68% | 76.86% |
| Extra Trees | 0.10 | 4605.15 | 30.25% | -36.42% | 76.25% |
| ElasticNet | 0.10 | 1942.77 | 26.78% | -36.46% | 73.81% |
| Ridge | 0.10 | 1107.01 | 24.56% | -45.68% | 73.99% |
| Baseline mean | 0.10 | 1002.89 | 24.18% | -36.51% | 77.44% |

두 가지 결론이 가능하다. 첫째, full-panel expansion은 1.25M date-balanced anchor 대비 연구 스토리를 약화시키지 않았다. 가장 강한 full-panel row의 reported CAGR은 기존 q=0.20 anchor보다 조금 높았다. 둘째, q=0.10과 tree model이 더 두드러졌기 때문에 이를 exact replication이라고 부르면 안 된다. 더 적절한 표현은 shape robustness다. Larger local sample에서도 broad long/short factor-construction signal이 유지되었지만, 내부 ranking은 바뀌었다.

Full-panel matrix의 defensive side도 중요하다. ElasticNet q=0.20은 full-panel row 중 낮은 drawdown profile을 보였고, cumulative return 160.79, CAGR 17.28%, MDD -23.57%, turnover 60.99%를 기록했다. 이는 이후 factor-router loop에서 sparse-linear model과 local/global quota policy가 중요해지는 흐름을 예고했다.

## 5. Cost, Borrow, Slippage, Simplified Tax Proxy

Full-panel matrix에는 gross return을 과도하게 해석하지 않기 위한 sensitivity row가 포함되었다. Full-panel report의 conservative sensitivity, 즉 25 bps transaction cost, 150 bps annual borrow, 10 bps slippage, positive post-cost monthly return에 대한 40.8% simplified tax proxy를 적용하면 Random Forest q=0.10 row는 여전히 leading tested candidate였지만 성과가 크게 압축되었다. Conservative row 기준 mean monthly return은 0.58%, monthly volatility는 4.97%, cumulative return은 4.88, MDD는 -47.34%였다.

이 sensitivity는 의도적으로 단순하다. Tax-lot accounting도 아니고, 세무 조언도 아니며, production execution model도 아니다. 이 stress layer의 의미는 “large gross return”을 “friction에 크게 의존하는 gross signal”로 바꾸는 데 있다.

같은 패턴은 factor-router report에서도 반복되었다. 가장 강한 ElasticNet quota 3:10 q=0.20 branch는 gross cumulative return 235.43이었지만, conservative sensitivity row에서는 cumulative 0.420, conservative MDD -41.75%로 압축되었다. 따라서 해당 branch는 연구적으로 흥미롭지만, practical conclusion은 훨씬 좁아진다.

## 6. 발전된 연구: Factor-Router Loop

Full-panel long/short matrix 이후 연구 질문은 바뀌었다. “Full-panel long/short surface가 유지되는가?”에서 “새 데이터 없이 local/global factor routing, q variation, lightweight model variation으로 return/drawdown/turnover frontier를 개선할 수 있는가?”로 이동했다.

Factor-router loop는 같은 2,082,485-row local prepared artifact를 사용했고 walk-forward OOS protocol을 유지했다. 한 번에 하나의 heavy experiment만 실행했으며, 가능한 경우 각 branch에 대해 ledger/report pair를 남겼다. Search path는 다음을 포함했다.

1. selected factor-count reduction;
2. local-only versus global-only isolation;
3. local/global quota policy;
4. category cap;
5. q=0.20/q=0.30/q=0.40 robustness;
6. local-heavy quota sweep;
7. ridge 및 ElasticNet model-axis check;
8. adjacent ElasticNet robustness branch.

Loop가 찾은 strongest gross frontier는 tree model이 아니라 local-heavy quota design 위의 ElasticNet이었다.

| Branch | Model | q | Policy | Quota | Cumulative | CAGR | MDD | Turnover |
|---|---|---:|---|---:|---:|---:|---:|---:|
| ElasticNet quota 3:10 q=0.20 | elasticnet | 0.20 | quota | 3:10 | 235.43 | 18.68% | -21.20% | 61.29% |
| ElasticNet quota 4:9 q=0.20 | elasticnet | 0.20 | quota | 4:9 | 234.44 | 18.66% | -21.55% | 61.08% |
| ElasticNet quota 2:11 q=0.20 | elasticnet | 0.20 | quota | 2:11 | 221.75 | 18.46% | -21.43% | 61.13% |
| ElasticNet category-cap=3 q=0.20 | elasticnet | 0.20 | category-capped | — | 193.66 | 17.96% | -23.09% | 61.57% |

가장 defensive한 branch는 달랐다.

| Branch | Model | q | Policy | Quota | Cumulative | CAGR | MDD | Turnover |
|---|---|---:|---|---:|---:|---:|---:|---:|
| baseline quota 1:12 q=0.40 | baseline_mean | 0.40 | quota | 1:12 | 7.88 | 7.08% | -17.14% | 14.59% |
| ElasticNet quota 1:12 q=0.40 | elasticnet | 0.40 | quota | 1:12 | 9.60 | 7.68% | -17.32% | 35.23% |
| ElasticNet quota 3:10 q=0.40 | elasticnet | 0.40 | quota | 3:10 | 10.85 | 8.05% | -18.09% | 34.56% |

결과는 하나의 universal winner가 아니라 frontier다. ElasticNet q=0.20 branch는 gross-return frontier이고, baseline q=0.40 1:12 branch는 defensive drawdown frontier다. 이 분리가 바로 이 문서가 strategy recommendation을 하지 않는 핵심 이유다.

## 7. Factor 해석과 Drawdown 진단

Factor diagnostics는 ElasticNet 결과를 단순한 local-only bet으로 오해하지 않게 해준다. ElasticNet quota 3:10 q=0.20 branch에서 local factor의 mean weight mass가 더 컸지만, global factor도 여전히 존재했다.

Top mean-weight factor는 다음과 같았다.

| Factor | Scope | Category | Mean weight | Holdout corr. |
|---|---|---|---:|---:|
| `size_local_small_size` | local | size_flow | 12.79% | 0.129 |
| `quality_global_net_income_yoy` | global | quality_growth | 12.74% | 0.033 |
| `reversal_local_ma_gap_1m` | local | reversal | 11.31% | 0.156 |
| `reversal_local_price_reversal_1m` | local | reversal | 11.31% | 0.156 |
| `val_global_pb_fwd` | global | valuation | 7.80% | 0.105 |
| `val_global_relative_pb_industry_fwd` | global | valuation | 7.80% | 0.105 |

Scope mass는 대략 local 72.41%, global 28.35%였다. Category mass는 earnings, reversal, quality/growth, valuation, size/flow에 집중되었다. 즉 high-return branch는 global factor를 완전히 버린 것이 아니라 local state factor를 중심으로 일부 global stabilizer를 결합했다.

Defensive baseline branch도 비슷한 메시지를 준다. Quota 1:12 q=0.40 design은 global slot 하나를 유지했고, pure local-only q=0.40보다 drawdown이 훨씬 낮았기 때문에 그 한 개 global slot은 진단적으로 의미가 있어 보인다. Defensive branch는 high-return은 아니지만 MDD를 -17.14%까지 낮추고 turnover도 낮게 유지했다.

Worst-month diagnostics 역시 조심스러운 해석을 요구한다. ElasticNet quota 3:10 q=0.20은 1999-11 -12.68%, 2001-02 -12.02%, 2000-10 -9.17%, 2000-11 -8.52%, 2015-06 -8.29%의 월별 손실을 기록했다. Defensive q=0.40 branch는 worst month 크기를 낮췄지만 stress loss 자체를 제거하지는 못했다. 따라서 이 결과는 finished strategy가 아니라 research frontier다.

## 8. Autonomous AI-Agent Research Process

이 프로젝트의 autonomous 부분은 agent 자체가 새로운 scientific method를 만들었다는 주장이 아니다. 이는 practical experiment-management process였다. 사용자는 constraint, stop condition, research preference를 지정했고, harness는 한 branch씩 실행하고, ledger를 남기고, progress 여부를 해석하고, 관찰된 frontier에서 다음 hypothesis를 제안했다.

이 과정은 네 가지 점에서 중요했다.

첫째, constraint를 유지했다. Loop는 local artifacts only, no WRDS login, no external raw data, no cloud auto-provisioning, no team/swarm heavy parallel experiments, additive outputs only, research diagnostics only라는 guardrail을 반복적으로 유지했다.

둘째, search path를 audit 가능하게 만들었다. 각 hypothesis는 가능한 경우 ledger/report pair를 남겼다. Infrastructure failure도 지워지지 않았다. Category-cap 첫 시도는 local disk pressure로 실패했고, 이 사실이 기록된 뒤 retry가 진행되었다.

셋째, search가 관찰 결과에 따라 적응했다. Local-only가 global-only보다 강했기 때문에 이후 run은 local-heavy quota에 집중했다. q=0.40은 낮은 return 대신 drawdown을 개선했기 때문에 defensive branch가 매핑되었다. q=0.20은 return을 높였지만 turnover/drawdown 부담이 컸기 때문에 aggressive frontier와 defensive frontier가 분리되었다. ElasticNet이 local-heavy q=0.20 frontier를 개선했기 때문에 adjacent quota와 category-cap check가 이어졌다.

넷째, 명시적 종료 로직이 있었다. Heavy loop는 다섯 개 연속 completed non-progress hypotheses 이후 종료했다. Run 25-29는 기존 sparse-linear frontier나 defensive frontier를 개선하지 못했고, 따라서 disk가 2GB hard stop보다 위에 있었음에도 search가 종료되었다. 더 많은 variation이 가능하다는 이유만으로 계속 돌리지 않았다는 점이 중요하다.

이 process의 한계도 분명하다. Loop는 path-dependent하다. 다음 hypothesis는 직전 해석에 의존한다. Local compute, disk, stored artifact에 의해 제한된다. Metric 비교는 가능하지만 econometric identification, causal inference, capacity, borrow availability, tax-lot accounting을 해결하지는 않는다. Reproducible research trail은 만들 수 있지만, claim strength와 interpretation은 여전히 사람이 책임져야 한다.

## 9. Limitations

주요 한계는 방법론적, 실증적, 운영적이다.

1. **Gross backtest limitation.** 가장 큰 headline return은 gross research number다. Cost, slippage, borrow, simplified tax proxy, market impact, capacity는 아직 해결되지 않았다.
2. **Comparison limitation.** 1.25M-to-2.08M 비교는 shape와 lineage 비교이지, exact matched-sample replication이 아니다.
3. **Data boundary limitation.** 결과는 local prepared artifact만 사용한다. 이 writing pass에서 신규 WRDS validation이나 external raw data는 사용하지 않았다.
4. **Model-selection limitation.** 많은 branch를 탐색했지만 exhaustive hyperparameter search나 statistical-significance space는 아니다.
5. **Router limitation.** Local/global quota 결과는 diagnostic이다. Fixed quota가 live execution constraint하에서 경제적으로 optimal하다는 증명은 아니다.
6. **AI-agent limitation.** Autonomous loop는 ledgering과 iteration discipline을 개선하지만, research path에 overfit하거나 너무 일찍 멈추거나 scorecard에 없는 질문을 과소평가할 수 있다.
7. **Publication limitation.** 이 저장소는 raw data, private note, generated parquet artifact, vendor/reference PDF를 제외한다. 따라서 이 문서는 완전한 public replication package가 아니라 source-controlled summary와 private-local reproducibility context 위의 public report다.

## 10. Conclusion

Full-panel 연구 기록은 cautious empirical conclusion을 지지한다. 기존 1.25M date-balanced DDQM2 실험은 stock-score long/short QSpread construction이 U.S. adaptation에서 가장 강한 표현임을 보였다. 2.08M full-panel 확장은 이 결을 뒤집지 않았다. 오히려 더 큰 local panel에서도 broad gross long/short factor-construction signal이 유지되었고, full-panel matrix의 strongest row는 q=0.10 tree model 쪽으로 이동했다.

이후 factor-router loop는 연구를 더 발전시켰다. Aggressive frontier와 defensive frontier를 분리했고, local-heavy quota design이 global-only isolation보다 유용함을 보였으며, 강한 ElasticNet q=0.20 branch와 낮은 drawdown의 q=0.40 defensive branch를 찾았다. 또한 AI-agent loop는 hypothesis, ledger, failure, stop rule, non-progress branch를 기록함으로써 연구 과정 자체를 더 audit 가능하게 만들었다.

최종 해석은 의도적으로 절제한다. 이 결과는 long/short factor construction, local/global factor routing, cost-aware objective, turnover control, dashboard-grade attribution에 대한 추가 연구를 정당화한다. 그러나 production trading claim을 정당화하지는 않는다. 다음 단계는 frictions와 robustness를 post-hoc sensitivity가 아니라 objective 자체의 일부로 만드는 것이다.
