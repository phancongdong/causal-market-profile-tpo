"""Example 4: Causal Prior-Session Attachment (Zero Lookahead Guarantee).

Demonstrates:
1. Constructing TPO Market Profiles across multiple consecutive trading days.
2. Causally attaching prior session structural levels to current intraday bars.
3. Proving point-in-time integrity:
   - Day 1 intraday bars have no prior profile (NaN).
   - Day 2 intraday bars strictly reference completed Day 1 levels.
   - Day 3 intraday bars strictly reference completed Day 2 levels.
   - Zero lookahead bias: today's intraday bars never access today's developing profile.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from causal_market_profile.causal import attach_prior_profiles
from causal_market_profile.config import TPOConfig
from causal_market_profile.tpo import build_tpo_profiles


def generate_multiday_data(days: list[str], base_price: float = 100.0) -> pd.DataFrame:
    dfs = []
    rng = np.random.default_rng(42)
    current_price = base_price

    for day in days:
        timestamps = pd.date_range(f"{day} 00:00:00", periods=96, freq="15min", tz="UTC")
        drift = np.linspace(-0.5, 0.5, 96) + rng.normal(0, 0.1, 96)
        close = current_price + np.cumsum(drift)
        open_ = np.r_[current_price, close[:-1]]
        high = np.maximum(open_, close) + rng.uniform(0.1, 0.2, 96)
        low = np.minimum(open_, close) - rng.uniform(0.1, 0.2, 96)

        dfs.append(pd.DataFrame({
            "timestamp_ms": timestamps.as_unit("ns").astype("int64") // 1_000_000,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": rng.uniform(10, 50, 96),
        }))
        current_price = float(close[-1])

    return pd.concat(dfs, ignore_index=True)


def main():
    print("=" * 70)
    print("Example 4: Causal Prior-Session Profile Attachment (Zero Lookahead)")
    print("=" * 70)

    days = ["2026-01-05", "2026-01-06", "2026-01-07"]
    bars = generate_multiday_data(days)
    print(f"[+] Generated {len(bars)} 15-minute bars across 3 sessions: {days}")

    config = TPOConfig(row_bps=1.0, tick_size=0.01)
    profiles = build_tpo_profiles(bars, source_interval_minutes=15, config=config)

    print("\n[+] Daily TPO Profiles Computed:")
    for _, row in profiles.iterrows():
        d = row["profile_date"].strftime("%Y-%m-%d")
        print(f"    Date: {d} | POC: ${row['poc']:>7.2f} | VAH: ${row['vah']:>7.2f} | VAL: ${row['val']:>7.2f} | Shape: {row['shape']}")

    # Attach prior session profiles to raw bars
    joined = attach_prior_profiles(bars, profiles)

    print("\n[+] Point-in-Time Causal Join Verification:")
    for day in days:
        day_bars = joined[joined["session_date"].dt.strftime("%Y-%m-%d") == day]
        prior_date = day_bars["prior_profile_date"].iloc[0]
        prior_poc = day_bars["prior_poc"].iloc[0]
        prior_vah = day_bars["prior_vah"].iloc[0]
        prior_val = day_bars["prior_val"].iloc[0]

        date_str = prior_date.strftime("%Y-%m-%d") if pd.notna(prior_date) else "None (First Day)"
        poc_str = f"${prior_poc:.2f}" if pd.notna(prior_poc) else "NaN"
        va_str = f"[${prior_val:.2f} - ${prior_vah:.2f}]" if pd.notna(prior_poc) else "None"

        print(f"    Bars on {day}: Prior Profile Date = {date_str:<17s} | Prior POC = {poc_str:<7s} | Prior VA = {va_str}")

    # Assertion checks
    d1 = joined[joined["session_date"].dt.strftime("%Y-%m-%d") == "2026-01-05"]
    d2 = joined[joined["session_date"].dt.strftime("%Y-%m-%d") == "2026-01-06"]
    d3 = joined[joined["session_date"].dt.strftime("%Y-%m-%d") == "2026-01-07"]

    assert d1["prior_poc"].isna().all(), "Day 1 must have no prior profile"
    assert d2["prior_profile_date"].dt.strftime("%Y-%m-%d").eq("2026-01-05").all(), "Day 2 must strictly use Day 1"
    assert d3["prior_profile_date"].dt.strftime("%Y-%m-%d").eq("2026-01-06").all(), "Day 3 must strictly use Day 2"

    print("\n[+] All causality and point-in-time invariants verified successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
