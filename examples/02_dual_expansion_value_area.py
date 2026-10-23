"""Example 2: The Dual-Expansion Value Area Algorithm Step-by-Step.

This example visually steps through Steidlmayer's 70% Value Area Dual-Expansion:
1. Locate the Point of Control (POC = mode of TPOs).
2. Look one price row above (upper frontier) and one row below (lower frontier).
3. Expand towards the level with the higher count.
4. If tied, expand towards the level closer to POC (or default upper).
5. Stop as soon as cumulative TPOs reach 70% of the total session distribution.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from causal_market_profile.dual_expansion import dual_expansion_value_area


def main():
    print("=" * 70)
    print("Example 2: Step-by-Step Dual-Expansion Value Area Algorithm")
    print("=" * 70)

    # Synthetic 11-row distribution of TPO counts (price $100 to $110)
    prices = np.array([100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0])
    row_size = 1.0
    tpos = np.array([2, 5, 8, 14, 22, 35, 26, 18, 11, 6, 3])  # Peak at $105 with 35 TPOs

    total_tpo = int(tpos.sum())
    target_70 = total_tpo * 0.70
    poc_idx = int(np.argmax(tpos))

    print(f"Total TPO Prints: {total_tpo}")
    print(f"70% Target TPOs:  {target_70:.1f}")
    print(f"POC Price:        ${prices[poc_idx]:.2f} (Index: {poc_idx}, Count: {tpos[poc_idx]})")
    print("\nVisual Distribution (TPO Histogram):")
    for p, count in zip(prices, tpos):
        bar = "#" * count
        tag = "<-- POC" if count == tpos[poc_idx] else ""
        print(f"  ${p:5.1f} | {count:2d} | {bar} {tag}")

    print("\n--- Running Dual-Expansion Loop ---")
    lower = poc_idx
    upper = poc_idx
    accum = tpos[poc_idx]
    step = 0

    print(f"Step {step:02d}: Seed at POC (${prices[poc_idx]:.1f}) | Accum: {accum}/{target_70:.1f} ({accum/total_tpo*100:.1f}%)")

    while accum < target_70 and (lower > 0 or upper < len(tpos) - 1):
        step += 1
        down = lower - 1 if lower > 0 else None
        up = upper + 1 if upper < len(tpos) - 1 else None

        if down is None:
            chosen = "UP (Bottom boundary reached)"
            upper += 1
            added = tpos[upper]
        elif up is None:
            chosen = "DOWN (Top boundary reached)"
            lower -= 1
            added = tpos[lower]
        else:
            up_val = tpos[up]
            down_val = tpos[down]
            if up_val > down_val:
                chosen = f"UP (${prices[up]:.1f} has {up_val} > ${prices[down]:.1f} has {down_val})"
                upper += 1
                added = tpos[upper]
            elif down_val > up_val:
                chosen = f"DOWN (${prices[down]:.1f} has {down_val} > ${prices[up]:.1f} has {up_val})"
                lower -= 1
                added = tpos[lower]
            else:
                chosen = f"TIE -> UP (Both have {up_val})"
                upper += 1
                added = tpos[upper]

        accum += added
        pct = accum / total_tpo * 100
        print(f"Step {step:02d}: Expand {chosen:35s} | Row +{added:2d} -> Accum: {accum:3d}/{target_70:.1f} ({pct:.1f}%)")

    va = dual_expansion_value_area(tpos.astype(float), prices, row_size, value_area_fraction=0.70)

    print("\n" + "=" * 70)
    print("Dual Expansion Final Value Area Results:")
    print(f"  Value Area High (VAH): ${va.vah:.2f} (Row Index: {va.upper_index})")
    print(f"  Point of Control (POC):${va.poc:.2f} (Row Index: {va.poc_index})")
    print(f"  Value Area Low (VAL):  ${va.val:.2f} (Row Index: {va.lower_index})")
    print(f"  Value Area Span:       ${va.val:.2f} - ${va.vah:.2f}")
    print(f"  Total Area TPOs:       {va.area_metric:.0f} / {va.total_metric:.0f} ({va.actual_fraction*100:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    main()
