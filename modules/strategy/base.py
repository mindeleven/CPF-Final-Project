"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.strategy.base
Purpose: Abstract base class for all trading strategies.

Defines a consistent interface that all strategy implementations must follow.
Provides common validation, signal-to-position conversion, and signal counting.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


class Strategy(ABC):
    """Abstract base class for trading strategies.

    All strategies inherit from this class and implement the
    `generate_signals` method. Provides common utilities for data
    validation, position tracking, and signal analysis.

    Attributes:
        name: Strategy name (e.g., "MA_RSI_MOM_5min").
        params: Dictionary of strategy parameters.
        timeframe: Timeframe this strategy operates on.

    Example:
        >>> class MyStrategy(Strategy):
        ...     def __init__(self):
        ...         self.name = "SMA_Crossover"
        ...         self.params = {"fast": 20, "slow": 50}
        ...         self.timeframe = "5min"
        ...     def generate_signals(self, data):
        ...         self.validate_data(data, ['close'])
        ...         # ... calculate signals ...
        ...         return data
    """

    name: str
    params: Dict[str, Any]
    timeframe: str

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals from price data.

        Args:
            data: DataFrame with OHLC data and datetime index.
                Must contain: open, high, low, close, volume.

        Returns:
            DataFrame with original data plus new columns:
            - 'signal': int (1=BUY, -1=SELL, 0=HOLD)
            - 'position': int (1=LONG, -1=SHORT, 0=FLAT)
            Plus optional strategy-specific columns (indicator values, etc.)

        Raises:
            ValueError: If required columns missing.
            ValueError: If insufficient data.
        """

    def validate_data(self, data: pd.DataFrame, required_columns: List[str]) -> None:
        """Validate input DataFrame.

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

    def _signals_to_positions(self, signals: pd.Series) -> pd.Series:
        """Convert signals to positions using forward-fill logic.

        BUY signal (1) enters LONG (1) until a SELL signal.
        SELL signal (-1) enters SHORT (-1) until a BUY signal.
        HOLD signal (0) maintains the current position.

        Args:
            signals: Series with values (1=BUY, -1=SELL, 0=HOLD).

        Returns:
            Series with positions (1=LONG, -1=SHORT, 0=FLAT).

        Example:
            >>> signals:   [0, 0, 1, 0, 0, -1, 0, 0, 1]
            >>> positions: [0, 0, 1, 1, 1, -1, -1, -1, 1]
        """
        positions = signals.replace(0, pd.NA).ffill().fillna(0).infer_objects(copy=False).astype(int)
        return positions

    def get_signal_count(self, signals: pd.DataFrame) -> Dict[str, int]:
        """Count signal occurrences.

        Args:
            signals: DataFrame with 'signal' column.

        Returns:
            Dict with counts: {'BUY': n, 'SELL': m, 'HOLD': k}.
        """
        signal_col = signals["signal"]
        return {
            "BUY": int((signal_col == 1).sum()),
            "SELL": int((signal_col == -1).sum()),
            "HOLD": int((signal_col == 0).sum()),
        }
