# From Date-Balanced DDQM2 Anchors to Full-Panel Autonomous Factor-Router Research

Date: 2026-05-29

Korean companion: [`full_run_research_paper_20260529_ko.md`](full_run_research_paper_20260529_ko.md)

Primary source artifacts:

- 1.25M predecessor report: [`usa_ddqm2_matrix_report_en.md`](usa_ddqm2_matrix_report_en.md)
- 2.08M full-panel long/short report: [`full_long_short_qspread_full_chunked_analysis_en.md`](full_long_short_qspread_full_chunked_analysis_en.md)
- Full-panel matrix ledger: [`full_long_short_qspread_full_chunked_ledger.json`](full_long_short_qspread_full_chunked_ledger.json)
- Autonomous factor-router report: [`factor_router_autonomous_research_final_20260529_en.md`](factor_router_autonomous_research_final_20260529_en.md)
- Autonomous run ledger: [`factor_router_autonomous_research_20260529T111620Z.json`](factor_router_autonomous_research_20260529T111620Z.json)
- Autonomous run log: [`factor_router_autonomous_research_20260529T111620Z.md`](factor_router_autonomous_research_20260529T111620Z.md)

> **Research-only disclaimer.** This document is a report-style research manuscript over existing local artifacts. It is not production-trading guidance, investment advice, legal advice, tax advice, or a statement that any backtest is directly tradable. No WRDS login, external raw-data acquisition, cloud provisioning, or new experiment execution was used to write this paper.

## Abstract

This paper documents the progression from the earlier 1.25M-row date-balanced USA-DDQM2 experiment to the later 2,082,485-row full-panel long/short QSpread and factor-router research loop. The predecessor experiment established a strong gross stock-score QSpread signal on a formation-date-balanced panel cap: q=0.20 and q=0.30 stock-score long/short portfolios produced high cumulative returns over 383 out-of-sample months, while the report emphasized that the results were gross-only and not cost adjusted. The full-panel experiment expanded the same research direction to the existing local chunked artifact, preserving the walk-forward out-of-sample protocol and the no-WRDS/no-new-data boundary.

The full-panel result did not collapse the earlier research shape. In the 18-row full-panel model/q matrix, the strongest gross row was Random Forest q=0.10 with cumulative return 6173.30, CAGR 31.45%, MDD -34.86%, and turnover 75.90%. LightGBM q=0.10 and Extra Trees q=0.10 followed closely. The broader interpretation is not exact replication of a single q or model choice, but continuity of the long/short stock-score QSpread signal under a larger local panel.

The follow-on autonomous factor-router loop then used the same local 2.08M-row artifact to explore factor-count, local/global universe routing, q variation, quota policies, category caps, and lightweight model variation. It found two useful research frontiers: a defensive baseline branch, quota 1:12 q=0.40, with MDD -17.14% and CAGR 7.08%; and a stronger gross sparse-linear branch, ElasticNet quota 3:10 q=0.20, with cumulative return 235.43, CAGR 18.68%, MDD -21.20%, and turnover 61.29%. However, cost, borrow, slippage, and simplified tax-proxy sensitivity compressed the gross interpretation materially. The paper therefore concludes cautiously: the full-data extension preserves a gross long/short factor-construction signal, but practical use depends on turnover, costs, borrow, capacity, tax treatment, and further robustness analysis.

## 1. Introduction

The first source-controlled USA-DDQM2 report in this repository used a 1,250,000-row date-balanced prepared-panel cap. In that context, “date-balanced” means that the cap is spread approximately evenly across monthly formation dates. It preserves the full 1990-2024 research window, but it does not preserve the full local monthly cross-section. That predecessor run established the initial empirical shape: the stock-level weighted factor-score QSpread surface was materially stronger than the direct weighted factor-return surface, and q=0.20/q=0.30 became the main aggressive-versus-balanced interpretation axis.

The natural next question was whether that shape was merely an artifact of the 1.25M date-balanced cap. The full-panel branch answered this by moving to the existing local chunked feature artifact, `experiments/prepared/features_full_chunked/`, containing 2,082,485 prepared rows. The same broad DDQM2/EQR walk-forward OOS spirit was retained: monthly formation dates, next-month forward-return labels, 12-month walk-forward test blocks, and no runtime external data.

This paper is the report-style narrative over that full sequence. It does not present a new experiment. Instead, it consolidates the existing reports and ledgers into a single research record:

1. the 1.25M date-balanced DDQM2 anchor;
2. the 2.08M full-panel long/short QSpread matrix;
3. the later autonomous factor-router research loop; and
4. the limitations imposed by costs, turnover, simplified tax proxies, storage constraints, and AI-agent experiment-path dependence.

The central claim is deliberately modest. The full-data extension preserved the broad gross research signal of long/short factor construction, but the signal should not be interpreted as a production strategy. It is a research frontier that needs cost-aware objectives, additional robustness checks, and more detailed attribution before stronger claims are warranted.

## 2. Research Design and Data Boundary

All evidence in this paper is derived from existing local artifacts already summarized in the repository. The writing pass did not log into WRDS, download new data, provision cloud resources, or run new heavy experiments.

The experimental lineage has three stages.

| Stage | Main source | Rows / runs | Purpose |
|---|---|---:|---|
| 1.25M date-balanced anchor | `usa_ddqm2_matrix_report_en.md` | 1,250,000 prepared rows | Establish DDQM2-style U.S. adaptation and stock-score QSpread surface |
| 2.08M full-panel matrix | `full_long_short_qspread_full_chunked_analysis_en.md` | 2,082,485 prepared rows; 18 model/q rows | Test whether the long/short shape survives full-panel expansion |
| Autonomous factor-router loop | `factor_router_autonomous_research_final_20260529_en.md` and ledger | 29 completed/attempted research steps after anchor sequence | Explore local/global routing, q variation, factor-count and model frontiers |

The protocol is best understood as a walk-forward research harness rather than a single final strategy backtest. Each monthly portfolio uses information available before the evaluated next-month return. Models are refit by walk-forward blocks, not by peeking at future labels. The repository reports also separate private local data and generated artifacts from source-controlled summaries.

## 3. The 1.25M Date-Balanced Predecessor

The predecessor report framed autoquant-lab as a U.S. adaptation of the DDQM/DDQM2 idea. It preserved the high-level method chain: forecast factor long-short returns from macro/market variables, convert predicted factor returns into non-negative factor allocations, and evaluate long/short or QSpread-style portfolios.

The key empirical observation was that the stock-score QSpread surface looked closer to the final DDQM2 portfolio construction than the weighted factor-return surface. On the 1.25M date-balanced panel, the LightGBM stock-score QSpread rows were:

| Predecessor run | q | OOS periods | Cumulative return | Approx. CAGR | MDD | Turnover |
|---|---:|---:|---:|---:|---:|---:|
| 1.25M stock-score QSpread | 0.20 | 383 | 5202.07 | about 30.75% | -36.02% | 71.93% |
| 1.25M stock-score QSpread | 0.30 | 383 | 4366.44 | about 30.03% | -35.71% | 71.39% |

The predecessor interpretation was already cautious. It treated q=0.20 as the aggressive return candidate and q=0.30 as a somewhat more balanced candidate, while stressing that both were gross backtests without transaction costs, slippage, borrow, taxes, market impact, capacity constraints, or final tradability review.

This matters for the full-panel paper because the 1.25M result is not used here as a benchmark to beat mechanically. It is used as a predecessor shape: long/short stock-score QSpread appeared to matter, q was a live research axis, and costs/turnover remained unresolved.

## 4. The 2.08M Full-Panel Extension

The 2.08M full-panel long/short report extended the predecessor study to the existing local full chunked artifact. The full-panel matrix ran six model families over three q values:

- baseline mean;
- ridge;
- elasticnet;
- LightGBM;
- random forest;
- extra trees;
- q=0.10, q=0.20, and q=0.30.

The headline result was not that the exact same model/q combination dominated. Instead, the expanded sample preserved the broad long/short QSpread shape while changing the model ranking. The best gross rows were:

| Full-panel row | q | Cumulative return | CAGR | MDD | Turnover |
|---|---:|---:|---:|---:|---:|
| Random Forest | 0.10 | 6173.30 | 31.45% | -34.86% | 75.90% |
| LightGBM | 0.10 | 4932.48 | 30.53% | -32.68% | 76.86% |
| Extra Trees | 0.10 | 4605.15 | 30.25% | -36.42% | 76.25% |
| ElasticNet | 0.10 | 1942.77 | 26.78% | -36.46% | 73.81% |
| Ridge | 0.10 | 1107.01 | 24.56% | -45.68% | 73.99% |
| Baseline mean | 0.10 | 1002.89 | 24.18% | -36.51% | 77.44% |

Two conclusions follow. First, full-panel expansion did not weaken the research story relative to the 1.25M date-balanced anchor; the best full-panel row had a slightly higher reported CAGR than the prior q=0.20 anchor. Second, the full-panel result should not be described as exact replication because q=0.10 and tree models became more prominent in the expanded panel. A better phrase is “shape robustness”: the broad long/short factor-construction signal survived the larger local sample, even though the internal ranking changed.

The defensive side of the full-panel matrix also matters. ElasticNet q=0.20 had lower drawdown among the full-panel rows, with cumulative return 160.79, CAGR 17.28%, MDD -23.57%, and turnover 60.99%. This foreshadowed the later factor-router loop, where sparse-linear models and local/global quota policies became important.

## 5. Costs, Borrow, Slippage, and Simplified Tax Proxy

The full-panel matrix included sensitivity rows to avoid over-reading gross returns. Under the conservative sensitivity used in the full-panel report—25 bps transaction cost, 150 bps annual borrow, 10 bps slippage, and a 40.8% simplified tax proxy on positive post-cost monthly returns—the Random Forest q=0.10 row remained the leading tested candidate but compressed sharply. Its conservative row had mean monthly return 0.58%, monthly volatility 4.97%, cumulative return 4.88, and MDD -47.34%.

This sensitivity is intentionally simple. It is not tax-lot accounting, not tax advice, and not a production execution model. It is a stress layer that changes the interpretation from “large gross return” to “gross signal whose practical economic value depends heavily on frictions.”

That pattern repeated in the later factor-router report. For the strongest ElasticNet quota 3:10 q=0.20 branch, gross cumulative return was 235.43, but the conservative sensitivity row compressed to 0.420 cumulative with conservative MDD -41.75%. The branch remained research-relevant, but the practical conclusion became much narrower.

## 6. Developed Research: The Factor-Router Loop

After the full-panel long/short matrix, the research moved from a broad model/q matrix to a factor-router loop. The question changed from “does the full-panel long/short surface survive?” to “can local/global factor routing, q variation, and lightweight model variation improve the return/drawdown/turnover frontier without new data?”

The loop used the same 2,082,485-row local prepared artifact and retained the walk-forward OOS protocol. It ran one heavy experiment at a time and wrote ledgers/reports for each branch. Its search path included:

1. selected factor-count reduction;
2. local-only versus global-only isolation;
3. local/global quota policies;
4. category caps;
5. q=0.20/q=0.30/q=0.40 robustness;
6. local-heavy quota sweeps;
7. ridge and ElasticNet model-axis checks; and
8. adjacent ElasticNet robustness branches.

The strongest gross frontier found by the loop was not a tree model. It was ElasticNet on a local-heavy quota design:

| Branch | Model | q | Policy | Quota | Cumulative | CAGR | MDD | Turnover |
|---|---|---:|---|---:|---:|---:|---:|---:|
| ElasticNet quota 3:10 q=0.20 | elasticnet | 0.20 | quota | 3:10 | 235.43 | 18.68% | -21.20% | 61.29% |
| ElasticNet quota 4:9 q=0.20 | elasticnet | 0.20 | quota | 4:9 | 234.44 | 18.66% | -21.55% | 61.08% |
| ElasticNet quota 2:11 q=0.20 | elasticnet | 0.20 | quota | 2:11 | 221.75 | 18.46% | -21.43% | 61.13% |
| ElasticNet category-cap=3 q=0.20 | elasticnet | 0.20 | category-capped | — | 193.66 | 17.96% | -23.09% | 61.57% |

The most defensive branch was different:

| Branch | Model | q | Policy | Quota | Cumulative | CAGR | MDD | Turnover |
|---|---|---:|---|---:|---:|---:|---:|---:|
| baseline quota 1:12 q=0.40 | baseline_mean | 0.40 | quota | 1:12 | 7.88 | 7.08% | -17.14% | 14.59% |
| ElasticNet quota 1:12 q=0.40 | elasticnet | 0.40 | quota | 1:12 | 9.60 | 7.68% | -17.32% | 35.23% |
| ElasticNet quota 3:10 q=0.40 | elasticnet | 0.40 | quota | 3:10 | 10.85 | 8.05% | -18.09% | 34.56% |

The result is a frontier, not a single universal winner. The ElasticNet q=0.20 branch is the gross-return frontier, while the baseline q=0.40 1:12 branch is the defensive drawdown frontier. That split is one of the central reasons this paper avoids recommending a strategy.

## 7. Factor Interpretation and Drawdown Diagnostics

The factor diagnostics help prevent the ElasticNet result from being misread as a generic local-only bet. In the ElasticNet quota 3:10 q=0.20 branch, local factors carried most of the mean weight mass, but global factors were still present.

Top mean-weight factors included:

| Factor | Scope | Category | Mean weight | Holdout corr. |
|---|---|---|---:|---:|
| `size_local_small_size` | local | size_flow | 12.79% | 0.129 |
| `quality_global_net_income_yoy` | global | quality_growth | 12.74% | 0.033 |
| `reversal_local_ma_gap_1m` | local | reversal | 11.31% | 0.156 |
| `reversal_local_price_reversal_1m` | local | reversal | 11.31% | 0.156 |
| `val_global_pb_fwd` | global | valuation | 7.80% | 0.105 |
| `val_global_relative_pb_industry_fwd` | global | valuation | 7.80% | 0.105 |

The scope mass was approximately 72.41% local and 28.35% global. Category mass was concentrated in earnings, reversal, quality/growth, valuation, and size/flow. This suggests that the high-return branch combined local state factors with a smaller set of global stabilizers rather than discarding global factors entirely.

The defensive baseline branch tells a related story. Its quota 1:12 q=0.40 design kept one global slot, and that slot appeared diagnostically meaningful because pure local-only q=0.40 had worse drawdown. The defensive branch was not high-return, but it reduced MDD to -17.14% with low turnover.

Worst-month diagnostics also argue for caution. ElasticNet quota 3:10 q=0.20 had monthly losses of -12.68% in 1999-11, -12.02% in 2001-02, -9.17% in 2000-10, -8.52% in 2000-11, and -8.29% in 2015-06. The defensive q=0.40 branch reduced the size of worst months but did not remove stress losses. These diagnostics keep the result in the realm of research frontiers rather than finished strategy design.

## 8. Autonomous AI-Agent Research Process

The autonomous part of the project was not a claim that the agent itself created a new scientific method. It was a practical experiment-management process. The user specified constraints, stop conditions, and research preferences; the harness executed one branch at a time, recorded ledgers, interpreted whether progress occurred, and proposed the next hypothesis from the observed frontier.

The process mattered in four ways.

First, it preserved constraints. The loop repeatedly carried the same guardrails: local artifacts only, no WRDS login, no external raw data, no cloud auto-provisioning, no team/swarm heavy parallel experiments, additive outputs only, and research diagnostics only.

Second, it made the search path auditable. Each hypothesis produced a ledger/report pair where possible. Failed infrastructure attempts were not silently erased: the category-cap first attempt failed from local disk pressure and was recorded before a retry.

Third, it allowed the search to adapt. Local-only beat global-only, so later runs emphasized local-heavy quotas. q=0.40 improved drawdown at lower returns, so defensive branches were mapped. q=0.20 improved return but increased turnover/drawdown, so aggressive frontiers were separated from defensive frontiers. ElasticNet improved the local-heavy q=0.20 frontier, so adjacent quota and category-cap checks were run.

Fourth, it had explicit stopping logic. The heavy loop stopped after five consecutive completed non-progress hypotheses. Runs 25-29 did not beat the existing sparse-linear frontier or defensive frontier, so the search terminated despite remaining disk above the 2GB hard stop. That termination is important: the loop did not continue merely because more variations were possible.

The limitations of this process are equally important. The loop is path-dependent: the next hypothesis depends on prior interpretation. It is bounded by local compute, disk, and stored artifacts. It can compare reported metrics, but it does not independently solve econometric identification, causal inference, capacity, borrow availability, or tax-lot accounting. It can produce a reproducible research trail, but the human still owns claim strength and interpretation.

## 9. Limitations

The main limitations are methodological, empirical, and operational.

1. **Gross backtest limitation.** The largest headline returns are gross research numbers. Cost, slippage, borrow, simplified tax proxy, market impact, and capacity all remain unresolved.
2. **Comparison limitation.** The 1.25M-to-2.08M comparison is a shape and lineage comparison, not an exact matched-sample replication.
3. **Data boundary limitation.** The results use local prepared artifacts only. No new WRDS validation or external raw data were used in the full-run writing pass.
4. **Model-selection limitation.** The search explored many branches, but not an exhaustive hyperparameter or statistical-significance space.
5. **Router limitation.** Local/global quota results are diagnostic; they do not prove that a fixed quota is economically optimal under live execution constraints.
6. **AI-agent limitation.** The autonomous loop improves ledgering and iteration discipline, but it can still overfit a research path, stop too early, or underweight questions not encoded in the scorecard.
7. **Publication limitation.** This repository excludes raw data, private notes, generated parquet artifacts, and vendor/reference PDFs. The paper is therefore a public report over source-controlled summaries and private-local reproducibility context, not a fully self-contained public replication package.

## 10. Conclusion

The full-panel research record supports a cautious empirical conclusion. The earlier 1.25M date-balanced DDQM2 experiment found that stock-score long/short QSpread construction was the strongest expression of the U.S. adaptation. The 2.08M full-panel extension did not overturn that result. Instead, it preserved the broad shape of the gross long/short factor-construction signal under a larger local panel, while shifting the strongest full-panel matrix row toward q=0.10 tree models.

The later factor-router loop developed the research further. It separated aggressive and defensive frontiers, showed that local-heavy quota designs were more useful than global-only isolation, and found a strong ElasticNet q=0.20 branch as well as a low-drawdown q=0.40 defensive branch. The loop also made the research process itself more auditable by recording hypotheses, ledgers, failures, stop rules, and non-progress branches.

The final interpretation remains deliberately restrained. The evidence supports continued research into long/short factor construction, local/global factor routing, cost-aware objectives, turnover control, and dashboard-grade attribution. It does not support a production trading claim. The next stage should make frictions and robustness first-class objectives rather than treating them as a post-hoc sensitivity layer.
