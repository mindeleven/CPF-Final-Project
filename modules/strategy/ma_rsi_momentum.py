"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.strategy.ma_rsi_momentum
Purpose: Multi-indicator confirmation strategy (MA crossover + RSI + Momentum).

Implements a parametric trading strategy that generates signals only when
SMA crossover, RSI filter, and Momentum filter all align. Default parameters
are loaded per-timeframe from modules.config.TIMEFRAME_CONFIGS.

Example:
    from modules.strategy import MARSIMomentumStrategy
    from modules.data import load_timeframe_data

    df = load_timeframe_data('5min')
    strategy = MARSIMomentumStrategy(timeframe='5min')
    signals = strategy.generate_signals(df)
"""

import logging
from typing import Any, Dict, Optional

import pandas as pd

from modules.config import TIMEFRAME_CONFIGS
from modules.indicators import SMA, RSI, Momentum
from modules.strategy.base import Strategy

logger = logging.getLogger(__name__)


class MARSIMomentumStrategy(Strategy):
    """Multi-indicator confirmation strategy.

    Generates trading signals using SMA crossover as the primary signal,
    filtered by RSI (overbought/oversold) and Momentum (directional strength).

    BUY signal (1):
        - Fast SMA crosses ABOVE slow SMA
        - RSI < rsi_upper (not overbought)
        - Momentum > momentum_threshold (positive direction)

    SELL signal (-1):
        - Fast SMA crosses BELOW slow SMA
        - RSI > rsi_lower (not oversold)
        - Momentum < -momentum_threshold (negative direction)

    HOLD signal (0):
        - No crossover, or crossover rejected by filters.

    Attributes:
        name: Strategy name, e.g. "MA_RSI_MOM_5min".
        params: Dictionary of all strategy parameters.
        timeframe: Timeframe this strategy operates on.

    Example:
        >>> strategy = MARSIMomentumStrategy(timeframe='5min')
        >>> signals = strategy.generate_signals(df)
        >>> buy_count = (signals['signal'] == 1).sum()
    """

    def __init__(
        self,
        timeframe: str = "5min",
        sma_fast: Optional[int] = None,
        sma_slow: Optional[int] = None,
        rsi_period: Optional[int] = None,
        rsi_lower: int = 30,
        rsi_upper: int = 70,
        momentum_period: Optional[int] = None,
        momentum_threshold: float = 0.0,
    ) -> None:
        """Initialize MA + RSI + Momentum strategy.

        Args:
            timeframe: Timeframe for this strategy ('5min', '4H', '1D').
            sma_fast: Fast SMA period (default from config).
            sma_slow: Slow SMA period (default from config).
            rsi_period: RSI period (default from config).
            rsi_lower: RSI lower threshold (default: 30, oversold).
            rsi_upper: RSI upper threshold (default: 70, overbought).
            momentum_period: Momentum period (default from config).
            momentum_threshold: Minimum momentum to confirm signal
                (default: 0.0).

        Raises:
            ValueError: If timeframe not in TIMEFRAME_CONFIGS.
            ValueError: If sma_fast >= sma_slow.
        """
        if timeframe not in TIMEFRAME_CONFIGS:
            raise ValueError(
                f"Invalid timeframe '{timeframe}'. "
                f"Available: {sorted(TIMEFRAME_CONFIGS.keys())}"
            )

        cfg = TIMEFRAME_CONFIGS[timeframe]

        # Load defaults from config when not specified
        sma_fast = sma_fast if sma_fast is not None else cfg["sma_fast"]
        sma_slow = sma_slow if sma_slow is not None else cfg["sma_slow"]
        rsi_period = rsi_period if rsi_period is not None else cfg["rsi_period"]
        momentum_period = (
            momentum_period if momentum_period is not None else cfg["momentum_lookback"]
        )

        if sma_fast >= sma_slow:
            raise ValueError(
                f"sma_fast ({sma_fast}) must be less than sma_slow ({sma_slow})"
            )

        self.name = f"MA_RSI_MOM_{timeframe}"
        self.timeframe = timeframe
        self.params: Dict[str, Any] = {
            "sma_fast": sma_fast,
            "sma_slow": sma_slow,
            "rsi_period": rsi_period,
            "rsi_lower": rsi_lower,
            "rsi_upper": rsi_upper,
            "momentum_period": momentum_period,
            "momentum_threshold": momentum_threshold,
        }

        logger.info(f"Initialized {self.name} with params: {self.params}")

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals using multi-indicator confirmation.

        Strategy logic:
            BUY: bullish SMA crossover + RSI not overbought + positive momentum
            SELL: bearish SMA crossover + RSI not oversold + negative momentum
            HOLD: no crossover or filters reject it

        Args:
            data: DataFrame with columns: open, high, low, close, volume.

        Returns:
            DataFrame with added columns:
            - 'sma_fast': Fast SMA values
            - 'sma_slow': Slow SMA values
            - 'rsi': RSI values
            - 'momentum': Momentum values
            - 'signal': Trading signals (1, -1, 0)
            - 'position': Positions (1, -1, 0)

        Raises:
            ValueError: If required columns missing or data empty.
            ValueError: If insufficient data for indicator calculation.

        Example:
            >>> strategy = MARSIMomentumStrategy(timeframe='5min')
            >>> signals = strategy.generate_signals(df)
            >>> buy_signals = signals[signals['signal'] == 1]
        """
        self.validate_data(data, ["close"])

        min_rows = self.params["sma_slow"] + 1
        if len(data) < min_rows:
            raise ValueError(
                f"{self.name}: Need at least {min_rows} rows, " f"got {len(data)}"
            )

        # Work on a copy to avoid modifying original
        result = data.copy()

        # Step 1: Calculate indicators
        sma_fast_ind = SMA(self.params["sma_fast"])
        sma_slow_ind = SMA(self.params["sma_slow"])
        rsi_ind = RSI(self.params["rsi_period"])
        mom_ind = Momentum(self.params["momentum_period"])

        result["sma_fast"] = sma_fast_ind(result)
        result["sma_slow"] = sma_slow_ind(result)
        result["rsi"] = rsi_ind(result)
        result["momentum"] = mom_ind(result)

        # Step 2: Detect crossovers
        sma_fast_prev = result["sma_fast"].shift(1)
        sma_slow_prev = result["sma_slow"].shift(1)

        bullish_cross = (result["sma_fast"] > result["sma_slow"]) & (
            sma_fast_prev <= sma_slow_prev
        )
        bearish_cross = (result["sma_fast"] < result["sma_slow"]) & (
            sma_fast_prev >= sma_slow_prev
        )

        # Step 3: Apply filters
        rsi_allows_buy = result["rsi"] < self.params["rsi_upper"]
        rsi_allows_sell = result["rsi"] > self.params["rsi_lower"]

        momentum_positive = result["momentum"] > self.params["momentum_threshold"]
        momentum_negative = result["momentum"] < -self.params["momentum_threshold"]

        # Combined conditions
        buy_signal = bullish_cross & rsi_allows_buy & momentum_positive
        sell_signal = bearish_cross & rsi_allows_sell & momentum_negative

        # Step 4: Generate signal column
        result["signal"] = 0
        result.loc[buy_signal, "signal"] = 1
        result.loc[sell_signal, "signal"] = -1

        # Step 5: Convert to positions
        result["position"] = self._signals_to_positions(result["signal"])

        # Log signal counts
        buy_count = int(buy_signal.sum())
        sell_count = int(sell_signal.sum())
        logger.info(
            f"{self.name}: Generated {buy_count} BUY, "
            f"{sell_count} SELL signals from {len(result)} rows"
        )

        return result
