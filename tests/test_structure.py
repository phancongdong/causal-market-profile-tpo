"""Unit tests for auction structure, profile shapes, and extremes."""
from __future__ import annotations

import numpy as np

from causal_market_profile.structure import (
    detect_extremes,
    determine_profile_shape,
    find_contiguous_runs,
    find_single_prints,
)


def test_profile_shape_classification():
    # Symmetric bell -> 'D'
    d_counts = np.array([1, 5, 12, 25, 30, 24, 11, 4, 1])
    assert determine_profile_shape(d_counts, poc_position=4) == "D"

    # High POC (upper 32%) -> 'P'
    p_counts = np.array([1, 1, 2, 4, 10, 20, 35, 15, 2])
    assert determine_profile_shape(p_counts, poc_position=6) == "P"

    # Low POC (lower 32%) -> 'b'
    b_counts = np.array([2, 18, 32, 20, 8, 4, 2, 1, 1])
    assert determine_profile_shape(b_counts, poc_position=2) == "b"

    # Double distribution -> 'B'
    double_counts = np.array([1, 8, 20, 22, 15, 2, 1, 2, 16, 25, 18, 5, 1])
    # valley between peak at 3 and peak at 9
    assert determine_profile_shape(double_counts, poc_position=9) in {"B", "P"}


def test_detect_extremes_excess_and_poor():
    # High excess: top row has 1 TPO, previous has >= 2
    high_excess_counts = np.array([2, 5, 10, 8, 4, 1])
    he, le, hp, lp = detect_extremes(high_excess_counts)
    assert he == 1
    assert hp == 0
    assert lp == 1  # bottom has 2 -> poor low

    # Poor high: top row has >= 2 TPOs (blunt edge)
    poor_high_counts = np.array([1, 5, 10, 8, 4, 3])
    he, le, hp, lp = detect_extremes(poor_high_counts)
    assert hp == 1
    assert he == 0


def test_find_contiguous_runs():
    indices = np.array([2, 3, 4, 8, 9, 15])
    runs = find_contiguous_runs(indices)
    assert runs == [(2, 4), (8, 9), (15, 15)]
    assert find_contiguous_runs(np.array([])) == []


def test_find_single_prints():
    # Interior single prints at indices 3 and 4
    counts = np.array([2, 8, 15, 1, 1, 12, 20, 2])
    low, high = find_single_prints(counts, row_size=1.0, minimum_row_index=100)
    assert low == 103.0
    assert high == 105.0
