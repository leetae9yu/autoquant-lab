# Factor Router Autonomous Research Ledger

Started: 20260529T111620Z UTC

## Non-negotiable constraints

- WRDS login is forbidden.
- No external or new raw data; use local prepared parquet/artifacts only.
- No cloud/OCI auto-provisioning.
- No parallel heavy experiments; run one heavy command at a time.
- Do not overwrite existing reports, ledgers, manifests, or experiment outputs.
- Research diagnostics only; not investment, trading, legal, tax, production, or deployment advice.

## Termination rule

Continue sequentially and autonomously until the user explicitly stops, or until 5 consecutive hypotheses produce no meaningful progress.

## Anchor

Baseline anchor: reports/factor_router_anchor_20260529T082412Z.md / reports/factor_router_anchor_20260529T082412Z.json

## Runs


### 1. selected-factor-count-7

- Ledger/report: `reports/factor_router_seq_1_selected-factor-count-7_20260529T111620Z.json` / `reports/factor_router_seq_1_selected-factor-count-7_20260529T111620Z.md`
- Result: cumulative 11.282145, CAGR 8.18%, MDD -29.51%, turnover 11.30%.
- Anchor deltas: cumulative -1.273594, CAGR -0.33%, MDD +13.56%, turnover -3.94%.
- Progress: yes (materially lower MDD than N=13 anchor; materially lower turnover than N=13 anchor; child manifest data-boundary now matches harness boundary). Consecutive no-progress count: 0.
- Interpretation: N=7 reduces concentration breadth and gives up some cumulative return/CAGR versus N=13, but substantially improves OOS max drawdown and turnover. Treat as a useful risk/implementation-efficiency branch, not an outright replacement because tax-proxy rows and missing factor/leg diagnostics still require follow-up.
- Next hypothesis: Run local-only under the same walk-forward OOS protocol to isolate local-state factor families and compare whether the drawdown/turnover improvement comes from local versus global factor composition.

### 2. local-only

- Ledger/report: `reports/factor_router_seq_2_local-only_20260529T112801Z.json` / `reports/factor_router_seq_2_local-only_20260529T112801Z.md`
- Result: cumulative 34.782338, CAGR 11.86%, MDD -33.24%, turnover 43.46%.
- Anchor deltas: cumulative +22.226599, CAGR +3.35%, MDD +9.83%, turnover +28.22%.
- Progress: yes (materially higher cumulative return than anchor; higher CAGR than anchor; lower MDD than anchor). Consecutive no-progress count: 0.
- Interpretation: Local-only strongly improves gross OOS return/CAGR versus the selected-13 anchor while also improving MDD, but it carries much higher turnover. This makes local-state factors promising for alpha, while implementation realism/cost sensitivity must be checked before any preference.
- Next hypothesis: Run global-only under the same protocol to complete the local/global isolation pair and determine whether global-return families are diversifying, return-generating, or mostly dilutive relative to local-only.

### 3. global-only

- Ledger/report: `reports/factor_router_seq_3_global-only_20260529T113939Z.json` / `reports/factor_router_seq_3_global-only_20260529T113939Z.md`
- Result: cumulative 5.323066, CAGR 5.96%, MDD -59.35%, turnover 19.98%.
- Anchor deltas: cumulative -7.232673, CAGR -2.55%, MDD -16.28%, turnover +4.74%.
- Local-only deltas: cumulative -29.459272, CAGR -5.90%, MDD -26.11%, turnover -23.48%.
- Progress: yes (completed local/global isolation pair; global-only is materially weaker than local-only, narrowing the next search toward local-heavy or quota designs; identified worse drawdown risk in global-only branch). Consecutive no-progress count: 0.
- Interpretation: Global-only is much weaker than local-only and weaker than the selected-13 anchor on gross return and MDD. This supports the hypothesis that local-state factors carry most of the useful signal in this full-panel QSpread setup; global factors may be useful only as constrained diversifiers, not as a standalone universe.
- Next hypothesis: Run quota 6:7 to test whether a forced global/local blend can preserve part of local-only return while controlling turnover/drawdown better than pure local-only.

### 4. quota-policy 6:7

- Ledger/report: `reports/factor_router_seq_4_quota-policy_20260529T115054Z.json` / `reports/factor_router_seq_4_quota-policy_20260529T115054Z.md`
- Result: cumulative 16.705907, CAGR 9.42%, MDD -35.19%, turnover 16.21%.
- Anchor deltas: cumulative +4.150167, CAGR +0.91%, MDD +7.88%, turnover +0.96%.
- Local-only deltas: cumulative -18.076432, CAGR -2.44%, MDD -1.95%, turnover -27.26%.
- Progress: yes (higher cumulative return than anchor; higher CAGR than anchor; lower MDD than anchor; much lower turnover than local-only while retaining positive return lift over anchor). Consecutive no-progress count: 0.
- Interpretation: The 6:7 quota branch is a useful middle ground: it beats the selected-13 anchor on gross return/CAGR and MDD, and it sharply reduces turnover versus local-only. It does not dominate local-only on return, so it is best framed as a balanced implementation-realism branch.
- Next hypothesis: Run category cap=3 to test whether reducing family concentration improves drawdown/turnover without sacrificing too much of the local-heavy gross signal.

### 5a. category-cap=3 first attempt: infrastructure failure

- Ledger/report: `reports/factor_router_seq_5_family-cap-policy_20260529T120222Z.json` / `reports/factor_router_seq_5_family-cap-policy_20260529T120222Z.md`
- Status: failed and ledgered by harness before producing performance metrics.
- Failure: local disk full while writing local parquet factor-score artifact. No WRDS, external data, cloud, or parallel execution was involved.
- Non-progress counter: unchanged because this was an infrastructure failure, not a completed hypothesis result.
- Recovery: free non-project caches only, preserve completed experiment/report artifacts, then retry with a fresh unique path.

### 5b. category-cap=3 retry

- Ledger/report: `reports/factor_router_seq_5_family-cap-policy_retry_20260529T120707Z.json` / `reports/factor_router_seq_5_family-cap-policy_retry_20260529T120707Z.md`
- Result: cumulative 27.302132, CAGR 11.04%, MDD -31.48%, turnover 56.27%.
- Anchor deltas: cumulative +14.746393, CAGR +2.53%, MDD +11.59%, turnover +41.03%.
- Local-only deltas: cumulative -7.480206, CAGR -0.82%, MDD +1.76%, turnover +12.81%.
- Quota deltas: cumulative +10.596225, CAGR +1.62%, MDD +3.71%, turnover +40.07%.
- Progress: yes (higher cumulative return than anchor; higher CAGR than anchor; lower MDD than anchor; lower max factor weight / concentration than anchor). Consecutive no-progress count: 0.
- Interpretation: Category cap=3 is a high-return/high-turnover branch: it beats anchor and quota on gross return and MDD and lowers factor concentration, but its turnover exceeds local-only. It is research-useful for factor-family diversification diagnostics, not immediately preferable on execution realism.
- Next hypothesis: Because disk capacity is now the binding resource, first add/report a storage-aware continuation note; then prioritize one-at-a-time q robustness on the most informative branches: local-only q=0.20/0.40 or quota q=0.20/0.40, unless storage-light harnessing is added.

### 6. local-only q=0.40 storage-light follow-up

- Ledger/report: `reports/factor_router_auto_6_local-only-q40_20260529T122202Z.json` / `reports/factor_router_auto_6_local-only-q40_20260529T122202Z.md`
- Result: cumulative 15.138968, CAGR 9.11%, MDD -27.22%, turnover 37.28%.
- Local q=0.30 deltas: cumulative -19.643370, CAGR -2.76%, MDD +6.02%, turnover -6.18%.
- Progress: yes (local-only q=0.40 materially lowers MDD versus local-only q=0.30; local-only q=0.40 lowers turnover versus local-only q=0.30).
- Interpretation: q=0.40 local-only trades off much lower cumulative/CAGR versus local-only q=0.30 for materially better drawdown and lower turnover; storage-light mode completed and reclaimed factor-score intermediates for this new run.

### 7. local-only q=0.20 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_7_local-only-q20_20260529T132756Z.json` / `reports/factor_router_auto_7_local-only-q20_20260529T132756Z.md`
- Result: cumulative 76.778691, CAGR 14.62%, MDD -39.18%, turnover 63.87%.
- Local q=0.30 deltas: cumulative +41.996353, CAGR +2.75%, MDD -5.94%, turnover +20.41%.
- Local q=0.40 deltas: cumulative +61.639723, CAGR +5.51%, MDD -11.96%, turnover +26.59%.
- Progress: yes (local-only q=0.20 improves cumulative return versus q=0.30; local-only q=0.20 improves CAGR versus q=0.30). Consecutive no-progress count: 0.
- Interpretation: local-only q=0.20 completes the first local-only q robustness triangle with q=0.30 and q=0.40. It is preserved with factor_scores for dashboard-grade stock/factor drilldowns.

### 8. quota 6:7 q=0.20 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_8_quota-q20_20260529T133938Z.json` / `reports/factor_router_auto_8_quota-q20_20260529T133938Z.md`
- Result: cumulative 86.701693, CAGR 15.05%, MDD -41.16%, turnover 65.09%.
- Quota q=0.30 deltas: cumulative +69.995786, CAGR +5.63%, MDD -5.97%, turnover +48.89%.
- Local q=0.20 deltas: cumulative +9.923002, CAGR +0.43%, MDD -1.98%, turnover +1.22%.
- Progress: yes (quota q=0.20 improves cumulative return versus quota q=0.30; quota q=0.20 improves CAGR versus quota q=0.30). Consecutive no-progress count: 0.
- Interpretation: quota 6:7 q=0.20 tests whether the high-return q=0.20 tail can be kept while reducing local-only turnover/drawdown through constrained global/local blending.

### 9. quota 6:7 q=0.40 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_9_quota-q40_20260529T135115Z.json` / `reports/factor_router_auto_9_quota-q40_20260529T135115Z.md`
- Result: cumulative 9.512148, CAGR 7.65%, MDD -30.59%, turnover 14.01%.
- Quota q=0.30 deltas: cumulative -7.193759, CAGR -1.77%, MDD +4.60%, turnover -2.20%.
- Quota q=0.20 deltas: cumulative -77.189545, CAGR -7.40%, MDD +10.57%, turnover -51.08%.
- Progress: yes (quota q=0.40 improves MDD versus quota q=0.30; quota q=0.40 is materially more defensive than quota q=0.20; quota q=0.40 materially lowers turnover versus quota q=0.20). Consecutive no-progress count: 0.
- Interpretation: quota 6:7 q=0.40 closes the quota q-grid triangle and tests whether the blended branch can become a defensive/low-turnover candidate.

### 10. quota 6:7 q=0.20 min_weight=0.01 storage-light follow-up

- Ledger/report: `reports/factor_router_auto_10_quota-q20-mw001_20260529T140336Z.json` / `reports/factor_router_auto_10_quota-q20-mw001_20260529T140336Z.md`
- Result: cumulative 87.726836, CAGR 15.09%, MDD -41.16%, turnover 65.10%.
- Quota q=0.20 baseline deltas: cumulative +1.025143, CAGR +0.04%, MDD +0.00%, turnover +0.00%.
- Progress: no (no material balanced-scorecard improvement). Consecutive no-progress count: 1.
- Interpretation: min_weight 0.01 checks whether smoothing factor allocations improves implementation realism for the aggressive quota q=0.20 branch.

### 11. quota 4:9 q=0.30 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_11_quota4x9-q30_20260529T141514Z.json` / `reports/factor_router_auto_11_quota4x9-q30_20260529T141514Z.md`
- Result: cumulative 18.491299, CAGR 9.75%, MDD -31.64%, turnover 16.67%.
- Quota 6:7 q=0.30 deltas: cumulative +1.785392, CAGR +0.33%, MDD +3.56%, turnover +0.46%.
- Local q=0.30 deltas: cumulative -16.291040, CAGR -2.11%, MDD +1.61%, turnover -26.79%.
- Progress: yes (quota 4:9 q=0.30 improves cumulative return versus quota 6:7 q=0.30; quota 4:9 keeps turnover below local-only while improving over quota 6:7; quota 4:9 improves MDD versus quota 6:7). Consecutive no-progress count: 0.
- Interpretation: quota 4:9 q=0.30 tests whether a local-heavier blend improves the balanced q30 branch without fully inheriting local-only turnover.

### 12. quota 3:10 q=0.30 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_12_quota3x10-q30_20260529T142649Z.json` / `reports/factor_router_auto_12_quota3x10-q30_20260529T142649Z.md`
- Result: cumulative 18.433526, CAGR 9.74%, MDD -29.61%, turnover 16.91%.
- Quota 4:9 q=0.30 deltas: cumulative -0.057773, CAGR -0.01%, MDD +2.02%, turnover +0.24%.
- Local q=0.30 deltas: cumulative -16.348813, CAGR -2.12%, MDD +3.63%, turnover -26.55%.
- Progress: yes (quota 3:10 q=0.30 improves MDD versus quota 4:9; quota 3:10 remains lower-turnover than local-only while beating quota 6:7). Consecutive no-progress count: 0.
- Interpretation: quota 3:10 q=0.30 pushes the local-heavy blend further to test whether the q30 balanced branch has a better local/global allocation than 4:9 or 6:7.

### 13. quota 2:11 q=0.30 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_13_quota2x11-q30_20260529T143825Z.json` / `reports/factor_router_auto_13_quota2x11-q30_20260529T143825Z.md`
- Result: cumulative 16.061166, CAGR 9.30%, MDD -29.05%, turnover 17.17%.
- Quota 3:10 q=0.30 deltas: cumulative -2.372360, CAGR -0.45%, MDD +0.57%, turnover +0.26%.
- Local q=0.30 deltas: cumulative -18.721172, CAGR -2.57%, MDD +4.20%, turnover -26.29%.
- Progress: no (no material balanced-scorecard improvement). Consecutive no-progress count: 1.
- Interpretation: quota 2:11 q=0.30 checks whether local-heavy blending keeps improving or starts converging toward local-only behavior.

### 14. quota 3:10 q=0.40 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_14_quota3x10-q40_20260529T145236Z.json` / `reports/factor_router_auto_14_quota3x10-q40_20260529T145236Z.md`
- Result: cumulative 9.605838, CAGR 7.68%, MDD -23.68%, turnover 14.24%.
- Quota 3:10 q=0.30 deltas: cumulative -8.827688, CAGR -2.06%, MDD +5.93%, turnover -2.67%.
- Quota 6:7 q=0.40 deltas: cumulative +0.093690, CAGR +0.03%, MDD +6.91%, turnover +0.23%.
- Local-only q=0.40 deltas: cumulative -5.533131, CAGR -1.43%, MDD +3.54%, turnover -23.04%.
- Factor scores: preserved for later dashboard/drilldown use.
- Progress: yes (lowest MDD observed so far among completed full-panel factor-router runs; materially improves MDD versus quota 3:10 q=0.30 while keeping turnover low; improves MDD versus quota 6:7 q=0.40 with essentially similar gross return profile). Consecutive no-progress count: 0.
- Interpretation: quota 3:10 q=0.40 converts the best local-heavy q30 branch into the current most defensive branch: return falls versus q30, but MDD improves sharply to -23.68% and turnover remains low. This is a strong dashboard/report candidate for the defensive sleeve, with factor_scores preserved.
- Next hypothesis: Test quota 4:9 q=0.40 to see whether the q40 defensive improvement is specific to 3:10 or robust across adjacent local-heavy quota allocations.

### 15. quota 4:9 q=0.40 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_15_quota4x9-q40_20260529T150514Z.json` / `reports/factor_router_auto_15_quota4x9-q40_20260529T150514Z.md`
- Result: cumulative 9.753405, CAGR 7.73%, MDD -25.73%, turnover 14.15%.
- Quota 4:9 q=0.30 deltas: cumulative -8.737894, CAGR -2.03%, MDD +5.91%, turnover -2.52%.
- Quota 3:10 q=0.40 deltas: cumulative +0.147568, CAGR +0.05%, MDD -2.05%, turnover -0.09%.
- Quota 6:7 q=0.40 deltas: cumulative +0.241257, CAGR +0.08%, MDD +4.86%, turnover +0.14%.
- Factor scores: preserved for later dashboard/drilldown use.
- Progress: yes (confirms the q=0.40 defensive improvement is robust in an adjacent local-heavy 4:9 quota branch; materially improves MDD versus the same 4:9 quota at q=0.30 with lower turnover; beats the earlier 6:7 q=0.40 branch on MDD with similar turnover and slightly higher return). Consecutive no-progress count: 0.
- Interpretation: quota 4:9 q=0.40 does not beat quota 3:10 q=0.40 on MDD, but it confirms that the defensive q40 result is not a one-off: local-heavy 4:9 also shifts the q30 branch toward much lower drawdown and turnover at the cost of return.
- Next hypothesis: Run quota 2:11 q=0.40 to test whether the defensive q40 pattern persists when the quota becomes even more local-heavy, or whether it starts converging toward local-only behavior.

### 16. quota 2:11 q=0.40 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_16_quota2x11-q40_20260529T151702Z.json` / `reports/factor_router_auto_16_quota2x11-q40_20260529T151702Z.md`
- Result: cumulative 9.289577, CAGR 7.58%, MDD -20.68%, turnover 14.46%.
- Quota 2:11 q=0.30 deltas: cumulative -6.771588, CAGR -1.72%, MDD +8.37%, turnover -2.71%.
- Quota 3:10 q=0.40 deltas: cumulative -0.316260, CAGR -0.10%, MDD +3.00%, turnover +0.22%.
- Local-only q=0.40 deltas: cumulative -5.849391, CAGR -1.53%, MDD +6.54%, turnover -22.82%.
- Factor scores: preserved for later dashboard/drilldown use.
- Progress: yes (new lowest MDD observed so far among completed full-panel factor-router runs; materially improves MDD versus quota 2:11 q=0.30 with lower turnover; improves MDD versus quota 3:10 q=0.40, extending the local-heavy defensive frontier). Consecutive no-progress count: 0.
- Interpretation: quota 2:11 q=0.40 pushes the defensive frontier further: it sacrifices additional return versus 3:10/4:9 q40, but improves MDD to -20.68% with still-low turnover. This suggests a small number of global factors may stabilize an otherwise very local-heavy q40 sleeve better than pure local-only q40.
- Next hypothesis: Run quota 1:12 q=0.40 as a boundary test: determine whether even less global exposure continues improving drawdown or starts reverting toward local-only q40 behavior.

### 17. quota 1:12 q=0.40 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_17_quota1x12-q40_20260529T152859Z.json` / `reports/factor_router_auto_17_quota1x12-q40_20260529T152859Z.md`
- Result: cumulative 7.882552, CAGR 7.08%, MDD -17.14%, turnover 14.59%.
- Quota 2:11 q=0.40 deltas: cumulative -1.407025, CAGR -0.49%, MDD +3.54%, turnover +0.13%.
- Local-only q=0.40 deltas: cumulative -7.256416, CAGR -2.02%, MDD +10.08%, turnover -22.70%.
- Factor scores: preserved for later dashboard/drilldown use.
- Progress: yes (new lowest MDD observed so far among completed full-panel factor-router runs; extends the local-heavy q40 defensive frontier from 2:11 to 1:12; shows the return-drawdown trade-off remains monotonic toward lower drawdown before pure local-only reversion). Consecutive no-progress count: 0.
- Interpretation: quota 1:12 q=0.40 is the current defensive extreme: MDD improves to -17.14% while cumulative return/CAGR fall. Because pure local-only q40 has much worse MDD, one global slot appears to be a stabilizing bridge rather than a useless dilution.
- Next hypothesis: Switch from defensive q40 mapping to aggressive q20 mapping on the best local-heavy quota family; run quota 3:10 q=0.20 to see whether local-heavy quotas can improve the high-return q20 branch or only add drawdown/turnover.

### 18. quota 3:10 q=0.20 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_18_quota3x10-q20_20260529T154046Z.json` / `reports/factor_router_auto_18_quota3x10-q20_20260529T154046Z.md`
- Result: cumulative 95.020090, CAGR 15.37%, MDD -39.27%, turnover 64.72%.
- Quota 6:7 q=0.20 deltas: cumulative +8.318397, CAGR +0.33%, MDD +1.89%, turnover -0.37%.
- Local-only q=0.20 deltas: cumulative +18.241399, CAGR +0.76%, MDD -0.09%, turnover +0.85%.
- Quota 3:10 q=0.30 deltas: cumulative +76.586565, CAGR +5.63%, MDD -9.66%, turnover +47.82%.
- Factor scores: preserved for later dashboard/drilldown use.
- Progress: yes (new highest cumulative return observed so far among completed full-panel factor-router runs; higher CAGR than quota 6:7 q=0.20 with slightly better MDD and turnover; extends the local-heavy quota result to the aggressive q=0.20 branch). Consecutive no-progress count: 0.
- Interpretation: quota 3:10 q=0.20 becomes the current aggressive-return frontier: it improves cumulative return/CAGR over the prior 6:7 q20 branch while modestly improving MDD and turnover. This suggests local-heavy quota tuning is useful on both the defensive q40 and aggressive q20 surfaces, though q20 still carries high drawdown and turnover.
- Next hypothesis: Run quota 2:11 q=0.20 to test whether making the aggressive q20 branch even more local-heavy keeps improving return/MDD or starts converging toward weaker local-only q20 behavior.

### 19. quota 2:11 q=0.20 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_19_quota2x11-q20_20260529T155216Z.json` / `reports/factor_router_auto_19_quota2x11-q20_20260529T155216Z.md`
- Result: cumulative 87.516475, CAGR 15.08%, MDD -40.79%, turnover 64.52%.
- Quota 3:10 q=0.20 deltas: cumulative -7.503615, CAGR -0.29%, MDD -1.53%, turnover -0.20%.
- Quota 6:7 q=0.20 deltas: cumulative +0.814782, CAGR +0.03%, MDD +0.37%, turnover -0.57%.
- Local-only q=0.20 deltas: cumulative +10.737784, CAGR +0.47%, MDD -1.62%, turnover +0.65%.
- Factor scores: preserved for later dashboard/drilldown use.
- Progress: no (no material balanced-scorecard improvement over the 3:10 q=0.20 aggressive frontier). Consecutive no-progress count: 1.
- Interpretation: quota 2:11 q=0.20 does not improve the aggressive frontier. It gives up meaningful cumulative return/CAGR versus quota 3:10 q20 and worsens MDD, while only slightly lowering turnover. This suggests the aggressive q20 optimum may be around 3:10 rather than more local-heavy.
- Next hypothesis: Run quota 4:9 q=0.20 to complete the adjacent aggressive q20 sweep around the 3:10 winner and check whether a slightly less local-heavy quota can beat it.

### 20. quota 4:9 q=0.20 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_20_quota4x9-q20_20260529T160344Z.json` / `reports/factor_router_auto_20_quota4x9-q20_20260529T160344Z.md`
- Result: cumulative 93.270822, CAGR 15.31%, MDD -40.08%, turnover 64.84%.
- Quota 3:10 q=0.20 deltas: cumulative -1.749268, CAGR -0.07%, MDD -0.81%, turnover +0.12%.
- Quota 2:11 q=0.20 deltas: cumulative +5.754347, CAGR +0.23%, MDD +0.72%, turnover +0.32%.
- Quota 6:7 q=0.20 deltas: cumulative +6.569129, CAGR +0.26%, MDD +1.08%, turnover -0.25%.
- Factor scores: preserved for later dashboard/drilldown use.
- Progress: no (does not materially improve the quota 3:10 q=0.20 aggressive frontier). Consecutive no-progress count: 2.
- Interpretation: quota 4:9 q=0.20 is strong but still does not beat quota 3:10 q20: it has lower return/CAGR, worse MDD, and slightly higher turnover. Together with 2:11 q20, this brackets 3:10 as the current aggressive quota peak rather than proving a new branch.
- Next hypothesis: Move from quota-only tuning to model variation on the best aggressive branch. Run a budget-aware non-baseline model on quota 3:10 q=0.20, preserving local-data/no-WRDS and one-heavy-run constraints.

### 21. ridge quota 3:10 q=0.20 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_21_ridge-quota3x10-q20_20260529T161527Z.json` / `reports/factor_router_auto_21_ridge-quota3x10-q20_20260529T161527Z.md`
- Result: cumulative 78.039576, CAGR 14.67%, MDD -38.36%, turnover 60.61%.
- Baseline_mean quota 3:10 q=0.20 deltas: cumulative -16.980514, CAGR -0.70%, MDD +0.91%, turnover -4.12%.
- Quota 6:7 q=0.20 deltas: cumulative -8.662117, CAGR -0.37%, MDD +2.80%, turnover -4.48%.
- Local-only q=0.20 deltas: cumulative +1.260885, CAGR +0.06%, MDD +0.82%, turnover -3.26%.
- Factor scores: preserved for later model/factor dashboard drilldown.
- Progress: yes (adds the first non-baseline ML model comparison on the strongest aggressive branch; ridge lowers MDD and turnover versus baseline_mean quota 3:10 q=0.20; ridge provides a lower-risk/lower-turnover model diagnostic despite lower return). Consecutive no-progress count: 0.
- Interpretation: Ridge does not beat baseline_mean on return, but it materially reduces MDD and turnover on the same 3:10 q20 surface. This is useful evidence that model choice changes the return/risk/implementation trade-off and can support factor-diagnostic comparisons in the final report.
- Next hypothesis: Run elasticnet on the same quota 3:10 q=0.20 branch to test whether sparse linear regularization changes the model-factor trade-off relative to ridge and baseline_mean.

### 22. elasticnet quota 3:10 q=0.20 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_22_elasticnet-quota3x10-q20_20260529T162656Z.json` / `reports/factor_router_auto_22_elasticnet-quota3x10-q20_20260529T162656Z.md`
- Result: cumulative 235.433656, CAGR 18.68%, MDD -21.20%, turnover 61.29%.
- Baseline_mean quota 3:10 q=0.20 deltas: cumulative +140.413566, CAGR +3.30%, MDD +18.07%, turnover -3.43%.
- Ridge quota 3:10 q=0.20 deltas: cumulative +157.394080, CAGR +4.01%, MDD +17.16%, turnover +0.69%.
- Defensive quota 1:12 q=0.40 deltas: cumulative +227.551104, CAGR +11.60%, MDD -4.07%, turnover +46.71%.
- Factor scores: preserved for later model/factor dashboard drilldown.
- Progress: yes (new highest cumulative return and CAGR observed so far; materially improves MDD versus baseline_mean quota 3:10 q=0.20 while also increasing return; elasticnet creates a distinct sparse-linear model branch worth diagnostics and q-robustness follow-up). Consecutive no-progress count: 0.
- Interpretation: ElasticNet is a major model-axis break from the baseline: on quota 3:10 q20 it sharply raises cumulative return/CAGR while cutting MDD close to the defensive q40 family, though turnover remains high and factor concentration rises. This branch must be treated as research evidence needing robustness checks, not as production advice.
- Next hypothesis: Run elasticnet on quota 3:10 q=0.30 to test whether the sparse-linear improvement is robust beyond the aggressive q=0.20 cutoff.

### 23. elasticnet quota 3:10 q=0.30 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_23_elasticnet-quota3x10-q30_20260529T163847Z.json` / `reports/factor_router_auto_23_elasticnet-quota3x10-q30_20260529T163847Z.md`
- Result: cumulative 27.099912, CAGR 11.02%, MDD -21.33%, turnover 40.79%.
- Elasticnet quota 3:10 q=0.20 deltas: cumulative -208.333745, CAGR -7.66%, MDD -0.13%, turnover -20.50%.
- Baseline_mean quota 3:10 q=0.30 deltas: cumulative +8.666386, CAGR +1.28%, MDD +8.28%, turnover +23.88%.
- Defensive quota 1:12 q=0.40 deltas: cumulative +19.217359, CAGR +3.93%, MDD -4.19%, turnover +26.20%.
- Factor scores: preserved for later model/factor dashboard drilldown.
- Progress: yes (elasticnet q=0.30 improves both return and MDD versus baseline_mean quota 3:10 q=0.30; confirms elasticnet improvement is not limited to the q=0.20 cutoff, though the explosive q20 return is not replicated; provides a medium-q model/factor branch for final q-robustness diagnostics). Consecutive no-progress count: 0.
- Interpretation: ElasticNet q30 is not the q20-style high-return outlier, but it remains better than baseline_mean q30 on return and drawdown. The trade-off is materially higher turnover and higher factor concentration, so this branch is useful for q-robustness and model-factor diagnostics rather than an unqualified replacement.
- Next hypothesis: Run elasticnet on quota 3:10 q=0.40 to complete the q robustness triangle for the sparse-linear model.



> Additional stop condition: disk availability <= 2GB now stops further heavy experiments and moves the workflow to reporting/verification.

### 24. elasticnet quota 3:10 q=0.40 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_24_elasticnet-quota3x10-q40_20260529T165043Z.json` / `reports/factor_router_auto_24_elasticnet-quota3x10-q40_20260529T165043Z.md`
- Result: cumulative 10.847985, CAGR 8.05%, MDD -18.09%, turnover 34.56%.
- Elasticnet quota 3:10 q=0.30 deltas: cumulative -16.251927, CAGR -2.96%, MDD +3.23%, turnover -6.23%.
- Baseline_mean quota 3:10 q=0.40 deltas: cumulative +1.242147, CAGR +0.37%, MDD +5.58%, turnover +20.31%.
- Defensive baseline quota 1:12 q=0.40 deltas: cumulative +2.965433, CAGR +0.97%, MDD -0.96%, turnover +19.97%.
- Factor scores: preserved for later model/factor dashboard drilldown.
- Progress: yes (completes elasticnet q=0.20/0.30/0.40 robustness triangle; elasticnet q=0.40 improves return and MDD versus baseline_mean quota 3:10 q=0.40; provides a sparse-linear defensive branch close to the best baseline defensive MDD while retaining higher return). Consecutive no-progress count: 0.
- Disk stop check after completion: 11GB available, above the new 2GB stop threshold.
- Interpretation: ElasticNet q40 completes the sparse-linear q triangle. It is not the high-return q20 outlier, but it improves baseline 3:10 q40 on both return and drawdown. Compared with the baseline 1:12 q40 defensive extreme, it gives up some MDD and much more turnover for higher return, so it belongs in the return/drawdown frontier discussion rather than as a single winner.
- Next hypothesis: Run elasticnet quota 1:12 q=0.40 to test whether the sparse-linear model can combine the baseline defensive quota extreme with elasticnet model lift.

### 25. elasticnet quota 1:12 q=0.40 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_25_elasticnet-quota1x12-q40_20260529T170240Z.json` / `reports/factor_router_auto_25_elasticnet-quota1x12-q40_20260529T170240Z.md`
- Result: cumulative 9.601885, CAGR 7.68%, MDD -17.32%, turnover 35.23%.
- Elasticnet quota 3:10 q=0.40 deltas: cumulative -1.246100, CAGR -0.38%, MDD +0.78%, turnover +0.67%.
- Baseline quota 1:12 q=0.40 deltas: cumulative +1.719332, CAGR +0.60%, MDD -0.18%, turnover +20.64%.
- Elasticnet quota 3:10 q=0.20 deltas: cumulative -225.831772, CAGR -11.00%, MDD +3.89%, turnover -26.07%.
- Factor scores: preserved for later model/factor dashboard drilldown.
- Progress: no (boundary diagnostic, but no material balanced-scorecard frontier improvement). Consecutive no-progress count: 1.
- Disk stop check after completion: 10GB available, above the 2GB stop threshold.
- Interpretation: ElasticNet 1:12 q40 does not create a cleaner defensive frontier. It marginally improves MDD versus ElasticNet 3:10 q40, but loses return and raises turnover; versus baseline 1:12 q40 it raises return but slightly worsens MDD and substantially raises turnover. Treat as a boundary diagnostic, not a new preferred branch.
- Next hypothesis: Run ElasticNet 2:11 q=0.40 as the intermediate defensive point between 3:10 and 1:12 to check whether the sparse-linear defensive trade-off has a better interior quota.

### 26. elasticnet quota 2:11 q=0.40 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_26_elasticnet-quota2x11-q40_20260529T171433Z.json` / `reports/factor_router_auto_26_elasticnet-quota2x11-q40_20260529T171433Z.md`
- Result: cumulative 10.424073, CAGR 7.93%, MDD -18.20%, turnover 34.90%.
- Elasticnet quota 3:10 q=0.40 deltas: cumulative -0.423912, CAGR -0.12%, MDD -0.11%, turnover +0.34%.
- Elasticnet quota 1:12 q=0.40 deltas: cumulative +0.822188, CAGR +0.25%, MDD -0.89%, turnover -0.33%.
- Baseline quota 2:11 q=0.40 deltas: cumulative +1.134495, CAGR +0.35%, MDD +2.47%, turnover +20.44%.
- Factor scores: preserved for later model/factor dashboard drilldown.
- Progress: no (no material frontier improvement on the sparse-linear defensive q40 surface). Consecutive no-progress count: 2.
- Disk stop check after completion: 9.4GB available, above the 2GB stop threshold.
- Interpretation: ElasticNet 2:11 q40 also fails to improve the sparse-linear defensive frontier. It sits between 3:10 and 1:12 on return, but does not improve drawdown or turnover enough to justify another frontier. The ElasticNet defensive q40 surface is therefore less attractive than the q20/q30 ElasticNet evidence.
- Next hypothesis: Shift back to the high-return ElasticNet q=0.20 branch and test adjacent quota 4:9 to see whether the sparse-linear aggressive peak is truly at 3:10 or can be improved by slightly more global exposure.

### 27. elasticnet quota 4:9 q=0.20 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_27_elasticnet-quota4x9-q20_20260529T172616Z.json` / `reports/factor_router_auto_27_elasticnet-quota4x9-q20_20260529T172616Z.md`
- Result: cumulative 234.435052, CAGR 18.66%, MDD -21.55%, turnover 61.08%.
- Elasticnet quota 3:10 q=0.20 deltas: cumulative -0.998605, CAGR -0.02%, MDD -0.35%, turnover -0.21%.
- Baseline quota 4:9 q=0.20 deltas: cumulative +141.164229, CAGR +3.35%, MDD +18.53%, turnover -3.76%.
- Ridge quota 3:10 q=0.20 deltas: cumulative +156.395476, CAGR +3.99%, MDD +16.81%, turnover +0.48%.
- Factor scores: preserved for later model/factor dashboard drilldown.
- Progress: no (near tie, but no material improvement over ElasticNet 3:10 q=0.20). Consecutive no-progress count: 3.
- Disk stop check after completion: 8.8GB available, above the 2GB stop threshold.
- Interpretation: ElasticNet 4:9 q20 is nearly tied with 3:10 q20 but does not improve it: return/CAGR and MDD are slightly worse, while turnover is only modestly lower. This brackets the sparse-linear aggressive peak from the more-global side and keeps 3:10 q20 as the current high-return ElasticNet branch.
- Next hypothesis: Run ElasticNet 2:11 q=0.20 to bracket the sparse-linear aggressive peak from the more-local side before deciding whether to stop or move to another axis.

### 28. elasticnet quota 2:11 q=0.20 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_28_elasticnet-quota2x11-q20_20260529T173755Z.json` / `reports/factor_router_auto_28_elasticnet-quota2x11-q20_20260529T173755Z.md`
- Result: cumulative 221.749419, CAGR 18.46%, MDD -21.43%, turnover 61.13%.
- Elasticnet quota 3:10 q=0.20 deltas: cumulative -13.684237, CAGR -0.22%, MDD -0.23%, turnover -0.16%.
- Elasticnet quota 4:9 q=0.20 deltas: cumulative -12.685632, CAGR -0.21%, MDD +0.12%, turnover +0.05%.
- Baseline quota 2:11 q=0.20 deltas: cumulative +134.232944, CAGR +3.38%, MDD +19.36%, turnover -3.39%.
- Factor scores: preserved for later model/factor dashboard drilldown.
- Progress: no (does not improve ElasticNet 3:10 q=0.20 or the near-tie 4:9 q=0.20 branch). Consecutive no-progress count: 4.
- Disk stop check after completion: 8.2GB available, above the 2GB stop threshold.
- Interpretation: ElasticNet 2:11 q20 is worse than the 3:10 q20 frontier and also below the near-tie 4:9 q20 branch. The sparse-linear aggressive peak is now bracketed on both quota sides, with 3:10 remaining the best observed q20 allocation.
- Next hypothesis: Use the last pre-stop slot on a different axis: ElasticNet category-cap=3 q=0.20, testing whether family diversification can reduce concentration/drawdown or improve return before terminating on five non-progress hypotheses.

### 29. elasticnet category-cap=3 q=0.20 preserved-score follow-up

- Ledger/report: `reports/factor_router_auto_29_elasticnet-categorycap3-q20_20260529T174935Z.json` / `reports/factor_router_auto_29_elasticnet-categorycap3-q20_20260529T174935Z.md`
- Result: cumulative 193.656964, CAGR 17.96%, MDD -23.09%, turnover 61.57%.
- Elasticnet quota 3:10 q=0.20 deltas: cumulative -41.776692, CAGR -0.72%, MDD -1.89%, turnover +0.27%.
- Baseline category-cap=3 q=0.30 deltas: cumulative +166.354832, CAGR +6.92%, MDD +8.39%, turnover +5.29%.
- Elasticnet quota 4:9 q=0.20 deltas: cumulative -40.778087, CAGR -0.71%, MDD -1.54%, turnover +0.48%.
- Factor scores: preserved for later model/factor dashboard drilldown.
- Progress: no (category cap lowers concentration slightly but does not improve the balanced-scorecard frontier). Consecutive no-progress count: 5.
- Disk stop check after completion: 7.6GB available, above the 2GB disk threshold.
- Stop trigger: five consecutive completed non-progress hypotheses reached; heavy experiments stop here.
- Interpretation: ElasticNet category-cap=3 q20 improves greatly over the old baseline category-cap branch, but it does not improve the ElasticNet 3:10 q20 frontier: lower return/CAGR, worse MDD, and slightly higher turnover. It does slightly lower factor concentration, but not enough to count as a balanced-scorecard improvement.
- Next step: Stop heavy experiments because five consecutive completed hypotheses produced no material frontier improvement; move to final reporting, README update, and verification.


## Heavy-experiment stop

Heavy experiments stopped after run 29 because the user-defined rule of five consecutive completed non-progress hypotheses was reached. The disk threshold did not trigger; available space was still 7.6GB, above the 2GB stop rule.
