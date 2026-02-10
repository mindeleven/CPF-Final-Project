
---

# **Specification 5: Backtesting Engine Module**

**Project:** CPF Final Project - Automated Trading System  
**Module:** `modules/backtest/`  
**Session:** 5  
**Date:** February 10, 2026  
**Prerequisites:** Session 1 (Config) ✅, Session 2 (Data) ✅, Session 3 (Indicators) ✅, Session 4 (Strategy) ✅

---

## **📋 Overview**

Implement a backtesting engine that:
1. Processes strategy signals bar-by-bar
2. Tracks positions and calculates P&L
3. Applies realistic transaction costs (spread + commission)
4. Computes performance metrics (Sharpe ratio, max drawdown, win rate, etc.)
5. Generates detailed trade logs for analysis

**Key Principle:** The backtest simulates realistic trading conditions including:
- Entry/exit at next bar's open price (no look-ahead bias)
- Spread costs on every trade
- Commission costs on every trade
- Position sizing (fixed size for this project)

---

## **🎯 Success Criteria**

- ✅ BacktestEngine processes signals correctly
- ✅ P&L calculations verified against manual calculations
- ✅ Transaction costs applied realistically
- ✅ All performance metrics calculated correctly
- ✅ Trade log tracks every entry/exit
- ✅ Works with all three timeframes
- ✅ Type hints and Google docstrings throughout
- ✅ PEP 8 compliant, file headers present

---

## **📁 Files to Create**

```
modules/backtest/
├── __init__.py              # Clean exports
├── engine.py                # Main backtesting engine
├── transaction_costs.py     # Spread and commission modeling
└── metrics.py               # Performance metrics calculations
```

---

## **1️⃣ FILE: modules/backtest/transaction_costs.py**

### **Purpose**
Model realistic transaction costs for forex trading (spread + commission).

### **Class: `TransactionCosts`**

**Constructor:**
```python
def __init__(
    self,
    spread_pips: float = 1.0,
    commission_pct: float = 0.0,
    pip_value: float = 0.0001
) -> None:
    """
    Initialize transaction cost model.
    
    Args:
        spread_pips: Bid-ask spread in pips (default: 1.0 for EUR/USD)
        commission_pct: Commission as percentage of trade value (default: 0.0)
        pip_value: Value of one pip (default: 0.0001 for EUR/USD)
    
    Notes:
        - EUR/USD typical retail spread: 1-2 pips
        - Commission: usually 0% for retail forex (spread is main cost)
        - Pip value: 0.0001 for EUR/USD (4th decimal place)
    
    Example:
        costs = TransactionCosts(spread_pips=1.5, commission_pct=0.0)
    """
```

**Methods:**

**1. Calculate Spread Cost:**
```python
def calculate_spread_cost(
    self,
    entry_price: float,
    position_size: float,
    direction: int
) -> float:
    """
    Calculate spread cost for entering a position.
    
    Args:
        entry_price: Price at entry
        position_size: Size of position (in base currency units)
        direction: 1 for LONG, -1 for SHORT
    
    Returns:
        Spread cost in quote currency (USD for EUR/USD)
    
    Formula:
        spread_cost = spread_pips * pip_value * position_size
    
    Notes:
        - Spread is paid on EVERY trade (entry and exit)
        - Direction doesn't affect spread cost (always positive cost)
        - For EUR/USD: spread_cost = 1.0 * 0.0001 * 10000 = $1.00
    
    Example:
        >>> costs = TransactionCosts(spread_pips=1.0)
        >>> cost = costs.calculate_spread_cost(1.1000, 10000, 1)
        >>> print(cost)  # 1.0 USD
    """
```

**2. Calculate Commission:**
```python
def calculate_commission(
    self,
    entry_price: float,
    position_size: float
) -> float:
    """
    Calculate commission for entering a position.
    
    Args:
        entry_price: Price at entry
        position_size: Size of position (in base currency units)
    
    Returns:
        Commission in quote currency
    
    Formula:
        commission = entry_price * position_size * commission_pct / 100
    
    Notes:
        - Most retail forex brokers charge 0% commission (spread only)
        - Some brokers charge small commission (0.01-0.05%)
        - Commission typically same for entry and exit
    
    Example:
        >>> costs = TransactionCosts(commission_pct=0.02)
        >>> comm = costs.calculate_commission(1.1000, 10000)
        >>> print(comm)  # 2.20 USD (1.1 * 10000 * 0.02 / 100)
    """
```

**3. Total Transaction Cost:**
```python
def calculate_total_cost(
    self,
    entry_price: float,
    position_size: float,
    direction: int
) -> float:
    """
    Calculate total transaction cost (spread + commission).
    
    Args:
        entry_price: Price at entry
        position_size: Size of position
        direction: 1 for LONG, -1 for SHORT
    
    Returns:
        Total cost in quote currency
    
    Example:
        >>> costs = TransactionCosts(spread_pips=1.0, commission_pct=0.0)
        >>> total = costs.calculate_total_cost(1.1000, 10000, 1)
        >>> print(total)  # 1.0 USD (spread only)
    """
```

---

## **2️⃣ FILE: modules/backtest/metrics.py**

### **Purpose**
Calculate performance metrics for backtested strategies.

### **Functions (Pure Functions, Not a Class)**

**1. Calculate Returns:**
```python
def calculate_returns(equity_curve: pd.Series) -> pd.Series:
    """
    Calculate percentage returns from equity curve.
    
    Args:
        equity_curve: Series of portfolio values over time
    
    Returns:
        Series of percentage returns
    
    Formula:
        return_t = (equity_t - equity_{t-1}) / equity_{t-1}
    
    Example:
        >>> equity = pd.Series([10000, 10100, 10050, 10200])
        >>> returns = calculate_returns(equity)
        >>> print(returns)
        # [NaN, 0.01, -0.00495, 0.01493]
    """
```

**2. Sharpe Ratio:**
```python
def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """
    Calculate annualized Sharpe ratio.
    
    Args:
        returns: Series of period returns
        risk_free_rate: Annual risk-free rate (default: 0.0)
        periods_per_year: Number of periods in a year
            - 252 for daily (trading days)
            - 2080 for 4H (6 bars/day * 5 days * 52 weeks)
            - 72000 for 5min (288 bars/day * 250 trading days)
    
    Returns:
        Annualized Sharpe ratio
    
    Formula:
        sharpe = (mean_return - risk_free_rate) / std_return * sqrt(periods_per_year)
    
    Notes:
        - Higher is better (>1.0 is good, >2.0 is excellent)
        - Measures risk-adjusted return
        - Assumes returns are normally distributed
    
    Example:
        >>> returns = pd.Series([0.01, -0.005, 0.015, 0.002])
        >>> sharpe = calculate_sharpe_ratio(returns, periods_per_year=252)
    """
```

**3. Maximum Drawdown:**
```python
def calculate_max_drawdown(equity_curve: pd.Series) -> Dict[str, float]:
    """
    Calculate maximum drawdown and related metrics.
    
    Args:
        equity_curve: Series of portfolio values
    
    Returns:
        Dict with keys:
        - 'max_drawdown': Maximum drawdown as decimal (e.g., -0.15 = -15%)
        - 'max_drawdown_pct': Maximum drawdown as percentage (e.g., -15.0)
        - 'drawdown_duration': Number of periods in drawdown
        - 'peak_value': Equity at peak before max drawdown
        - 'valley_value': Equity at bottom of max drawdown
    
    Formula:
        drawdown_t = (equity_t - peak_equity_t) / peak_equity_t
        max_drawdown = min(all drawdowns)
    
    Notes:
        - Always negative or zero
        - Lower magnitude is better (e.g., -10% better than -20%)
        - Key risk metric for investors
    
    Example:
        >>> equity = pd.Series([10000, 11000, 10500, 9500, 10000, 11500])
        >>> dd = calculate_max_drawdown(equity)
        >>> print(dd['max_drawdown_pct'])  # -13.64%
    """
```

**4. Win Rate:**
```python
def calculate_win_rate(trades: pd.DataFrame) -> float:
    """
    Calculate percentage of winning trades.
    
    Args:
        trades: DataFrame with 'pnl' column (profit/loss per trade)
    
    Returns:
        Win rate as decimal (e.g., 0.55 = 55%)
    
    Formula:
        win_rate = (number of trades with pnl > 0) / (total number of trades)
    
    Example:
        >>> trades = pd.DataFrame({'pnl': [100, -50, 75, -25, 150]})
        >>> win_rate = calculate_win_rate(trades)
        >>> print(win_rate)  # 0.60 (3 wins out of 5 trades)
    """
```

**5. Profit Factor:**
```python
def calculate_profit_factor(trades: pd.DataFrame) -> float:
    """
    Calculate profit factor (gross profit / gross loss).
    
    Args:
        trades: DataFrame with 'pnl' column
    
    Returns:
        Profit factor (ratio)
    
    Formula:
        profit_factor = sum(winning trades) / abs(sum(losing trades))
    
    Notes:
        - >1.0 means profitable overall
        - >2.0 is good
        - Undefined if no losing trades (returns inf)
    
    Example:
        >>> trades = pd.DataFrame({'pnl': [100, -50, 75, -25]})
        >>> pf = calculate_profit_factor(trades)
        >>> print(pf)  # 2.33 (175 profit / 75 loss)
    """
```

**6. Total Return:**
```python
def calculate_total_return(
    initial_capital: float,
    final_capital: float
) -> float:
    """
    Calculate total return percentage.
    
    Args:
        initial_capital: Starting portfolio value
        final_capital: Ending portfolio value
    
    Returns:
        Total return as percentage (e.g., 15.5 = 15.5%)
    
    Formula:
        total_return = ((final - initial) / initial) * 100
    """
```

**7. Summary Metrics:**
```python
def calculate_all_metrics(
    equity_curve: pd.Series,
    trades: pd.DataFrame,
    initial_capital: float,
    periods_per_year: int = 252
) -> Dict[str, float]:
    """
    Calculate all performance metrics at once.
    
    Args:
        equity_curve: Series of portfolio values
        trades: DataFrame of all trades
        initial_capital: Starting capital
        periods_per_year: For Sharpe ratio calculation
    
    Returns:
        Dict with all metrics:
        - 'total_return_pct'
        - 'sharpe_ratio'
        - 'max_drawdown_pct'
        - 'win_rate'
        - 'profit_factor'
        - 'num_trades'
        - 'avg_trade_pnl'
        - 'final_capital'
    """
```

---

## **3️⃣ FILE: modules/backtest/engine.py**

### **Purpose**
Main backtesting engine that processes strategy signals and calculates performance.

### **Class: `BacktestEngine`**

**Constructor:**
```python
def __init__(
    self,
    initial_capital: float = 10000.0,
    position_size: float = 10000.0,
    transaction_costs: TransactionCosts = None
) -> None:
    """
    Initialize backtesting engine.
    
    Args:
        initial_capital: Starting capital in quote currency (USD)
        position_size: Fixed position size in base currency (EUR)
        transaction_costs: TransactionCosts object (default: 1 pip spread, 0% commission)
    
    Notes:
        - Fixed position sizing for simplicity (10,000 EUR standard lot)
        - Can be extended to percentage-based sizing later
        - Transaction costs default to typical retail forex spreads
    
    Example:
        engine = BacktestEngine(
            initial_capital=10000.0,
            position_size=10000.0,
            transaction_costs=TransactionCosts(spread_pips=1.5)
        )
    """
```

**Attributes:**
```python
self.initial_capital: float
self.position_size: float
self.transaction_costs: TransactionCosts
self.trades: List[Dict] = []  # Trade log
self.equity_curve: List[float] = []  # Portfolio value at each bar
```

**Main Method: Run Backtest:**
```python
def run(
    self,
    data: pd.DataFrame,
    strategy_signals: pd.DataFrame
) -> Dict[str, Any]:
    """
    Run backtest on historical data with strategy signals.
    
    Args:
        data: DataFrame with OHLC data (from load_timeframe_data)
        strategy_signals: DataFrame with signal and position columns (from strategy.generate_signals)
    
    Returns:
        Dict containing:
        - 'metrics': Dict of performance metrics
        - 'trades': DataFrame of all trades
        - 'equity_curve': Series of portfolio values
        - 'final_capital': Final portfolio value
    
    Process:
        1. Initialize portfolio at initial_capital
        2. Loop through each bar
        3. Check for position changes (signal != 0)
        4. Execute trades at next bar's open price
        5. Calculate P&L for current position
        6. Apply transaction costs at entry/exit
        7. Update equity curve
        8. Track trades
    
    Trading Logic:
        - Signal at bar t → execute at bar t+1 open
        - This avoids look-ahead bias
        - P&L calculated using close prices
        - Transaction costs paid at entry and exit
    
    Example:
        >>> from modules.data import load_timeframe_data
        >>> from modules.strategy import MARSIMomentumStrategy
        >>> 
        >>> df = load_timeframe_data('5min')
        >>> strategy = MARSIMomentumStrategy(timeframe='5min')
        >>> signals = strategy.generate_signals(df)
        >>> 
        >>> engine = BacktestEngine(initial_capital=10000)
        >>> results = engine.run(df, signals)
        >>> 
        >>> print(f"Total Return: {results['metrics']['total_return_pct']:.2f}%")
        >>> print(f"Sharpe Ratio: {results['metrics']['sharpe_ratio']:.2f}")
        >>> print(f"Number of Trades: {results['metrics']['num_trades']}")
    """
```

**Implementation Details:**

**Step 1: Initialize:**
```python
cash = self.initial_capital
position = 0  # Current position: 1 (LONG), -1 (SHORT), 0 (FLAT)
position_entry_price = 0.0
position_entry_bar = 0
equity = cash
self.equity_curve = [equity]
self.trades = []
```

**Step 2: Main Loop (Bar-by-Bar):**
```python
for i in range(len(strategy_signals)):
    current_signal = strategy_signals.iloc[i]['signal']
    current_position = strategy_signals.iloc[i]['position']
    current_price = data.iloc[i]['close']
    
    # Check for position change
    if current_signal != 0:  # BUY or SELL signal
        # Close existing position if any
        if position != 0:
            exit_price = data.iloc[i+1]['open'] if i+1 < len(data) else current_price
            pnl = self._calculate_pnl(position, position_entry_price, exit_price, self.position_size)
            exit_cost = self.transaction_costs.calculate_total_cost(exit_price, self.position_size, position)
            net_pnl = pnl - exit_cost
            cash += net_pnl
            
            # Log trade
            self.trades.append({
                'entry_bar': position_entry_bar,
                'exit_bar': i,
                'entry_price': position_entry_price,
                'exit_price': exit_price,
                'direction': 'LONG' if position == 1 else 'SHORT',
                'pnl': pnl,
                'costs': exit_cost,
                'net_pnl': net_pnl
            })
        
        # Enter new position
        if i+1 < len(data):
            entry_price = data.iloc[i+1]['open']
            entry_cost = self.transaction_costs.calculate_total_cost(entry_price, self.position_size, current_signal)
            cash -= entry_cost
            
            position = current_signal
            position_entry_price = entry_price
            position_entry_bar = i+1
    
    # Update equity
    if position != 0:
        unrealized_pnl = self._calculate_pnl(position, position_entry_price, current_price, self.position_size)
        equity = cash + unrealized_pnl
    else:
        equity = cash
    
    self.equity_curve.append(equity)
```

**Helper Method: Calculate P&L:**
```python
def _calculate_pnl(
    self,
    direction: int,
    entry_price: float,
    exit_price: float,
    size: float
) -> float:
    """
    Calculate profit/loss for a position.
    
    Args:
        direction: 1 for LONG, -1 for SHORT
        entry_price: Entry price
        exit_price: Exit price
        size: Position size
    
    Returns:
        P&L in quote currency
    
    Formula:
        LONG: pnl = (exit_price - entry_price) * size
        SHORT: pnl = (entry_price - exit_price) * size
        
        Or generally: pnl = direction * (exit_price - entry_price) * size
    """
```

**Step 3: Calculate Final Metrics:**
```python
equity_series = pd.Series(self.equity_curve, index=data.index)
trades_df = pd.DataFrame(self.trades)

metrics = calculate_all_metrics(
    equity_curve=equity_series,
    trades=trades_df,
    initial_capital=self.initial_capital,
    periods_per_year=self._get_periods_per_year(data)
)

return {
    'metrics': metrics,
    'trades': trades_df,
    'equity_curve': equity_series,
    'final_capital': equity_series.iloc[-1]
}
```

**Helper: Determine Periods Per Year:**
```python
def _get_periods_per_year(self, data: pd.DataFrame) -> int:
    """
    Determine number of periods per year based on data frequency.
    
    Args:
        data: DataFrame with datetime index
    
    Returns:
        Approximate number of bars per year
    
    Logic:
        - Infer timeframe from median time delta
        - 5min: ~72,000 bars/year (288/day * 250 trading days)
        - 4H: ~2,080 bars/year (6/day * 5 days * 52 weeks)
        - 1D: ~252 bars/year (trading days)
    """
```

---

## **4️⃣ FILE: modules/backtest/__init__.py**

### **Purpose**
Clean package exports.

### **Contents:**
```python
"""
Backtesting Module

Provides backtesting engine for evaluating trading strategies
on historical data with realistic transaction costs.

Components:
- BacktestEngine: Main backtesting loop
- TransactionCosts: Spread and commission modeling
- metrics: Performance metric calculations

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
        transaction_costs=costs
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
    'BacktestEngine',
    'TransactionCosts',
    'metrics',
]
```

---

## **🧪 Testing Strategy**

### **Test 1: Basic Backtest (5min Data)**

```python
from modules.data import load_timeframe_data
from modules.strategy import MARSIMomentumStrategy
from modules.backtest import BacktestEngine, TransactionCosts

# Load data
df = load_timeframe_data('5min')

# Generate signals
strategy = MARSIMomentumStrategy(timeframe='5min')
signals = strategy.generate_signals(df)

# Run backtest
costs = TransactionCosts(spread_pips=1.0)
engine = BacktestEngine(
    initial_capital=10000.0,
    position_size=10000.0,
    transaction_costs=costs
)

results = engine.run(df, signals)

# Display results
print("=== Backtest Results (5min) ===")
print(f"Total Return: {results['metrics']['total_return_pct']:.2f}%")
print(f"Sharpe Ratio: {results['metrics']['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['metrics']['max_drawdown_pct']:.2f}%")
print(f"Win Rate: {results['metrics']['win_rate']*100:.1f}%")
print(f"Profit Factor: {results['metrics']['profit_factor']:.2f}")
print(f"Number of Trades: {results['metrics']['num_trades']}")
print(f"Avg Trade P&L: ${results['metrics']['avg_trade_pnl']:.2f}")
print(f"Final Capital: ${results['final_capital']:.2f}")

# Verify trade count matches signal count
num_signals = (signals['signal'] != 0).sum()
print(f"\nSignal count: {num_signals}, Trade count: {len(results['trades'])}")
```

### **Test 2: All Timeframes**

```python
for tf in ['5min', '4H', '1D']:
    df = load_timeframe_data(tf)
    strategy = MARSIMomentumStrategy(timeframe=tf)
    signals = strategy.generate_signals(df)
    
    engine = BacktestEngine(initial_capital=10000, position_size=10000)
    results = engine.run(df, signals)
    
    print(f"\n{tf}: Return={results['metrics']['total_return_pct']:.2f}%, "
          f"Sharpe={results['metrics']['sharpe_ratio']:.2f}, "
          f"Trades={results['metrics']['num_trades']}")
```

### **Test 3: Transaction Cost Impact**

```python
# Compare with/without transaction costs
df = load_timeframe_data('5min')
strategy = MARSIMomentumStrategy(timeframe='5min')
signals = strategy.generate_signals(df)

# Zero costs
costs_zero = TransactionCosts(spread_pips=0.0)
engine_zero = BacktestEngine(initial_capital=10000, transaction_costs=costs_zero)
results_zero = engine_zero.run(df, signals)

# Normal costs (1 pip)
costs_normal = TransactionCosts(spread_pips=1.0)
engine_normal = BacktestEngine(initial_capital=10000, transaction_costs=costs_normal)
results_normal = engine_normal.run(df, signals)

# High costs (3 pips)
costs_high = TransactionCosts(spread_pips=3.0)
engine_high = BacktestEngine(initial_capital=10000, transaction_costs=costs_high)
results_high = engine_high.run(df, signals)

print("Transaction Cost Impact:")
print(f"0 pips: {results_zero['metrics']['total_return_pct']:.2f}%")
print(f"1 pip: {results_normal['metrics']['total_return_pct']:.2f}%")
print(f"3 pips: {results_high['metrics']['total_return_pct']:.2f}%")
```

### **Test 4: Manual P&L Verification**

```python
# Verify first trade P&L manually
results = engine.run(df, signals)
first_trade = results['trades'].iloc[0]

entry_price = first_trade['entry_price']
exit_price = first_trade['exit_price']
direction = 1 if first_trade['direction'] == 'LONG' else -1
size = 10000

manual_pnl = direction * (exit_price - entry_price) * size
print(f"Manual P&L: ${manual_pnl:.2f}")
print(f"Engine P&L: ${first_trade['pnl']:.2f}")
print(f"Match: {abs(manual_pnl - first_trade['pnl']) < 0.01}")
```

### **Expected Results (Approximate)**

**5min Strategy (139 signals):**
- Total Return: -5% to +15% (depends on market conditions)
- Sharpe Ratio: 0.5 to 2.0
- Max Drawdown: -10% to -25%
- Win Rate: 40-60%
- Number of Trades: ~69 (139 signals / 2, since each round-trip is entry+exit)

**Note:** Actual results depend on EUR/USD price action during data period.

---

## **📊 Key Formulas Reference**

### **P&L Calculation:**
```
LONG: pnl = (exit_price - entry_price) * size
SHORT: pnl = (entry_price - exit_price) * size
General: pnl = direction * (exit_price - entry_price) * size
```

### **Transaction Costs:**
```
spread_cost = spread_pips * pip_value * size
commission = price * size * commission_pct / 100
total_cost = spread_cost + commission
```

### **Sharpe Ratio:**
```
sharpe = (mean_return - risk_free_rate) / std_return * sqrt(periods_per_year)
```

### **Maximum Drawdown:**
```
drawdown_t = (equity_t - peak_equity_up_to_t) / peak_equity_up_to_t
max_drawdown = min(all drawdowns)
```

### **Win Rate:**
```
win_rate = count(trades with pnl > 0) / total_trades
```

### **Profit Factor:**
```
profit_factor = sum(winning_trades) / abs(sum(losing_trades))
```

---

## **🔧 Implementation Notes**

### **Dependencies**
```python
import pandas as pd
import numpy as np
from typing import Any, Dict, List
import logging

from modules.config import TIMEFRAME_CONFIGS
```

### **Critical Design Decisions**

**1. Signal Execution Timing:**
- Signal at bar t → execute at bar t+1 open
- This prevents look-ahead bias
- Realistic: can't trade on current bar's close

**2. Fixed Position Sizing:**
- Simplifies implementation
- Standard lot: 10,000 EUR
- Can extend to percentage-based sizing later

**3. Transaction Costs:**
- Applied at BOTH entry and exit
- Typical retail EUR/USD spread: 1-2 pips
- Commission usually 0% for retail forex

**4. Equity Curve:**
- Cash + unrealized P&L of open position
- Updated at every bar
- Used for drawdown calculation

**5. Trade Logging:**
- One trade = entry + exit (round-trip)
- Logs entry/exit prices, P&L, costs
- Used for trade analysis

### **Edge Cases to Handle**
- Last bar: can't execute signal (no next bar)
- First signal: no existing position to close
- Consecutive same signals: don't double-enter
- All losing trades: profit factor undefined (set to 0.0)

### **Logging**
```python
logger = logging.getLogger(__name__)

# Log backtest start
logger.info(f"Starting backtest with {len(data)} bars")

# Log completion
logger.info(f"Backtest complete. Trades: {len(self.trades)}, "
           f"Final capital: ${final_capital:.2f}")
```

---

## **📝 Commit Message**

After implementation:

```
Add backtesting engine module

- Created BacktestEngine with bar-by-bar simulation
- Implemented TransactionCosts (spread + commission)
- Added performance metrics (Sharpe, MDD, win rate, profit factor)
- Trade execution at next bar open (no look-ahead bias)
- Tested with all 3 timeframes (5min, 4H, 1D)
- Full P&L tracking and trade logging
```

---

## **✅ Definition of Done**

- [ ] All 4 files created
- [ ] BacktestEngine processes signals correctly
- [ ] P&L calculations verified manually
- [ ] Transaction costs applied at entry and exit
- [ ] All metrics calculated correctly
- [ ] Equity curve tracks portfolio value
- [ ] Trade log captures all entries/exits
- [ ] Tested with all three timeframes
- [ ] Type hints on all methods
- [ ] Google docstrings with examples
- [ ] PEP 8 compliant (black formatted)
- [ ] File headers present
- [ ] Committed and pushed to GitHub

---

## **🎯 Ready for Implementation**

**This specification is complete and self-contained.**

**Estimated API cost:** ~$1.25 (10-12 minutes)

**Next step:** Pass this specification to Claude Code (Opus 4.6).

---

**End of Specification 5**

---
