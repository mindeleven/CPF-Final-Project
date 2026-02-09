"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Jürgen Kober
Co-developed with: Claude Code (Opus 4.5)
Created: February 2026

Module: modules/config/timeframes.py
Purpose: Timeframe configuration for the multi-timeframe trading system.

This module is part of a parametric multi-timeframe trading system for EUR/USD
forex trading, implementing a trend-following strategy with MA crossover, RSI,
and Momentum confirmation filters.
"""

import logging

logger = logging.getLogger(__name__)

# Keys required in every timeframe configuration entry
_REQUIRED_KEYS = [
    "name",
    "trading_style",
    "bar_duration",
    "expected_trades_per_year",
    "sma_fast",
    "sma_slow",
    "sma_ratio",
    "rsi_period",
    "rsi_overbought",
    "rsi_oversold",
    "rsi_neutral_upper",
    "rsi_neutral_lower",
    "momentum_lookback",
    "ib_bar_size",
    "ib_duration",
]

TIMEFRAME_CONFIGS: dict[str, dict] = {
    "5min": {
        "name": "5-minute",
        "trading_style": "Day Trading / Scalping",
        "bar_duration": "5 mins",
        "expected_trades_per_year": "500-2000",
        # SMA Parameters (from literature: Forex.in.rs 2022, FXOpen 2025)
        "sma_fast": 20,
        "sma_slow": 50,
        "sma_ratio": 2.5,
        # RSI Parameters (standard 14-period, thresholds to be optimized)
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "rsi_neutral_upper": 55,
        "rsi_neutral_lower": 45,
        # Momentum Parameters (time-proportional to SMA)
        "momentum_lookback": 10,  # Half of fast SMA
        # IB Gateway bar size string
        "ib_bar_size": "5 mins",
        "ib_duration": "30 D",  # Fetch 30 days for testing
    },
    "4H": {
        "name": "4-hour",
        "trading_style": "Day Trading",
        "bar_duration": "4 hours",
        "expected_trades_per_year": "50-200",
        # SMA Parameters (from literature: Teo 2024, TopBrokers 2023)
        "sma_fast": 20,
        "sma_slow": 50,
        "sma_ratio": 2.5,
        # RSI Parameters
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "rsi_neutral_upper": 55,
        "rsi_neutral_lower": 45,
        # Momentum Parameters
        "momentum_lookback": 10,
        # IB Gateway bar size string
        "ib_bar_size": "4 hours",
        "ib_duration": "3 Y",  # Fetch 3 years (2023-2025)
    },
    "1D": {
        "name": "Daily",
        "trading_style": "Swing Trading",
        "bar_duration": "1 day",
        "expected_trades_per_year": "20-100",
        # SMA Parameters (from literature: Murphy 1999, Elder 1993)
        "sma_fast": 50,
        "sma_slow": 200,
        "sma_ratio": 4.0,
        # RSI Parameters
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "rsi_neutral_upper": 55,
        "rsi_neutral_lower": 45,
        # Momentum Parameters
        "momentum_lookback": 14,  # Standard for daily
        # IB Gateway bar size string
        "ib_bar_size": "1 day",
        "ib_duration": "3 Y",  # Fetch 3 years (2023-2025)
    },
}


def _validate_configs() -> None:
    """Validate all timeframe configurations at import time.

    Checks that every timeframe entry contains all required keys and that
    the SMA ratio matches the actual sma_slow / sma_fast relationship.

    Raises:
        ValueError: If a required key is missing or the SMA ratio is
            inconsistent with the configured SMA periods.
    """
    for tf_key, cfg in TIMEFRAME_CONFIGS.items():
        # Check required keys
        missing = [k for k in _REQUIRED_KEYS if k not in cfg]
        if missing:
            raise ValueError(
                f"Timeframe '{tf_key}' is missing required keys: {missing}"
            )

        # Validate SMA ratio consistency
        expected_ratio = cfg["sma_slow"] / cfg["sma_fast"]
        if abs(expected_ratio - cfg["sma_ratio"]) > 0.01:
            raise ValueError(
                f"Timeframe '{tf_key}': sma_ratio {cfg['sma_ratio']} does not "
                f"match sma_slow/sma_fast = {expected_ratio:.2f}"
            )

    logger.info(
        "All %d timeframe configurations validated successfully.",
        len(TIMEFRAME_CONFIGS),
    )


# Run validation when module is imported
_validate_configs()


def get_timeframe_config(timeframe: str) -> dict:
    """Return the configuration dictionary for a given timeframe.

    Args:
        timeframe: Timeframe key (e.g. '5min', '4H', '1D').

    Returns:
        Configuration dictionary for the requested timeframe.

    Raises:
        ValueError: If the timeframe key is not found.
    """
    if timeframe not in TIMEFRAME_CONFIGS:
        available = ", ".join(sorted(TIMEFRAME_CONFIGS.keys()))
        raise ValueError(
            f"Unknown timeframe '{timeframe}'. Available timeframes: {available}"
        )
    return TIMEFRAME_CONFIGS[timeframe]


def list_timeframes() -> list[str]:
    """Return a list of available timeframe keys.

    Returns:
        Sorted list of timeframe key strings.
    """
    return sorted(TIMEFRAME_CONFIGS.keys())
