
---

# **Specification 6: Parameter Optimization Module**

**Project:** CPF Final Project - Automated Trading System  
**Module:** `modules/optimization/`  
**Session:** 6  
**Date:** February 10, 2026  
**Prerequisites:** Sessions 1-5 complete ✅

---

## **📋 Overview**

Implement parameter optimization to systematically test different parameter combinations and find potentially better-performing configurations. Given Session 5's negative returns, optimization will:

1. Test various SMA period combinations
2. Test different RSI thresholds
3. Test momentum thresholds
4. Compare results across timeframes
5. Identify which parameters (if any) improve performance
6. **Document when optimization doesn't improve results** (equally valuable)

**Critical Principle:** Avoid overfitting. We're exploring parameter space, not curve-fitting to historical data. If no parameters work well, that's a valid conclusion.

---

## **🎯 Success Criteria**

- ✅ Grid search tests all parameter combinations
- ✅ Results ranked by multiple metrics (not just returns)
- ✅ Overfitting warnings included
- ✅ Comparison tables clearly show best/worst combinations
- ✅ Works with all three timeframes
- ✅ Execution time reasonable (<5 minutes for typical grid)
- ✅ Type hints and Google docstrings throughout
- ✅ Results can be exported for notebook analysis

---

## **📁 Files to Create**

```
modules/optimization/
├── __init__.py              # Clean exports
├── grid_search.py           # Parameter grid search
└── results.py               # Results storage and ranking
```

---

## **1️⃣ FILE: modules/optimization/results.py**

### **Purpose**
Store, compare, and rank optimization results.

### **Class: `OptimizationResults`**

**Constructor:**
```python
def __init__(self) -> None:
    """
    Initialize optimization results container.
    
    Attributes:
        results: List of dicts, each containing:
            - 'params': Dict of strategy parameters
            - 'metrics': Dict of backtest metrics
            - 'timeframe': Timeframe tested
    """
```

**Methods:**

**1. Add Result:**
```python
def add_result(
    self,
    params: Dict[str, Any],
    metrics: Dict[str, float],
    timeframe: str
) -> None:
    """
    Add a single optimization result.
    
    Args:
        params: Strategy parameters tested (e.g., {'sma_fast': 20, 'sma_slow': 50})
        metrics: Backtest metrics from this parameter set
        timeframe: Timeframe tested ('5min', '4H', '1D')
    """
```

**2. Get DataFrame:**
```python
def to_dataframe(self) -> pd.DataFrame:
    """
    Convert results to DataFrame for analysis.
    
    Returns:
        DataFrame with columns:
        - Parameter columns (sma_fast, sma_slow, rsi_lower, etc.)
        - Metric columns (total_return_pct, sharpe_ratio, etc.)
        - timeframe column
    
    Example:
        >>> results = OptimizationResults()
        >>> # ... add results ...
        >>> df = results.to_dataframe()
        >>> print(df.head())
    """
```

**3. Rank by Metric:**
```python
def rank_by_metric(
    self,
    metric: str,
    ascending: bool = False,
    top_n: int = 10
) -> pd.DataFrame:
    """
    Rank parameter combinations by a specific metric.
    
    Args:
        metric: Metric name (e.g., 'sharpe_ratio', 'total_return_pct')
        ascending: If True, lower is better (e.g., for max_drawdown)
        top_n: Number of top results to return
    
    Returns:
        DataFrame of top N parameter combinations
    
    Example:
        >>> # Best Sharpe ratios
        >>> top_sharpe = results.rank_by_metric('sharpe_ratio', top_n=5)
        >>> 
        >>> # Lowest drawdowns
        >>> low_dd = results.rank_by_metric('max_drawdown_pct', ascending=True, top_n=5)
    """
```

**4. Compare Metrics:**
```python
def get_metric_statistics(self, metric: str) -> Dict[str, float]:
    """
    Get statistics for a specific metric across all results.
    
    Args:
        metric: Metric name
    
    Returns:
        Dict with keys: min, max, mean, median, std
    
    Example:
        >>> stats = results.get_metric_statistics('sharpe_ratio')
        >>> print(f"Sharpe range: {stats['min']:.2f} to {stats['max']:.2f}")
    """
```

**5. Best Overall:**
```python
def get_best_overall(
    self,
    primary_metric: str = 'sharpe_ratio',
    secondary_metric: str = 'total_return_pct',
    min_trades: int = 10
) -> Dict[str, Any]:
    """
    Get best parameter combination using multiple criteria.
    
    Args:
        primary_metric: Primary ranking metric
        secondary_metric: Tiebreaker metric
        min_trades: Minimum number of trades required (filter out low-activity params)
    
    Returns:
        Dict containing:
        - 'params': Best parameter combination
        - 'metrics': Metrics for this combination
        - 'rank': Ranking details
    
    Logic:
        1. Filter results with >= min_trades
        2. Rank by primary_metric
        3. Break ties with secondary_metric
    
    Example:
        >>> best = results.get_best_overall(
        ...     primary_metric='sharpe_ratio',
        ...     secondary_metric='total_return_pct',
        ...     min_trades=20
        ... )
        >>> print(f"Best params: {best['params']}")
    """
```

---

## **2️⃣ FILE: modules/optimization/grid_search.py**

### **Purpose**
Perform grid search across parameter space.

### **Class: `GridSearchOptimizer`**

**Constructor:**
```python
def __init__(
    self,
    timeframe: str = '5min',
    initial_capital: float = 10000.0,
    position_size: float = 10000.0,
    transaction_costs: TransactionCosts = None
) -> None:
    """
    Initialize grid search optimizer.
    
    Args:
        timeframe: Timeframe to optimize for
        initial_capital: Starting capital for backtests
        position_size: Fixed position size
        transaction_costs: Transaction cost model (default: 1 pip spread)
    
    Example:
        optimizer = GridSearchOptimizer(
            timeframe='5min',
            initial_capital=10000,
            transaction_costs=TransactionCosts(spread_pips=1.0)
        )
    """
```

**Main Method: Run Grid Search:**
```python
def run_grid_search(
    self,
    data: pd.DataFrame,
    param_grid: Dict[str, List[Any]],
    verbose: bool = True
) -> OptimizationResults:
    """
    Run grid search over parameter combinations.
    
    Args:
        data: Historical data (from load_timeframe_data)
        param_grid: Dictionary defining parameter ranges:
            {
                'sma_fast': [10, 20, 30],
                'sma_slow': [40, 50, 60],
                'rsi_lower': [25, 30, 35],
                'rsi_upper': [65, 70, 75],
                'momentum_threshold': [0.0, 0.0001, 0.0002]
            }
        verbose: If True, print progress during optimization
    
    Returns:
        OptimizationResults object with all tested combinations
    
    Process:
        1. Generate all parameter combinations
        2. For each combination:
           a. Create strategy with these parameters
           b. Generate signals
           c. Run backtest
           d. Store results
        3. Return complete results
    
    Example:
        >>> from modules.data import load_timeframe_data
        >>> 
        >>> df = load_timeframe_data('5min')
        >>> optimizer = GridSearchOptimizer(timeframe='5min')
        >>> 
        >>> param_grid = {
        ...     'sma_fast': [15, 20, 25],
        ...     'sma_slow': [45, 50, 55],
        ...     'rsi_lower': [30],
        ...     'rsi_upper': [70],
        ...     'momentum_threshold': [0.0]
        ... }
        >>> 
        >>> results = optimizer.run_grid_search(df, param_grid)
        >>> print(f"Tested {len(results.results)} combinations")
        >>> 
        >>> # View best results
        >>> best = results.rank_by_metric('sharpe_ratio', top_n=5)
        >>> print(best[['sma_fast', 'sma_slow', 'sharpe_ratio', 'total_return_pct']])
    """
```

**Implementation Details:**

**Step 1: Generate Combinations:**
```python
from itertools import product

# Generate all combinations
param_names = list(param_grid.keys())
param_values = list(param_grid.values())
combinations = list(product(*param_values))

total_combinations = len(combinations)
print(f"Testing {total_combinations} parameter combinations...")
```

**Step 2: Loop Through Combinations:**
```python
results = OptimizationResults()

for i, combo in enumerate(combinations):
    # Create parameter dict
    params = dict(zip(param_names, combo))
    
    # Skip invalid combinations
    if params['sma_fast'] >= params['sma_slow']:
        if verbose:
            print(f"Skipping invalid: fast={params['sma_fast']} >= slow={params['sma_slow']}")
        continue
    
    if verbose and i % 10 == 0:
        print(f"Progress: {i}/{total_combinations} ({i/total_combinations*100:.1f}%)")
    
    # Run backtest with these parameters
    try:
        metrics = self._run_single_backtest(data, params)
        results.add_result(params, metrics, self.timeframe)
    except Exception as e:
        if verbose:
            print(f"Error with params {params}: {e}")
        continue

if verbose:
    print(f"\nCompleted: {len(results.results)} successful backtests")
```

**Helper Method: Single Backtest:**
```python
def _run_single_backtest(
    self,
    data: pd.DataFrame,
    params: Dict[str, Any]
) -> Dict[str, float]:
    """
    Run single backtest with given parameters.
    
    Args:
        data: Historical data
        params: Strategy parameters
    
    Returns:
        Metrics dict from backtest
    """
    from modules.strategy import MARSIMomentumStrategy
    from modules.backtest import BacktestEngine
    
    # Create strategy
    strategy = MARSIMomentumStrategy(
        timeframe=self.timeframe,
        sma_fast=params['sma_fast'],
        sma_slow=params['sma_slow'],
        rsi_lower=params['rsi_lower'],
        rsi_upper=params['rsi_upper'],
        momentum_threshold=params['momentum_threshold']
    )
    
    # Generate signals
    signals = strategy.generate_signals(data)
    
    # Run backtest
    engine = BacktestEngine(
        initial_capital=self.initial_capital,
        position_size=self.position_size,
        transaction_costs=self.transaction_costs
    )
    
    backtest_results = engine.run(data, signals)
    
    return backtest_results['metrics']
```

**Helper: Default Parameter Grid:**
```python
@staticmethod
def get_default_param_grid(timeframe: str = '5min') -> Dict[str, List[Any]]:
    """
    Get reasonable default parameter grid for a timeframe.
    
    Args:
        timeframe: '5min', '4H', or '1D'
    
    Returns:
        Default parameter grid dict
    
    Examples:
        For 5min/4H:
        {
            'sma_fast': [15, 20, 25, 30],
            'sma_slow': [40, 50, 60, 70],
            'rsi_lower': [25, 30, 35],
            'rsi_upper': [65, 70, 75],
            'momentum_threshold': [0.0, 0.00005, 0.0001]
        }
        
        For 1D:
        {
            'sma_fast': [40, 50, 60],
            'sma_slow': [180, 200, 220],
            'rsi_lower': [25, 30, 35],
            'rsi_upper': [65, 70, 75],
            'momentum_threshold': [0.0, 0.0001, 0.0002]
        }
    
    Notes:
        - These are EXAMPLES, not necessarily optimal
        - Covers range around current defaults
        - Adjust based on computational budget
    """
```

---

## **3️⃣ FILE: modules/optimization/__init__.py**

### **Purpose**
Clean package exports.

### **Contents:**
```python
"""
Parameter Optimization Module

Provides grid search and optimization tools for finding better
strategy parameters.

Components:
- GridSearchOptimizer: Systematic parameter grid search
- OptimizationResults: Results storage and ranking

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
        'momentum_threshold': [0.0]
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
    'GridSearchOptimizer',
    'OptimizationResults',
]
```

---

## **🧪 Testing Strategy**

### **Test 1: Small Grid Search (5min)**

```python
from modules.data import load_timeframe_data
from modules.optimization import GridSearchOptimizer

# Load data
df = load_timeframe_data('5min')

# Create optimizer
optimizer = GridSearchOptimizer(timeframe='5min')

# Small test grid (3 × 3 × 1 × 1 × 1 = 9 combinations)
param_grid = {
    'sma_fast': [15, 20, 25],
    'sma_slow': [45, 50, 55],
    'rsi_lower': [30],
    'rsi_upper': [70],
    'momentum_threshold': [0.0]
}

# Run optimization
results = optimizer.run_grid_search(df, param_grid, verbose=True)

print(f"\nTested {len(results.results)} combinations")

# Best by Sharpe
top_sharpe = results.rank_by_metric('sharpe_ratio', top_n=3)
print("\n=== Top 3 by Sharpe Ratio ===")
print(top_sharpe[['sma_fast', 'sma_slow', 'sharpe_ratio', 'total_return_pct', 'num_trades']])

# Best by return
top_return = results.rank_by_metric('total_return_pct', top_n=3)
print("\n=== Top 3 by Return ===")
print(top_return[['sma_fast', 'sma_slow', 'sharpe_ratio', 'total_return_pct', 'num_trades']])

# Statistics
sharpe_stats = results.get_metric_statistics('sharpe_ratio')
print(f"\nSharpe Ratio Statistics:")
print(f"  Range: {sharpe_stats['min']:.2f} to {sharpe_stats['max']:.2f}")
print(f"  Mean: {sharpe_stats['mean']:.2f}")
print(f"  Std: {sharpe_stats['std']:.2f}")
```

### **Test 2: Compare to Baseline**

```python
# Get baseline (current defaults) results
from modules.strategy import MARSIMomentumStrategy
from modules.backtest import BacktestEngine

strategy_baseline = MARSIMomentumStrategy(timeframe='5min')
signals_baseline = strategy_baseline.generate_signals(df)

engine = BacktestEngine(initial_capital=10000, position_size=10000)
baseline_results = engine.run(df, signals_baseline)

baseline_sharpe = baseline_results['metrics']['sharpe_ratio']
baseline_return = baseline_results['metrics']['total_return_pct']

print(f"Baseline (20/50): Sharpe={baseline_sharpe:.2f}, Return={baseline_return:.2f}%")

# Compare with best optimized
best = results.get_best_overall(primary_metric='sharpe_ratio', min_trades=20)
print(f"Best optimized: Sharpe={best['metrics']['sharpe_ratio']:.2f}, "
      f"Return={best['metrics']['total_return_pct']:.2f}%")
print(f"Improvement: {best['metrics']['sharpe_ratio'] - baseline_sharpe:.2f} Sharpe points")
```

### **Test 3: Medium Grid (All Timeframes)**

```python
# Test with default grid (more comprehensive)
for tf in ['5min', '4H', '1D']:
    print(f"\n{'='*50}")
    print(f"Optimizing {tf}")
    print('='*50)
    
    df = load_timeframe_data(tf)
    optimizer = GridSearchOptimizer(timeframe=tf)
    
    # Get default grid for this timeframe
    param_grid = optimizer.get_default_param_grid(tf)
    
    # Show grid size
    grid_size = 1
    for values in param_grid.values():
        grid_size *= len(values)
    print(f"Grid size: {grid_size} combinations")
    
    # Run optimization
    results = optimizer.run_grid_search(df, param_grid, verbose=False)
    
    # Show best result
    best = results.get_best_overall(min_trades=10)
    print(f"\nBest parameters: {best['params']}")
    print(f"Sharpe: {best['metrics']['sharpe_ratio']:.2f}")
    print(f"Return: {best['metrics']['total_return_pct']:.2f}%")
    print(f"Max DD: {best['metrics']['max_drawdown_pct']:.2f}%")
    print(f"Trades: {best['metrics']['num_trades']}")
```

### **Expected Results**

**Optimization may show:**
- Slight improvements over baseline (1-3 Sharpe points)
- Or NO improvement (all parameters negative)
- Different "best" parameters for each timeframe
- High sensitivity to parameter changes

**Important:** If optimization doesn't improve results significantly, that's a VALID finding. It means:
- Strategy fundamentally doesn't work well in this period
- Transaction costs dominate strategy edge
- Need different approach (different strategy type, different asset, etc.)

**For CPF:** Document whatever you find honestly.

---

## **⚠️ Overfitting Warnings**

### **Include These Warnings in Output**

```python
def print_overfitting_warnings(self, results: OptimizationResults) -> None:
    """
    Print warnings about overfitting risks.
    
    Should be called after optimization completes.
    """
    print("\n" + "="*60)
    print("⚠️  OVERFITTING WARNING")
    print("="*60)
    print("These results are optimized to THIS specific historical period.")
    print("Past performance does NOT guarantee future results.")
    print("\nBest practices:")
    print("- Use walk-forward analysis for robustness testing")
    print("- Test on out-of-sample data")
    print("- Consider parameter stability across different periods")
    print("- Prioritize Sharpe ratio over raw returns")
    print("- Require minimum number of trades (20+) for statistical significance")
    print("="*60 + "\n")
```

---

## **📊 Computational Considerations**

### **Grid Size Estimation**

**Small grid:** 3 × 3 × 1 × 1 × 1 = 9 combinations → ~1 minute  
**Medium grid:** 4 × 4 × 3 × 3 × 3 = 432 combinations → ~15 minutes  
**Large grid:** 5 × 5 × 4 × 4 × 5 = 2000 combinations → ~60 minutes

**Recommendation:** Start small (9-27 combinations), then expand if needed.

---

## **🔧 Implementation Notes**

### **Dependencies**
```python
import pandas as pd
import numpy as np
from typing import Any, Dict, List
from itertools import product
import time

from modules.strategy import MARSIMomentumStrategy
from modules.backtest import BacktestEngine, TransactionCosts
```

### **Parameter Validation**
- Skip combinations where sma_fast >= sma_slow
- Skip if rsi_lower >= rsi_upper
- Log skipped combinations if verbose=True

### **Performance Tips**
- Print progress every 10 combinations
- Estimate time remaining
- Catch and log exceptions (don't crash on single failure)

### **Logging**
```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Starting grid search: {total_combinations} combinations")
logger.info(f"Timeframe: {self.timeframe}")
logger.info(f"Completed: {len(results.results)} successful backtests")
```

---

## **📝 Commit Message**

After implementation:

```
Add parameter optimization module (grid search)

- Created GridSearchOptimizer for systematic parameter testing
- Implemented OptimizationResults for ranking and comparison
- Tested with small/medium grids across all timeframes
- Includes overfitting warnings and best practices
- Results can be exported to DataFrame for notebook analysis
- Default parameter grids for each timeframe
```

---

## **✅ Definition of Done**

- [ ] All 3 files created
- [ ] GridSearchOptimizer runs successfully
- [ ] OptimizationResults stores and ranks correctly
- [ ] Tested with small grid (9 combinations)
- [ ] Tested with all three timeframes
- [ ] Comparison to baseline working
- [ ] Overfitting warnings included
- [ ] Type hints on all methods
- [ ] Google docstrings with examples
- [ ] PEP 8 compliant (black formatted)
- [ ] File headers present
- [ ] Committed and pushed to GitHub

---

## **🎯 Ready for Implementation**

**This specification is complete and self-contained.**

**Estimated API cost:** ~$1.00 (8-10 minutes)

**Next step:** Pass this specification to Claude Code (Opus 4.6).

---

**End of Specification 6**

---
