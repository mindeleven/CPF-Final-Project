"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Jürgen Kober
Co-developed with: Claude Code (Opus 4.5)
Created: February 2026

Module: modules/config/constants.py
Purpose: Global constants and helper utilities for the trading system.

This module is part of a parametric multi-timeframe trading system for EUR/USD
forex trading, implementing a trend-following strategy with MA crossover, RSI,
and Momentum confirmation filters.
"""

import logging
import os

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Instrument
# ---------------------------------------------------------------------------
INSTRUMENT_SYMBOL: str = "EUR.USD"
INSTRUMENT_CURRENCY: str = "USD"
INSTRUMENT_EXCHANGE: str = "IDEALPRO"

# ---------------------------------------------------------------------------
# IB Gateway Connection
# ---------------------------------------------------------------------------
IB_HOST: str = "127.0.0.1"  # localhost for local testing
IB_PORT: int = 4002  # Paper trading port
IB_CLIENT_ID: int = 100  # For data fetching (different from live trading)

# ---------------------------------------------------------------------------
# Transaction Costs (EUR/USD forex)
# ---------------------------------------------------------------------------
SPREAD_PIPS: int = 1  # Typical EUR/USD spread
PIP_VALUE: float = 0.0001  # EUR/USD pip definition
SPREAD_PERCENTAGE: float = 0.0085 / 100  # ~0.0085% per side
COMMISSION_PER_TRADE: float = 0.0  # IB forex commission minimal for retail

# ---------------------------------------------------------------------------
# Position Sizing
# ---------------------------------------------------------------------------
DEFAULT_POSITION_SIZE: int = 10_000  # $10,000 notional
LEVERAGE: float = 1.0  # No leverage (1:1)

# ---------------------------------------------------------------------------
# Data Paths
# ---------------------------------------------------------------------------
DATA_DIR: str = "data/historical"
RESULTS_DIR: str = "results"
LOGS_DIR: str = "logs"

# ---------------------------------------------------------------------------
# Backtesting
# ---------------------------------------------------------------------------
TRAIN_TEST_SPLIT: float = 0.7  # 70% training, 30% testing
MIN_TRADES_FOR_SIGNIFICANCE: int = 20

# ---------------------------------------------------------------------------
# Date Range for Historical Data
# ---------------------------------------------------------------------------
DATA_START_DATE: str = "2023-01-01"
DATA_END_DATE: str = "2025-12-31"


def get_data_path(timeframe: str, filename: str | None = None) -> str:
    """Construct the full path to a data file for a given timeframe.

    Args:
        timeframe: Timeframe key (e.g. '5min', '4H', '1D').
        filename: Optional filename within the timeframe directory.
            If *None*, returns the timeframe directory path itself.

    Returns:
        Absolute or relative path string to the data file or directory.
    """
    path = os.path.join(DATA_DIR, timeframe)
    if filename is not None:
        path = os.path.join(path, filename)
    return path


def ensure_directories() -> None:
    """Create required project directories if they do not already exist.

    Creates the following directory tree:
        - data/historical/  (plus one subdirectory per timeframe)
        - results/
        - logs/
    """
    from modules.config.timeframes import TIMEFRAME_CONFIGS

    dirs_to_create = [
        DATA_DIR,
        RESULTS_DIR,
        LOGS_DIR,
    ]

    # Add per-timeframe data directories
    for tf_key in TIMEFRAME_CONFIGS:
        dirs_to_create.append(os.path.join(DATA_DIR, tf_key))

    for directory in dirs_to_create:
        os.makedirs(directory, exist_ok=True)
        logger.info("Ensured directory exists: %s", directory)
