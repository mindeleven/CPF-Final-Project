"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.indicators.base
Purpose: Abstract base class for all technical indicators.

Defines a consistent interface that all indicator implementations must follow.
Provides common validation logic for input DataFrames.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


class Indicator(ABC):
    """Abstract base class for technical indicators.

    All indicators inherit from this class and implement the `calculate` method.
    Indicators can be called as functions via `__call__`.

    Attributes:
        name: Indicator name (e.g., "SMA_20").
        params: Dictionary of indicator parameters.

    Example:
        >>> sma = SMA(period=20)
        >>> values = sma(df)  # equivalent to sma.calculate(df)
    """

    name: str
    params: Dict[str, Any]

    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """Calculate indicator values.

        Args:
            data: DataFrame with OHLC columns (open, high, low, close, volume)
                indexed by datetime.

        Returns:
            Series with indicator values, same index as input data.

        Raises:
            ValueError: If required columns are missing.
            ValueError: If insufficient data for calculation.
        """

    def validate_data(self, data: pd.DataFrame, required_columns: List[str]) -> None:
        """Validate input DataFrame has required columns.

        Args:
            data: DataFrame to validate.
            required_columns: List of required column names.

        Raises:
            ValueError: If data is empty.
            ValueError: If any required columns are missing.
        """
        if data.empty:
            raise ValueError(f"{self.name}: Input DataFrame is empty")

        missing = [col for col in required_columns if col not in data.columns]
        if missing:
            raise ValueError(f"{self.name}: Missing required columns: {missing}")

    def __call__(self, data: pd.DataFrame) -> pd.Series:
        """Allow indicator to be called like a function."""
        return self.calculate(data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.params})"
