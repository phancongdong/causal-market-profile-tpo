"""Configuration dataclasses for Market Profile, TPO, and Volume Profile."""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TPOConfig:
    """Configuration for Time-Price Opportunity (TPO) Market Profile construction.

    Args:
        row_bps: Price row bucket width in basis points of reference price (e.g. 1.0 bps).
        tick_size: Minimum price increment of instrument.
        bracket_minutes: Duration of each letter bracket in minutes (standard: 30 min).
        value_area_fraction: Fraction of total session TPOs inside Value Area (standard: 0.70).
        initial_balance_minutes: Duration of the Initial Balance in minutes (standard: 60 min).
    """
    row_bps: float
    tick_size: float
    bracket_minutes: int = 30
    value_area_fraction: float = 0.70
    initial_balance_minutes: int = 60

    def __post_init__(self) -> None:
        if self.row_bps <= 0 or self.tick_size <= 0:
            raise ValueError("row_bps and tick_size must be positive")
        if self.bracket_minutes <= 0 or 1_440 % self.bracket_minutes:
            raise ValueError("bracket_minutes must divide a 1440-minute UTC day")
        if not 0 < self.value_area_fraction < 1:
            raise ValueError("value_area_fraction must be in (0, 1)")
        if self.initial_balance_minutes <= 0 or self.initial_balance_minutes % self.bracket_minutes:
            raise ValueError("initial_balance_minutes must be a positive multiple of bracket_minutes")

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VolumeProfileConfig:
    """Configuration for Volume Profile Value Area construction.

    Args:
        row_size_bps: Row bucket width in basis points.
        value_area_fraction: Value Area volume fraction (standard: 0.70).
    """
    row_size_bps: float = 1.0
    value_area_fraction: float = 0.70

    def __post_init__(self) -> None:
        if self.row_size_bps <= 0:
            raise ValueError("row_size_bps must be positive")
        if not 0 < self.value_area_fraction < 1:
            raise ValueError("value_area_fraction must be in (0, 1)")

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


def calculate_aligned_row_size(reference_price: float, tick_size: float, row_bps: float) -> float:
    """Compute scale-invariant row size aligned upward to the exact exchange tick size."""
    if reference_price <= 0 or tick_size <= 0 or row_bps <= 0:
        raise ValueError("reference_price, tick_size, and row_bps must be positive")
    raw = reference_price * row_bps / 10_000.0
    ticks = max(1, int(math.ceil(raw / tick_size - 1e-12)))
    return float(round(ticks * tick_size, 12))
