"""Example 5: TPO Value Area vs Volume Profile Value Area Comparison.

Demonstrates:
1. Constructing both TPO Profile (Time-Price Opportunities) and Volume Profile (Volume-at-Price)
   from the same trading session.
2. Applying the exact same Dual-Expansion 70% Value Area algorithm to both distributions.
3. Highlighting the microstructure divergence:
   - TPO POC represents the price where the market spent the most time (advertising efficiency).
   - Volume POC represents the price where the greatest business was actually transacted.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from causal_market_profile.config import TPOConfig
from causal_market_profile.tpo import build_tpo_profiles
from causal_market_profile.volume import calculate_volume_profile


def generate_session_with_volume_divergence():
    """Generate session where price lingered near $100 (high TPO), but huge volume traded at $102 (high volume)."""
    timestamps = pd.date_range("2026-01-05 00:00:00", periods=96, freq="15min", tz="UTC")
    rng = np.random.default_rng(123)

    # 80 bars hovering near 100
    prices_base = 100.0 + rng.normal(0, 0.3, 80)
    volumes_base = rng.uniform(5, 15, 80)  # low volume

    # 16 bars surging to 102 with massive institutional volume spikes
    prices_surge = 102.0 + rng.normal(0, 0.2, 16)
    volumes_surge = rng.uniform(100, 300, 16)  # high institutional volume

    prices = np.r_[prices_base, prices_surge]
    volumes = np.r_[volumes_base, volumes_surge]

    open_ = prices - 0.05
    high = prices + 0.15
    low = prices - 0.15
    close = prices + 0.05

    return pd.DataFrame({
        "timestamp_ms": timestamps.as_unit("ns").astype("int64") // 1_000_000,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volumes,
    })


def main():
    print("=" * 70)
    print("Example 5: TPO Value Area vs Volume Profile Value Area Comparison")
    print("=" * 70)

    bars = generate_session_with_volume_divergence()
    row_size = 0.05

    # 1. Compute TPO Profile
    config = TPOConfig(row_bps=5.0, tick_size=0.01)
    tpo_profiles = build_tpo_profiles(bars, source_interval_minutes=15, config=config)
    tpo_res = tpo_profiles.iloc[0]

    # 2. Compute Volume Profile
    vol_table, vol_va = calculate_volume_profile(bars, row_size=row_size, value_area_fraction=0.70)

    print("\n[+] Metric Comparison across Same Trading Session:")
    print(f"{'Metric':<28s} | {'TPO Profile (Time)':<20s} | {'Volume Profile (Quantity)':<20s}")
    print("-" * 75)
    print(f"{'Point of Control (POC)':<28s} | ${tpo_res['poc']:<19.2f} | ${vol_va.poc:<19.2f}")
    print(f"{'Value Area High (VAH)':<28s} | ${tpo_res['vah']:<19.2f} | ${vol_va.vah:<19.2f}")
    print(f"{'Value Area Low (VAL)':<28s} | ${tpo_res['val']:<19.2f} | ${vol_va.val:<19.2f}")
    print(f"{'Value Area Width':<28s} | ${tpo_res['vah'] - tpo_res['val']:<19.2f} | ${vol_va.vah - vol_va.val:<19.2f}")
    print(f"{'Actual Distribution Coverage':<28s} | {tpo_res['value_area_fraction_actual']*100:<18.1f}% | {vol_va.actual_fraction*100:<18.1f}%")

    print("\n" + "=" * 70)
    print("Microstructure Takeaway:")
    print("  * TPO Profile measures TIME spent at price. Prices where the market spends")
    print("    prolonged periods indicate acceptance and high advertising efficiency.")
    print("  * Volume Profile measures CAPITAL EXCHANGED at price. High-volume nodes")
    print("    represent institutional commitment and strong market memory.")
    print("  * When TPO POC and Volume POC diverge significantly, an initiative auction")
    print("    or high-volume absorption event has occurred.")
    print("=" * 70)


if __name__ == "__main__":
    main()
