"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.indicators
Purpose: Technical analysis indicators for trading strategies.

Available indicators:
- SMA: Simple Moving Average
- RSI: Relative Strength Index
- Momentum: Rate of change indicator

Example:
    from modules.indicators import SMA, RSI, Momentum

    sma = SMA(period=20)
    rsi = RSI(period=14)
    momentum = Momentum(period=10)

    df['SMA_20'] = sma(df)
    df['RSI_14'] = rsi(df)
    df['MOM_10'] = momentum(df)
"""

from .base import Indicator
from .momentum import Momentum
from .rsi import RSI
from .sma import SMA

__all__ = [
    "Indicator",
    "SMA",
    "RSI",
    "Momentum",
]
