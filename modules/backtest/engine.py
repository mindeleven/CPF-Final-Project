"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.backtest.engine
Purpose: Main backtesting engine for evaluating trading strategies.

Processes strategy signals bar-by-bar, tracks positions, calculates P&L with
realistic transaction costs, and computes performance metrics.

Key design:
    - Signal at bar t -> execute at bar t+1 open (no look-ahead bias)
    - Transaction costs at both entry and exit
    - Fixed position sizing (configurable)

Example:
    from modules.backtest.engine import BacktestEngine
    from modules.backtest.transaction_costs import TransactionCosts

    engine = BacktestEngine(initial_capital=10000, position_size=10000)
    results = engine.run(data, signals)
    print(f"Return: {results['metrics']['total_return_pct']:.2f}%")
"""

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from modules.backtest.metrics import calculate_all_metrics
from modules.backtest.transaction_costs import TransactionCosts

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Backtesting engine for evaluating trading strategies.

    Simulates bar-by-bar trade execution with realistic transaction costs.
    Tracks positions, equity curve, and generates a detailed trade log.

    Attributes:
        initial_capital: Starting capital in quote currency (USD).
        position_size: Fixed position size in base currency (EUR).
        transaction_costs: TransactionCosts model.
        trades: List of trade dictionaries (populated after run).
        equity_curve: List of portfolio values at each bar (populated after run).

    Example:
        >>> engine = BacktestEngine(initial_capital=10000, position_size=10000)
        >>> results = engine.run(data, signals)
        >>> print(results['metrics']['sharpe_ratio'])
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        position_size: float = 10000.0,
        transaction_costs: TransactionCosts = None,
    ) -> None:
        """Initialize backtesting engine.

        Args:
            initial_capital: Starting capital in quote currency (USD).
            position_size: Fixed position size in base currency (EUR).
            transaction_costs: TransactionCosts object. Defaults to
                1 pip spread, 0% commission if not provided.

        Example:
            engine = BacktestEngine(
                initial_capital=10000.0,
                position_size=10000.0,
                transaction_costs=TransactionCosts(spread_pips=1.5),
            )
        """
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.transaction_costs = (
            transaction_costs if transaction_costs is not None else TransactionCosts()
        )
        self.trades: List[Dict] = []
        self.equity_curve: List[float] = []

        logger.info(
            "BacktestEngine initialized: capital=$%.2f, size=%.0f, " "spread=%.1f pips",
            self.initial_capital,
            self.position_size,
            self.transaction_costs.spread_pips,
        )

    def run(
        self,
        data: pd.DataFrame,
        strategy_signals: pd.DataFrame,
    ) -> Dict[str, Any]:
        """Run backtest on historical data with strategy signals.

        Args:
            data: DataFrame with OHLC data (from load_timeframe_data).
                Must contain 'open' and 'close' columns.
            strategy_signals: DataFrame with 'signal' and 'position' columns
                (from strategy.generate_signals).

        Returns:
            Dict containing:
            - 'metrics': Dict of performance metrics.
            - 'trades': DataFrame of all trades.
            - 'equity_curve': Series of portfolio values.
            - 'final_capital': Final portfolio value.

        Example:
            >>> results = engine.run(df, signals)
            >>> print(f"Return: {results['metrics']['total_return_pct']:.2f}%")
        """
        logger.info("Starting backtest with %d bars", len(data))

        # Initialize state
        cash = self.initial_capital
        position = 0  # 1=LONG, -1=SHORT, 0=FLAT
        position_entry_price = 0.0
        position_entry_bar = 0
        self.equity_curve = [self.initial_capital]
        self.trades = []

        num_bars = len(strategy_signals)

        for i in range(num_bars):
            current_signal = int(strategy_signals.iloc[i]["signal"])
            current_price = float(data.iloc[i]["close"])

            # Check for position change
            if current_signal != 0:
                # Close existing position if any
                if position != 0:
                    if i + 1 < num_bars:
                        exit_price = float(data.iloc[i + 1]["open"])
                    else:
                        exit_price = current_price

                    pnl = self._calculate_pnl(
                        position, position_entry_price, exit_price, self.position_size
                    )
                    exit_cost = self.transaction_costs.calculate_total_cost(
                        exit_price, self.position_size, position
                    )
                    net_pnl = pnl - exit_cost
                    cash += net_pnl

                    self.trades.append(
                        {
                            "entry_bar": position_entry_bar,
                            "exit_bar": i,
                            "entry_price": position_entry_price,
                            "exit_price": exit_price,
                            "direction": "LONG" if position == 1 else "SHORT",
                            "pnl": pnl,
                            "costs": exit_cost,
                            "net_pnl": net_pnl,
                        }
                    )

                # Enter new position
                if i + 1 < num_bars:
                    entry_price = float(data.iloc[i + 1]["open"])
                    entry_cost = self.transaction_costs.calculate_total_cost(
                        entry_price, self.position_size, current_signal
                    )
                    cash -= entry_cost

                    position = current_signal
                    position_entry_price = entry_price
                    position_entry_bar = i + 1

            # Update equity
            if position != 0:
                unrealized_pnl = self._calculate_pnl(
                    position,
                    position_entry_price,
                    current_price,
                    self.position_size,
                )
                equity = cash + unrealized_pnl
            else:
                equity = cash

            self.equity_curve.append(equity)

        # Close any remaining open position at last close
        if position != 0:
            last_price = float(data.iloc[-1]["close"])
            pnl = self._calculate_pnl(
                position, position_entry_price, last_price, self.position_size
            )
            exit_cost = self.transaction_costs.calculate_total_cost(
                last_price, self.position_size, position
            )
            net_pnl = pnl - exit_cost
            cash += net_pnl

            self.trades.append(
                {
                    "entry_bar": position_entry_bar,
                    "exit_bar": num_bars - 1,
                    "entry_price": position_entry_price,
                    "exit_price": last_price,
                    "direction": "LONG" if position == 1 else "SHORT",
                    "pnl": pnl,
                    "costs": exit_cost,
                    "net_pnl": net_pnl,
                }
            )
            # Update final equity to reflect closed position
            self.equity_curve[-1] = cash

        # Build results
        equity_series = pd.Series(
            self.equity_curve[1:], index=data.index, name="equity"
        )
        trades_df = pd.DataFrame(self.trades)

        periods_per_year = self._get_periods_per_year(data)
        metrics = calculate_all_metrics(
            equity_curve=equity_series,
            trades=trades_df,
            initial_capital=self.initial_capital,
            periods_per_year=periods_per_year,
        )

        final_capital = float(equity_series.iloc[-1])
        logger.info(
            "Backtest complete. Trades: %d, Final capital: $%.2f",
            len(self.trades),
            final_capital,
        )

        return {
            "metrics": metrics,
            "trades": trades_df,
            "equity_curve": equity_series,
            "final_capital": final_capital,
        }

    def _calculate_pnl(
        self,
        direction: int,
        entry_price: float,
        exit_price: float,
        size: float,
    ) -> float:
        """Calculate profit/loss for a position.

        Args:
            direction: 1 for LONG, -1 for SHORT.
            entry_price: Entry price.
            exit_price: Exit price.
            size: Position size.

        Returns:
            P&L in quote currency.
        """
        return direction * (exit_price - entry_price) * size

    def _get_periods_per_year(self, data: pd.DataFrame) -> int:
        """Determine number of periods per year based on data frequency.

        Args:
            data: DataFrame with datetime index.

        Returns:
            Approximate number of bars per year.
        """
        if len(data) < 2:
            return 252

        # Use median time delta to infer frequency
        time_deltas = pd.Series(data.index).diff().dropna()
        median_delta = time_deltas.median()
        minutes = median_delta.total_seconds() / 60

        if minutes <= 10:  # 5min bars
            return 72000
        elif minutes <= 300:  # 4H bars
            return 2080
        else:  # 1D bars
            return 252
