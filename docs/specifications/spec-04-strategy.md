
---

# **Specification 4: Trading Strategy Module**

**Project:** CPF Final Project - Automated Trading System  
**Module:** `modules/strategy/`  
**Session:** 4  
**Date:** February 10, 2026  
**Prerequisites:** Session 1 (Config) ✅, Session 2 (Data) ✅, Session 3 (Indicators) ✅

---

## **📋 Overview**

Implement the parametric multi-timeframe trading strategy using Moving Average crossover with RSI and Momentum confirmation filters. The strategy will:

1. Generate trading signals (BUY, SELL, HOLD) based on indicator combinations
2. Apply multi-indicator confirmation for signal validation
3. Support different timeframe configurations from Session 1
4. Provide position entry/exit logic

**Strategy Logic:**
- **Primary Signal:** SMA crossover (fast crosses above/below slow)
- **RSI Filter:** Confirm trend isn't overextended
- **Momentum Filter:** Confirm directional strength
- **Result:** Only generate signals when all three indicators align

---

## **🎯 Success Criteria**

- ✅ Abstract base Strategy class for extensibility
- ✅ Complete MA + RSI + Momentum strategy implementation
- ✅ Signal generation tested with real EUR/USD data
- ✅ All signals have timestamps and can be backtested
- ✅ Type hints and Google docstrings throughout
- ✅ PEP 8 compliant, file headers present

---

## **📁 Files to Create**

```
modules/strategy/
├── __init__.py              # Clean exports
├── base.py                  # Abstract Strategy base class
└── ma_rsi_momentum.py       # Multi-indicator confirmation strategy
```

---

## **1️⃣ FILE: modules/strategy/base.py**

### **Purpose**
Abstract base class for all trading strategies. Enforces consistent interface and provides common utilities.

### **Requirements**

**Class: `Strategy` (ABC)**

**Abstract Methods:**
```python
@abstractmethod
def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
    """
    Generate trading signals from price data.
    
    Args:
        data: DataFrame with OHLC data and datetime index
              Must contain: open, high, low, close, volume
    
    Returns:
        DataFrame with original data plus new columns:
        - 'signal': int (1=BUY, -1=SELL, 0=HOLD)
        - 'position': int (1=LONG, -1=SHORT, 0=FLAT)
        Optional strategy-specific columns (indicator values, etc.)
    
    Raises:
        ValueError: If required columns missing
        ValueError: If insufficient data
    """
    pass
```

**Concrete Helper Methods:**
```python
def validate_data(self, data: pd.DataFrame, required_columns: List[str]) -> None:
    """
    Validate input DataFrame.
    
    Args:
        data: DataFrame to validate
        required_columns: List of required column names
    
    Raises:
        ValueError: If columns missing or data empty
    """
    pass

def _signals_to_positions(self, signals: pd.Series) -> pd.Series:
    """
    Convert signals to positions using forward-fill logic.
    
    Args:
        signals: Series with values (1=BUY, -1=SELL, 0=HOLD)
    
    Returns:
        Series with positions (1=LONG, -1=SHORT, 0=FLAT)
        
    Logic:
        - BUY signal (1) → enter LONG (1) until SELL
        - SELL signal (-1) → enter SHORT (-1) until BUY
        - HOLD signal (0) → maintain current position
        - Forward-fill: position persists until opposite signal
    
    Example:
        signals:   [0, 0, 1, 0, 0, -1, 0, 0, 1]
        positions: [0, 0, 1, 1, 1, -1, -1, -1, 1]
    """
    pass

def get_signal_count(self, signals: pd.DataFrame) -> Dict[str, int]:
    """
    Count signal occurrences.
    
    Args:
        signals: DataFrame with 'signal' column
    
    Returns:
        Dict with counts: {'BUY': n, 'SELL': m, 'HOLD': k}
    """
    pass
```

**Attributes:**
- `name: str` - Strategy name
- `params: Dict[str, Any]` - Strategy parameters
- `timeframe: str` - Timeframe this strategy operates on

**Example Usage:**
```python
class MyStrategy(Strategy):
    def __init__(self, fast_period: int = 20, slow_period: int = 50):
        self.name = "SMA_Crossover"
        self.params = {"fast": fast_period, "slow": slow_period}
        self.timeframe = "5min"
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        self.validate_data(data, ['close'])
        # ... calculate signals ...
        data['signal'] = signals
        data['position'] = self._signals_to_positions(signals)
        return data
```

---

## **2️⃣ FILE: modules/strategy/ma_rsi_momentum.py**

### **Purpose**
Implements the parametric multi-indicator confirmation strategy:
- SMA crossover for trend
- RSI filter for overbought/oversold
- Momentum filter for directional confirmation

### **Class: `MARSIMomentumStrategy(Strategy)`**

**Constructor:**
```python
def __init__(
    self,
    timeframe: str = '5min',
    sma_fast: int = None,
    sma_slow: int = None,
    rsi_period: int = None,
    rsi_lower: int = 30,
    rsi_upper: int = 70,
    momentum_period: int = None,
    momentum_threshold: float = 0.0
) -> None:
    """
    Initialize MA + RSI + Momentum strategy.
    
    Args:
        timeframe: Timeframe for this strategy ('5min', '4H', '1D')
        sma_fast: Fast SMA period (default from config)
        sma_slow: Slow SMA period (default from config)
        rsi_period: RSI period (default from config)
        rsi_lower: RSI lower threshold (default: 30, oversold)
        rsi_upper: RSI upper threshold (default: 70, overbought)
        momentum_period: Momentum period (default from config)
        momentum_threshold: Minimum momentum to confirm signal (default: 0.0)
    
    Raises:
        ValueError: If invalid timeframe
        ValueError: If sma_fast >= sma_slow
    
    Notes:
        If periods are None, loads from config.TIMEFRAME_CONFIGS[timeframe]
    """
```

**Implementation Details:**
- Load default parameters from `modules.config.TIMEFRAME_CONFIGS[timeframe]`
- Store all parameters in `self.params`
- Set `self.name = f"MA_RSI_MOM_{timeframe}"`
- Set `self.timeframe = timeframe`

**Generate Signals Method:**
```python
def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
    """
    Generate trading signals using multi-indicator confirmation.
    
    Strategy Logic:
    
    BUY SIGNAL (signal = 1):
        1. SMA Crossover: fast_sma crosses ABOVE slow_sma
        2. RSI Filter: RSI < rsi_upper (not overbought)
        3. Momentum Filter: momentum > momentum_threshold (positive)
        → All three conditions must be TRUE
    
    SELL SIGNAL (signal = -1):
        1. SMA Crossover: fast_sma crosses BELOW slow_sma
        2. RSI Filter: RSI > rsi_lower (not oversold)
        3. Momentum Filter: momentum < -momentum_threshold (negative)
        → All three conditions must be TRUE
    
    HOLD SIGNAL (signal = 0):
        - No crossover occurred, OR
        - Crossover occurred but filters reject it
    
    Args:
        data: DataFrame with columns: open, high, low, close, volume
    
    Returns:
        DataFrame with added columns:
        - 'sma_fast': Fast SMA values
        - 'sma_slow': Slow SMA values
        - 'rsi': RSI values
        - 'momentum': Momentum values
        - 'signal': Trading signals (1, -1, 0)
        - 'position': Positions (1, -1, 0)
    
    Example:
        strategy = MARSIMomentumStrategy(timeframe='5min')
        signals_df = strategy.generate_signals(df)
        
        # Inspect signals
        buy_signals = signals_df[signals_df['signal'] == 1]
        sell_signals = signals_df[signals_df['signal'] == -1]
    """
```

**Implementation Steps:**

**Step 1: Calculate Indicators**
```python
from modules.indicators import SMA, RSI, Momentum

# Calculate all indicators
sma_fast_ind = SMA(self.params['sma_fast'])
sma_slow_ind = SMA(self.params['sma_slow'])
rsi_ind = RSI(self.params['rsi_period'])
mom_ind = Momentum(self.params['momentum_period'])

data['sma_fast'] = sma_fast_ind(data)
data['sma_slow'] = sma_slow_ind(data)
data['rsi'] = rsi_ind(data)
data['momentum'] = mom_ind(data)
```

**Step 2: Detect Crossovers**
```python
# Crossover detection
# BUY: fast crosses above slow
# SELL: fast crosses below slow

# Previous values
data['sma_fast_prev'] = data['sma_fast'].shift(1)
data['sma_slow_prev'] = data['sma_slow'].shift(1)

# Crossover conditions
bullish_cross = (
    (data['sma_fast'] > data['sma_slow']) &
    (data['sma_fast_prev'] <= data['sma_slow_prev'])
)

bearish_cross = (
    (data['sma_fast'] < data['sma_slow']) &
    (data['sma_fast_prev'] >= data['sma_slow_prev'])
)
```

**Step 3: Apply Filters**
```python
# RSI filter
rsi_allows_buy = data['rsi'] < self.params['rsi_upper']
rsi_allows_sell = data['rsi'] > self.params['rsi_lower']

# Momentum filter
momentum_positive = data['momentum'] > self.params['momentum_threshold']
momentum_negative = data['momentum'] < -self.params['momentum_threshold']

# Combined conditions
buy_signal = bullish_cross & rsi_allows_buy & momentum_positive
sell_signal = bearish_cross & rsi_allows_sell & momentum_negative
```

**Step 4: Generate Signal Column**
```python
# Initialize with 0 (HOLD)
data['signal'] = 0

# Set BUY and SELL
data.loc[buy_signal, 'signal'] = 1
data.loc[sell_signal, 'signal'] = -1
```

**Step 5: Convert to Positions**
```python
data['position'] = self._signals_to_positions(data['signal'])
```

**Step 6: Clean Up and Return**
```python
# Drop temporary columns
data = data.drop(['sma_fast_prev', 'sma_slow_prev'], axis=1)

return data
```

---

## **3️⃣ FILE: modules/strategy/__init__.py**

### **Purpose**
Clean package exports.

### **Contents:**
```python
"""
Trading Strategy Module

Implements trading strategies that combine technical indicators
to generate buy/sell signals.

Available strategies:
- MARSIMomentumStrategy: MA crossover + RSI + Momentum filters

Example:
    from modules.strategy import MARSIMomentumStrategy
    from modules.data import load_timeframe_data
    
    # Load data
    df = load_timeframe_data('5min')
    
    # Create strategy
    strategy = MARSIMomentumStrategy(timeframe='5min')
    
    # Generate signals
    signals = strategy.generate_signals(df)
    
    # Analyze
    buy_count = (signals['signal'] == 1).sum()
    sell_count = (signals['signal'] == -1).sum()
    print(f"BUY signals: {buy_count}, SELL signals: {sell_count}")
"""

from modules.strategy.base import Strategy
from modules.strategy.ma_rsi_momentum import MARSIMomentumStrategy

__all__ = [
    'Strategy',
    'MARSIMomentumStrategy',
]
```

---

## **🧪 Testing Strategy**

### **Test 1: Signal Generation (5min Data)**

```python
from modules.data import load_timeframe_data
from modules.strategy import MARSIMomentumStrategy

# Load 5min data
df = load_timeframe_data('5min')

# Create strategy with defaults from config
strategy = MARSIMomentumStrategy(timeframe='5min')

# Generate signals
signals = strategy.generate_signals(df)

# Verify columns exist
assert 'sma_fast' in signals.columns
assert 'sma_slow' in signals.columns
assert 'rsi' in signals.columns
assert 'momentum' in signals.columns
assert 'signal' in signals.columns
assert 'position' in signals.columns

# Count signals
buy_signals = (signals['signal'] == 1).sum()
sell_signals = (signals['signal'] == -1).sum()
hold_signals = (signals['signal'] == 0).sum()

print(f"5min Strategy Results:")
print(f"  BUY signals: {buy_signals}")
print(f"  SELL signals: {sell_signals}")
print(f"  HOLD periods: {hold_signals}")
print(f"  Total rows: {len(signals)}")

# Verify signal values are valid
assert signals['signal'].isin([1, -1, 0]).all()
assert signals['position'].isin([1, -1, 0]).all()

# Display first few signals
print("\nFirst 5 signal events:")
print(signals[signals['signal'] != 0][['close', 'sma_fast', 'sma_slow', 'rsi', 'momentum', 'signal']].head())
```

### **Test 2: All Timeframes**

```python
for tf in ['5min', '4H', '1D']:
    df = load_timeframe_data(tf)
    strategy = MARSIMomentumStrategy(timeframe=tf)
    signals = strategy.generate_signals(df)
    
    buy_count = (signals['signal'] == 1).sum()
    sell_count = (signals['signal'] == -1).sum()
    
    print(f"{tf}: {buy_count} BUYs, {sell_count} SELLs")
```

### **Test 3: Position Forward-Fill Logic**

```python
# Verify positions persist until opposite signal
signals_only = signals[signals['signal'] != 0].copy()

for i in range(len(signals_only) - 1):
    current_signal = signals_only.iloc[i]['signal']
    next_signal = signals_only.iloc[i + 1]['signal']
    
    # Find positions between these signals
    current_idx = signals_only.index[i]
    next_idx = signals_only.index[i + 1]
    
    between = signals.loc[current_idx:next_idx, 'position']
    
    # All should match current signal
    if current_signal == 1:
        assert (between == 1).all(), "LONG position not maintained"
    elif current_signal == -1:
        assert (between == -1).all(), "SHORT position not maintained"

print("✓ Position forward-fill logic correct")
```

### **Expected Results (Approximate)**

**5min data (~8,372 rows):**
- BUY signals: 15-30
- SELL signals: 15-30
- Signal frequency: ~1-2% of bars

**4H data (~5,421 rows):**
- BUY signals: 10-20
- SELL signals: 10-20
- Signal frequency: ~0.5-1% of bars

**Daily data (~776 rows):**
- BUY signals: 3-8
- SELL signals: 3-8
- Signal frequency: ~1-2% of bars

**Note:** Exact counts depend on EUR/USD price action during data period.

---

## **📊 Parameter Reference**

**From Session 1 Config (TIMEFRAME_CONFIGS):**

| Timeframe | SMA Fast | SMA Slow | RSI Period | RSI Lower | RSI Upper | Momentum Period |
|-----------|----------|----------|------------|-----------|-----------|-----------------|
| 5min      | 20       | 50       | 14         | 30        | 70        | 10              |
| 4H        | 20       | 50       | 14         | 30        | 70        | 10              |
| 1D        | 50       | 200      | 14         | 30        | 70        | 14              |

**Strategy uses these as defaults when `timeframe` is specified.**

---

## **🔧 Implementation Notes**

### **Dependencies**
```python
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from modules.config import TIMEFRAME_CONFIGS
from modules.indicators import SMA, RSI, Momentum
```

### **Edge Cases to Handle**
- Insufficient data (need at least slow_sma + momentum_period rows)
- All NaN indicators at start (first N rows will have no signals)
- No crossovers in data (all signals = 0, valid scenario)
- RSI exactly at threshold (use < and >, not <= and >=)

### **Logging**
```python
import logging
logger = logging.getLogger(__name__)

# Log strategy initialization
logger.info(f"Initialized {self.name} with params: {self.params}")

# Log signal counts after generation
logger.info(f"Generated {buy_count} BUY, {sell_count} SELL signals")
```

### **Performance**
- Strategy should complete in <200ms for 10K rows
- Use vectorized pandas operations (no loops)
- Calculate all indicators once upfront

---

## **📝 Commit Message**

After implementation:

```
Add trading strategy module (MA + RSI + Momentum)

- Created abstract Strategy base class
- Implemented MARSIMomentumStrategy with multi-indicator confirmation
- Signal generation: SMA crossover + RSI filter + Momentum filter
- Position tracking with forward-fill logic
- Tested with all 3 timeframes (5min, 4H, 1D)
- Parameters loaded from config by default
```

---

## **✅ Definition of Done**

- [ ] All 3 files created
- [ ] Base Strategy class is abstract (ABC)
- [ ] MARSIMomentumStrategy implements full logic
- [ ] Signals tested with real EUR/USD data
- [ ] All timeframes produce valid signals
- [ ] Position forward-fill works correctly
- [ ] Type hints on all methods
- [ ] Google docstrings with examples
- [ ] PEP 8 compliant (black formatted)
- [ ] File headers present
- [ ] Committed and pushed to GitHub

---

## **🎯 Ready for Implementation**

**This specification is complete and self-contained.**

**Estimated API cost:** ~$0.75 (6-8 minutes)

**Next step:** Pass this specification to Claude Code (Opus 4.6).

---

**End of Specification 4**

---
