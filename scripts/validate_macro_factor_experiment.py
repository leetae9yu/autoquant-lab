#!/usr/bin/env python3
# pyright: reportAny=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportExplicitAny=false, reportMissingImports=false, reportMissingTypeStubs=false, reportReturnType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnusedCallResult=false
"""Validate macro-factor LightGBM experiment artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from autoquant_lab import schemas


DATASET_NAME = "macro-factor LightGBM experiment"
METRIC_NAMES: tuple[str, ...] = ("mae", "rmse", "r2", "pearson_ic")
REQUIRED_BASELINES: tuple[str, ...] = ("zero_return", "train_mean_return")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a macro-factor LightGBM experiment directory.")
    parser.add_argument("experiment_dir", type=Path, help="Directory containing experiment artifacts.")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON artifact {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must contain an object: {path}")
    return payload


def require_files(experiment_dir: Path) -> None:
    if not experiment_dir.exists():
        raise FileNotFoundError(f"Experiment directory not found: {experiment_dir}")
    if not experiment_dir.is_dir():
        raise NotADirectoryError(f"Experiment path is not a directory: {experiment_dir}")
    missing = [filename for filename in schemas.EXPERIMENT_ARTIFACT_REQUIRED_FILES if not (experiment_dir / filename).exists()]
    if missing:
        raise FileNotFoundError(f"{DATASET_NAME} is missing required artifact files: {missing}")


def parse_date_field(payload: dict[str, Any], field: str) -> pd.Timestamp:
    value = payload.get(field)
    if value is None or str(value).strip() == "":
        raise ValueError(f"manifest field {field!r} must be present and nonblank")
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"manifest field {field!r} is not a parseable date: {value!r}")
    return pd.Timestamp(parsed).tz_localize(None) if pd.Timestamp(parsed).tzinfo else pd.Timestamp(parsed)


def validate_manifest(manifest: dict[str, Any]) -> None:
    missing_fields = sorted(set(schemas.EXPERIMENT_MANIFEST_REQUIRED_FIELDS).difference(manifest))
    if missing_fields:
        raise ValueError(f"manifest.json is missing required fields: {missing_fields}")
    if "prototype" not in str(manifest.get("prototype_warning", "")).lower():
        raise ValueError("manifest.json prototype_warning must be present and mention prototype limitations")
    if manifest.get("split_method") != "time_holdout_by_formation_date_no_random_split":
        raise ValueError("manifest split_method must document time holdout and no random split")
    if manifest.get("target_column") != "target_long_short_return":
        raise ValueError("manifest target_column must be target_long_short_return")
    feature_columns = manifest.get("feature_columns")
    if not isinstance(feature_columns, list) or not feature_columns:
        raise ValueError("manifest feature_columns must be a non-empty list")
    if not any(str(column).startswith(schemas.MACRO_FEATURE_PREFIX) for column in feature_columns):
        raise ValueError(f"manifest feature_columns must include at least one {schemas.MACRO_FEATURE_PREFIX} feature")
    if not any(str(column).startswith("factor_") for column in feature_columns):
        raise ValueError("manifest feature_columns must include deterministic factor one-hot features")

    train_start = parse_date_field(manifest, "train_start_date")
    train_end = parse_date_field(manifest, "train_end_date")
    validation_start = parse_date_field(manifest, "validation_start_date")
    validation_end = parse_date_field(manifest, "validation_end_date")
    if train_start > train_end:
        raise ValueError("manifest train_start_date must be <= train_end_date")
    if validation_start > validation_end:
        raise ValueError("manifest validation_start_date must be <= validation_end_date")
    if validation_start <= train_end:
        boundary = manifest.get("split_boundary_date")
        if not boundary:
            raise ValueError("validation_start_date must be after train_end_date or split_boundary_date must document the holdout boundary")
        boundary_date = pd.to_datetime(boundary, errors="coerce")
        if pd.isna(boundary_date) or pd.Timestamp(boundary_date).tz_localize(None) <= train_end:
            raise ValueError("split_boundary_date must be parseable and after train_end_date when validation_start_date overlaps")


def validate_metrics(metrics: dict[str, Any]) -> None:
    validation_metrics = metrics.get("validation")
    if not isinstance(validation_metrics, dict):
        raise ValueError("metrics.json must contain a validation metrics object")
    required_models = ("lightgbm", *REQUIRED_BASELINES)
    missing_models = [name for name in required_models if name not in validation_metrics]
    if missing_models:
        raise ValueError(f"metrics.json validation metrics missing model/baseline entries: {missing_models}")
    baseline_names = metrics.get("baseline_names")
    if isinstance(baseline_names, list):
        missing_baseline_names = [name for name in REQUIRED_BASELINES if name not in baseline_names]
        if missing_baseline_names:
            raise ValueError(f"metrics.json baseline_names missing required baselines: {missing_baseline_names}")

    for model_name, model_metrics in validation_metrics.items():
        if not isinstance(model_metrics, dict):
            raise ValueError(f"metrics for {model_name} must be an object")
        missing_metric_names = [metric for metric in METRIC_NAMES if metric not in model_metrics]
        if missing_metric_names:
            raise ValueError(f"metrics for {model_name} missing required metric fields: {missing_metric_names}")
        for metric_name in METRIC_NAMES:
            value = model_metrics[metric_name]
            if value is None and metric_name in {"r2", "pearson_ic"}:
                continue
            if not isinstance(value, (int, float)) or not np.isfinite(float(value)):
                raise ValueError(f"metric {model_name}.{metric_name} must be finite numeric or documented null for IC/R2")


def validate_predictions(path: Path, manifest: dict[str, Any]) -> pd.DataFrame:
    predictions = pd.read_parquet(path)
    schemas.require_columns(predictions, schemas.EXPERIMENT_PREDICTIONS_REQUIRED_COLUMNS, "experiment predictions")
    if predictions.empty:
        raise ValueError("predictions.parquet must contain at least one row")
    if "validation" not in set(predictions["split"].astype(str)):
        raise ValueError("predictions.parquet must contain validation split predictions")
    if schemas.prototype_true_count(predictions["prototype_only"]) != len(predictions):
        raise ValueError("predictions.parquet must have prototype_only=True for every row")
    run_ids = set(predictions["run_id"].astype(str))
    if run_ids != {str(manifest.get("run_id"))}:
        raise ValueError(f"predictions.parquet run_id values do not match manifest run_id: {sorted(run_ids)}")
    predictions["formation_date"] = pd.to_datetime(predictions["formation_date"], errors="coerce")
    if bool(predictions["formation_date"].isna().any()):
        raise ValueError("predictions.parquet contains invalid formation_date values")
    for column in ("target_long_short_return", "prediction"):
        values = pd.to_numeric(predictions[column], errors="coerce").to_numpy(dtype=float)
        if int((~np.isfinite(values)).sum()):
            raise ValueError(f"predictions.parquet column {column!r} contains non-finite values")
    validation = predictions.loc[predictions["split"].astype(str).eq("validation"), :]
    validation_start = parse_date_field(manifest, "validation_start_date")
    validation_end = parse_date_field(manifest, "validation_end_date")
    if validation["formation_date"].min() != validation_start or validation["formation_date"].max() != validation_end:
        raise ValueError("validation prediction date range must match manifest validation date range")
    return predictions


def validate_feature_importance(path: Path, manifest: dict[str, Any]) -> pd.DataFrame:
    importance = pd.read_csv(path)
    schemas.require_columns(importance, schemas.EXPERIMENT_FEATURE_IMPORTANCE_REQUIRED_COLUMNS, "experiment feature importance")
    if importance.empty:
        raise ValueError("feature_importance.csv must contain at least one row")
    if set(importance["run_id"].astype(str)) != {str(manifest.get("run_id"))}:
        raise ValueError("feature_importance.csv run_id values must match manifest run_id")
    if not {"gain", "split"}.issubset(set(importance["importance_type"].astype(str))):
        raise ValueError("feature_importance.csv must contain gain and split importance_type rows")
    values = pd.to_numeric(importance["importance"], errors="coerce").to_numpy(dtype=float)
    if int((~np.isfinite(values)).sum()):
        raise ValueError("feature_importance.csv importance values must be finite numeric")
    return importance


def validate_artifact_references(experiment_dir: Path, manifest: dict[str, Any]) -> None:
    expected = {
        "config_artifact": experiment_dir / "config.json",
        "metrics_artifact": experiment_dir / "metrics.json",
        "predictions_artifact": experiment_dir / "predictions.parquet",
        "feature_importance_artifact": experiment_dir / "feature_importance.csv",
    }
    for field, expected_path in expected.items():
        manifest_path = Path(str(manifest.get(field)))
        if manifest_path.resolve() != expected_path.resolve():
            raise ValueError(f"manifest {field} must point to {expected_path.resolve()}")


def print_validation_summary(experiment_dir: Path, manifest: dict[str, Any], predictions: pd.DataFrame, importance: pd.DataFrame) -> None:
    validation_rows = int(predictions["split"].astype(str).eq("validation").sum())
    print(f"Experiment dir: {experiment_dir}")
    print(f"Run id: {manifest['run_id']}")
    print(f"Split method: {manifest['split_method']}")
    print(f"Train date range: {manifest['train_start_date']} to {manifest['train_end_date']}")
    print(f"Validation date range: {manifest['validation_start_date']} to {manifest['validation_end_date']}")
    print(f"Prediction rows: {len(predictions)}")
    print(f"Validation prediction rows: {validation_rows}")
    print(f"Feature importance rows: {len(importance)}")
    print(f"Prototype warning: {manifest['prototype_warning']}")


def main() -> None:
    args = parse_args()
    experiment_dir = args.experiment_dir
    require_files(experiment_dir)
    config = read_json(experiment_dir / "config.json")
    metrics = read_json(experiment_dir / "metrics.json")
    manifest = read_json(experiment_dir / "manifest.json")
    if config.get("run_id") != manifest.get("run_id"):
        raise ValueError("config.json run_id must match manifest.json run_id")
    validate_manifest(manifest)
    validate_artifact_references(experiment_dir, manifest)
    validate_metrics(metrics)
    predictions = validate_predictions(experiment_dir / "predictions.parquet", manifest)
    importance = validate_feature_importance(experiment_dir / "feature_importance.csv", manifest)
    print_validation_summary(experiment_dir, manifest, predictions, importance)


if __name__ == "__main__":
    main()
