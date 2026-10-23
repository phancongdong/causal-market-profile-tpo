"""Point-in-time causal session alignment ensuring zero lookahead bias."""
from __future__ import annotations

import pandas as pd


def attach_prior_profiles(
    bars: pd.DataFrame,
    profiles: pd.DataFrame,
    *,
    prefix: str = "prior_",
) -> pd.DataFrame:
    """Join the latest completed session profile strictly before each bar's session.

    Ensures zero lookahead bias: an intraday bar on session date T can ONLY access
    structural auction levels (POC, VAH, VAL, IB) from session T-1 or earlier.

    Args:
        bars: Intraday bar DataFrame containing 'timestamp_ms' and optionally 'session_date'.
        profiles: Session-level profile DataFrame from build_tpo_profiles.
        prefix: Column prefix for attached prior features (default: 'prior_').

    Returns:
        pd.DataFrame: Bars DataFrame with merged prior-session profile columns.
    """
    work = bars.copy()
    if work.empty or profiles.empty:
        return work

    if "session_date" not in work.columns:
        if "timestamp_ms" in work.columns:
            work["session_date"] = pd.to_datetime(
                work["timestamp_ms"], unit="ms", utc=True
            ).dt.normalize()
        elif "timestamp" in work.columns:
            work["session_date"] = pd.to_datetime(work["timestamp"], utc=True).dt.normalize()
        else:
            raise ValueError("bars must contain 'timestamp_ms' or 'session_date'")

    work.sort_values("timestamp_ms" if "timestamp_ms" in work.columns else "session_date", kind="stable", inplace=True)

    profile_work = profiles.copy()
    profile_work["profile_date"] = pd.to_datetime(profile_work["profile_date"], utc=True).dt.normalize()
    profile_work.sort_values("profile_date", kind="stable", inplace=True)

    profile_columns = [
        "profile_date",
        "profile_open",
        "profile_close",
        "profile_high",
        "profile_low",
        "profile_range",
        "poc",
        "vah",
        "val",
        "row_size",
        "ib_high",
        "ib_low",
        "shape",
        "direction",
        "high_excess",
        "low_excess",
        "high_poor",
        "low_poor",
        "single_print_low",
        "single_print_high",
        "tpo_rows",
        "tpo_count_total",
        "poc_tpo_count",
    ]

    available_cols = [c for c in profile_columns if c in profile_work.columns]
    mapping = {c: f"{prefix}{c}" for c in available_cols}

    # Shift profile_date forward by 1 session so that session T joins profile from T-1
    # Using merge_asof with backward direction on date:
    profile_work["effective_join_date"] = profile_work["profile_date"]

    # For strict causality, profile for date D becomes active starting strictly AFTER date D
    joined = pd.merge_asof(
        work,
        profile_work[available_cols].rename(columns=mapping),
        left_on="session_date",
        right_on=f"{prefix}profile_date",
        allow_exact_matches=False,  # Strictly strictly prior: session_date > prior_profile_date
        direction="backward",
    )

    return joined
