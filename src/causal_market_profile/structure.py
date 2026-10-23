"""Auction Market Theory profile structure, shapes, single prints, and extremes."""
from __future__ import annotations

import numpy as np


def determine_profile_shape(counts: np.ndarray, poc_position: int) -> str:
    """Classify the Market Profile structure into canonical Auction Theory shapes.

    - 'D'-shape: Balanced auction, symmetric normal/bell-shaped profile.
    - 'P'-shape: Buying initiative / short-covering rally; high POC near the top.
    - 'b'-shape: Selling initiative / long liquidation; low POC near the bottom.
    - 'B'-shape: Double distribution trend day with two balance regions separated by a valley.
    """
    if len(counts) < 3:
        return "UNKNOWN"

    location = poc_position / max(1, len(counts) - 1)
    if location >= 0.68:
        return "P"
    if location <= 0.32:
        return "b"

    # Detect double distribution 'B'-shape:
    # Look for at least two prominent local maxima separated by a deep valley
    peaks = np.flatnonzero(
        (counts[1:-1] >= counts[:-2]) & (counts[1:-1] >= counts[2:])
    ) + 1

    if len(peaks) >= 2:
        top_two = peaks[np.argsort(counts[peaks])[-2:]]
        left, right = int(min(top_two)), int(max(top_two))
        if right - left >= max(2, len(counts) // 8):
            valley = float(counts[left:right + 1].min())
            peak_floor = float(min(counts[left], counts[right]))
            if peak_floor > 0 and valley / peak_floor <= 0.55:
                return "B"

    return "D"


def find_contiguous_runs(indices: np.ndarray) -> list[tuple[int, int]]:
    """Find contiguous index spans [start, end]."""
    if len(indices) == 0:
        return []
    runs: list[tuple[int, int]] = []
    start = previous = int(indices[0])
    for value in indices[1:]:
        current = int(value)
        if current != previous + 1:
            runs.append((start, previous))
            start = current
        previous = current
    runs.append((start, previous))
    return runs


def find_single_prints(
    counts: np.ndarray,
    row_size: float,
    minimum_row_index: int,
) -> tuple[float | None, float | None]:
    """Identify interior single-print regions (fast directional auction movement).

    Returns:
        tuple (low_price, high_price) of the longest single print run, or (None, None).
    """
    if len(counts) < 3:
        return None, None

    # Single print: exactly 1 TPO, excluding top and bottom extreme rows
    interior_single = np.flatnonzero(
        (counts == 1) & (np.arange(len(counts)) > 0) & (np.arange(len(counts)) < len(counts) - 1)
    )
    runs = find_contiguous_runs(interior_single)
    if not runs:
        return None, None

    # Pick the longest contiguous run
    best = max(runs, key=lambda pair: (pair[1] - pair[0] + 1, -pair[0]))
    low_price = float((minimum_row_index + best[0]) * row_size)
    high_price = float((minimum_row_index + best[1] + 1) * row_size)
    return low_price, high_price


def detect_extremes(counts: np.ndarray) -> tuple[int, int, int, int]:
    """Detect Excess tails and Poor (unfinished) auction extremes.

    Returns:
        tuple[int, int, int, int]: (high_excess, low_excess, high_poor, low_poor)
    """
    if len(counts) < 2:
        return 0, 0, 0, 0

    high_count = int(counts[-1])
    low_count = int(counts[0])

    # Excess tail: single print at extreme followed by confirmed acceptance depth (>= 2)
    high_excess = int(high_count == 1 and counts[-2] >= 2)
    low_excess = int(low_count == 1 and counts[1] >= 2)

    # Poor extreme: blunt edge (>= 2 TPOs) indicating the market ran out of time, not buyers/sellers
    high_poor = int(high_count >= 2)
    low_poor = int(low_count >= 2)

    return high_excess, low_excess, high_poor, low_poor
