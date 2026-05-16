from __future__ import annotations

import pandas as pd

from scripts.eqr_prepare_panel import _cap_panel_rows


def _panel() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for date in pd.date_range("2020-01-31", periods=6, freq="ME"):
        for permno in range(1, 11):
            rows.append({"formation_date": date, "permno": permno})
    return pd.DataFrame(rows)


def test_chronological_row_cap_keeps_earliest_dates() -> None:
    capped = _cap_panel_rows(_panel(), 20, "chronological")

    assert len(capped) == 20
    assert capped["formation_date"].nunique() == 2
    assert capped["formation_date"].max() == pd.Timestamp("2020-02-29")


def test_date_balanced_row_cap_spans_full_date_range() -> None:
    capped = _cap_panel_rows(_panel(), 24, "date-balanced")

    assert len(capped) == 24
    assert capped["formation_date"].nunique() == 6
    assert capped["formation_date"].min() == pd.Timestamp("2020-01-31")
    assert capped["formation_date"].max() == pd.Timestamp("2020-06-30")
    assert capped.groupby("formation_date").size().min() == 4
    assert capped.groupby("formation_date").size().max() == 4
