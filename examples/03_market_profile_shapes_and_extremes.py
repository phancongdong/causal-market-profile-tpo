"""Example 3: Market Profile Shape Classification & Auction Extremes.

Demonstrates identifying:
1. Canonical Profile Shapes:
   - 'D'-shape: Normal balanced distribution (symmetric Gaussian bell)
   - 'P'-shape: Upward trending or short-covering rally (high POC)
   - 'b'-shape: Downward trending or long liquidation (low POC)
   - 'B'-shape: Double distribution trend day (two balance areas with a valley)
2. Auction Extremes:
   - Excess Tails: Single print tail (sharp rejection of value)
   - Poor Extremes: Blunt edges (>= 2 TPOs, unfinished auction)
3. Single Prints: Interior fast price discovery regions.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from causal_market_profile.structure import (
    detect_extremes,
    determine_profile_shape,
    find_single_prints,
)


def print_profile_analysis(name: str, counts: np.ndarray, poc_idx: int):
    shape = determine_profile_shape(counts, poc_idx)
    high_excess, low_excess, high_poor, low_poor = detect_extremes(counts)
    single_low, single_high = find_single_prints(counts, row_size=1.0, minimum_row_index=0)

    print(f"\n--- {name} ---")
    print(f"  Distribution: {counts.tolist()}")
    print(f"  Classified Shape: '{shape}'")
    print(f"  Top Extreme:    {'Excess Tail (Sharp Rejection)' if high_excess else 'Poor High (Unfinished Auction)' if high_poor else 'Neutral'}")
    print(f"  Bottom Extreme: {'Excess Tail (Sharp Rejection)' if low_excess else 'Poor Low (Unfinished Auction)' if low_poor else 'Neutral'}")
    if single_low is not None:
        print(f"  Interior Single Prints: Price span ${single_low:.1f} - ${single_high:.1f}")
    else:
        print("  Interior Single Prints: None")


def main():
    print("=" * 70)
    print("Example 3: Auction Market Theory Shapes & Extreme Classifications")
    print("=" * 70)

    # 1. Normal Balanced 'D'-shape: POC centered, tapering tails
    d_shape = np.array([1, 4, 8, 16, 25, 30, 24, 15, 7, 3, 1])
    print_profile_analysis("Normal Balanced Day ('D'-shape)", d_shape, poc_idx=5)

    # 2. 'P'-shape: Thin bottom stem, fat top (POC in upper 30%)
    p_shape = np.array([1, 1, 1, 2, 3, 5, 12, 28, 35, 20, 2])
    print_profile_analysis("Short-Covering / Buying Rally ('P'-shape)", p_shape, poc_idx=8)

    # 3. 'b'-shape: Fat bottom (POC in lower 30%), thin top stem
    b_shape = np.array([2, 22, 32, 25, 10, 4, 2, 1, 1, 1, 1])
    print_profile_analysis("Long Liquidation / Selling Day ('b'-shape)", b_shape, poc_idx=2)

    # 4. Double Distribution 'B'-shape: Two separate balance peaks separated by low volume valley
    b_double = np.array([1, 6, 18, 22, 16, 3, 2, 3, 15, 24, 19, 5, 1])
    print_profile_analysis("Double Distribution Trend Day ('B'-shape)", b_double, poc_idx=9)

    # 5. Poor High Unfinished Auction (High count >= 2, blunt edge)
    poor_high = np.array([1, 3, 7, 15, 20, 25, 22, 18])  # Extreme high has 18 TPOs
    print_profile_analysis("Unfinished Auction at the High (Poor High)", poor_high, poc_idx=5)

    print("\n" + "=" * 70)
    print("Auction Theory Structural Significance:")
    print("  * 'D'-shape indicates market consensus and rotational bracket trading.")
    print("  * 'P'-shape signals aggressive buyers or trapped shorts covering.")
    print("  * 'b'-shape signals aggressive sellers or long positions liquidating.")
    print("  * Excess tails denote strong rejection by longer-term other timeframe traders.")
    print("  * Poor extremes denote unfinished business that is frequently retested.")
    print("=" * 70)


if __name__ == "__main__":
    main()
