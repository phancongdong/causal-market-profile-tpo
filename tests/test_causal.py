"""Unit tests for point-in-time causal profile joining."""
from __future__ import annotations

import numpy as np
import pandas as pd

from causal_market_profile.causal import attach_prior_profiles
from causal_market_profile.config import TPOConfig
from causal_market_profile.tpo import build_tpo_profiles


def _day(date: str, base: float) -> pd.DataFrame:
    timestamps = pd.date_range(f"{date} 00:00:00", periods=96, freq="15min", tz="UTC")
    phase = np.linspace(0.0, 2.0 * np.pi, 96)
    close = base + np.sin(phase) * 0.5
    open_ = np.r_[close[0], close[:-1]]
    return pd.DataFrame({
        "timestamp_ms": timestamps.as_unit("ns").astype("int64") // 1_000_000,
        "open": open_,
        "high": np.maximum(open_, close) + 0.1,
        "low": np.minimum(open_, close) - 0.1,
        "close": close,
        "volume": 10.0,
    })


def test_attach_prior_profiles_strictly_causal():
    d1 = _day("2026-01-01", 100.0)
    d2 = _day("2026-01-02", 102.0)
    d3 = _day("2026-01-03", 104.0)
    source = pd.concat([d1, d2, d3], ignore_index=True)

    config = TPOConfig(row_bps=1.0, tick_size=0.01)
    profiles = build_tpo_profiles(source, source_interval_minutes=15, config=config)

    assert len(profiles) == 3
    joined = attach_prior_profiles(source, profiles)

    day1_mask = joined["session_date"].dt.strftime("%Y-%m-%d") == "2026-01-01"
    day2_mask = joined["session_date"].dt.strftime("%Y-%m-%d") == "2026-01-02"
    day3_mask = joined["session_date"].dt.strftime("%Y-%m-%d") == "2026-01-03"

    # Day 1 has no prior profile -> prior_poc must be NaN
    assert joined.loc[day1_mask, "prior_poc"].isna().all()

    # Day 2 must strictly reference Day 1 profile
    d1_poc = profiles.loc[profiles["profile_date"].dt.strftime("%Y-%m-%d") == "2026-01-01", "poc"].iloc[0]
    assert (joined.loc[day2_mask, "prior_poc"] == d1_poc).all()
    assert (joined.loc[day2_mask, "prior_profile_date"].dt.strftime("%Y-%m-%d") == "2026-01-01").all()

    # Day 3 must strictly reference Day 2 profile
    d2_poc = profiles.loc[profiles["profile_date"].dt.strftime("%Y-%m-%d") == "2026-01-02", "poc"].iloc[0]
    assert (joined.loc[day3_mask, "prior_poc"] == d2_poc).all()
    assert (joined.loc[day3_mask, "prior_profile_date"].dt.strftime("%Y-%m-%d") == "2026-01-02").all()
