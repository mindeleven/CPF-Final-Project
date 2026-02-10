"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.backtest.transaction_costs
Purpose: Model realistic transaction costs for forex trading (spread + commission).

Provides a TransactionCosts class that calculates spread and commission costs
for each trade. EUR/USD defaults: 1 pip spread, 0% commission.

Example:
    from modules.backtest.transaction_costs import TransactionCosts

    costs = TransactionCosts(spread_pips=1.5, commission_pct=0.0)
    total = costs.calculate_total_cost(entry_price=1.1000, position_size=10000, direction=1)
"""

import logging

logger = logging.getLogger(__name__)


class TransactionCosts:
    """Transaction cost model for forex trading.

    Models spread and commission costs applied at both entry and exit
    of every trade. For EUR/USD, the spread is the primary cost component.

    Attributes:
        spread_pips: Bid-ask spread in pips.
        commission_pct: Commission as percentage of trade value.
        pip_value: Value of one pip (0.0001 for EUR/USD).

    Example:
        >>> costs = TransactionCosts(spread_pips=1.0)
        >>> costs.calculate_total_cost(1.1000, 10000, 1)
        1.0
    """

    def __init__(
        self,
        spread_pips: float = 1.0,
        commission_pct: float = 0.0,
        pip_value: float = 0.0001,
    ) -> None:
        """Initialize transaction cost model.

        Args:
            spread_pips: Bid-ask spread in pips (default: 1.0 for EUR/USD).
            commission_pct: Commission as percentage of trade value (default: 0.0).
            pip_value: Value of one pip (default: 0.0001 for EUR/USD).

        Example:
            costs = TransactionCosts(spread_pips=1.5, commission_pct=0.0)
        """
        self.spread_pips = spread_pips
        self.commission_pct = commission_pct
        self.pip_value = pip_value

        logger.info(
            "TransactionCosts initialized: spread=%.1f pips, commission=%.3f%%, "
            "pip_value=%.4f",
            self.spread_pips,
            self.commission_pct,
            self.pip_value,
        )

    def calculate_spread_cost(
        self,
        entry_price: float,
        position_size: float,
        direction: int,
    ) -> float:
        """Calculate spread cost for entering or exiting a position.

        Args:
            entry_price: Price at entry.
            position_size: Size of position (in base currency units).
            direction: 1 for LONG, -1 for SHORT.

        Returns:
            Spread cost in quote currency (USD for EUR/USD).

        Example:
            >>> costs = TransactionCosts(spread_pips=1.0)
            >>> costs.calculate_spread_cost(1.1000, 10000, 1)
            1.0
        """
        return self.spread_pips * self.pip_value * position_size

    def calculate_commission(
        self,
        entry_price: float,
        position_size: float,
    ) -> float:
        """Calculate commission for entering or exiting a position.

        Args:
            entry_price: Price at entry.
            position_size: Size of position (in base currency units).

        Returns:
            Commission in quote currency.

        Example:
            >>> costs = TransactionCosts(commission_pct=0.02)
            >>> costs.calculate_commission(1.1000, 10000)
            2.2
        """
        return entry_price * position_size * self.commission_pct / 100

    def calculate_total_cost(
        self,
        entry_price: float,
        position_size: float,
        direction: int,
    ) -> float:
        """Calculate total transaction cost (spread + commission).

        Args:
            entry_price: Price at entry.
            position_size: Size of position.
            direction: 1 for LONG, -1 for SHORT.

        Returns:
            Total cost in quote currency.

        Example:
            >>> costs = TransactionCosts(spread_pips=1.0, commission_pct=0.0)
            >>> costs.calculate_total_cost(1.1000, 10000, 1)
            1.0
        """
        spread = self.calculate_spread_cost(entry_price, position_size, direction)
        commission = self.calculate_commission(entry_price, position_size)
        return spread + commission
