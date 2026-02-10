"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.backtest
Purpose: Backtesting engine for evaluating trading strategies on historical data.

Provides backtesting engine with bar-by-bar simulation, realistic transaction
costs (spread + commission), and comprehensive performance metrics.

Components:
    BacktestEngine: Main backtesting loop.
    TransactionCosts: Spread and commission modeling.
    metrics: Performance metric calculations.

Example:
    from modules.backtest import BacktestEngine, TransactionCosts
    from modules.data import load_timeframe_data
    from modules.strategy import MARSIMomentumStrategy

    # Load data
    df = load_timeframe_data('5min')

    # Generate signals
    strategy = MARSIMomentumStrategy(timeframe='5min')
    signals = strategy.generate_signals(df)

    # Run backtest
    costs = TransactionCosts(spread_pips=1.5)
    engine = BacktestEngine(
        initial_capital=10000,
        position_size=10000,
        transaction_costs=costs,
    )
    results = engine.run(df, signals)

    # Analyze
    print(f"Sharpe: {results['metrics']['sharpe_ratio']:.2f}")
    print(f"Max DD: {results['metrics']['max_drawdown_pct']:.1f}%")
    print(f"Win Rate: {results['metrics']['win_rate']*100:.1f}%")
"""

from modules.backtest.engine import BacktestEngine
from modules.backtest.transaction_costs import TransactionCosts
from modules.backtest import metrics

__all__ = [
    "BacktestEngine",
    "TransactionCosts",
    "metrics",
]
