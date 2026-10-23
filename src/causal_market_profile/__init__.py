"""Causal Market Profile & TPO Dual-Expansion Value Area Package.

Implements Peter Steidlmayer's Market Profile (CBOT, 1986), Time-Price Opportunity (TPO)
histogram construction, the canonical 70% Dual-Expansion Value Area Algorithm, Auction
Theory structure classification (D, P, b, B shapes, Initial Balance, Excess tails, Poor extremes),
and point-in-time causal prior-session attachment (zero lookahead bias).
"""
from causal_market_profile.causal import attach_prior_profiles
from causal_market_profile.config import (
    TPOConfig,
    VolumeProfileConfig,
    calculate_aligned_row_size,
)
from causal_market_profile.dual_expansion import dual_expansion_value_area
from causal_market_profile.models import (
    MarketProfileSummary,
    ProfileRow,
    ValueArea,
)
from causal_market_profile.structure import (
    detect_extremes,
    determine_profile_shape,
    find_contiguous_runs,
    find_single_prints,
)
from causal_market_profile.tpo import build_tpo_profiles
from causal_market_profile.volume import calculate_volume_profile

__version__ = "1.0.0"

__all__ = [
    # Core Dual-Expansion Algorithm
    "dual_expansion_value_area",
    # Config & Models
    "TPOConfig",
    "VolumeProfileConfig",
    "calculate_aligned_row_size",
    "ValueArea",
    "ProfileRow",
    "MarketProfileSummary",
    # TPO & Volume Builders
    "build_tpo_profiles",
    "calculate_volume_profile",
    # Auction Structure
    "determine_profile_shape",
    "find_contiguous_runs",
    "find_single_prints",
    "detect_extremes",
    # Causal Point-in-Time Alignment
    "attach_prior_profiles",
]
