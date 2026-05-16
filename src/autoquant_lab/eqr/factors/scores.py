"""Build stock-level EQR factor scores from prepared feature panels."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .definitions import FactorDefinition, implemented_factor_definitions


def _standardize(values: pd.Series) -> pd.Series:
    numeric = pd.Series(values, index=values.index, dtype="float64")
    mean = float(numeric.mean(skipna=True))
    std = float(numeric.std(skipna=True))
    if pd.isna(std) or std <= 1e-12:
        return pd.Series(np.nan, index=numeric.index, dtype="float64")
    standardized = ((numeric - mean) / std).clip(-5.0, 5.0)
    return pd.Series(standardized, index=numeric.index, dtype="float64")


def _score_one_factor(frame: pd.DataFrame, definition: FactorDefinition) -> pd.DataFrame:
    if definition.source_column is None or definition.source_column not in frame.columns:
        return pd.DataFrame(
            {
                "formation_date": pd.Series(dtype="datetime64[ns]"),
                "permno": pd.Series(dtype="Int64"),
                "factor_id": pd.Series(dtype="category"),
                "factor_name_ko": pd.Series(dtype="category"),
                "factor_family": pd.Series(dtype="category"),
                "scope": pd.Series(dtype="category"),
                "source_column": pd.Series(dtype="category"),
                "status": pd.Series(dtype="category"),
                "raw_value": pd.Series(dtype="float32"),
                "factor_score": pd.Series(dtype="float32"),
            }
        )
    keys = ["formation_date", "permno", definition.source_column]
    if definition.scope == "local" and "exchcd" in frame.columns:
        keys.append("exchcd")
    work = frame.loc[:, keys].copy()
    work["formation_date"] = pd.to_datetime(work["formation_date"], errors="coerce")
    group_keys = ["formation_date"] + (["exchcd"] if definition.scope == "local" and "exchcd" in work.columns else [])
    work["raw_value"] = pd.to_numeric(work[definition.source_column], errors="coerce")
    work["factor_score"] = work.groupby(group_keys, group_keys=False)["raw_value"].transform(_standardize) * definition.direction
    out = work.loc[
        work["formation_date"].notna() & work["permno"].notna() & work["factor_score"].notna(),
        ["formation_date", "permno", "factor_score", "raw_value"],
    ].copy()
    out["permno"] = pd.Series(pd.to_numeric(out["permno"], errors="coerce"), index=out.index).astype("Int64")
    out["factor_score"] = pd.Series(pd.to_numeric(out["factor_score"], errors="coerce"), index=out.index).astype("float32")
    out["raw_value"] = pd.Series(pd.to_numeric(out["raw_value"], errors="coerce"), index=out.index).astype("float32")
    out["factor_id"] = pd.Categorical([definition.factor_id] * len(out))
    out["factor_name_ko"] = pd.Categorical([definition.name_ko] * len(out))
    out["factor_family"] = pd.Categorical([definition.family] * len(out))
    out["scope"] = pd.Categorical([definition.scope] * len(out))
    out["source_column"] = pd.Categorical([definition.source_column] * len(out))
    out["status"] = pd.Categorical([definition.status] * len(out))
    return out[["formation_date", "permno", "factor_id", "factor_name_ko", "factor_family", "scope", "source_column", "status", "raw_value", "factor_score"]]


def build_factor_scores(feature_panel: pd.DataFrame, definitions: tuple[FactorDefinition, ...] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return long stock-level factor scores and definition metadata."""

    required = {"formation_date", "permno"}
    missing = sorted(required.difference(feature_panel.columns))
    if missing:
        raise ValueError(f"Feature panel missing required score keys: {missing}")
    definitions = definitions or implemented_factor_definitions()
    frames = [_score_one_factor(feature_panel, definition) for definition in definitions]
    scores = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    metadata = pd.DataFrame([definition.to_dict() for definition in definitions])
    if not scores.empty:
        scores = scores.sort_values(["formation_date", "factor_id", "permno"]).reset_index(drop=True)
    return scores, metadata
