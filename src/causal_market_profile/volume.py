"""Volume Profile construction using the Dual-Expansion Value Area Algorithm."""
from __future__ import annotations

import numpy as np
import pandas as pd

from causal_market_profile.dual_expansion import dual_expansion_value_area
from causal_market_profile.models import ValueArea


def calculate_volume_profile(
    frame: pd.DataFrame,
    row_size: float,
    *,
    session_vwap: float | None = None,
    value_area_fraction: float = 0.70,
    price_col: str = "price",
    volume_col: str = "volume",
) -> tuple[pd.DataFrame, ValueArea]:
    """Construct Volume Profile and determine Value Area via Dual Expansion.

    Args:
        frame: DataFrame containing price and volume.
        row_size: Discretization step width.
        session_vwap: Optional session VWAP for tie-breaking equidistant POCs.
        value_area_fraction: Target volume fraction inside Value Area (standard: 0.70).
        price_col: Column name for price (falls back to 'close' if 'price' absent).
        volume_col: Column name for volume (falls back to 'quantity' if 'volume' absent).

    Returns:
        tuple[pd.DataFrame, ValueArea]:
            - Table of price rows with volume and in_value_area boolean flag.
            - ValueArea containing Volume POC, VAH, VAL, and actual volume coverage.
    """
    if frame.empty:
        raise ValueError("Cannot calculate volume profile on empty DataFrame")
    if row_size <= 0:
        raise ValueError("row_size must be positive")

    # Graceful fallback for column names
    actual_price_col = price_col
    if actual_price_col not in frame.columns:
        if "close" in frame.columns:
            actual_price_col = "close"
        else:
            raise ValueError(f"DataFrame must contain '{price_col}' or 'close'")

    actual_vol_col = volume_col
    if actual_vol_col not in frame.columns:
        if "quantity" in frame.columns:
            actual_vol_col = "quantity"
        elif "base_volume" in frame.columns:
            actual_vol_col = "base_volume"
        else:
            raise ValueError(f"DataFrame must contain '{volume_col}', 'quantity', or 'base_volume'")

    prices = pd.to_numeric(frame[actual_price_col], errors="raise").to_numpy(dtype=float)
    volumes = pd.to_numeric(frame[actual_vol_col], errors="raise").to_numpy(dtype=float)

    if (prices <= 0).any() or (volumes < 0).any():
        raise ValueError("Prices must be positive and volumes non-negative")
    if float(volumes.sum()) <= 0:
        raise ValueError("Total volume must be positive")

    row_indices = np.floor(prices / row_size + 1e-10).astype("int64")
    work = pd.DataFrame({"row_index": row_indices, "volume": volumes})
    aggregated = work.groupby("row_index", sort=True, as_index=False).sum()

    min_row = int(aggregated["row_index"].min())
    max_row = int(aggregated["row_index"].max())
    full_rows = np.arange(min_row, max_row + 1, dtype="int64")

    volume_array = np.zeros(len(full_rows), dtype=float)
    offsets = aggregated["row_index"].to_numpy(dtype="int64") - min_row
    volume_array[offsets] = aggregated["volume"].to_numpy(dtype=float)

    centers = (full_rows.astype(float) + 0.5) * row_size

    # Fallback reference price if VWAP not provided
    ref = session_vwap if session_vwap is not None else float(np.average(centers, weights=volume_array))

    va = dual_expansion_value_area(
        metrics=volume_array,
        centers=centers,
        row_size=row_size,
        reference_price=ref,
        value_area_fraction=value_area_fraction,
    )

    profile_df = pd.DataFrame({
        "row_index": full_rows,
        "price_low": full_rows.astype(float) * row_size,
        "price_high": (full_rows.astype(float) + 1.0) * row_size,
        "price_center": centers,
        "volume": volume_array,
        "in_value_area": False,
        "is_poc": False,
    })

    profile_df.loc[va.lower_index : va.upper_index, "in_value_area"] = True
    profile_df.loc[va.poc_index, "is_poc"] = True

    return profile_df, va
