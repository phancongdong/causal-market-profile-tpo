"""The Core Dual-Expansion Value Area Algorithm (Steidlmayer 70% Rule).

References:
    Steidlmayer, J. P., & Hawkins, K. (1986).
    Markets & Market Logic. Porcupine Press.
    CBOT Market Profile Manual (1991).
"""
from __future__ import annotations

import numpy as np

from causal_market_profile.models import ValueArea


def dual_expansion_value_area(
    metrics: np.ndarray,
    centers: np.ndarray,
    row_size: float,
    *,
    reference_price: float | None = None,
    value_area_fraction: float = 0.70,
) -> ValueArea:
    """Compute the Point of Control (POC) and contiguous Value Area via Dual Expansion.

    The Dual-Expansion algorithm starts at the POC (mode of distribution) and simultaneously
    evaluates expanding one row above (upper frontier) versus one row below (lower frontier).
    At each step, it incorporates the adjacent price level with higher activity (TPO count or volume).
    Expansion continues until the cumulative activity reaches the target fraction (typically 70%).

    Args:
        metrics: 1D array of non-negative activity counts (TPO counts or volume) sorted by price ascending.
        centers: 1D array of corresponding price level midpoints.
        row_size: Width of each price row.
        reference_price: Optional session midpoint or VWAP to break ties if multiple POCs exist.
        value_area_fraction: Target distribution fraction (default 0.70 for ~1 standard deviation).

    Returns:
        ValueArea: The resulting POC, VAH, VAL, and distribution coverage metrics.

    Raises:
        ValueError: If metrics is empty, contains negative values, or sums to zero.
    """
    if len(metrics) == 0:
        raise ValueError("Cannot calculate Value Area on empty distribution")
    if (metrics < 0).any():
        raise ValueError("Distribution metrics must be non-negative")
    total_metric = float(metrics.sum())
    if total_metric <= 0:
        raise ValueError("Total distribution metric must be positive")
    if not 0 < value_area_fraction < 1:
        raise ValueError("value_area_fraction must be in (0, 1)")

    # 1. Identify Point of Control (POC)
    max_val = float(metrics.max())
    poc_candidates = np.flatnonzero(np.isclose(metrics, max_val, rtol=1e-12, atol=1e-12))

    if len(poc_candidates) == 1:
        poc_position = int(poc_candidates[0])
    else:
        # Tie-breaker: choose POC candidate closest to reference price (midpoint or VWAP)
        ref = reference_price if reference_price is not None else float(np.median(centers))
        distances = np.abs(centers[poc_candidates] - ref)
        # Lexicographic sort: smallest distance first, then lower price index for determinism
        tie_order = np.lexsort((poc_candidates, distances))
        poc_position = int(poc_candidates[tie_order[0]])

    poc_price = float(centers[poc_position])
    target_metric = total_metric * value_area_fraction

    # 2. Dual Expansion from POC
    lower = poc_position
    upper = poc_position
    area_metric = float(metrics[poc_position])

    while area_metric < target_metric and (lower > 0 or upper < len(metrics) - 1):
        down_pos = lower - 1 if lower > 0 else None
        up_pos = upper + 1 if upper < len(metrics) - 1 else None

        if down_pos is None:
            choose_up = True
        elif up_pos is None:
            choose_up = False
        else:
            up_val = float(metrics[up_pos])
            down_val = float(metrics[down_pos])

            if up_val != down_val:
                choose_up = up_val > down_val
            else:
                # Secondary tie-breaker when upper and lower levels have identical TPO/volume:
                # Favor expansion closer to the POC; if symmetric, default upward for consistency
                up_dist = up_pos - poc_position
                down_dist = poc_position - down_pos
                choose_up = up_dist <= down_dist

        if choose_up:
            upper += 1
            area_metric += float(metrics[upper])
        else:
            lower -= 1
            area_metric += float(metrics[lower])

    val = float(centers[lower] - 0.5 * row_size)
    vah = float(centers[upper] + 0.5 * row_size)

    return ValueArea(
        poc=poc_price,
        vah=vah,
        val=val,
        poc_index=poc_position,
        lower_index=lower,
        upper_index=upper,
        total_metric=total_metric,
        area_metric=area_metric,
        actual_fraction=float(area_metric / total_metric),
    )
