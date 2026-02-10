
---

# **Specification 3: Technical Indicators Module**

**Project:** CPF Final Project - Automated Trading System  
**Module:** `modules/indicators/`  
**Session:** 3  
**Date:** February 10, 2026  
**Prerequisites:** Session 1 (Config) ✅, Session 2 (Data) ✅

---

## **📋 Overview**

Create a modular technical indicators system with:
1. Abstract base class for all indicators
2. Simple Moving Average (SMA) implementation
3. Relative Strength Index (RSI) implementation
4. Momentum indicator implementation

All indicators will accept pandas DataFrames with OHLC data and return Series with calculated values.

---

## **🎯 Success Criteria**

- ✅ All indicators follow base class pattern
- ✅ Type hints on all functions
- ✅ Google-style docstrings
- ✅ Indicators tested with actual EUR/USD data
- ✅ Results match expected calculations
- ✅ PEP 8 compliant (black formatted)
- ✅ File headers: "Jürgen Kober + Claude Code Opus 4.6"

---

## **📁 Files to Create**

```
modules/indicators/
├── __init__.py           # Clean exports
├── base.py              # Abstract Indicator base class
├── sma.py               # Simple Moving Average
├── rsi.py               # Relative Strength Index
└── momentum.py          # Momentum indicator
```

---

## **1️⃣ FILE: modules/indicators/base.py**

### **Purpose**
Abstract base class that all indicators inherit from. Enforces consistent interface.

### **Requirements**

**Class: `Indicator` (ABC)**

**Abstract Methods:**
```python
@abstractmethod
def calculate(self, data: pd.DataFrame) -> pd.Series:
    """
    Calculate indicator values.
    
    Args:
        data: DataFrame with OHLC columns (Open, High, Low, Close, Volume)
              Indexed by datetime
    
    Returns:
        Series with indicator values, same index as input data
    
    Raises:
        ValueError: If required columns missing
        ValueError: If insufficient data for calculation
    """
    pass
```

**Concrete Methods:**
```python
def validate_data(self, data: pd.DataFrame, required_columns: List[str]) -> None:
    """
    Validate input DataFrame has required columns.
    
    Args:
        data: DataFrame to validate
        required_columns: List of required column names
    
    Raises:
        ValueError: If any required columns missing
        ValueError: If data is empty
    """
    pass

def __call__(self, data: pd.DataFrame) -> pd.Series:
    """Allow indicator to be called like a function."""
    return self.calculate(data)
```

**Attributes:**
- `name: str` - Indicator name (e.g., "SMA_20")
- `params: Dict[str, Any]` - Indicator parameters

**Example Usage:**
```python
class MySMA(Indicator):
    def __init__(self, period: int = 20):
        self.name = f"SMA_{period}"
        self.params = {"period": period}
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_data(data, ["Close"])
        return data['Close'].rolling(window=self.params['period']).mean()
```

---

## **2️⃣ FILE: modules/indicators/sma.py**

### **Purpose**
Simple Moving Average - calculates the average of closing prices over N periods.

### **Class: `SMA(Indicator)`**

**Constructor:**
```python
def __init__(self, period: int = 20) -> None:
    """
    Initialize SMA indicator.
    
    Args:
        period: Number of periods for moving average (default: 20)
    
    Raises:
        ValueError: If period < 2
    """
```

**Calculate Method:**
```python
def calculate(self, data: pd.DataFrame) -> pd.Series:
    """
    Calculate Simple Moving Average.
    
    Formula: SMA = sum(Close prices over N periods) / N
    
    Args:
        data: DataFrame with 'Close' column
    
    Returns:
        Series with SMA values, NaN for first (period-1) rows
    
    Example:
        sma = SMA(period=20)
        sma_values = sma.calculate(df)
        # or: sma_values = sma(df)
    """
```

**Implementation Details:**
- Use `pandas.Series.rolling(window=period).mean()`
- First (period-1) values will be NaN
- Preserve input DataFrame index
- Work with any column via `data['Close']`

**Testing Requirements:**
- Test with period=20, period=50, period=200
- Verify first N-1 values are NaN
- Verify calculation matches manual calculation for small sample
- Test error handling (missing Close column, period < 2)

---

## **3️⃣ FILE: modules/indicators/rsi.py**

### **Purpose**
Relative Strength Index - measures momentum by comparing recent gains vs losses.

### **Class: `RSI(Indicator)`**

**Constructor:**
```python
def __init__(self, period: int = 14) -> None:
    """
    Initialize RSI indicator.
    
    Args:
        period: Number of periods for RSI calculation (default: 14)
    
    Raises:
        ValueError: If period < 2
    """
```

**Calculate Method:**
```python
def calculate(self, data: pd.DataFrame) -> pd.Series:
    """
    Calculate Relative Strength Index.
    
    Formula:
        1. Calculate price changes: delta = Close.diff()
        2. Separate gains and losses:
           gains = delta.where(delta > 0, 0)
           losses = -delta.where(delta < 0, 0)
        3. Calculate average gain/loss over period (using EMA):
           avg_gain = gains.ewm(alpha=1/period, adjust=False).mean()
           avg_loss = losses.ewm(alpha=1/period, adjust=False).mean()
        4. Calculate RS: rs = avg_gain / avg_loss
        5. Calculate RSI: rsi = 100 - (100 / (1 + rs))
    
    Args:
        data: DataFrame with 'Close' column
    
    Returns:
        Series with RSI values (0-100), NaN for first period rows
    
    Notes:
        - RSI values range from 0 to 100
        - Traditional interpretation: >70 overbought, <30 oversold
        - First period values will be NaN due to EMA initialization
    """
```

**Implementation Details:**
- Use exponential moving average (EMA) for smoothing (standard RSI formula)
- Handle division by zero (when avg_loss = 0, RSI = 100)
- Ensure output is bounded [0, 100]
- First `period` values will be NaN

**Testing Requirements:**
- Test with period=14 (standard)
- Verify RSI is bounded [0, 100]
- Test with trending data (verify values respond correctly)
- Test edge case: all prices increasing (RSI → 100)
- Test edge case: all prices decreasing (RSI → 0)

---

## **4️⃣ FILE: modules/indicators/momentum.py**

### **Purpose**
Momentum indicator - measures rate of change in price over N periods.

### **Class: `Momentum(Indicator)`**

**Constructor:**
```python
def __init__(self, period: int = 10) -> None:
    """
    Initialize Momentum indicator.
    
    Args:
        period: Number of periods to look back (default: 10)
    
    Raises:
        ValueError: If period < 1
    """
```

**Calculate Method:**
```python
def calculate(self, data: pd.DataFrame) -> pd.Series:
    """
    Calculate Momentum indicator.
    
    Formula: Momentum = Close(today) - Close(N periods ago)
    
    Alternative formula (percentage): ((Close(today) / Close(N periods ago)) - 1) * 100
    
    Implementation: Use absolute difference (not percentage)
    
    Args:
        data: DataFrame with 'Close' column
    
    Returns:
        Series with momentum values, NaN for first period rows
    
    Notes:
        - Positive values indicate upward momentum
        - Negative values indicate downward momentum
        - First period values will be NaN
    
    Example:
        If period=10:
        - momentum[10] = close[10] - close[0]
        - momentum[11] = close[11] - close[1]
    """
```

**Implementation Details:**
- Use `data['Close'].diff(periods=period)` for simple implementation
- OR: `data['Close'] - data['Close'].shift(period)` (equivalent)
- First `period` values will be NaN
- Preserve sign (positive = upward, negative = downward)

**Testing Requirements:**
- Test with period=10, period=14
- Verify first N values are NaN
- Test with uptrend (verify positive momentum)
- Test with downtrend (verify negative momentum)
- Verify calculation matches manual calculation

---

## **5️⃣ FILE: modules/indicators/__init__.py**

### **Purpose**
Clean package exports for easy imports.

### **Contents:**
```python
"""
Technical Indicators Module

Provides technical analysis indicators for trading strategies.

Available indicators:
- SMA: Simple Moving Average
- RSI: Relative Strength Index
- Momentum: Rate of change indicator

Example:
    from modules.indicators import SMA, RSI, Momentum
    
    sma = SMA(period=20)
    rsi = RSI(period=14)
    momentum = Momentum(period=10)
    
    df['SMA_20'] = sma(df)
    df['RSI_14'] = rsi(df)
    df['MOM_10'] = momentum(df)
"""

from modules.indicators.base import Indicator
from modules.indicators.sma import SMA
from modules.indicators.rsi import RSI
from modules.indicators.momentum import Momentum

__all__ = [
    'Indicator',
    'SMA',
    'RSI',
    'Momentum',
]
```

---

## **🧪 Testing Strategy**

### **Test with Real Data**

**After implementation, verify with actual EUR/USD data:**

```python
from modules.data import load_timeframe_data
from modules.indicators import SMA, RSI, Momentum

# Load 5min data
df = load_timeframe_data('5min')

# Calculate indicators
df['SMA_20'] = SMA(20)(df)
df['SMA_50'] = SMA(50)(df)
df['RSI_14'] = RSI(14)(df)
df['MOM_10'] = Momentum(10)(df)

# Verify results
print(f"SMA_20 range: {df['SMA_20'].min():.4f} - {df['SMA_20'].max():.4f}")
print(f"RSI_14 range: {df['RSI_14'].min():.2f} - {df['RSI_14'].max():.2f}")
print(f"MOM_10 range: {df['MOM_10'].min():.6f} - {df['MOM_10'].max():.6f}")

# Check for NaN counts
print(f"\nNaN counts:")
print(f"SMA_20: {df['SMA_20'].isna().sum()} (expected: 19)")
print(f"RSI_14: {df['RSI_14'].isna().sum()} (expected: ~14)")
print(f"MOM_10: {df['MOM_10'].isna().sum()} (expected: 10)")

# Verify RSI is bounded
assert df['RSI_14'].min() >= 0, "RSI below 0!"
assert df['RSI_14'].max() <= 100, "RSI above 100!"

print("\n✓ All indicators working correctly!")
```

### **Expected Output Ranges (EUR/USD 5min)**
- **SMA_20:** ~1.03 - 1.05 (depends on date range)
- **RSI_14:** 0 - 100 (should use full range during volatile periods)
- **Momentum_10:** -0.01 to +0.01 (small values for 5min data)

---

## **📊 Parameter Reference (from Session 1)**

**These are the literature-backed parameters already in config:**

| Timeframe | SMA Fast | SMA Slow | RSI Period | Momentum Period |
|-----------|----------|----------|------------|-----------------|
| 5min      | 20       | 50       | 14         | 10              |
| 4H        | 20       | 50       | 14         | 10              |
| Daily     | 50       | 200      | 14         | 14              |

**Your indicators should work with any period, but these are the defaults for strategy.**

---

## **🔧 Implementation Notes**

### **Dependencies**
```python
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Any, Dict, List
```

### **Error Handling**
- Validate period parameters (must be >= 1 or 2 depending on indicator)
- Validate DataFrame has required columns
- Handle edge cases (empty data, insufficient rows)
- Provide clear error messages

### **Performance**
- Use vectorized pandas operations (no loops)
- Avoid copying data unnecessarily
- All indicators should complete in <100ms for 10K rows

### **Code Quality**
- Every method has type hints
- Every method has Google-style docstring with examples
- Use logging for warnings (e.g., insufficient data)
- File headers: "Jürgen Kober + Claude Code Opus 4.6"

---

## **📝 Commit Message**

After implementation:

```
Add technical indicators module (SMA, RSI, Momentum)

- Created abstract Indicator base class
- Implemented SMA with configurable period
- Implemented RSI using EMA smoothing
- Implemented Momentum as price difference
- All indicators tested with EUR/USD data
- Full type hints and documentation
```

---

## **✅ Definition of Done**

- [ ] All 5 files created
- [ ] All classes inherit from Indicator base
- [ ] Type hints on every function/method
- [ ] Google docstrings on every function/method
- [ ] Indicators tested with real EUR/USD data
- [ ] RSI bounded [0, 100]
- [ ] NaN counts match expected values
- [ ] PEP 8 compliant (run `black --check`)
- [ ] File headers present
- [ ] Committed and pushed to GitHub

---

## **🎯 Ready for Implementation**

**This specification is complete and self-contained.**

**Estimated API cost:** ~$1.00 (8-10 minutes)

**Next step:** Pass this specification to Claude Code (Opus 4.6).

---

**End of Specification 3**

---
