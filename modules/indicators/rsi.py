"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.indicators.rsi
Purpose: Relative Strength Index (RSI) indicator.

Measures momentum by comparing recent gains versus losses using EMA smoothing.
RSI values range from 0 to 100, with >70 typically considered overbought
and <30 considered oversold.
"""

import logging

import numpy as np
import pandas as pd

from modules.indicators.base import Indicator

logger = logging.getLogger(__name__)


class RSI(Indicator):
    """Relative Strength Index indicator.

    Measures the speed and magnitude of price movements by comparing
    average gains to average losses over a specified period.

    Args:
        period: Number of periods for RSI calculation (default: 14).

    Raises:
        ValueError: If period < 2.

    Example:
        >>> rsi = RSI(period=14)
        >>> rsi_values = rsi(df)
    """

    def __init__(self, period: int = 14) -> None:
        """Initialize RSI indicator.

        Args:
            period: Number of periods for RSI calculation (default: 14).

        Raises:
            ValueError: If period < 2.
        """
        if period < 2:
            raise ValueError(f"RSI period must be >= 2, got {period}")

        self.name = f"RSI_{period}"
        self.params = {"period": period}

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Relative Strength Index.

        Formula:
            1. Price changes: delta = close.diff()
            2. Separate gains (positive) and losses (negative).
            3. Average gain/loss using EMA: ewm(alpha=1/period, adjust=False)
            4. RS = avg_gain / avg_loss
            5. RSI = 100 - (100 / (1 + RS))

        Args:
            data: DataFrame with 'close' column.

        Returns:
            Series with RSI values (0-100). First row is always NaN
            (from diff()), and early values reflect EMA warmup.

        Raises:
            ValueError: If 'close' column is missing.
            ValueError: If data is empty.

        Notes:
            - RSI > 70: traditionally considered overbought.
            - RSI < 30: traditionally considered oversold.
        """
        self.validate_data(data, ["close"])

        period = self.params["period"]

        if len(data) < period + 1:
            logger.warning(
                "%s: Data has %d rows, fewer than period+1 (%d)",
                self.name,
                len(data),
                period + 1,
            )

        delta = data["close"].diff()

        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)

        avg_gain = gains.ewm(alpha=1.0 / period, adjust=False).mean()
        avg_loss = losses.ewm(alpha=1.0 / period, adjust=False).mean()

        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))

        # Handle division by zero: when avg_loss is 0, RSI should be 100
        rsi = rsi.where(avg_loss != 0, 100.0)

        # First value is NaN from diff()
        rsi.iloc[0] = np.nan

        result = rsi
        result.name = self.name
        return result
