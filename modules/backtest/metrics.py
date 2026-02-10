"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.backtest.metrics
Purpose: Performance metrics calculations for backtested strategies.

Pure functions for computing Sharpe ratio, maximum drawdown, win rate,
profit factor, and other standard performance metrics.

Example:
    from modules.backtest.metrics import calculate_all_metrics

    metrics = calculate_all_metrics(equity_curve, trades_df, initial_capital=10000)
    print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
"""

import logging
from typing import Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_returns(equity_curve: pd.Series) -> pd.Series:
    """Calculate percentage returns from equity curve.

    Args:
        equity_curve: Series of portfolio values over time.

    Returns:
        Series of percentage returns (NaN for first entry).

    Example:
        >>> equity = pd.Series([10000, 10100, 10050, 10200])
        >>> returns = calculate_returns(equity)
    """
    return equity_curve.pct_change()


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """Calculate annualized Sharpe ratio.

    Args:
        returns: Series of period returns.
        risk_free_rate: Annual risk-free rate (default: 0.0).
        periods_per_year: Number of periods in a year.
            - 252 for daily (trading days)
            - 2080 for 4H (6 bars/day * 5 days * 52 weeks)
            - 72000 for 5min (288 bars/day * 250 trading days)

    Returns:
        Annualized Sharpe ratio. Returns 0.0 if std is zero.

    Example:
        >>> returns = pd.Series([0.01, -0.005, 0.015, 0.002])
        >>> sharpe = calculate_sharpe_ratio(returns, periods_per_year=252)
    """
    clean_returns = returns.dropna()
    if len(clean_returns) < 2:
        return 0.0

    mean_return = clean_returns.mean()
    std_return = clean_returns.std()

    if std_return == 0:
        return 0.0

    risk_free_per_period = risk_free_rate / periods_per_year
    sharpe = (
        (mean_return - risk_free_per_period) / std_return * np.sqrt(periods_per_year)
    )
    return float(sharpe)


def calculate_max_drawdown(equity_curve: pd.Series) -> Dict[str, float]:
    """Calculate maximum drawdown and related metrics.

    Args:
        equity_curve: Series of portfolio values.

    Returns:
        Dict with keys:
        - 'max_drawdown': Maximum drawdown as decimal (e.g., -0.15 = -15%).
        - 'max_drawdown_pct': Maximum drawdown as percentage (e.g., -15.0).
        - 'drawdown_duration': Number of periods in max drawdown.
        - 'peak_value': Equity at peak before max drawdown.
        - 'valley_value': Equity at bottom of max drawdown.

    Example:
        >>> equity = pd.Series([10000, 11000, 10500, 9500, 10000, 11500])
        >>> dd = calculate_max_drawdown(equity)
        >>> print(dd['max_drawdown_pct'])  # -13.64
    """
    if len(equity_curve) < 2:
        return {
            "max_drawdown": 0.0,
            "max_drawdown_pct": 0.0,
            "drawdown_duration": 0,
            "peak_value": equity_curve.iloc[0] if len(equity_curve) > 0 else 0.0,
            "valley_value": equity_curve.iloc[0] if len(equity_curve) > 0 else 0.0,
        }

    running_max = equity_curve.cummax()
    drawdowns = (equity_curve - running_max) / running_max

    max_dd = float(drawdowns.min())
    max_dd_idx = drawdowns.idxmin()

    # Find the peak before the max drawdown valley
    valley_loc = equity_curve.index.get_loc(max_dd_idx)
    peak_equity = running_max.iloc[valley_loc]
    valley_equity = equity_curve.iloc[valley_loc]

    # Calculate drawdown duration (peak to valley)
    peak_idx = equity_curve[: valley_loc + 1].idxmax()
    peak_loc = equity_curve.index.get_loc(peak_idx)
    duration = valley_loc - peak_loc

    return {
        "max_drawdown": max_dd,
        "max_drawdown_pct": max_dd * 100,
        "drawdown_duration": int(duration),
        "peak_value": float(peak_equity),
        "valley_value": float(valley_equity),
    }


def calculate_win_rate(trades: pd.DataFrame) -> float:
    """Calculate percentage of winning trades.

    Args:
        trades: DataFrame with 'net_pnl' column (profit/loss per trade).

    Returns:
        Win rate as decimal (e.g., 0.55 = 55%). Returns 0.0 if no trades.

    Example:
        >>> trades = pd.DataFrame({'net_pnl': [100, -50, 75, -25, 150]})
        >>> calculate_win_rate(trades)
        0.6
    """
    if trades.empty:
        return 0.0
    return float((trades["net_pnl"] > 0).sum() / len(trades))


def calculate_profit_factor(trades: pd.DataFrame) -> float:
    """Calculate profit factor (gross profit / gross loss).

    Args:
        trades: DataFrame with 'net_pnl' column.

    Returns:
        Profit factor (ratio). Returns 0.0 if no trades or all losing.
        Returns inf if all winning trades.

    Example:
        >>> trades = pd.DataFrame({'net_pnl': [100, -50, 75, -25]})
        >>> calculate_profit_factor(trades)
        2.33
    """
    if trades.empty:
        return 0.0

    gross_profit = trades.loc[trades["net_pnl"] > 0, "net_pnl"].sum()
    gross_loss = abs(trades.loc[trades["net_pnl"] < 0, "net_pnl"].sum())

    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0

    return float(gross_profit / gross_loss)


def calculate_total_return(
    initial_capital: float,
    final_capital: float,
) -> float:
    """Calculate total return percentage.

    Args:
        initial_capital: Starting portfolio value.
        final_capital: Ending portfolio value.

    Returns:
        Total return as percentage (e.g., 15.5 = 15.5%).

    Example:
        >>> calculate_total_return(10000, 11500)
        15.0
    """
    return ((final_capital - initial_capital) / initial_capital) * 100


def calculate_all_metrics(
    equity_curve: pd.Series,
    trades: pd.DataFrame,
    initial_capital: float,
    periods_per_year: int = 252,
) -> Dict[str, float]:
    """Calculate all performance metrics at once.

    Args:
        equity_curve: Series of portfolio values.
        trades: DataFrame of all trades.
        initial_capital: Starting capital.
        periods_per_year: For Sharpe ratio calculation.

    Returns:
        Dict with all metrics:
        - 'total_return_pct': Total return as percentage.
        - 'sharpe_ratio': Annualized Sharpe ratio.
        - 'max_drawdown_pct': Maximum drawdown as percentage.
        - 'win_rate': Fraction of winning trades.
        - 'profit_factor': Gross profit / gross loss.
        - 'num_trades': Total number of round-trip trades.
        - 'avg_trade_pnl': Average net P&L per trade.
        - 'final_capital': Final portfolio value.

    Example:
        >>> metrics = calculate_all_metrics(equity, trades, 10000, 252)
        >>> print(metrics['sharpe_ratio'])
    """
    final_capital = float(equity_curve.iloc[-1])
    returns = calculate_returns(equity_curve)
    dd_info = calculate_max_drawdown(equity_curve)

    avg_pnl = float(trades["net_pnl"].mean()) if not trades.empty else 0.0

    metrics = {
        "total_return_pct": calculate_total_return(initial_capital, final_capital),
        "sharpe_ratio": calculate_sharpe_ratio(
            returns, periods_per_year=periods_per_year
        ),
        "max_drawdown_pct": dd_info["max_drawdown_pct"],
        "win_rate": calculate_win_rate(trades),
        "profit_factor": calculate_profit_factor(trades),
        "num_trades": len(trades),
        "avg_trade_pnl": avg_pnl,
        "final_capital": final_capital,
    }

    logger.info(
        "Metrics calculated: return=%.2f%%, sharpe=%.2f, max_dd=%.2f%%, "
        "trades=%d, win_rate=%.1f%%",
        metrics["total_return_pct"],
        metrics["sharpe_ratio"],
        metrics["max_drawdown_pct"],
        metrics["num_trades"],
        metrics["win_rate"] * 100,
    )

    return metrics
