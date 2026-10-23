"""Time-Price Opportunity (TPO) Market Profile construction engine."""
from __future__ import annotations

import numpy as np
import pandas as pd

from causal_market_profile.config import TPOConfig, calculate_aligned_row_size
from causal_market_profile.dual_expansion import dual_expansion_value_area
from causal_market_profile.structure import (
    detect_extremes,
    determine_profile_shape,
    find_single_prints,
)

REQUIRED_OHLC = {"timestamp_ms", "open", "high", "low", "close"}


def _standardize_ohlc(frame: pd.DataFrame) -> pd.DataFrame:
    """Standardize source OHLC dataframe into sorted UTC milliseconds."""
    work = frame.copy()
    if "timestamp_ms" not in work.columns:
        if "bucket_start_ns" in work.columns:
            work["timestamp_ms"] = (
                pd.to_numeric(work["bucket_start_ns"], errors="raise") // 1_000_000
            ).astype("int64")
        elif "timestamp" in work.columns:
            ts = pd.to_datetime(work["timestamp"], utc=True, errors="raise")
            work["timestamp_ms"] = ts.astype("datetime64[ns, UTC]").astype("int64") // 1_000_000

    missing = REQUIRED_OHLC.difference(work.columns)
    if missing:
        raise ValueError(f"Input DataFrame missing required columns: {sorted(missing)}")

    cols = ["timestamp_ms", "open", "high", "low", "close"]
    if "volume" in work.columns:
        cols.append("volume")
    else:
        work["volume"] = 0.0
        cols.append("volume")

    res = work[cols].copy()
    res["timestamp_ms"] = pd.to_numeric(res["timestamp_ms"], errors="raise").astype("int64")
    # Auto-adjust if timestamps were in seconds
    if not res.empty and res["timestamp_ms"].abs().max() < 100_000_000_000:
        res["timestamp_ms"] *= 1_000

    for col in ("open", "high", "low", "close", "volume"):
        res[col] = pd.to_numeric(res[col], errors="raise").astype(float)

    res.sort_values("timestamp_ms", kind="stable", inplace=True)
    res.drop_duplicates("timestamp_ms", keep="last", inplace=True)
    res.reset_index(drop=True, inplace=True)

    if (res[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("Prices must be positive")
    if (res["high"] < res["low"]).any():
        raise ValueError("High cannot be less than low")

    return res


def build_tpo_profiles(
    source_frame: pd.DataFrame,
    *,
    source_interval_minutes: int,
    config: TPOConfig,
    require_complete: bool = True,
) -> pd.DataFrame:
    """Construct session TPO Market Profiles using the Dual-Expansion Value Area Algorithm.

    Each 30-minute bracket contributes one TPO count to every row touched by its observed
    high/low range (price-visit reconstruction).

    Args:
        source_frame: Intraday OHLC DataFrame.
        source_interval_minutes: Granularity of the source bars (e.g. 1, 5, 15).
        config: TPOConfig specifying row_bps, tick_size, bracket_minutes, and value_area_fraction.
        require_complete: If True, skips incomplete sessions missing bars.

    Returns:
        pd.DataFrame: Session-level profile table with POC, VAH, VAL, IB, and shape classifications.
    """
    if config.bracket_minutes % source_interval_minutes != 0:
        raise ValueError("bracket_minutes must be a multiple of source_interval_minutes")

    source = _standardize_ohlc(source_frame)
    if source.empty:
        return pd.DataFrame()

    source["timestamp"] = pd.to_datetime(source["timestamp_ms"], unit="ms", utc=True)
    source["session_date"] = source["timestamp"].dt.normalize()

    expected_day_bars = 1_440 // source_interval_minutes
    bars_per_bracket = config.bracket_minutes // source_interval_minutes
    expected_brackets = 1_440 // config.bracket_minutes
    source_step_ms = source_interval_minutes * 60_000
    ib_brackets = max(1, config.initial_balance_minutes // config.bracket_minutes)

    profiles: list[dict] = []

    for session_date, group in source.groupby("session_date", sort=True):
        group = group.sort_values("timestamp_ms", kind="stable")
        if require_complete and len(group) != expected_day_bars:
            continue

        timestamps = group["timestamp_ms"].to_numpy(dtype="int64")
        session_start_ms = int(pd.Timestamp(session_date).value // 1_000_000)
        expected_timestamps = session_start_ms + np.arange(expected_day_bars, dtype="int64") * source_step_ms

        if require_complete and not np.array_equal(timestamps, expected_timestamps):
            continue
        if len(group) % bars_per_bracket != 0:
            continue

        num_brackets = len(group) // bars_per_bracket
        highs = group["high"].to_numpy(dtype=float)[: num_brackets * bars_per_bracket].reshape(num_brackets, bars_per_bracket)
        lows = group["low"].to_numpy(dtype=float)[: num_brackets * bars_per_bracket].reshape(num_brackets, bars_per_bracket)
        bracket_high = highs.max(axis=1)
        bracket_low = lows.min(axis=1)

        reference = float(group["close"].median())
        row_size = calculate_aligned_row_size(reference, config.tick_size, config.row_bps)

        low_rows = np.floor(bracket_low / row_size + 1e-10).astype("int64")
        high_rows = np.floor(bracket_high / row_size + 1e-10).astype("int64")
        minimum = int(low_rows.min())
        maximum = int(high_rows.max())

        counts = np.zeros(maximum - minimum + 1, dtype="int16")
        for low_r, high_r in zip(low_rows, high_rows):
            if high_r < low_r:
                low_r, high_r = high_r, low_r
            counts[int(low_r - minimum) : int(high_r - minimum) + 1] += 1

        if counts.sum() <= 0:
            continue

        rows = np.arange(minimum, maximum + 1, dtype="int64")
        centers = (rows.astype(float) + 0.5) * row_size

        session_open = float(group["open"].iloc[0])
        session_close = float(group["close"].iloc[-1])
        session_high = float(group["high"].max())
        session_low = float(group["low"].min())
        midpoint = (session_high + session_low) / 2.0

        # Execute Dual-Expansion Value Area Algorithm
        va = dual_expansion_value_area(
            metrics=counts.astype(float),
            centers=centers,
            row_size=row_size,
            reference_price=midpoint,
            value_area_fraction=config.value_area_fraction,
        )

        shape = determine_profile_shape(counts, va.poc_index)
        single_low, single_high = find_single_prints(counts, row_size, minimum)
        high_excess, low_excess, high_poor, low_poor = detect_extremes(counts)

        actual_ib_count = min(ib_brackets, len(bracket_high))
        ib_high = float(bracket_high[:actual_ib_count].max())
        ib_low = float(bracket_low[:actual_ib_count].min())

        profile = {
            "profile_date": pd.Timestamp(session_date),
            "profile_open": session_open,
            "profile_close": session_close,
            "profile_high": session_high,
            "profile_low": session_low,
            "profile_range": session_high - session_low,
            "poc": va.poc,
            "vah": va.vah,
            "val": va.val,
            "row_size": row_size,
            "tpo_rows": int(len(counts)),
            "tpo_count_total": int(counts.sum()),
            "poc_tpo_count": int(counts[va.poc_index]),
            "value_area_fraction_actual": va.actual_fraction,
            "ib_high": ib_high,
            "ib_low": ib_low,
            "shape": shape,
            "direction": int(np.sign(session_close - session_open)),
            "high_excess": high_excess,
            "low_excess": low_excess,
            "high_poor": high_poor,
            "low_poor": low_poor,
            "single_print_low": single_low if single_low is not None else np.nan,
            "single_print_high": single_high if single_high is not None else np.nan,
            "valid": True,
        }
        profiles.append(profile)

    if not profiles:
        return pd.DataFrame()

    result = pd.DataFrame(profiles).sort_values("profile_date", kind="stable").reset_index(drop=True)

    # Shift columns to provide causal previous-session reference
    for col in ("poc", "vah", "val", "ib_high", "ib_low", "profile_high", "profile_low"):
        result[f"previous_{col}"] = result[col].shift(1)
    result["previous_shape"] = result["shape"].shift(1)
    result["previous_direction"] = result["direction"].shift(1)

    return result
