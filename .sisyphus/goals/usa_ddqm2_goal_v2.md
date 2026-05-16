# USA-version DDQM2 goal v2

You are working in `~/autoquant-lab` on the Oracle/main server. Start from the committed DDQM2-USA implementation and continue the research loop through verified experiment execution and reporting.

## Hard constraints

- Do not expose, print, upload, or commit private data, `.env`, `EQR.md`, PDFs, raw artifacts, or credentials.
- Do not run WRDS login, browser login, external data downloads, or credential prompts.
- Do not push unless explicitly asked.
- Commit continuously after each stable, verified atomic unit. Keep commits small and logical; never commit private/generated data.
- Keep `q=0.10` as DDQM2-reference only; preserve q=0.15/q=0.20/q=0.30 research freedom.
- Do not claim faithful DDQM2 replication unless selected-13, DDQM2 macro design, stock-level QSpread, turnover/diagnostics, and verification are all actually working.

## Current state

The previous goal implemented and committed DDQM2-USA scaffolding:
- factor universe axis: `all_implemented_current`, `selected_13_global_local`, `selected_13_plus_us_overrides`
- macro design axis: `current_macro_family`, `ddqm2_25x3_us_macro`, `expanded_us_macro`
- portfolio surface axis: `weighted_factor_return_current`, `stock_score_qspread_ddqm2`
- ablation planner: `scripts/eqr_plan_ddqm2_ablations.py`

A prior bash matrix failed because the generated script was corrupted by shell expansion. The corrected script is `.sisyphus/run_scripts/run_usa_ddqm2_matrix.sh`. Verify it before trusting it.

## Goal

1. Verify clean baseline:
   - `git status --short`
   - focused tests for ablation planner and factors
   - planner command rendering
   - `bash -n .sisyphus/run_scripts/run_usa_ddqm2_matrix.sh`
2. If any implementation bug blocks the smoke/matrix, patch it, test it, and commit the stable atomic fix.
3. Run the corrected USA-DDQM2 experiment matrix:
   - smoke with `--max-rows 200000` only for surface validation;
   - full-data LightGBM q10/q20/q30 selected13 current-macro weighted-factor-return;
   - full-data LightGBM q10/q20/q30 selected13 DDQM2-macro stock-score-QSpread with 3% floor.
4. Summarize produced `experiments/ddqm2/<run-id>/manifest.json` results without printing private raw data.
5. Update ignored reports/site only if useful for local review; do not commit generated reports unless explicitly asked.
6. Commit any code/test/script fixes you make. Do not commit experiments, data, reports, site, `.env`, PDFs, or raw artifacts.

## Useful commands

```bash
bash -n .sisyphus/run_scripts/run_usa_ddqm2_matrix.sh
.sisyphus/run_scripts/run_usa_ddqm2_matrix.sh
python scripts/eqr_plan_ddqm2_ablations.py --format commands --limit 8
```

Final response in the tmux/log should clearly state: what ran, which runs completed, best realistic candidate among the new USA-DDQM2 runs, what failed if anything, and commit hashes for any new commits.
