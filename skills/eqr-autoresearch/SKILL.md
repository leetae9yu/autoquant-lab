# EQR Autoresearch Skill

Codex Skill for `autoquant-lab`.

## Overview

This skill enables Codex (and Codex-like agents) to run autonomous, config-only experiments in `autoquant-lab`, the EQR (Equity Quant Research) platform. The target audience is agents that must propose, queue, execute, evaluate, and promote experiment variants without human intervention.

Core principles:
- **Configs-only autonomy**: agents may only modify YAML configs. Harness code, data, and scripts are frozen.
- **Offline-only**: no WRDS login, no network downloads, no external API calls.
- **SQLite FSM ledger**: all job coordination goes through the ledger at `experiments/ledger.sqlite`.
- **Multi-metric promotion**: a variant is promoted only when validation improves and holdout does not degrade across required metrics.
- **Adaptive budget**: trial counts are computed from queue pressure, failure rate, and metric plateau.

## Inspection

Before proposing any experiment, read these files in order:

1. `configs/golden_path.yaml` - the canonical config template showing all allowed keys and default values.
2. `src/autoquant_lab/eqr/config.py` - the validated config grammar (`ExperimentConfig`, `ModelConfig`, `FeaturesConfig`, etc.).
3. `src/autoquant_lab/eqr/models/registry.py` - available model names and their aliases.
4. `src/autoquant_lab/eqr/features/feature_registry.py` - available feature families (`macro`, `crsp`, `compustat`, `ibes`).
5. `src/autoquant_lab/eqr/metrics.py` - required metric keys and their definitions.
6. `src/autoquant_lab/eqr/data_contracts.py` - raw artifact contracts and column expectations.
7. `src/autoquant_lab/eqr/schemas.py` - artifact schemas for predictions, feature importance, and manifests.
8. `src/autoquant_lab/eqr/ledger.py` - job states and legal transitions.
9. `src/autoquant_lab/eqr/scheduler.py` - `adaptive_budget`, `propose_job`, `execute_job`, `run_batch`.
10. `scripts/eqr_autoresearch.py` - the CLI entry point for the autonomous loop.
11. `scripts/eqr_train.py` - the training script for single-model runs.

Data paths to check existence before running:
- `experiments/prepared/panel/monthly_labels.parquet` - the prepared monthly panel.
- `experiments/prepared/features/*.parquet` - pre-built feature family files.
- `data/` - raw offline data files.

## Stage Map

The autonomous experiment lifecycle follows this pipeline:

```
PREPARE  ->  PROPOSE  ->  QUEUE  ->  EXECUTE  ->  EVALUATE  ->  PERSIST  ->  RENDER
   |            |          |          |            |            |           |
   |            |          |          |            |            |           |
   v            v          v          v            v            v           v
Read configs  Validate   Insert    Claim job    Train/       Write        Generate
and data      config     into      from ledger  evaluate     metrics/     static
contracts     grammar    ledger    Run FSM      model        predictions/ HTML site
              Compute    as        transitions  on train/    model        and reports
              adaptive   QUEUED    through      val/holdout  artifacts
              budget               RUNNING ->
                                   EVALUATING ->
                                   PERSISTING ->
                                   RENDERING ->
                                   SUCCEEDED
```

On failure at any stage, the job transitions to `FAILED`. After max retries, it moves to `DEAD_LETTER`.

## Delegation Rules

| Task | Delegate To | Why |
|------|-------------|-----|
| Config grammar validation | `researcher` (read-only) | Understands schema and constraints |
| Feature family selection | `researcher` (read-only) | Knows data contracts and PIT rules |
| Hyperparameter search space design | `researcher` (read-only) | Understands model signatures |
| Config variant generation | `implementer` | Writes YAML files under `configs/` |
| Batch proposal and queuing | `implementer` | Calls `scripts/eqr_autoresearch.py propose` |
| Job execution (train/eval) | `implementer` | Calls `scripts/eqr_autoresearch.py run-batch` |
| Metrics interpretation | `researcher` (read-only) | Reads `metrics.json` and compares splits |
| Promotion decision | `reviewer` | Compares validation vs holdout, checks gates |
| Report generation | `implementer` | Calls report/site build scripts |
| Failure recovery | `implementer` | Checks ledger, retries, dead-letters |
| Stop condition check | `reviewer` | Evaluates budget, plateau, user instruction |

Agents must never cross these boundaries. A researcher must not write configs. An implementer must not override evaluation logic.

## Config-Only Mutation Rules

### Allowed Mutable Paths

Agents may create, read, update, and delete files only under these paths:

- `configs/*.yaml` - experiment config files
- `configs/report_templates/*.md` - report templates
- `experiments/runs/*/` - run output directories (written by harness, read by agents)
- `experiments/ledger.sqlite` - job ledger (written by harness, read by agents)
- `reports/*.md`, `reports/*.json` - generated reports
- `site/*.html`, `site/*.css`, `site/*.js` - static site files

### Frozen Paths

Agents must NEVER modify these paths:

- `src/autoquant_lab/eqr/` - all harness code (config grammar, scheduler, ledger, metrics, models, features, evaluation)
- `scripts/eqr_autoresearch.py` - the autoresearch CLI
- `scripts/eqr_train.py` - the training script
- `scripts/eqr_validate_*.py` - validation scripts
- `data/` - raw data files (read-only)
- `experiments/prepared/` - prepared panels and features (read-only)
- `.env`, `.env.example` - secrets and environment
- `requirements.txt` - dependencies

### Allowed Config Mutations

Within a config YAML, agents may modify:
- `model.name` - any registered model from `available_models()`
- `model.hyperparameters` - any key/value valid for the chosen model
- `model.search_space` - hyperparameter search space definitions
- `features.families` - boolean flags for `macro`, `crsp`, `compustat`, `ibes`
- `features.pit_availability.*` - lag days and future-leakage rules
- `panel.universe.*` - share codes, exchange codes, market cap filters
- `panel.forward_horizons` - target return horizons in months
- `splits.*` - train/validation/holdout fractions or explicit date ranges
- `budget.max_trials` - hard cap on trials
- `budget.max_runtime_minutes` - per-job runtime limit
- `budget.retry_limit` - retry count
- `promotion.required_metrics` - subset of `REQUIRED_METRIC_KEYS`
- `promotion.metric_thresholds` - per-metric promotion thresholds
- `report.template` - path to report template
- `report.output_formats` - `html`, `json`, `md`
- `artifacts.output_dir` - run output directory
- `artifacts.retention_policy.*` - keep_last, max_age_days

Agents must NOT add keys outside the validated config grammar. Invalid keys trigger `ConfigValidationError`.

## Experiment Proposal

### How to Create a New Experiment Config

1. Copy `configs/golden_path.yaml` to `configs/<experiment_name>.yaml`.
2. Modify allowed fields only. Keep the overall structure identical.
3. Validate the config before use:
   ```bash
   python scripts/eqr_validate_config.py configs/<experiment_name>.yaml
   ```

## Golden Path

Use the golden path when you need one reproducible end-to-end smoke of the active offline platform:

```bash
python scripts/eqr_autoresearch.py golden-path \
  --config configs/golden_path.yaml \
  --max-trials 3
```

This command runs the following stages in order:

| Stage | Script | Output |
|-------|--------|--------|
| 1. validate_raw_data | `scripts/eqr_validate_raw_data.py` | `reports/eqr_raw_data_validation.json` |
| 2. build_links | `scripts/eqr_build_links.py` | `experiments/prepared/links/` |
| 3. prepare_labels | `scripts/eqr_prepare_panel.py --stage labels` | `experiments/prepared/panel/monthly_labels.parquet` |
| 4. prepare_features | `scripts/eqr_prepare_panel.py --stage features` | `experiments/prepared/features/` |
| 5. validate_config | `scripts/eqr_validate_config.py` | config hash check |
| 6. execute_trials | `eqr_autoresearch.py` (internal) | `experiments/ledger.sqlite` + `experiments/runs/<run_id>/` |
| 7. render_site | `scripts/eqr_render_site.py` | `site/index.html` + `reports/` |
| 8. ci_smoke | `scripts/eqr_ci.py --smoke` | `reports/eqr_ci_report.json` |

The command defaults to `--max-rows 50000` so agents can run a smoke-sized prepared panel on local CI hardware. Use `--max-rows 0` only when intentionally running the full offline panel.

On success, inspect:

- `experiments/ledger.sqlite` for at least three terminal jobs.
- `experiments/runs/<run_id>/metrics.json` for per-run evidence.
- `reports/eqr_experiment_history.json` and `reports/eqr_experiment_history.md` for source reports.
- `site/index.html` for run metrics and promotion status.

The golden path exits 0 on success and 1 on any stage failure. The summary JSON printed to stdout includes `status`, `run_count`, `runs` (with per-run `promotion_status`), `site` path, and `ci` status.

Promotion status is an internal research gate. Do not describe any result as economically tradable.

### How to Vary Hyperparameters

Change `model.hyperparameters` for a single trial, or define `model.search_space` for future autoresearch integration:

```yaml
model:
  name: "lightgbm"
  target_column: "ret_1m_fwd"
  hyperparameters:
    num_leaves: 31
    learning_rate: 0.05
    n_estimators: 100
  search_space:
    num_leaves:
      type: "int"
      min: 16
      max: 128
    learning_rate:
      type: "float"
      min: 0.001
      max: 0.3
      scale: "log"
```

### How to Vary Feature Families

Toggle families in `features.families`. At least one family must be enabled:

```yaml
features:
  families:
    macro: true
    crsp: true
    compustat: false
    ibes: false
```

### How to Propose a Job

```bash
python scripts/eqr_autoresearch.py propose \
  --config configs/<experiment_name>.yaml \
  --ledger experiments/ledger.sqlite
```

This creates a `PROPOSED` job, transitions it to `QUEUED`, and prints the job ID and config hash.

## Batch Execution

### Smoke Test (Small Batch)

Run a single trial on a small subset to verify the config works:

```bash
python scripts/eqr_autoresearch.py run-batch \
  --config configs/<experiment_name>.yaml \
  --max-trials 1 \
  --max-rows 5000 \
  --ledger experiments/ledger.sqlite
```

### Full Batch

Run the adaptive budget batch:

```bash
python scripts/eqr_autoresearch.py run-batch \
  --config configs/<experiment_name>.yaml \
  --ledger experiments/ledger.sqlite \
  --panel experiments/prepared/panel/monthly_labels.parquet \
  --feature-dir experiments/prepared/features \
  --output-dir experiments/runs
```

This will:
1. Compute adaptive budget from queue pressure, failure rate, and plateau.
2. Propose and queue that many jobs.
3. Claim and execute each job sequentially.
4. Retry failed jobs up to `retry_limit`.
5. Move exhausted failures to dead letter.

### Worker Claim Pattern

For distributed or multi-worker execution, each worker claims one job:

```bash
python scripts/eqr_autoresearch.py claim \
  --config configs/<experiment_name>.yaml \
  --ledger experiments/ledger.sqlite \
  --worker-id worker-1
```

Workers must use the same ledger file. The ledger handles optimistic locking and lease requeue.

## Evaluation

### How to Read metrics.json

After a successful run, `experiments/runs/<run_id>/metrics.json` contains:

```json
{
  "run_id": "...",
  "job_id": "...",
  "model": "ridge",
  "target": "ret_1m_fwd",
  "feature_columns": [...],
  "train": {
    "rank_ic": 0.05,
    "pearson_ic": 0.04,
    "decile_long_short_return": 0.02,
    "hit_rate": 0.52,
    "mse": 0.04,
    "mae": 0.15,
    "turnover_proxy": 0.35,
    "max_drawdown": -0.12,
    "stability": 0.88,
    "feature_coverage": 0.92,
    "runtime": 12.3
  },
  "validation": { ... },
  "holdout": { ... }
}
```

### How to Interpret Multi-Metric Results

Key rules for interpretation:
- **rank_ic** > 0.01 is a minimal signal. Higher is better. Negative rank_ic means the model is worse than random.
- **decile_long_short_return** > 0 means the top decile outperforms the bottom decile. This is the primary P&L proxy.
- **hit_rate** > 0.50 means directional accuracy is better than coin flip.
- **feature_coverage** should be close to 1.0. Low coverage means too many missing features.
- **stability** > 0.80 means consistent performance across periods. Low stability means overfitting.
- Compare **validation** vs **holdout**. If holdout is much worse than validation, the model is overfit.
- Compare **train** vs **validation**. If train is much better, the model memorized the training set.

### Promotion Gate

A config variant is promoted when ALL of the following are true:
1. Every `promotion.required_metrics` is present in the validation split.
2. Every validation metric meets its `promotion.metric_thresholds` value.
3. Holdout metrics do not degrade by more than 10% relative to validation for any required metric.
4. `feature_coverage` on holdout is at least 0.80.

If any gate fails, the variant is rejected but its results are still recorded.

## Promotion

### When to Promote a Config Variant

Promote when:
- Validation improves over the previous best for at least one required metric.
- Holdout does not degrade for any required metric.
- The config passes all promotion gates.

### How to Promote

Promotion is currently a manual agent decision. To promote a variant:
1. Read its `metrics.json`.
2. Compare validation and holdout splits against thresholds.
3. If it passes, copy the config to `configs/promoted/<name>.yaml` and record the run_id in `reports/promotion_log.json`.

There is no automated promotion harness. The agent decides and documents.

## Reporting

### How to Generate Reports

After a batch completes, generate a report from the ledger:

```bash
python scripts/eqr_autoresearch.py export \
  --ledger experiments/ledger.sqlite \
  --output reports/ledger_export.json \
  --format json
```

Then build the static site:

```bash
python scripts/eqr_render_site.py \
  --ledger experiments/ledger.sqlite \
  --output site \
  --run-root experiments/runs \
  --reports reports
```

### Report Contents

A good report includes:
- Batch summary: total jobs, succeeded, failed, dead-lettered.
- Best config variant by each required metric.
- Validation vs holdout comparison table.
- Feature family usage breakdown.
- Hyperparameter sensitivity notes.
- Promotion recommendations.

## Recovery

### What to Do on Failure

1. **Check the ledger state**:
   ```bash
   python scripts/eqr_autoresearch.py export \
     --ledger experiments/ledger.sqlite \
     --output reports/ledger_debug.json
   ```

2. **List failed jobs**:
   Filter the export for `state == "FAILED"`.

3. **Inspect the dead letter**:
   ```bash
   python scripts/eqr_autoresearch.py dead-letter \
     --ledger experiments/ledger.sqlite
   ```

4. **Retry failed jobs**:
   ```bash
   python scripts/eqr_autoresearch.py retry \
     --ledger experiments/ledger.sqlite
   ```

5. **Retry a specific job**:
   ```bash
   python scripts/eqr_autoresearch.py retry \
     --ledger experiments/ledger.sqlite \
     --job-id <job_id>
   ```

### Retry Rules

- A job is retried only if `retry_count < max_retries`.
- After max retries, the job moves to `DEAD_LETTER`.
- Dead letter jobs are preserved for inspection but never automatically requeued.
- To requeue a dead letter job, create a new proposal with a modified config.

### Common Failure Modes

| Symptom | Likely Cause | Recovery |
|---------|-------------|----------|
| `Panel file not found` | Panel not prepared | Run panel preparation first |
| `No numeric feature columns` | All feature families disabled | Enable at least one family |
| `Target column not found` | Wrong target in config | Fix `model.target_column` |
| `ConfigValidationError` | Invalid key or path | Validate config before proposing |
| `split is empty` | Too few periods or too much filtering | Relax filters or use more data |
| Job stuck in `CLAIMED` | Worker crashed without releasing | Wait for lease expiry (default 300s) |
| Job stuck in `RUNNING` | Worker hung | Same as above, or manually fail via ledger API |

## Stop Conditions

Stop experimenting when ANY of the following is true:

1. **Budget exhausted**: `max_trials` reached or `max_runtime_minutes` exceeded.
2. **Metric plateau**: No required metric improved by more than 0.005 over the last 5 trials.
3. **High failure rate**: More than 50% of jobs in the last batch failed.
4. **User instruction**: The user explicitly says stop.
5. **Holdout degradation**: Holdout metrics degraded for 3 consecutive promoted variants.

When stopping, the agent must:
1. Export the ledger.
2. Generate the final report and static site.
3. Summarize the best config found and why it was chosen.
4. Note any dead letter jobs and their reasons.

## Forbidden Actions

Agents must NEVER do the following. Violation corrupts the harness and voids reproducibility.

1. **Edit harness code** - Never modify files under `src/autoquant_lab/eqr/` or `scripts/eqr_*.py`.
2. **Delete data** - Never delete files under `data/` or `experiments/prepared/`.
3. **WRDS login** - Never attempt WRDS connection, login, or password creation.
4. **Unlimited trials** - Never set `max_trials` above 100 or remove budget limits.
5. **Shell injection** - Never put shell metacharacters (`;`, `&&`, `|`, backticks, `$()`) in config paths or values.
6. **Path escape** - Never use `..` or absolute paths outside `APPROVED_PATH_ROOTS`.
7. **Future leakage** - Never set `forbid_future_leakage: false` without explicit user approval.
8. **Holdout training** - Never train on holdout data. Holdout is evaluation-only.
9. **Override evaluation** - Never modify `metrics.json` after it is written.
10. **Network downloads** - Never download data from the internet during autonomous runs.
11. **Delete ledger** - Never delete `experiments/ledger.sqlite`. Export instead.
12. **Bypass validation** - Never propose a config that fails `eqr_validate_config.py`.

## CI Contract

Before and after any autonomous batch, run the local CI contract to verify the platform is intact:

```bash
# Full CI (all validators, pytest, offline guard, secret scan)
python scripts/eqr_ci.py

# Fast smoke check (skips expensive data scans)
python scripts/eqr_ci.py --smoke
```

The CI stages run in order: pytest, raw_data, config, panel, ledger, skill, site, secrets, offline.
Any stage failure causes a nonzero exit. The JSON report is written to `reports/eqr_ci_report.json`.

## Example Session

Below is a complete example of proposing, running, evaluating, and reporting a batch.

### Step 1: Inspect the golden path

```bash
cat configs/golden_path.yaml
python scripts/eqr_validate_config.py --config configs/golden_path.yaml
```

### Step 2: Create a variant config

Copy `configs/golden_path.yaml` to `configs/lightgbm_macro_only.yaml` and modify:

```yaml
model:
  name: "lightgbm"
  target_column: "ret_1m_fwd"
  hyperparameters:
    num_leaves: 31
    learning_rate: 0.05
    n_estimators: 100

features:
  families:
    macro: true
    crsp: false
    compustat: false
    ibes: false

budget:
  max_trials: 6
  max_runtime_minutes: 60
  retry_limit: 2
```

Validate it:

```bash
python scripts/eqr_validate_config.py --config configs/lightgbm_macro_only.yaml
```

### Step 3: Smoke test

```bash
python scripts/eqr_autoresearch.py run-batch \
  --config configs/lightgbm_macro_only.yaml \
  --max-trials 1 \
  --max-rows 5000 \
  --ledger experiments/ledger.sqlite
```

Check the output JSON. If `succeeded == 1`, proceed.

### Step 4: Run full batch

```bash
python scripts/eqr_autoresearch.py run-batch \
  --config configs/lightgbm_macro_only.yaml \
  --ledger experiments/ledger.sqlite \
  --panel experiments/prepared/panel/monthly_labels.parquet \
  --feature-dir experiments/prepared/features \
  --output-dir experiments/runs
```

### Step 5: Evaluate results

```bash
# Find the latest run directory
ls -lt experiments/runs/ | head -5

# Read metrics
cat experiments/runs/<run_id>/metrics.json | jq '.validation.rank_ic, .holdout.rank_ic'
```

Compare validation and holdout. If validation rank_ic > 0.01, holdout rank_ic within 10% of validation, and feature_coverage > 0.85, the variant passes the promotion gate.

### Step 6: Export and report

```bash
python scripts/eqr_autoresearch.py export \
  --ledger experiments/ledger.sqlite \
  --output reports/batch_report.json

python scripts/eqr_build_links.py --input reports/batch_report.json --output site/
```

### Step 7: Retry any failures

```bash
python scripts/eqr_autoresearch.py retry --ledger experiments/ledger.sqlite
```

### Step 8: Stop or continue

If the batch succeeded and metrics look good, stop and report the best config. If metrics plateaued, try a different model or feature family. If failures are high, inspect dead letter and fix the config.

## Prompt Templates

### Template: Propose a Batch

```
You are an EQR autoresearch agent. Propose a batch of experiments from the config at {config_path}. 
1. Validate the config.
2. Compute adaptive budget.
3. Run a smoke test with --max-rows 5000.
4. If smoke passes, run the full batch.
5. Export the ledger and summarize results.
```

### Template: Evaluate and Promote

```
You are an EQR reviewer. Read the metrics.json files in {run_dir_glob}. 
For each run, check:
- validation.rank_ic > {threshold}
- holdout.rank_ic within 10% of validation
- feature_coverage > 0.85
List passing configs and recommend one for promotion. Do not modify harness code.
```

### Template: Recovery

```
You are an EQR implementer. The ledger at {ledger_path} has failed jobs. 
1. Export and inspect failed jobs.
2. List dead letter jobs.
3. Retry failed jobs.
4. Report which jobs recovered and which remain dead letter.
```

### Template: Stop Check

```
You are an EQR reviewer. Check if experimentation should stop:
1. Has max_trials been reached?
2. Has any required metric improved by > 0.005 in the last 5 trials?
3. Is the failure rate > 50%?
4. Has the user said to stop?
If any is true, generate final report and site. Otherwise, continue.
```

## Appendix: Metric Reference

| Metric | Direction | Good | Bad | Notes |
|--------|-----------|------|-----|-------|
| rank_ic | Higher | > 0.03 | < 0 | Spearman IC per period |
| pearson_ic | Higher | > 0.02 | < 0 | Pearson IC per period |
| decile_long_short_return | Higher | > 0 | < 0 | Top decile minus bottom decile |
| hit_rate | Higher | > 0.52 | < 0.48 | Directional accuracy |
| mse | Lower | < 0.05 | > 0.10 | Mean squared error |
| mae | Lower | < 0.15 | > 0.25 | Mean absolute error |
| turnover_proxy | Lower | < 0.50 | > 0.80 | Fraction of predictions that flip sign |
| max_drawdown | Higher (less negative) | > -0.10 | < -0.30 | Worst cumulative drawdown |
| stability | Higher | > 0.85 | < 0.60 | Std of period ICs / mean period IC |
| feature_coverage | Higher | > 0.90 | < 0.70 | Fraction of non-null feature values |
| runtime | Lower | < 60s | > 300s | Seconds to fit and predict |
