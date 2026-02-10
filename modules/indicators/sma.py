"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.indicators.sma
Purpose: Simple Moving Average (SMA) indicator.

Calculates the average of closing prices over N periods using a rolling window.
"""

import logging

import pandas as pd

from modules.indicators.base import Indicator

logger = logging.getLogger(__name__)


class SMA(Indicator):
    """Simple Moving Average indicator.

    Calculates the arithmetic mean of closing prices over a specified
    number of periods using a rolling window.

    Args:
        period: Number of periods for the moving average (default: 20).

    Raises:
        ValueError: If period < 2.

    Example:
        >>> sma = SMA(period=20)
        >>> sma_values = sma(df)
    """

    def __init__(self, period: int = 20) -> None:
        """Initialize SMA indicator.

        Args:
            period: Number of periods for moving average (default: 20).

        Raises:
            ValueError: If period < 2.
        """
        if period < 2:
            raise ValueError(f"SMA period must be >= 2, got {period}")

        self.name = f"SMA_{period}"
        self.params = {"period": period}

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Simple Moving Average.

        Formula: SMA = sum(close prices over N periods) / N

        Args:
            data: DataFrame with 'close' column.

        Returns:
            Series with SMA values. First (period-1) values will be NaN.

        Raises:
            ValueError: If 'close' column is missing.
            ValueError: If data is empty.
        """
        self.validate_data(data, ["close"])

        period = self.params["period"]

        if len(data) < period:
            logger.warning(
                "%s: Data has %d rows, fewer than period %d",
                self.name,
                len(data),
                period,
            )

        result = data["close"].rolling(window=period).mean()
        result.name = self.name
        return result
