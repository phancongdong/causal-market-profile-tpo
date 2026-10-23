"""Unit tests for the Dual-Expansion Value Area Algorithm."""
from __future__ import annotations

import numpy as np
import pytest

from causal_market_profile.dual_expansion import dual_expansion_value_area


def test_dual_expansion_symmetric_gaussian():
    metrics = np.array([1, 4, 10, 25, 40, 25, 10, 4, 1], dtype=float)
    centers = np.arange(100.0, 109.0, 1.0)
    row_size = 1.0

    va = dual_expansion_value_area(metrics, centers, row_size, value_area_fraction=0.70)

    # POC is at index 4 (metric=40)
    assert va.poc_index == 4
    assert va.poc == 104.0
    # Symmetric expansion: expands to 3 & 5, then 2 & 6
    assert va.lower_index <= 3
    assert va.upper_index >= 5
    assert va.val < va.poc < va.vah
    assert va.actual_fraction >= 0.70


def test_dual_expansion_asymmetric_distribution():
    # Heavily skewed upwards
    metrics = np.array([2, 5, 8, 15, 30, 25, 20, 15], dtype=float)
    centers = np.arange(10.0, 18.0, 1.0)
    row_size = 1.0

    va = dual_expansion_value_area(metrics, centers, row_size, value_area_fraction=0.70)
    assert va.poc_index == 4
    assert va.poc == 14.0
    # Should expand more to the right (upward) where metrics are 25, 20 vs 15, 8
    assert va.upper_index - va.poc_index >= va.poc_index - va.lower_index
    assert va.actual_fraction >= 0.70


def test_dual_expansion_tie_breaking_with_reference():
    # Two identical peaks at index 2 and index 6
    metrics = np.array([5, 10, 30, 10, 5, 10, 30, 10, 5], dtype=float)
    centers = np.arange(100.0, 109.0, 1.0)
    row_size = 1.0

    # If reference price is near 106.0, it should select index 6
    va_high = dual_expansion_value_area(metrics, centers, row_size, reference_price=106.0)
    assert va_high.poc_index == 6
    assert va_high.poc == 106.0

    # If reference price is near 102.0, it should select index 2
    va_low = dual_expansion_value_area(metrics, centers, row_size, reference_price=102.0)
    assert va_low.poc_index == 2
    assert va_low.poc == 102.0


def test_dual_expansion_boundary_limits():
    # POC is at extreme top (index 4)
    metrics = np.array([5, 10, 15, 20, 50], dtype=float)
    centers = np.arange(5) * 1.0
    row_size = 1.0

    va = dual_expansion_value_area(metrics, centers, row_size, value_area_fraction=0.70)
    assert va.poc_index == 4
    assert va.upper_index == 4  # Cannot expand upward
    assert va.lower_index < 4   # Expands downward
    assert va.actual_fraction >= 0.70


def test_dual_expansion_validation_errors():
    with pytest.raises(ValueError, match="empty distribution"):
        dual_expansion_value_area(np.array([]), np.array([]), 1.0)

    with pytest.raises(ValueError, match="non-negative"):
        dual_expansion_value_area(np.array([10.0, -5.0]), np.array([1.0, 2.0]), 1.0)

    with pytest.raises(ValueError, match="value_area_fraction"):
        dual_expansion_value_area(np.array([10.0]), np.array([1.0]), 1.0, value_area_fraction=1.5)
