"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.optimization.grid_search
Purpose: Perform grid search across strategy parameter space.

Systematically tests all parameter combinations from a user-defined
grid, runs backtests for each, and collects results into an
OptimizationResults container for analysis.

Example:
    from modules.data import load_timeframe_data
    from modules.optimization import GridSearchOptimizer

    df = load_timeframe_data('5min')
    optimizer = GridSearchOptimizer(timeframe='5min')

    param_grid = {
        'sma_fast': [15, 20, 25],
        'sma_slow': [45, 50, 55],
        'rsi_lower': [30],
        'rsi_upper': [70],
        'momentum_threshold': [0.0],
    }

    results = optimizer.run_grid_search(df, param_grid)
    top_5 = results.rank_by_metric('sharpe_ratio', top_n=5)
    print(top_5)
"""

import logging
import time
from itertools import product
from typing import Any, Dict, List, Optional

import pandas as pd

from modules.backtest import BacktestEngine, TransactionCosts
from modules.optimization.results import OptimizationResults
from modules.strategy import MARSIMomentumStrategy

logger = logging.getLogger(__name__)


class GridSearchOptimizer:
    """Systematic grid search optimizer for strategy parameters.

    Tests every combination in a parameter grid by running a full
    backtest for each, then collects results for ranking and analysis.

    Attributes:
        timeframe: Timeframe to optimize for ('5min', '4H', '1D').
        initial_capital: Starting capital for backtests.
        position_size: Fixed position size.
        transaction_costs: Transaction cost model.
    """

    def __init__(
        self,
        timeframe: str = "5min",
        initial_capital: float = 10000.0,
        position_size: float = 10000.0,
        transaction_costs: Optional[TransactionCosts] = None,
    ) -> None:
        """Initialize grid search optimizer.

        Args:
            timeframe: Timeframe to optimize for.
            initial_capital: Starting capital for backtests.
            position_size: Fixed position size.
            transaction_costs: Transaction cost model
                (default: 1 pip spread, no commission).

        Example:
            >>> optimizer = GridSearchOptimizer(
            ...     timeframe='5min',
            ...     initial_capital=10000,
            ...     transaction_costs=TransactionCosts(spread_pips=1.0),
            ... )
        """
        self.timeframe = timeframe
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.transaction_costs = transaction_costs or TransactionCosts()

    def run_grid_search(
        self,
        data: pd.DataFrame,
        param_grid: Dict[str, List[Any]],
        verbose: bool = True,
    ) -> OptimizationResults:
        """Run grid search over parameter combinations.

        Args:
            data: Historical data (from load_timeframe_data).
            param_grid: Dictionary defining parameter ranges, e.g.::

                {
                    'sma_fast': [10, 20, 30],
                    'sma_slow': [40, 50, 60],
                    'rsi_lower': [25, 30, 35],
                    'rsi_upper': [65, 70, 75],
                    'momentum_threshold': [0.0, 0.0001, 0.0002],
                }

            verbose: If True, print progress during optimization.

        Returns:
            OptimizationResults object with all tested combinations.

        Example:
            >>> from modules.data import load_timeframe_data
            >>> df = load_timeframe_data('5min')
            >>> optimizer = GridSearchOptimizer(timeframe='5min')
            >>> param_grid = {
            ...     'sma_fast': [15, 20, 25],
            ...     'sma_slow': [45, 50, 55],
            ...     'rsi_lower': [30],
            ...     'rsi_upper': [70],
            ...     'momentum_threshold': [0.0],
            ... }
            >>> results = optimizer.run_grid_search(df, param_grid)
            >>> print(f"Tested {len(results.results)} combinations")
        """
        # Generate all combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))
        total_combinations = len(combinations)

        logger.info(
            "Starting grid search: %d combinations for %s",
            total_combinations,
            self.timeframe,
        )
        if verbose:
            print(f"Testing {total_combinations} parameter combinations...")

        results = OptimizationResults()
        skipped = 0
        errors = 0
        start_time = time.time()

        for i, combo in enumerate(combinations):
            params = dict(zip(param_names, combo))

            # Skip invalid combinations
            if params.get("sma_fast", 0) >= params.get("sma_slow", float("inf")):
                if verbose:
                    print(
                        f"  Skipping invalid: sma_fast={params['sma_fast']} "
                        f">= sma_slow={params['sma_slow']}"
                    )
                skipped += 1
                continue

            if params.get("rsi_lower", 0) >= params.get("rsi_upper", 100):
                if verbose:
                    print(
                        f"  Skipping invalid: rsi_lower={params['rsi_lower']} "
                        f">= rsi_upper={params['rsi_upper']}"
                    )
                skipped += 1
                continue

            # Progress reporting
            if verbose and i % 10 == 0 and i > 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                remaining = (total_combinations - i) / rate if rate > 0 else 0
                print(
                    f"  Progress: {i}/{total_combinations} "
                    f"({i / total_combinations * 100:.1f}%) "
                    f"~{remaining:.0f}s remaining"
                )

            # Run backtest with these parameters
            try:
                metrics = self._run_single_backtest(data, params)
                results.add_result(params, metrics, self.timeframe)
            except Exception as e:
                errors += 1
                logger.warning("Error with params %s: %s", params, e)
                if verbose:
                    print(f"  Error with params {params}: {e}")
                continue

        elapsed_total = time.time() - start_time

        logger.info(
            "Completed: %d successful, %d skipped, %d errors in %.1fs",
            len(results.results),
            skipped,
            errors,
            elapsed_total,
        )

        if verbose:
            print(f"\nCompleted: {len(results.results)} successful backtests")
            print(f"Skipped: {skipped} invalid combinations")
            if errors:
                print(f"Errors: {errors}")
            print(f"Time: {elapsed_total:.1f}s")
            self._print_overfitting_warnings()

        return results

    def _run_single_backtest(
        self,
        data: pd.DataFrame,
        params: Dict[str, Any],
    ) -> Dict[str, float]:
        """Run single backtest with given parameters.

        Args:
            data: Historical data.
            params: Strategy parameters.

        Returns:
            Metrics dict from backtest.
        """
        strategy = MARSIMomentumStrategy(
            timeframe=self.timeframe,
            sma_fast=params.get("sma_fast"),
            sma_slow=params.get("sma_slow"),
            rsi_lower=params.get("rsi_lower", 30),
            rsi_upper=params.get("rsi_upper", 70),
            momentum_threshold=params.get("momentum_threshold", 0.0),
        )

        signals = strategy.generate_signals(data)

        engine = BacktestEngine(
            initial_capital=self.initial_capital,
            position_size=self.position_size,
            transaction_costs=self.transaction_costs,
        )

        backtest_results = engine.run(data, signals)
        return backtest_results["metrics"]

    @staticmethod
    def get_default_param_grid(timeframe: str = "5min") -> Dict[str, List[Any]]:
        """Get reasonable default parameter grid for a timeframe.

        Provides a moderate-sized grid centred around the default
        parameters from TIMEFRAME_CONFIGS.

        Args:
            timeframe: '5min', '4H', or '1D'.

        Returns:
            Default parameter grid dict.

        Example:
            >>> grid = GridSearchOptimizer.get_default_param_grid('5min')
            >>> for k, v in grid.items():
            ...     print(f"{k}: {v}")
        """
        if timeframe == "1D":
            return {
                "sma_fast": [40, 50, 60],
                "sma_slow": [180, 200, 220],
                "rsi_lower": [25, 30, 35],
                "rsi_upper": [65, 70, 75],
                "momentum_threshold": [0.0, 0.0001, 0.0002],
            }

        # 5min and 4H share similar default ranges
        return {
            "sma_fast": [15, 20, 25, 30],
            "sma_slow": [40, 50, 60, 70],
            "rsi_lower": [25, 30, 35],
            "rsi_upper": [65, 70, 75],
            "momentum_threshold": [0.0, 0.00005, 0.0001],
        }

    @staticmethod
    def _print_overfitting_warnings() -> None:
        """Print warnings about overfitting risks."""
        print("\n" + "=" * 60)
        print("  OVERFITTING WARNING")
        print("=" * 60)
        print("These results are optimized to THIS specific historical period.")
        print("Past performance does NOT guarantee future results.")
        print("\nBest practices:")
        print("- Use walk-forward analysis for robustness testing")
        print("- Test on out-of-sample data")
        print("- Consider parameter stability across different periods")
        print("- Prioritize Sharpe ratio over raw returns")
        print("- Require minimum number of trades (20+) for statistical significance")
        print("=" * 60 + "\n")
