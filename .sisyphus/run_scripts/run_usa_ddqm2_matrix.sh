#!/usr/bin/env bash
set -euo pipefail
cd ~/autoquant-lab
source ~/venvs/autoquant-lab/bin/activate
export PYTHONPATH=src:.
export CI=true

log() { printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

run_ddqm2() {
  local run_id="$1"
  shift
  log "START ${run_id}"
  python scripts/eqr_run_ddqm2.py \
    --config configs/server_full.yaml \
    --run-id "${run_id}" \
    "$@"
  log "DONE ${run_id}"
}

log "verify planner/tests"
python -m pytest tests/test_ddqm2_ablation_plan.py tests/test_factors.py -q
python scripts/eqr_plan_ddqm2_ablations.py --format commands --limit 8

log "smoke new USA-DDQM2 axes"
run_ddqm2 smoke_usa_ddqm2_q20_selected13_ddqm2macro_stockscore \
  --max-rows 200000 \
  --quantile 0.20 \
  --model baseline_mean \
  --factor-universe selected_13_global_local \
  --macro-feature-design ddqm2_25x3_us_macro \
  --portfolio-surface stock_score_qspread_ddqm2 \
  --min-weight 0.03 \
  --evaluation-mode walk_forward \
  --walk-forward-test-periods 12 \
  --walk-forward-validation-periods 12

log "limited practical USA-DDQM2 full-data matrix"
for q in 0.10 0.20 0.30; do
  qtag=${q/./}
  run_ddqm2 "usa_ddqm2_lightgbm_q${qtag}_selected13_currentmacro_factorret" \
    --quantile "$q" \
    --model lightgbm \
    --factor-universe selected_13_global_local \
    --macro-feature-design current_macro_family \
    --portfolio-surface weighted_factor_return_current \
    --min-weight 0.0
  run_ddqm2 "usa_ddqm2_lightgbm_q${qtag}_selected13_ddqm2macro_stockscore" \
    --quantile "$q" \
    --model lightgbm \
    --factor-universe selected_13_global_local \
    --macro-feature-design ddqm2_25x3_us_macro \
    --portfolio-surface stock_score_qspread_ddqm2 \
    --min-weight 0.03
done

log "USA-DDQM2 matrix complete"
