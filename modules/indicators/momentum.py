"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.indicators.momentum
Purpose: Momentum indicator.

Measures the rate of change in price by computing the difference between
the current close and the close N periods ago.
"""

import logging

import pandas as pd

from modules.indicators.base import Indicator

logger = logging.getLogger(__name__)


class Momentum(Indicator):
    """Momentum indicator.

    Calculates the absolute price difference between the current close
    and the close N periods ago. Positive values indicate upward momentum,
    negative values indicate downward momentum.

    Args:
        period: Number of periods to look back (default: 10).

    Raises:
        ValueError: If period < 1.

    Example:
        >>> mom = Momentum(period=10)
        >>> mom_values = mom(df)
    """

    def __init__(self, period: int = 10) -> None:
        """Initialize Momentum indicator.

        Args:
            period: Number of periods to look back (default: 10).

        Raises:
            ValueError: If period < 1.
        """
        if period < 1:
            raise ValueError(f"Momentum period must be >= 1, got {period}")

        self.name = f"MOM_{period}"
        self.params = {"period": period}

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Momentum indicator.

        Formula: Momentum = close(today) - close(N periods ago)

        Args:
            data: DataFrame with 'close' column.

        Returns:
            Series with momentum values. First N values will be NaN.

        Raises:
            ValueError: If 'close' column is missing.
            ValueError: If data is empty.

        Notes:
            - Positive values indicate upward momentum.
            - Negative values indicate downward momentum.
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

        result = data["close"].diff(periods=period)
        result.name = self.name
        return result
