"""Data models for Market Profile, TPO, and Value Area structures."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional
import pandas as pd


@dataclass(frozen=True)
class ValueArea:
    """Represents the results of the Dual-Expansion Value Area Algorithm.

    Attributes:
        poc: Point of Control price (level with highest TPO count or Volume).
        vah: Value Area High price (upper boundary containing 70% of distribution).
        val: Value Area Low price (lower boundary containing 70% of distribution).
        poc_index: Integer array index of the POC.
        lower_index: Lower bound index of the contiguous Value Area.
        upper_index: Upper bound index of the contiguous Value Area.
        total_metric: Total TPO count or total Volume across the entire profile.
        area_metric: Accumulated TPO count or Volume within [val, vah].
        actual_fraction: Exact ratio achieved (area_metric / total_metric >= target).
    """
    poc: float
    vah: float
    val: float
    poc_index: int
    lower_index: int
    upper_index: int
    total_metric: float
    area_metric: float
    actual_fraction: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProfileRow:
    """A discrete price bin in a Market Profile."""
    row_index: int
    price_low: float
    price_high: float
    price_center: float
    tpo_count: int
    tpo_letters: str = ""
    volume: float = 0.0
    in_value_area: bool = False
    is_poc: bool = False


@dataclass(frozen=True)
class MarketProfileSummary:
    """Full session-level Market Profile & Auction Theory summary."""
    profile_date: pd.Timestamp
    profile_open: float
    profile_high: float
    profile_low: float
    profile_close: float
    profile_range: float
    poc: float
    vah: float
    val: float
    row_size: float
    ib_high: float
    ib_low: float
    shape: str
    direction: int
    high_excess: int
    low_excess: int
    high_poor: int
    low_poor: int
    single_print_low: Optional[float]
    single_print_high: Optional[float]
    tpo_rows: int
    tpo_count_total: int
    poc_tpo_count: int
    value_area_fraction_actual: float

    def to_record(self) -> dict[str, Any]:
        return asdict(self)
