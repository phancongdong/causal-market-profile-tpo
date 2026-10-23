"""Unit tests for Volume Profile dual-expansion calculation."""
from __future__ import annotations

import pandas as pd
import pytest

from causal_market_profile.volume import calculate_volume_profile


def test_calculate_volume_profile_finds_poc_and_value_area():
    frame = pd.DataFrame({
        "price": [100.0, 101.0, 102.0, 103.0, 104.0],
        "volume": [10.0, 20.0, 50.0, 15.0, 5.0],
    })

    table, va = calculate_volume_profile(frame, row_size=1.0, value_area_fraction=0.70)

    # POC at 102.0 (volume 50.0)
    assert va.poc == 102.5
    assert va.actual_fraction >= 0.70
    assert (table["in_value_area"]).sum() >= 2
    assert table.loc[table["price_low"] == 102.0, "is_poc"].iloc[0]


def test_calculate_volume_profile_fallback_columns():
    frame = pd.DataFrame({
        "close": [50.0, 51.0, 52.0],
        "quantity": [100.0, 300.0, 50.0],
    })

    table, va = calculate_volume_profile(frame, row_size=1.0)
    assert va.poc == 51.5
    assert va.total_metric == 450.0


def test_calculate_volume_profile_validation():
    with pytest.raises(ValueError, match="empty DataFrame"):
        calculate_volume_profile(pd.DataFrame(), row_size=1.0)

    with pytest.raises(ValueError, match="row_size must be positive"):
        calculate_volume_profile(pd.DataFrame({"price": [10.0], "volume": [1.0]}), row_size=-1.0)
