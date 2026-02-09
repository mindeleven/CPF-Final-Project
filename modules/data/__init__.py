"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.data
Purpose: Data fetching and loading functionality.

This package provides tools for acquiring and loading historical forex data
for backtesting and analysis.
"""

from .loader import get_date_range, load_all_timeframes, load_timeframe_data

__all__ = [
    "load_timeframe_data",
    "load_all_timeframes",
    "get_date_range",
]
