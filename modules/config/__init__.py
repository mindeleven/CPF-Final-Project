"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Jürgen Kober
Co-developed with: Claude Code (Opus 4.5)
Created: February 2026

Module: modules/config/__init__.py
Purpose: Package initializer — exposes key configuration objects.

This module is part of a parametric multi-timeframe trading system for EUR/USD
forex trading, implementing a trend-following strategy with MA crossover, RSI,
and Momentum confirmation filters.
"""

from .timeframes import TIMEFRAME_CONFIGS, get_timeframe_config, list_timeframes
from .constants import (
    INSTRUMENT_SYMBOL,
    IB_HOST,
    IB_PORT,
    IB_CLIENT_ID,
    DATA_DIR,
    ensure_directories,
)

__all__ = [
    "TIMEFRAME_CONFIGS",
    "get_timeframe_config",
    "list_timeframes",
    "INSTRUMENT_SYMBOL",
    "IB_HOST",
    "IB_PORT",
    "IB_CLIENT_ID",
    "DATA_DIR",
    "ensure_directories",
]
