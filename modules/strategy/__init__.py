"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.strategy
Purpose: Trading strategy module for signal generation.

Implements trading strategies that combine technical indicators
to generate buy/sell signals with multi-indicator confirmation.

Available strategies:
    MARSIMomentumStrategy: MA crossover + RSI + Momentum filters

Example:
    from modules.strategy import MARSIMomentumStrategy
    from modules.data import load_timeframe_data

    df = load_timeframe_data('5min')
    strategy = MARSIMomentumStrategy(timeframe='5min')
    signals = strategy.generate_signals(df)

    buy_count = (signals['signal'] == 1).sum()
    sell_count = (signals['signal'] == -1).sum()
    print(f"BUY signals: {buy_count}, SELL signals: {sell_count}")
"""

from modules.strategy.base import Strategy
from modules.strategy.ma_rsi_momentum import MARSIMomentumStrategy

__all__ = [
    "Strategy",
    "MARSIMomentumStrategy",
]
