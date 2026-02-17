"""
Live Trading Bot for EUR/USD Forex

Author: Juergen Kober + Claude Code Opus 4.6
Date: February 2026
Session: 7E

This bot implements the optimized MA+RSI+Momentum strategy from Session 6B
for live trading via Interactive Brokers API.

Key Features:
- Real-time 5-minute bar data via IB reqHistoricalData
- Historical warmup on startup (no 70+ minute wait)
- Automated signal generation using SMA crossover + RSI + Momentum filters
- Order execution via IB API (market orders with GTC TIF)
- Proper order fill waiting with timeout
- EUR balance verification before trading
- Trade and P&L logging (CSV + console + log file) in EUR and USD
- Time-based runtime management
- Weekend position closing
- Automatic reconnection with exponential backoff (handles IB Gateway reboots)
- Position state reconciliation after reconnection (prevents double position errors)
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from ib_async import IB, Forex, MarketOrder

# Add project root to path so we can import our modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from modules.indicators import SMA, RSI, Momentum

from config_live import (
    CHECK_FREQUENCY,
    CLOSE_BEFORE_WEEKEND,
    IB_CLIENT_ID,
    IB_HOST,
    IB_PORT,
    INITIAL_CAPITAL,
    MIN_EUR_BALANCE,
    MOMENTUM_PERIOD,
    MOMENTUM_THRESHOLD,
    POSITION_SIZE,
    RSI_LOWER,
    RSI_PERIOD,
    RSI_UPPER,
    RUN_DURATION,
    SMA_FAST,
    SMA_SLOW,
    TIMEFRAME,
    WEEKEND_CLOSE_TIME,
)


class LiveTradingBot:
    """Live trading bot for EUR/USD forex.

    Connects to IB Gateway, streams price data, generates signals using
    the MA+RSI+Momentum strategy with Session 6B optimized parameters,
    and executes trades automatically.

    Attributes:
        ib: IB API connection instance.
        contract: EUR/USD forex contract.
        position: Current position (1=LONG, -1=SHORT, 0=FLAT).
        entry_price: Entry price of current position.
        trades: List of completed trade records.
        start_time: Bot start timestamp.
        end_time: Bot stop timestamp (based on RUN_DURATION).
        initial_capital: Starting capital in EUR.
        current_capital: Current capital including realized P&L in EUR.
    """

    def __init__(self) -> None:
        """Initialize trading bot with configuration from config_live.py."""
        self.ib = IB()
        self.contract = Forex("EURUSD")

        # Position tracking
        self.position: int = 0  # 0=FLAT, 1=LONG, -1=SHORT
        self.entry_price: float = 0.0
        self.entry_time: Optional[datetime] = None

        # Trade logging
        self.trades: List[Dict] = []

        # Runtime management
        self.start_time = datetime.now()
        self.end_time = self._calculate_end_time()

        # Capital tracking (EUR-denominated)
        self.initial_capital = INITIAL_CAPITAL
        self.current_capital = self.initial_capital

        # Price history for indicator calculation
        self.price_history = pd.DataFrame(columns=["timestamp", "close"])

        # Bar tracking for deduplication
        self.last_bar_time: Optional[datetime] = None

        # Logging (set up before any log calls)
        self._setup_logging()
        self.trade_log_file = self._create_trade_log_file()

        self.logger.info(f"Trading Bot initialized for {TIMEFRAME} timeframe")
        self.logger.info(
            f"Parameters: SMA {SMA_FAST}/{SMA_SLOW}, "
            f"RSI {RSI_PERIOD} ({RSI_LOWER}/{RSI_UPPER}), "
            f"Momentum {MOMENTUM_PERIOD} (threshold {MOMENTUM_THRESHOLD})"
        )
        self.logger.info(f"Position size: {POSITION_SIZE:,} EUR")
        self.logger.info(f"Runtime: {RUN_DURATION}")
        self.logger.info(
            f"Bot will run until: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    # =========================================================================
    # Connection Management
    # =========================================================================

    def is_connected(self) -> bool:
        """Check if connection to IB Gateway is active.

        Returns:
            True if connected, False otherwise.
        """
        return self.ib.isConnected()

    async def connect(self) -> bool:
        """Connect to IB Gateway.

        Returns:
            True if connection successful, False otherwise.
        """
        try:
            await self.ib.connectAsync(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID)
            self.logger.info(f"Connected to IB Gateway at {IB_HOST}:{IB_PORT}")

            # Qualify contract to populate conId (required for data requests and orders)
            await self.ib.qualifyContractsAsync(self.contract)
            self.logger.info(
                f"Contract qualified: {self.contract.symbol} (conId: {self.contract.conId})"
            )

            self.logger.info("Connection monitoring active")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to IB Gateway: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from IB Gateway."""
        if self.ib.isConnected():
            self.ib.disconnect()
            self.logger.info("Disconnected from IB Gateway")

    async def reconnect(self, max_retries: int = 10) -> bool:
        """Attempt to reconnect to IB Gateway with exponential backoff.

        Handles IB Gateway midnight reboot (2-5 minute downtime).
        Uses exponential backoff to avoid overwhelming the server:
        Retry 1: 1s, Retry 2: 2s, Retry 3: 4s, ..., Retry 6+: 60s (max).
        Total time for 10 retries: ~5 minutes.

        Args:
            max_retries: Maximum number of reconnection attempts.

        Returns:
            True if reconnected successfully, False if all retries exhausted.
        """
        # Disconnect existing connection if any
        if self.ib.isConnected():
            self.ib.disconnect()
            await asyncio.sleep(1)

        for attempt in range(1, max_retries + 1):
            wait_time = min(2 ** (attempt - 1), 60)

            self.logger.info(
                f"Reconnection attempt {attempt}/{max_retries} "
                f"(waiting {wait_time}s before trying)..."
            )

            await asyncio.sleep(wait_time)

            try:
                await self.ib.connectAsync(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID)

                if self.ib.isConnected():
                    self.logger.info(f"Reconnected successfully on attempt {attempt}")
                    # Re-qualify contract (conId may be lost after reconnection)
                    await self.ib.qualifyContractsAsync(self.contract)
                    self.logger.info(
                        f"Contract re-qualified: {self.contract.symbol} (conId: {self.contract.conId})"
                    )
                    return True

            except Exception as e:
                self.logger.warning(f"Reconnection attempt {attempt} failed: {e}")

        self.logger.error(f"Failed to reconnect after {max_retries} attempts")
        return False

    async def reconcile_positions(self) -> None:
        """Reconcile bot position state with Interactive Brokers reality.

        Called after reconnection to ensure bot knows about:
        1. Positions that exist at IB (bot may think FLAT but IB has position)
        2. Positions closed at IB (bot may think LONG/SHORT but IB is FLAT)
        3. Position direction changes (rare but possible)

        Preserves our fill-based entry_price when it exists (more accurate
        than IB's avgCost for P&L calculation).

        Uses IB's positions() API to query actual account state.
        """
        try:
            self.logger.info("Reconciling position state with IB...")

            # positions() is synchronous — returns complete list immediately
            positions = self.ib.positions()

            # Find EUR/USD position
            eur_usd_position = None
            for pos in positions:
                if hasattr(pos.contract, "pair") and pos.contract.pair() == "EURUSD":
                    eur_usd_position = pos
                    break
                elif (
                    hasattr(pos.contract, "symbol")
                    and pos.contract.symbol == "EUR"
                    and hasattr(pos.contract, "currency")
                    and pos.contract.currency == "USD"
                ):
                    eur_usd_position = pos
                    break

            old_position = self.position
            old_entry = self.entry_price

            if eur_usd_position:
                ib_size = eur_usd_position.position
                ib_avg_cost = eur_usd_position.avgCost
                ib_entry = abs(ib_avg_cost / ib_size) if ib_size != 0 else 0.0

                if ib_size > 0:
                    self.position = 1
                    # Only update entry_price from IB if we don't have one
                    if self.entry_price == 0.0:
                        self.entry_price = ib_entry
                        self.logger.info(
                            f"Entry price set from IB: {self.entry_price:.5f}"
                        )
                    else:
                        self.logger.info(
                            f"Keeping fill-based entry price: {self.entry_price:.5f} "
                            f"(IB reports: {ib_entry:.5f})"
                        )
                    self.entry_time = self.entry_time or datetime.now()

                    if old_position != 1:
                        self.logger.warning("Position mismatch detected!")
                        self.logger.warning(
                            f"  Bot thought: {self._position_name(old_position)} "
                            f"@ {old_entry:.4f}"
                        )
                        self.logger.warning(
                            f"  IB shows: LONG {abs(ib_size):,.0f} "
                            f"@ {ib_entry:.4f}"
                        )
                        self.logger.info(
                            f"Updated bot state to match IB: "
                            f"LONG @ {self.entry_price:.4f}"
                        )
                    else:
                        self.logger.info(
                            f"Position confirmed: LONG @ {self.entry_price:.4f} "
                            f"(size: {abs(ib_size):,.0f})"
                        )

                elif ib_size < 0:
                    self.position = -1
                    # Only update entry_price from IB if we don't have one
                    if self.entry_price == 0.0:
                        self.entry_price = ib_entry
                        self.logger.info(
                            f"Entry price set from IB: {self.entry_price:.5f}"
                        )
                    else:
                        self.logger.info(
                            f"Keeping fill-based entry price: {self.entry_price:.5f} "
                            f"(IB reports: {ib_entry:.5f})"
                        )
                    self.entry_time = self.entry_time or datetime.now()

                    if old_position != -1:
                        self.logger.warning("Position mismatch detected!")
                        self.logger.warning(
                            f"  Bot thought: {self._position_name(old_position)} "
                            f"@ {old_entry:.4f}"
                        )
                        self.logger.warning(
                            f"  IB shows: SHORT {abs(ib_size):,.0f} "
                            f"@ {ib_entry:.4f}"
                        )
                        self.logger.info(
                            f"Updated bot state to match IB: "
                            f"SHORT @ {self.entry_price:.4f}"
                        )
                    else:
                        self.logger.info(
                            f"Position confirmed: SHORT @ {self.entry_price:.4f} "
                            f"(size: {abs(ib_size):,.0f})"
                        )
                else:
                    self.position = 0
                    self.entry_price = 0.0
                    self.entry_time = None
                    self.logger.warning(
                        "IB returned position object but size is 0. Setting FLAT."
                    )
                    if old_position != 0:
                        self._record_reconcile_close(old_position, old_entry)
            else:
                if old_position != 0:
                    self.logger.warning("Position mismatch detected!")
                    self.logger.warning(
                        f"  Bot thought: {self._position_name(old_position)} "
                        f"@ {old_entry:.4f}"
                    )
                    self.logger.warning("  IB shows: FLAT (no position)")
                    self.logger.info("Updated bot state to match IB: FLAT")
                    self._record_reconcile_close(old_position, old_entry)
                else:
                    self.logger.info("Position confirmed: FLAT (no open positions)")

                self.position = 0
                self.entry_price = 0.0
                self.entry_time = None

            self.logger.info(
                f"Reconciliation complete. Current state: "
                f"{self._position_name(self.position)}"
            )

        except Exception as e:
            self.logger.error(f"Error during position reconciliation: {e}")
            self.logger.error("Continuing with current bot state (not updating)")

    def _position_name(self, position: int) -> str:
        """Convert position integer to readable name.

        Args:
            position: 1 (LONG), -1 (SHORT), 0 (FLAT).

        Returns:
            Human-readable position name.
        """
        if position == 1:
            return "LONG"
        elif position == -1:
            return "SHORT"
        return "FLAT"

    def _record_reconcile_close(
        self, old_position: int, old_entry: float
    ) -> None:
        """Record estimated P&L when a position vanishes during reconciliation.

        Uses the last known price from price_history as the exit price.
        Marks the trade direction with '(IB reconcile)' to distinguish
        it from bot-initiated closes.

        Args:
            old_position: The position the bot thought it had (1 or -1).
            old_entry: The entry price of the vanished position.
        """
        if len(self.price_history) > 0:
            exit_price = float(self.price_history["close"].iloc[-1])
        else:
            exit_price = old_entry  # fallback: P&L = 0

        gross_pnl = old_position * (exit_price - old_entry) * POSITION_SIZE
        spread_cost = 2 * 0.0001 * POSITION_SIZE
        net_pnl = gross_pnl - spread_cost
        net_pnl_eur = net_pnl / exit_price if exit_price > 0 else net_pnl
        self.current_capital += net_pnl_eur

        direction_name = self._position_name(old_position)
        trade_record = {
            "entry_time": self.entry_time,
            "exit_time": datetime.now(),
            "direction": f"{direction_name} (IB reconcile)",
            "entry_price": old_entry,
            "exit_price": exit_price,
            "size": POSITION_SIZE,
            "gross_pnl": gross_pnl,
            "costs": spread_cost,
            "net_pnl": net_pnl,
            "net_pnl_eur": net_pnl_eur,
            "capital_eur": self.current_capital,
        }
        self.trades.append(trade_record)
        self._save_trade(trade_record)

        self.logger.warning(
            f"Position closed by IB (reboot/reset). "
            f"Estimated exit: {exit_price:.5f}, "
            f"P&L: EUR {net_pnl_eur:.2f} (USD {net_pnl:.2f})"
        )

    # =========================================================================
    # Account Balance
    # =========================================================================

    async def check_eur_balance(
        self, min_balance: float = MIN_EUR_BALANCE
    ) -> Tuple[bool, float]:
        """Check if account has sufficient EUR balance for trading.

        Queries IB accountSummary for TotalCashBalance in EUR.

        Args:
            min_balance: Minimum required EUR balance.

        Returns:
            Tuple of (has_sufficient_balance, eur_balance).
        """
        try:
            self.logger.info("Checking EUR balance...")

            account_values = await self.ib.accountSummaryAsync()

            eur_balance = None
            for item in account_values:
                if item.tag == "TotalCashBalance" and item.currency == "EUR":
                    eur_balance = float(item.value)
                    break
                elif item.tag == "CashBalance" and item.currency == "EUR":
                    eur_balance = float(item.value)

            if eur_balance is None:
                self.logger.warning("Could not determine EUR balance")
                return False, 0.0

            has_sufficient = eur_balance >= min_balance

            self.logger.info(f"EUR balance: {eur_balance:,.2f} EUR")
            self.logger.info(f"Required minimum: {min_balance:,.2f} EUR")
            self.logger.info(
                f"Status: {'Sufficient' if has_sufficient else 'INSUFFICIENT'}"
            )

            return has_sufficient, eur_balance

        except Exception as e:
            self.logger.error(f"Error checking EUR balance: {e}")
            return False, 0.0

    # =========================================================================
    # Data Streaming
    # =========================================================================

    async def load_historical_warmup(self) -> None:
        """Load historical 5-minute bars for indicator warmup.

        Fetches enough bars from IB so that indicators can produce
        signals immediately, eliminating the 70+ minute cold-start wait.
        """
        bars_needed = max(SMA_SLOW, RSI_PERIOD + 1, MOMENTUM_PERIOD + 1) + 10
        # Convert bars to duration string (bars * 5 minutes, in seconds)
        duration_seconds = bars_needed * 5 * 60
        duration_str = f"{duration_seconds} S"

        self.logger.info(
            f"Loading {bars_needed} historical 5-min bars for warmup..."
        )

        try:
            bars = await self.ib.reqHistoricalDataAsync(
                self.contract,
                endDateTime="",
                durationStr=duration_str,
                barSizeSetting="5 mins",
                whatToShow="MIDPOINT",
                useRTH=False,
                formatDate=1,
            )

            if not bars:
                self.logger.warning("No historical bars returned for warmup")
                return

            # Populate price_history from bars
            rows = []
            for bar in bars:
                rows.append({"timestamp": bar.date, "close": bar.close})

            self.price_history = pd.DataFrame(rows)

            # Track last bar time for deduplication
            if bars:
                self.last_bar_time = bars[-1].date

            self.logger.info(
                f"Warmup complete: loaded {len(self.price_history)} bars "
                f"(need {SMA_SLOW + 10} for signals)"
            )

        except Exception as e:
            self.logger.error(f"Error loading historical warmup: {e}")
            self.logger.info("Will collect bars in real-time (slower startup)")

    async def fetch_latest_bar(self) -> Optional[Dict]:
        """Fetch the latest completed 5-minute bar via reqHistoricalData.

        Returns:
            Dict with {date, open, high, low, close}, or None if fetch fails.
        """
        try:
            bars = await self.ib.reqHistoricalDataAsync(
                self.contract,
                endDateTime="",
                durationStr="300 S",
                barSizeSetting="5 mins",
                whatToShow="MIDPOINT",
                useRTH=False,
                formatDate=1,
            )

            if not bars:
                self.logger.warning("No bar data returned")
                return None

            latest = bars[-1]
            return {
                "date": latest.date,
                "open": latest.open,
                "high": latest.high,
                "low": latest.low,
                "close": latest.close,
            }

        except Exception as e:
            self.logger.error(f"Error fetching bar: {e}")
            return None

    def update_price_history(self, bar: Dict) -> None:
        """Add new bar to price history for indicator calculation.

        Keeps only the most recent bars needed for the slowest indicator
        plus a buffer.

        Args:
            bar: Dict with 'date' and 'close' keys from fetch_latest_bar().
        """
        new_row = pd.DataFrame(
            {"timestamp": [bar["date"]], "close": [bar["close"]]}
        )
        self.price_history = pd.concat(
            [self.price_history, new_row], ignore_index=True
        )

        # Keep only necessary history (max indicator period + buffer)
        max_period = max(SMA_SLOW, RSI_PERIOD, MOMENTUM_PERIOD) + 50
        if len(self.price_history) > max_period:
            self.price_history = self.price_history.tail(max_period).reset_index(
                drop=True
            )

    # =========================================================================
    # Signal Generation
    # =========================================================================

    def calculate_indicators(self) -> Optional[Dict[str, pd.Series]]:
        """Calculate technical indicators on price history.

        Returns:
            Dict with indicator series keyed by name, or None if
            insufficient data for the slowest indicator.
        """
        min_required = SMA_SLOW + 10
        if len(self.price_history) < min_required:
            return None

        try:
            sma_fast_ind = SMA(period=SMA_FAST)
            sma_slow_ind = SMA(period=SMA_SLOW)
            rsi_ind = RSI(period=RSI_PERIOD)
            momentum_ind = Momentum(period=MOMENTUM_PERIOD)

            # Indicators expect a DataFrame with a 'close' column
            df = self.price_history[["close"]].copy()

            return {
                "sma_fast": sma_fast_ind.calculate(df),
                "sma_slow": sma_slow_ind.calculate(df),
                "rsi": rsi_ind.calculate(df),
                "momentum": momentum_ind.calculate(df),
            }
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return None

    def generate_signal(self, indicators: Dict[str, pd.Series]) -> int:
        """Generate trading signal based on latest indicator values.

        Implements the same crossover + filter logic as MARSIMomentumStrategy:
        - BUY: fast SMA crosses above slow SMA, RSI < upper, momentum > threshold
        - SELL: fast SMA crosses below slow SMA, RSI > lower, momentum < -threshold

        Args:
            indicators: Dict of indicator pd.Series.

        Returns:
            1 for BUY, -1 for SELL, 0 for HOLD.
        """
        sma_fast = indicators["sma_fast"].iloc[-1]
        sma_slow = indicators["sma_slow"].iloc[-1]
        sma_fast_prev = indicators["sma_fast"].iloc[-2]
        sma_slow_prev = indicators["sma_slow"].iloc[-2]
        rsi = indicators["rsi"].iloc[-1]
        momentum = indicators["momentum"].iloc[-1]

        # Bail out if any value is NaN
        if any(
            pd.isna(v)
            for v in [sma_fast, sma_slow, sma_fast_prev, sma_slow_prev, rsi, momentum]
        ):
            return 0

        # BUY Signal: SMA crossover UP + RSI filter + Momentum filter
        if (
            sma_fast_prev <= sma_slow_prev
            and sma_fast > sma_slow
            and rsi < RSI_UPPER
            and momentum > MOMENTUM_THRESHOLD
        ):
            self.logger.info(
                f"BUY Signal: SMA {sma_fast:.5f} crossed above {sma_slow:.5f}, "
                f"RSI {rsi:.1f}, Momentum {momentum:.6f}"
            )
            return 1

        # SELL Signal: SMA crossover DOWN + RSI filter + Momentum filter
        if (
            sma_fast_prev >= sma_slow_prev
            and sma_fast < sma_slow
            and rsi > RSI_LOWER
            and momentum < -MOMENTUM_THRESHOLD
        ):
            self.logger.info(
                f"SELL Signal: SMA {sma_fast:.5f} crossed below {sma_slow:.5f}, "
                f"RSI {rsi:.1f}, Momentum {momentum:.6f}"
            )
            return -1

        return 0  # HOLD

    # =========================================================================
    # Order Execution
    # =========================================================================

    async def execute_order(self, signal: int, price: float) -> None:
        """Execute order based on signal.

        Closes existing position if signal is opposite (with fill confirmation),
        then opens new position. Includes EUR balance check.

        Args:
            signal: 1 for BUY, -1 for SELL.
            price: Current market price for logging.
        """
        # Balance check before trading
        has_balance, _ = await self.check_eur_balance()
        if not has_balance:
            self.logger.warning(
                "Insufficient EUR balance. Skipping trade."
            )
            return

        # Close existing position if signal is opposite
        if self.position != 0 and signal != self.position:
            close_success = await self.close_position(price)

            if not close_success:
                self.logger.error(
                    "Close position failed. Aborting new position open."
                )
                return

            # Settlement delay between close and open
            await asyncio.sleep(1)

            # Verify close completed
            if self.position != 0:
                self.logger.error(
                    f"Position still {self._position_name(self.position)} after close. "
                    f"Aborting new position open."
                )
                return

        # Open new position if now FLAT
        if self.position == 0 and signal != 0:
            await self.open_position(signal, price)

    async def open_position(self, direction: int, price: float) -> None:
        """Open new position via IB market order.

        Uses GTC TIF and waits for fill confirmation with timeout.
        Sets entry_price from actual fill price.

        Args:
            direction: 1 for LONG, -1 for SHORT.
            price: Current price for logging (actual fill may differ).
        """
        try:
            action = "BUY" if direction == 1 else "SELL"
            order = MarketOrder(action, POSITION_SIZE)
            order.tif = "GTC"

            trade = self.ib.placeOrder(self.contract, order)

            # Wait for fill with timeout
            timeout = 30
            elapsed = 0.0
            while not trade.isDone() and elapsed < timeout:
                await asyncio.sleep(0.5)
                elapsed += 0.5

            if trade.isDone() and trade.orderStatus.status == "Filled":
                fill_price = trade.orderStatus.avgFillPrice or price
                self.position = direction
                self.entry_price = fill_price
                self.entry_time = datetime.now()

                slippage_pips = abs(fill_price - price) * 10000

                self.logger.info(
                    f"OPENED: {action} {POSITION_SIZE:,} EUR @ {fill_price:.5f} "
                    f"(slippage: {slippage_pips:.1f} pips)"
                )
                self.logger.info(f"Entry price recorded: {fill_price:.5f}")
            else:
                self.logger.error(
                    f"Order not filled within {timeout}s. "
                    f"Status: {trade.orderStatus.status}. "
                    f"NOT updating position state."
                )

        except Exception as e:
            self.logger.error(f"Error executing open order: {e}")

    async def close_position(self, price: float) -> bool:
        """Close current position and log the completed trade.

        Uses GTC TIF and waits for fill confirmation with timeout.
        Only resets position state after confirmed fill.

        Args:
            price: Current price for logging (actual fill may differ).

        Returns:
            True if position was closed successfully, False otherwise.
        """
        if self.position == 0:
            return True

        try:
            action = "SELL" if self.position == 1 else "BUY"
            order = MarketOrder(action, POSITION_SIZE)
            order.tif = "GTC"

            trade = self.ib.placeOrder(self.contract, order)

            # Wait for fill with timeout
            timeout = 30
            elapsed = 0.0
            while not trade.isDone() and elapsed < timeout:
                await asyncio.sleep(0.5)
                elapsed += 0.5

            if not trade.isDone():
                self.logger.error(
                    f"Close order not filled within {timeout}s. "
                    f"Status: {trade.orderStatus.status}"
                )
                return False

            fill_price = trade.orderStatus.avgFillPrice or price

            # Calculate P&L in USD
            gross_pnl = self.position * (fill_price - self.entry_price) * POSITION_SIZE
            # Transaction costs: 1 pip spread at entry + exit
            spread_cost = 2 * 0.0001 * POSITION_SIZE
            net_pnl = gross_pnl - spread_cost

            # Convert to EUR using fill price
            net_pnl_eur = net_pnl / fill_price if fill_price > 0 else net_pnl
            gross_pnl_eur = gross_pnl / fill_price if fill_price > 0 else gross_pnl

            # Update capital (EUR-denominated)
            self.current_capital += net_pnl_eur

            # Record trade
            trade_record = {
                "entry_time": self.entry_time,
                "exit_time": datetime.now(),
                "direction": "LONG" if self.position == 1 else "SHORT",
                "entry_price": self.entry_price,
                "exit_price": fill_price,
                "size": POSITION_SIZE,
                "gross_pnl": gross_pnl,
                "costs": spread_cost,
                "net_pnl": net_pnl,
                "net_pnl_eur": net_pnl_eur,
                "capital_eur": self.current_capital,
            }
            self.trades.append(trade_record)
            self._save_trade(trade_record)

            self.logger.info(
                f"CLOSED: {action} {POSITION_SIZE:,} EUR @ {fill_price:.5f}"
            )
            self.logger.info(
                f"P&L: EUR {net_pnl_eur:.2f} (USD {net_pnl:.2f}) | "
                f"Gross: EUR {gross_pnl_eur:.2f} (USD {gross_pnl:.2f}), "
                f"Costs: USD {spread_cost:.2f}"
            )
            self.logger.info(
                f"Cumulative P&L: EUR {self.current_capital - self.initial_capital:.2f}"
            )

            # Reset position only after confirmed fill
            self.position = 0
            self.entry_price = 0.0
            self.entry_time = None

            return True

        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return False

    # =========================================================================
    # Runtime Management
    # =========================================================================

    def should_continue_running(self) -> bool:
        """Check if bot should continue running.

        Returns:
            True if should continue, False if runtime expired or weekend.
        """
        now = datetime.now()

        if now >= self.end_time:
            self.logger.info(f"Runtime expired ({RUN_DURATION}). Stopping.")
            return False

        if CLOSE_BEFORE_WEEKEND and self._is_approaching_weekend():
            self.logger.info("Approaching weekend. Stopping.")
            return False

        return True

    def _is_approaching_weekend(self) -> bool:
        """Check if it's Friday at or past the configured close time.

        Returns:
            True if should close for weekend.
        """
        now = datetime.now()
        if now.weekday() != 4:  # 0=Monday, 4=Friday
            return False

        hour, minute = map(int, WEEKEND_CLOSE_TIME.split(":"))
        close_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return now >= close_time

    def _is_forex_open(self) -> bool:
        """Check if forex market is likely open.

        Forex trades Sunday ~5pm EST through Friday ~5pm EST.
        This is an approximate check using local time.

        Returns:
            True if market is likely open.
        """
        now = datetime.now()
        weekday = now.weekday()  # 0=Monday, 6=Sunday

        # Closed all Saturday
        if weekday == 5:
            return False

        # Most of Sunday is closed (opens ~5pm EST)
        if weekday == 6:
            return now.hour >= 17

        # Friday closes ~5pm EST
        if weekday == 4:
            return now.hour < 17

        # Monday through Thursday: open
        return True

    def _calculate_end_time(self) -> datetime:
        """Calculate when bot should stop based on RUN_DURATION config.

        Parses duration strings like "1h", "8h", "5d", "30m".

        Returns:
            End datetime.
        """
        duration = RUN_DURATION.strip().lower()

        if duration.endswith("h"):
            hours = int(duration[:-1].strip())
            return self.start_time + timedelta(hours=hours)
        elif duration.endswith("d"):
            days = int(duration[:-1].strip())
            return self.start_time + timedelta(days=days)
        elif duration.endswith("m"):
            minutes = int(duration[:-1].strip())
            return self.start_time + timedelta(minutes=minutes)
        else:
            # Default: 8 hours
            self._log_warning_if_ready(
                f"Unrecognized RUN_DURATION '{RUN_DURATION}', defaulting to 8h"
            )
            return self.start_time + timedelta(hours=8)

    def _log_warning_if_ready(self, msg: str) -> None:
        """Log a warning if logger is set up, otherwise print."""
        if hasattr(self, "logger"):
            self.logger.warning(msg)
        else:
            print(f"WARNING: {msg}")

    # =========================================================================
    # Main Loop
    # =========================================================================

    async def run(self) -> None:
        """Main trading loop with reconnection handling.

        Connects to IB Gateway, checks EUR balance, loads historical
        warmup data, then loops: fetch bar, check for new bar, calculate
        indicators, generate signal, execute trades. Monitors connection
        health and reconnects automatically if IB Gateway reboots.
        Stops when runtime expires, weekend approaches, or an unrecoverable
        error occurs.
        """
        if not await self.connect():
            self.logger.error("Failed to connect. Exiting.")
            return

        try:
            self.logger.info("Trading bot started")

            # EUR balance check — abort if insufficient
            has_balance, eur_balance = await self.check_eur_balance()
            if not has_balance:
                self.logger.error(
                    f"Insufficient EUR balance ({eur_balance:,.2f} EUR). "
                    f"Need at least {MIN_EUR_BALANCE:,.2f} EUR. Aborting."
                )
                return

            # Set initial capital from actual EUR balance
            self.initial_capital = eur_balance
            self.current_capital = eur_balance
            self.logger.info(
                f"Capital set from account: {eur_balance:,.2f} EUR"
            )

            await self.reconcile_positions()

            # Historical warmup — load bars so indicators work immediately
            await self.load_historical_warmup()

            self.logger.info(f"Checking for new bars every {CHECK_FREQUENCY} seconds")
            self.logger.info(
                "Connection monitoring enabled (handles IB Gateway reboots)"
            )

            iteration = 0

            while self.should_continue_running():
                iteration += 1

                # Connection health check
                if not self.is_connected():
                    self.logger.warning("Connection lost detected!")
                    self.logger.info("Attempting automatic reconnection...")

                    if self.position != 0:
                        self.logger.warning(
                            "Open position exists but connection lost. "
                            "Cannot close safely. Will retry after reconnect."
                        )

                    if not await self.reconnect(max_retries=10):
                        self.logger.error("Reconnection failed. Shutting down.")
                        break

                    self.logger.info("Reconnected successfully.")
                    await self.reconcile_positions()
                    self.logger.info("Position state verified. Resuming trading.")
                    await asyncio.sleep(5)
                    continue

                # Check if market is open
                if not self._is_forex_open():
                    self.logger.info("Market closed. Waiting...")
                    await asyncio.sleep(CHECK_FREQUENCY)
                    continue

                # Fetch latest 5-minute bar
                bar = await self.fetch_latest_bar()
                if bar is None:
                    await asyncio.sleep(CHECK_FREQUENCY)
                    continue

                # Only process new bars (deduplication)
                if self.last_bar_time is not None and bar["date"] == self.last_bar_time:
                    # Same bar — heartbeat every 5 checks
                    if iteration % 5 == 0:
                        self.logger.info(
                            f"Waiting for new bar... "
                            f"(last: {self.last_bar_time}, price: {bar['close']:.5f})"
                        )
                    await asyncio.sleep(CHECK_FREQUENCY)
                    continue

                # New bar arrived
                self.last_bar_time = bar["date"]
                price = bar["close"]
                self.logger.info(
                    f"New bar: {bar['date']} | "
                    f"O={bar['open']:.5f} H={bar['high']:.5f} "
                    f"L={bar['low']:.5f} C={price:.5f}"
                )

                # Update price history
                self.update_price_history(bar)

                # Status update every 10 new bars
                if iteration % 10 == 0:
                    remaining = self.end_time - datetime.now()
                    hours_left = remaining.total_seconds() / 3600
                    pos_str = self._position_name(self.position)

                    unrealized_pnl = ""
                    if self.position != 0 and self.entry_price > 0:
                        upl = self.position * (price - self.entry_price) * POSITION_SIZE
                        upl_eur = upl / price if price > 0 else upl
                        unrealized_pnl = f", Unrealized: EUR {upl_eur:.2f}"

                    self.logger.info(
                        f"Status: Price={price:.5f}, Position={pos_str}, "
                        f"Bars={len(self.price_history)}, "
                        f"P&L=EUR {self.current_capital - self.initial_capital:.2f}"
                        f"{unrealized_pnl}, "
                        f"Remaining={hours_left:.1f}h"
                    )

                # Calculate indicators and generate signal
                indicators = self.calculate_indicators()
                if indicators is not None:
                    signal = self.generate_signal(indicators)
                    if signal != 0:
                        await self.execute_order(signal, price)

                await asyncio.sleep(CHECK_FREQUENCY)

            # Close any open position before shutdown
            if self.position != 0:
                self.logger.info("Closing open position before shutdown...")
                bar = await self.fetch_latest_bar()
                if bar is not None:
                    await self.close_position(bar["close"])

            self._print_summary()

        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            await self.disconnect()

    # =========================================================================
    # Logging and File Management
    # =========================================================================

    def _setup_logging(self) -> None:
        """Set up logging to both file and console."""
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        log_dir = Path(__file__).resolve().parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"trading_bot_{TIMEFRAME}_{RUN_DURATION}_{timestamp}.log"

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def _create_trade_log_file(self) -> Path:
        """Create CSV file for trade logging with header row.

        Returns:
            Path to the trade log CSV file.
        """
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        log_dir = Path(__file__).resolve().parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"trades_{TIMEFRAME}_{RUN_DURATION}_{timestamp}.csv"

        with open(log_file, "w") as f:
            f.write(
                "entry_time,exit_time,direction,entry_price,exit_price,"
                "size,gross_pnl,costs,net_pnl,net_pnl_eur,capital_eur\n"
            )

        return log_file

    def _save_trade(self, trade: Dict) -> None:
        """Append a completed trade record to the CSV log.

        Args:
            trade: Dict with trade details.
        """
        with open(self.trade_log_file, "a") as f:
            f.write(
                f"{trade['entry_time']},{trade['exit_time']},"
                f"{trade['direction']},"
                f"{trade['entry_price']:.5f},{trade['exit_price']:.5f},"
                f"{trade['size']},"
                f"{trade['gross_pnl']:.2f},{trade['costs']:.2f},"
                f"{trade['net_pnl']:.2f},{trade['net_pnl_eur']:.2f},"
                f"{trade['capital_eur']:.2f}\n"
            )

    def _print_summary(self) -> None:
        """Print and save final trading session summary."""
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("TRADING SESSION SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"Timeframe: {TIMEFRAME}")
        self.logger.info(
            f"Parameters: SMA {SMA_FAST}/{SMA_SLOW}, "
            f"RSI {RSI_LOWER}/{RSI_UPPER}, Mom {MOMENTUM_THRESHOLD}"
        )
        self.logger.info(f"Duration: {datetime.now() - self.start_time}")
        self.logger.info(f"Total Bars Collected: {len(self.price_history)}")
        self.logger.info(f"Total Trades: {len(self.trades)}")

        winning_trades: List[float] = []
        losing_trades: List[float] = []
        total_return = 0.0

        if self.trades:
            net_pnls_eur = [t["net_pnl_eur"] for t in self.trades]
            winning_trades = [p for p in net_pnls_eur if p > 0]
            losing_trades = [p for p in net_pnls_eur if p < 0]

            self.logger.info(f"Winning Trades: {len(winning_trades)}")
            self.logger.info(f"Losing Trades: {len(losing_trades)}")
            self.logger.info(
                f"Win Rate: {len(winning_trades) / len(self.trades) * 100:.1f}%"
            )
            self.logger.info(f"Total P&L: EUR {sum(net_pnls_eur):.2f}")
            self.logger.info(f"Avg Trade: EUR {np.mean(net_pnls_eur):.2f}")
            self.logger.info(f"Best Trade: EUR {max(net_pnls_eur):.2f}")
            self.logger.info(f"Worst Trade: EUR {min(net_pnls_eur):.2f}")

        self.logger.info(f"Final Capital: EUR {self.current_capital:,.2f}")
        if self.initial_capital > 0:
            total_return = (self.current_capital / self.initial_capital - 1) * 100
        self.logger.info(f"Return: {total_return:.2f}%")
        self.logger.info("=" * 70)

        # Save summary to text file
        summary_file = self.trade_log_file.with_name(
            self.trade_log_file.stem + "_summary.txt"
        )
        with open(summary_file, "w") as f:
            f.write("Trading Session Summary\n")
            f.write(f"Timeframe: {TIMEFRAME}\n")
            f.write(
                f"Parameters: SMA {SMA_FAST}/{SMA_SLOW}, "
                f"RSI {RSI_LOWER}/{RSI_UPPER}, Mom {MOMENTUM_THRESHOLD}\n"
            )
            f.write(f"Duration: {datetime.now() - self.start_time}\n")
            f.write(f"Total Trades: {len(self.trades)}\n")
            if self.trades:
                net_pnls_eur = [t["net_pnl_eur"] for t in self.trades]
                f.write(
                    f"Win Rate: "
                    f"{len(winning_trades) / len(self.trades) * 100:.1f}%\n"
                )
                f.write(f"Total P&L: EUR {sum(net_pnls_eur):.2f}\n")
            f.write(f"Final Capital: EUR {self.current_capital:,.2f}\n")
            f.write(f"Return: {total_return:.2f}%\n")


async def main() -> None:
    """Entry point for the live trading bot."""
    bot = LiveTradingBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
