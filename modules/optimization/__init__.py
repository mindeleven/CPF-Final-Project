"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.optimization
Purpose: Parameter optimization for trading strategies.

Provides grid search and optimization tools for finding better
strategy parameters.

Components:
    - GridSearchOptimizer: Systematic parameter grid search.
    - OptimizationResults: Results storage and ranking.

Example:
    from modules.data import load_timeframe_data
    from modules.optimization import GridSearchOptimizer

    # Load data
    df = load_timeframe_data('5min')

    # Create optimizer
    optimizer = GridSearchOptimizer(timeframe='5min')

    # Define parameter grid
    param_grid = {
        'sma_fast': [15, 20, 25],
        'sma_slow': [45, 50, 55],
        'rsi_lower': [30],
        'rsi_upper': [70],
        'momentum_threshold': [0.0],
    }

    # Run optimization
    results = optimizer.run_grid_search(df, param_grid)

    # Analyze results
    top_5 = results.rank_by_metric('sharpe_ratio', top_n=5)
    print(top_5)

    best = results.get_best_overall(min_trades=20)
    print(f"Best parameters: {best['params']}")

Warning:
    Grid search can overfit to historical data. Use results as
    starting points for further testing, not as guaranteed profits.
    Consider walk-forward analysis for robustness testing.
"""

from modules.optimization.grid_search import GridSearchOptimizer
from modules.optimization.results import OptimizationResults

__all__ = [
    "GridSearchOptimizer",
    "OptimizationResults",
]
