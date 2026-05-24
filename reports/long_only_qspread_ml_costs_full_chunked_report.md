# autoquant-lab Long-only QSpread 추가 실험 보고서

작성일: 2026-05-24

기존 DDQM2 matrix report: [`reports/usa_ddqm2_matrix_report_ko.md`](usa_ddqm2_matrix_report_ko.md)

## 초록

본 추가 실험은 기존 DDQM2/EQR long-short 결과를 덮지 않고, 같은 연구 결을 유지한 채 stock-score QSpread를 **long-only top-q equal-weight fully-invested** 포트폴리오로 재해석한 것이다. 실험은 로컬 parquet artifact만 사용했으며 WRDS 로그인, 신규 원천 데이터 다운로드, 외부 데이터 보강은 수행하지 않았다.

핵심 변경점은 세 가지다. 첫째, full monthly label panel 2,082,485 rows를 사용하기 위해 feature preparation을 date-partitioned chunk 방식으로 확장했다. 둘째, 기존 short leg 최적화는 추가하지 않고 long-only top-q surface만 별도 산출물로 평가했다. 셋째, gross 성과와 함께 보수적 거래비용/세금 proxy를 primary net lens로 기록했다.

## 1. 연구 범위와 보존 원칙

- 기존 `reports/usa_ddqm2_matrix_report_*.md`와 기존 `experiments/ddqm2*` 결과를 수정하지 않는다.
- 이번 결과는 `experiments/ddqm2_long_only_full_chunked/` 및 본 report/ledger에만 additive로 남긴다.
- raw data와 generated experiment parquet은 계속 git 공개 대상에서 제외한다.
- 투자/세무 조언이 아니라 research backtest 및 sensitivity report로만 해석한다.

## 2. 데이터와 메모리 하네스

- Feature directory: `experiments/prepared/features_full_chunked`
- Run output directory: `experiments/ddqm2_long_only_full_chunked`
- Full label panel: `experiments/prepared/panel/monthly_labels.parquet` 기준 1990-01~2024-12, 420개월.
- Partitioned feature artifact: full 2,082,485 rows, 159 features, macro/crsp/compustat/ibes families.
- Feature chunk months: 12
- Model runs are sequential; tree/boosting estimators force `n_jobs=1` where applicable.
- Factor score construction reads only date chunks and does not materialize all stock-factor scores for long-only backtest.

## 3. Conservative cost/tax assumptions

- Primary transaction cost: 50.0 bps per one-way turnover.
- Primary tax drag: 40.8% applied to positive monthly gains realized by turnover.
- This is a simplified research sensitivity assumption, not tax/legal advice.

## 4. Matrix summary

### 4.1 모델별 best-q 요약

| model | best q | net cumulative | gross cumulative | MDD | turnover | run_id |
|---|---:|---:|---:|---:|---:|---|
| baseline_mean | 0.30 | 51.322593 | 142.832212 | -0.599271 | 0.159131 | `longonly_full_chunked_20260524_baseline_mean_q30` |
| extra_trees | 0.30 | 28.048746 | 269.394256 | -0.584286 | 0.352090 | `longonly_full_chunked_20260524_extra_trees_q30` |
| random_forest | 0.30 | 25.395444 | 289.516978 | -0.600565 | 0.370048 | `longonly_full_chunked_20260524_random_forest_q30` |
| lightgbm | 0.30 | 21.895557 | 299.617899 | -0.584324 | 0.415116 | `longonly_full_chunked_20260524_lightgbm_q30` |
| elasticnet | 0.30 | 13.087143 | 180.803946 | -0.629269 | 0.421751 | `longonly_full_chunked_20260524_elasticnet_q30` |
| ridge | 0.30 | 7.595449 | 100.998272 | -0.614620 | 0.400174 | `longonly_full_chunked_20260524_ridge_q30` |

### 4.2 전체 run table

| status | family | label | model | q | periods | net cum | gross cum | MDD | turnover | avg tax drag | avg trading drag | top weighted factors | run_id |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| ok | core_q | lightgbm | lightgbm | 0.10 | 383 | 6.034166 | 4425.722113 | -0.662654 | 0.756846 | 0.014799 | 0.003784 | size_local_small_size (0.153), reversal_local_ma_gap_1m (0.148), reversal_local_price_reversal_1m (0.148), quality_global_net_income_yoy (0.107), earn_global_op_income_change_fy1_1m_voladj (0.086) | `longonly_full_chunked_20260524_lightgbm_q10` |
| ok | core_q | lightgbm | lightgbm | 0.20 | 383 | 4.048132 | 616.387713 | -0.642334 | 0.648654 | 0.010223 | 0.003243 | reversal_local_ma_gap_1m (0.121), reversal_local_price_reversal_1m (0.121), size_local_small_size (0.118), quality_global_net_income_yoy (0.111), quality_local_net_income_yoy (0.079) | `longonly_full_chunked_20260524_lightgbm_q20` |
| ok | core_q | lightgbm | lightgbm | 0.30 | 383 | 21.895557 | 299.617899 | -0.584324 | 0.415116 | 0.004975 | 0.002076 | size_local_small_size (0.147), quality_global_net_income_yoy (0.142), quality_local_net_income_yoy (0.128), val_global_pb_fwd (0.097), val_global_relative_pb_industry_fwd (0.097) | `longonly_full_chunked_20260524_lightgbm_q30` |
| ok | core_q | ridge | ridge | 0.10 | 383 | 2.726859 | 1861.713206 | -0.726170 | 0.735841 | 0.014195 | 0.003679 | size_local_small_size (0.149), reversal_local_ma_gap_1m (0.142), reversal_local_price_reversal_1m (0.142), earn_local_target_price_gap_3m (0.108), earn_global_op_income_change_fy1_1m_voladj (0.086) | `longonly_full_chunked_20260524_ridge_q10` |
| ok | core_q | ridge | ridge | 0.20 | 383 | 1.521176 | 252.411956 | -0.668279 | 0.621377 | 0.009826 | 0.003107 | size_local_small_size (0.133), reversal_local_ma_gap_1m (0.129), reversal_local_price_reversal_1m (0.129), quality_global_net_income_yoy (0.087), val_global_pb_fwd (0.086) | `longonly_full_chunked_20260524_ridge_q20` |
| ok | core_q | ridge | ridge | 0.30 | 383 | 7.595449 | 100.998272 | -0.614620 | 0.400174 | 0.004781 | 0.002001 | size_local_small_size (0.205), val_global_pb_fwd (0.114), val_global_relative_pb_industry_fwd (0.114), quality_global_net_income_yoy (0.105), quality_local_net_income_yoy (0.096) | `longonly_full_chunked_20260524_ridge_q30` |
| ok | core_q | elasticnet | elasticnet | 0.10 | 383 | 4.859060 | 2830.369662 | -0.659558 | 0.736477 | 0.014087 | 0.003682 | size_local_small_size (0.157), reversal_local_ma_gap_1m (0.133), reversal_local_price_reversal_1m (0.133), earn_local_target_price_gap_3m (0.116), quality_local_net_income_yoy (0.089) | `longonly_full_chunked_20260524_elasticnet_q10` |
| ok | core_q | elasticnet | elasticnet | 0.20 | 383 | 4.185112 | 516.563327 | -0.647824 | 0.623808 | 0.009798 | 0.003119 | quality_global_net_income_yoy (0.133), size_local_small_size (0.126), reversal_local_ma_gap_1m (0.116), reversal_local_price_reversal_1m (0.116), val_global_pb_fwd (0.075) | `longonly_full_chunked_20260524_elasticnet_q20` |
| ok | core_q | elasticnet | elasticnet | 0.30 | 383 | 13.087143 | 180.803946 | -0.629269 | 0.421751 | 0.004892 | 0.002109 | size_local_small_size (0.183), quality_global_net_income_yoy (0.139), val_global_pb_fwd (0.113), val_global_relative_pb_industry_fwd (0.113), quality_local_net_income_yoy (0.113) | `longonly_full_chunked_20260524_elasticnet_q30` |
| ok | core_q | random_forest | random_forest | 0.10 | 383 | 8.496163 | 6332.032286 | -0.643573 | 0.742210 | 0.015012 | 0.003711 | size_local_small_size (0.162), reversal_local_ma_gap_1m (0.142), reversal_local_price_reversal_1m (0.142), quality_global_net_income_yoy (0.100), val_global_pb_fwd (0.094) | `longonly_full_chunked_20260524_random_forest_q10` |
| ok | core_q | random_forest | random_forest | 0.20 | 383 | 5.410548 | 864.788408 | -0.658413 | 0.641540 | 0.010543 | 0.003208 | size_local_small_size (0.126), reversal_local_ma_gap_1m (0.115), reversal_local_price_reversal_1m (0.115), quality_global_net_income_yoy (0.105), val_global_pb_fwd (0.086) | `longonly_full_chunked_20260524_random_forest_q20` |
| ok | core_q | random_forest | random_forest | 0.30 | 383 | 25.395444 | 289.516978 | -0.600565 | 0.370048 | 0.004741 | 0.001850 | quality_global_net_income_yoy (0.155), size_local_small_size (0.145), quality_local_net_income_yoy (0.126), val_global_pb_fwd (0.111), val_global_relative_pb_industry_fwd (0.111) | `longonly_full_chunked_20260524_random_forest_q30` |
| ok | core_q | extra_trees | extra_trees | 0.10 | 383 | 6.963795 | 5075.641390 | -0.637128 | 0.748118 | 0.014856 | 0.003741 | size_local_small_size (0.147), reversal_local_ma_gap_1m (0.145), reversal_local_price_reversal_1m (0.145), quality_global_net_income_yoy (0.101), val_global_pb_fwd (0.096) | `longonly_full_chunked_20260524_extra_trees_q10` |
| ok | core_q | extra_trees | extra_trees | 0.20 | 383 | 5.032797 | 712.866206 | -0.629791 | 0.636116 | 0.010196 | 0.003181 | quality_global_net_income_yoy (0.116), reversal_local_ma_gap_1m (0.114), reversal_local_price_reversal_1m (0.114), size_local_small_size (0.114), quality_local_net_income_yoy (0.093) | `longonly_full_chunked_20260524_extra_trees_q20` |
| ok | core_q | extra_trees | extra_trees | 0.30 | 383 | 28.048746 | 269.394256 | -0.584286 | 0.352090 | 0.004367 | 0.001760 | quality_global_net_income_yoy (0.160), size_local_small_size (0.131), quality_local_net_income_yoy (0.131), val_global_pb_fwd (0.116), val_global_relative_pb_industry_fwd (0.116) | `longonly_full_chunked_20260524_extra_trees_q30` |
| ok | core_q | baseline_mean | baseline_mean | 0.10 | 383 | 2.135122 | 2021.079126 | -0.702322 | 0.745039 | 0.014883 | 0.003725 | reversal_local_ma_gap_1m (0.175), reversal_local_price_reversal_1m (0.175), size_local_small_size (0.149), val_global_pb_fwd (0.096), val_global_relative_pb_industry_fwd (0.096) | `longonly_full_chunked_20260524_baseline_mean_q10` |
| ok | core_q | baseline_mean | baseline_mean | 0.20 | 383 | 1.725806 | 332.665038 | -0.642328 | 0.643223 | 0.010296 | 0.003216 | reversal_local_ma_gap_1m (0.141), reversal_local_price_reversal_1m (0.141), quality_global_net_income_yoy (0.137), size_local_small_size (0.107), quality_local_net_income_yoy (0.103) | `longonly_full_chunked_20260524_baseline_mean_q20` |
| ok | core_q | baseline_mean | baseline_mean | 0.30 | 383 | 51.322593 | 142.832212 | -0.599271 | 0.159131 | 0.001999 | 0.000796 | quality_global_net_income_yoy (0.194), quality_local_net_income_yoy (0.157), val_global_pb_fwd (0.131), val_global_relative_pb_industry_fwd (0.131), size_local_small_size (0.125) | `longonly_full_chunked_20260524_baseline_mean_q30` |

## 5. Existing long-short comparison anchor

The existing source-controlled DDQM2 matrix report remains the comparison baseline: `reports/usa_ddqm2_matrix_report_ko.md` / `reports/usa_ddqm2_matrix_report_en.md`. This report does not rewrite those claims; it adds a long-only, conservative-net lens beside them.

## 6. Factor/model diagnostics

각 run은 `factor_diagnostics.csv`를 남긴다. 표의 `top weighted factors`는 해당 모델이 long-only stock score를 만들 때 평균적으로 높은 weight를 둔 factor들이다. 전반적으로 size, reversal, quality/value 계열이 반복적으로 상위에 나타나며, 모델별/q별로 quality/value 비중과 turnover tradeoff가 달라진다.

## 7. Interpretation hooks for user review

- Which models keep attractive net returns after conservative tax drag rather than only gross returns?
- Do linear models and tree models concentrate on different factor families?
- Does wider q reduce turnover/tax drag enough to offset weaker raw selection?
- Are the high-turnover months explaining most of the net/gross gap?

## 8. Limitations

- No new data was acquired; all results depend on current local artifacts.
- Tax treatment is intentionally simplified and conservative; it is not advice.
- Slippage/market impact/capacity are proxied, not measured from order book data.
- Long-only top-q equal-weight is a first-pass research surface, not a deployable strategy.
- Some gross cumulative returns are extremely large because this is a long-horizon monthly research backtest; interpretation should prioritize robustness, turnover, drawdown, and net/gross gap rather than headline gross alone.

Ledger: `reports/long_only_qspread_ml_costs_full_chunked_ledger.json`
