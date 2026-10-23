"""Example 1: Time-Price Opportunity (TPO) Market Profile Construction.

Demonstrates:
1. Generating a 24-hour intraday session (96 x 15-minute bars).
2. Discretizing price ranges into tick-aligned rows.
3. Calculating 30-minute letter bracket TPO visits.
4. Computing Point of Control (POC), Value Area High (VAH), and Value Area Low (VAL).
5. Extracting the Initial Balance (IB: first hour of session).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from causal_market_profile.config import TPOConfig
from causal_market_profile.tpo import build_tpo_profiles


def generate_synthetic_session(day: str = "2026-01-05", base_price: float = 100.0) -> pd.DataFrame:
    """Generate a 24-hour complete 15-minute OHLC sequence with a balanced bell curve auction."""
    timestamps = pd.date_range(f"{day} 00:00:00", periods=96, freq="15min", tz="UTC")
    # Sine wave oscillation with random noise to simulate auction price discovery
    t = np.linspace(0, 3 * np.pi, len(timestamps))
    drift = np.sin(t) * 1.5
    rng = np.random.default_rng(42)
    noise = rng.normal(0, 0.2, len(timestamps))
    close = base_price + drift + noise
    open_ = np.r_[base_price, close[:-1]]
    high = np.maximum(open_, close) + rng.uniform(0.1, 0.3, len(timestamps))
    low = np.minimum(open_, close) - rng.uniform(0.1, 0.3, len(timestamps))

    return pd.DataFrame({
        "timestamp_ms": timestamps.as_unit("ns").astype("int64") // 1_000_000,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": rng.uniform(10, 50, len(timestamps)),
    })


def main():
    print("=" * 70)
    print("Example 1: TPO Market Profile & Value Area Construction")
    print("=" * 70)

    bars = generate_synthetic_session()
    print(f"[+] Generated {len(bars)} 15-minute bars for session {bars['timestamp_ms'].iloc[0]}")

    config = TPOConfig(
        row_bps=1.0,           # 1.0 bps bucket width
        tick_size=0.01,        # 0.01 tick size
        bracket_minutes=30,    # Standard 30-min brackets
        value_area_fraction=0.70, # 70% Steidlmayer Value Area
        initial_balance_minutes=60, # First 1 hour (Brackets A & B)
    )

    profiles = build_tpo_profiles(bars, source_interval_minutes=15, config=config)

    if profiles.empty:
        print("[!] No complete profile generated.")
        return

    p = profiles.iloc[0]
    print("\n[+] Market Profile Summary for Session:", p["profile_date"].strftime("%Y-%m-%d"))
    print(f"    Session Open:   ${p['profile_open']:>8.2f} | Session Close: ${p['profile_close']:>8.2f}")
    print(f"    Session High:   ${p['profile_high']:>8.2f} | Session Low:   ${p['profile_low']:>8.2f}")
    print(f"    Session Range:  ${p['profile_range']:>8.2f}")
    print("-" * 50)
    print(f"    Value Area High (VAH): ${p['vah']:>8.2f}")
    print(f"    Point of Control (POC):${p['poc']:>8.2f} (TPO Count: {p['poc_tpo_count']})")
    print(f"    Value Area Low (VAL):  ${p['val']:>8.2f}")
    print(f"    Actual Value Coverage:  {p['value_area_fraction_actual'] * 100:.1f}% (Target: 70.0%)")
    print("-" * 50)
    print(f"    Initial Balance (IB):  ${p['ib_low']:.2f} - ${p['ib_high']:.2f}")
    print(f"    Profile Shape:         '{p['shape']}' ({'Normal Balanced' if p['shape'] == 'D' else p['shape']})")
    print(f"    Total TPO Prints:       {p['tpo_count_total']} across {p['tpo_rows']} price rows")
    print("=" * 70)


if __name__ == "__main__":
    main()
