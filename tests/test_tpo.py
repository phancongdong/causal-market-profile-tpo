"""Unit tests for TPO Market Profile construction."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from causal_market_profile.config import TPOConfig
from causal_market_profile.tpo import build_tpo_profiles


def _generate_test_day(day: str = "2026-01-01", base: float = 100.0) -> pd.DataFrame:
    timestamps = pd.date_range(f"{day} 00:00:00", periods=96, freq="15min", tz="UTC")
    phase = np.linspace(0.0, 4.0 * np.pi, len(timestamps))
    close = base + np.sin(phase) * 1.5
    open_ = np.r_[close[0], close[:-1]]
    high = np.maximum(open_, close) + 0.2
    low = np.minimum(open_, close) - 0.2
    return pd.DataFrame({
        "timestamp_ms": timestamps.as_unit("ns").astype("int64") // 1_000_000,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": 10.0,
    })


def test_tpo_profile_builds_valid_value_area():
    bars = _generate_test_day("2026-01-01")
    config = TPOConfig(row_bps=1.0, tick_size=0.01, bracket_minutes=30, value_area_fraction=0.70)

    profiles = build_tpo_profiles(bars, source_interval_minutes=15, config=config)

    assert len(profiles) == 1
    p = profiles.iloc[0]
    assert p["val"] < p["poc"] < p["vah"]
    assert p["profile_low"] <= p["val"]
    assert p["vah"] <= p["profile_high"]
    assert p["value_area_fraction_actual"] >= 0.70
    assert p["ib_low"] <= p["ib_high"]
    assert p["tpo_count_total"] > 0


def test_tpo_profile_skips_incomplete_days():
    bars = _generate_test_day("2026-01-01")
    # Drop 6 bars so 90 bars remain (90 is divisible by bars_per_bracket=2)
    incomplete = bars.iloc[:90]

    config = TPOConfig(row_bps=1.0, tick_size=0.01)
    # With require_complete=True (default), it skips incomplete day
    res_strict = build_tpo_profiles(incomplete, source_interval_minutes=15, config=config, require_complete=True)
    assert len(res_strict) == 0

    # With require_complete=False, it processes the 45 available brackets
    res_lenient = build_tpo_profiles(incomplete, source_interval_minutes=15, config=config, require_complete=False)
    assert len(res_lenient) == 1


def test_tpo_config_validation():
    # 70 does not divide 1440
    with pytest.raises(ValueError, match="bracket_minutes must divide"):
        TPOConfig(row_bps=1.0, tick_size=0.01, bracket_minutes=70)

    with pytest.raises(ValueError, match="row_bps and tick_size must be positive"):
        TPOConfig(row_bps=-1.0, tick_size=0.01)
