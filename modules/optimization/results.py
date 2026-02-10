"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.optimization.results
Purpose: Store, compare, and rank optimization results.

Provides the OptimizationResults container for collecting backtest
metrics across many parameter combinations and ranking them by
various criteria.

Example:
    from modules.optimization.results import OptimizationResults

    results = OptimizationResults()
    results.add_result(
        params={'sma_fast': 20, 'sma_slow': 50},
        metrics={'sharpe_ratio': 0.5, 'total_return_pct': 2.3},
        timeframe='5min',
    )
    df = results.to_dataframe()
    print(df)
"""

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class OptimizationResults:
    """Container for storing, comparing, and ranking optimization results.

    Collects parameter/metrics pairs from grid search runs and provides
    methods to convert to DataFrame, rank by metric, compute statistics,
    and identify the best overall combination.

    Attributes:
        results: List of dicts, each containing 'params', 'metrics',
            and 'timeframe' keys.
    """

    def __init__(self) -> None:
        """Initialize optimization results container."""
        self.results: List[Dict[str, Any]] = []

    def add_result(
        self,
        params: Dict[str, Any],
        metrics: Dict[str, float],
        timeframe: str,
    ) -> None:
        """Add a single optimization result.

        Args:
            params: Strategy parameters tested
                (e.g., {'sma_fast': 20, 'sma_slow': 50}).
            metrics: Backtest metrics from this parameter set.
            timeframe: Timeframe tested ('5min', '4H', '1D').

        Example:
            >>> results = OptimizationResults()
            >>> results.add_result(
            ...     params={'sma_fast': 20, 'sma_slow': 50},
            ...     metrics={'sharpe_ratio': 0.5, 'total_return_pct': 2.3},
            ...     timeframe='5min',
            ... )
            >>> len(results.results)
            1
        """
        self.results.append(
            {
                "params": params,
                "metrics": metrics,
                "timeframe": timeframe,
            }
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to DataFrame for analysis.

        Returns:
            DataFrame with parameter columns, metric columns, and a
            timeframe column. Returns empty DataFrame if no results.

        Example:
            >>> results = OptimizationResults()
            >>> results.add_result(
            ...     params={'sma_fast': 20, 'sma_slow': 50},
            ...     metrics={'sharpe_ratio': 0.5},
            ...     timeframe='5min',
            ... )
            >>> df = results.to_dataframe()
            >>> 'sma_fast' in df.columns
            True
        """
        if not self.results:
            return pd.DataFrame()

        rows = []
        for result in self.results:
            row: Dict[str, Any] = {}
            row.update(result["params"])
            row.update(result["metrics"])
            row["timeframe"] = result["timeframe"]
            rows.append(row)

        return pd.DataFrame(rows)

    def rank_by_metric(
        self,
        metric: str,
        ascending: bool = False,
        top_n: int = 10,
    ) -> pd.DataFrame:
        """Rank parameter combinations by a specific metric.

        Args:
            metric: Metric name (e.g., 'sharpe_ratio', 'total_return_pct').
            ascending: If True, lower is better (e.g., for max_drawdown_pct).
            top_n: Number of top results to return.

        Returns:
            DataFrame of top N parameter combinations sorted by metric.

        Raises:
            ValueError: If no results stored or metric not found.

        Example:
            >>> top_sharpe = results.rank_by_metric('sharpe_ratio', top_n=5)
            >>> low_dd = results.rank_by_metric(
            ...     'max_drawdown_pct', ascending=True, top_n=5
            ... )
        """
        if not self.results:
            raise ValueError("No results to rank")

        df = self.to_dataframe()

        if metric not in df.columns:
            raise ValueError(
                f"Metric '{metric}' not found. "
                f"Available: {[c for c in df.columns if c not in ['timeframe']]}"
            )

        return (
            df.sort_values(metric, ascending=ascending)
            .head(top_n)
            .reset_index(drop=True)
        )

    def get_metric_statistics(self, metric: str) -> Dict[str, float]:
        """Get statistics for a specific metric across all results.

        Args:
            metric: Metric name.

        Returns:
            Dict with keys: min, max, mean, median, std.

        Raises:
            ValueError: If no results stored or metric not found.

        Example:
            >>> stats = results.get_metric_statistics('sharpe_ratio')
            >>> print(f"Range: {stats['min']:.2f} to {stats['max']:.2f}")
        """
        if not self.results:
            raise ValueError("No results to compute statistics")

        df = self.to_dataframe()

        if metric not in df.columns:
            raise ValueError(
                f"Metric '{metric}' not found. "
                f"Available: {[c for c in df.columns if c not in ['timeframe']]}"
            )

        values = df[metric].dropna()
        return {
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "std": float(np.std(values)),
        }

    def get_best_overall(
        self,
        primary_metric: str = "sharpe_ratio",
        secondary_metric: str = "total_return_pct",
        min_trades: int = 10,
    ) -> Dict[str, Any]:
        """Get best parameter combination using multiple criteria.

        Filters results by minimum trade count, then ranks by primary
        metric with secondary metric as tiebreaker.

        Args:
            primary_metric: Primary ranking metric.
            secondary_metric: Tiebreaker metric.
            min_trades: Minimum number of trades required.

        Returns:
            Dict containing 'params', 'metrics', and 'rank' keys.

        Raises:
            ValueError: If no results match the criteria.

        Example:
            >>> best = results.get_best_overall(
            ...     primary_metric='sharpe_ratio',
            ...     secondary_metric='total_return_pct',
            ...     min_trades=20,
            ... )
            >>> print(f"Best params: {best['params']}")
        """
        if not self.results:
            raise ValueError("No results to evaluate")

        df = self.to_dataframe()

        # Filter by minimum trades
        if "num_trades" in df.columns:
            filtered = df[df["num_trades"] >= min_trades]
        else:
            filtered = df

        if filtered.empty:
            raise ValueError(
                f"No results with >= {min_trades} trades. " f"Try lowering min_trades."
            )

        # Sort by primary then secondary metric (both descending)
        sorted_df = filtered.sort_values(
            [primary_metric, secondary_metric],
            ascending=[False, False],
        )

        best_row = sorted_df.iloc[0]

        # Extract params and metrics from the best row
        param_keys = list(self.results[0]["params"].keys())
        metric_keys = list(self.results[0]["metrics"].keys())

        best_params = {k: best_row[k] for k in param_keys if k in best_row.index}
        best_metrics = {k: best_row[k] for k in metric_keys if k in best_row.index}

        return {
            "params": best_params,
            "metrics": best_metrics,
            "rank": {
                "primary_metric": primary_metric,
                "primary_value": best_row[primary_metric],
                "secondary_metric": secondary_metric,
                "secondary_value": best_row[secondary_metric],
                "filtered_count": len(filtered),
                "total_count": len(df),
            },
        }
