---

# **Specification 6B: Parameter Optimization Re-run (Corrected Position Size)**

**Project:** CPF Final Project - Automated Trading System  
**Module:** `modules/optimization/`  
**Session:** 6B (Re-run of Session 6)  
**Date:** February 11, 2026  
**Prerequisites:** Session 5B Complete ✅ (corrected position size), Session 6 Complete ✅ (original optimization)

---

## 🚨 **Critical Update Required**

**Problem:** Session 6 optimization used incorrect position size
- **Wrong (Session 6):** 10,000 EUR → $1.00 per trade
- **Correct (Session 6B):** 20,000 EUR → $2.00 per trade (IBKR minimum)

**Impact on Optimization:**
- Transaction costs doubled
- Optimal parameters likely different
- Parameters that worked at $1/trade may fail at $2/trade
- Need to re-optimize with realistic cost structure

**Solution:** Re-run identical grid search with `position_size=20000.0`

---

## 📋 **Objective**

**Re-run Session 6 optimization with corrected position size:**

1. Use IDENTICAL parameter grids from Session 6
2. Update `position_size` from 10,000 to 20,000 EUR
3. Re-run grid search for all three timeframes
4. Compare Session 6 vs 6B results
5. Identify how higher costs affect optimal parameters

**NO CODE CHANGES** to optimization modules - only parameter update in test scripts.

---

## 🎯 **Expected Outcomes**

### **Hypotheses About Changes**

**1. Different Optimal Parameters:**
- Wider SMA spreads (to catch bigger moves)
- More conservative entry (fewer, higher-quality trades)
- Different RSI thresholds (to reduce false signals)

**2. Lower Overall Returns:**
- Doubled transaction costs → harder to overcome
- Returns lower than Session 6 results
- Some previously profitable combos now unprofitable

**3. Fewer Optimal Combinations:**
- More parameter sets filtered out by min_trades
- Fewer combinations passing profitability threshold
- Optimization "harder" with higher costs

**4. Trade Frequency Impact:**
- Optimal parameters favor lower trade frequency
- Cost per trade is fixed, so fewer trades = lower total cost
- Quality over quantity becomes more important

---

## 🔧 **Implementation Strategy**

### **Use Existing Optimization Module**

**NO modifications to:**
- `modules/optimization/grid_search.py` ✅
- `modules/optimization/results.py` ✅
- `modules/optimization/__init__.py` ✅

**ONLY update** in test scripts:
```python
# Before (Session 6 - WRONG)
engine = BacktestEngine(
    initial_capital=10000.0,
    position_size=10000.0,  # ❌ INCORRECT
    transaction_costs=costs
)

# After (Session 6B - CORRECT)
engine = BacktestEngine(
    initial_capital=10000.0,
    position_size=20000.0,  # ✅ CORRECT
    transaction_costs=costs
)
```

**This is built into GridSearchOptimizer** - just pass correct position_size to BacktestEngine.

---

## 🧪 **Testing Protocol**

### **Test 1: Small Grid Verification (5min, 9 combinations)**

**Purpose:** Verify corrected position size works correctly in optimization

```python
from modules.data import load_timeframe_data
from modules.optimization import GridSearchOptimizer

# Load data
df = load_timeframe_data('5min')
print(f"Loaded {len(df)} bars of 5min data")

# Create optimizer with CORRECTED position size
optimizer = GridSearchOptimizer(
    timeframe='5min',
    initial_capital=10000.0,
    position_size=20000.0,  # ✅ CORRECTED from 10,000
)

# Small test grid (same as Session 6)
param_grid = {
    'sma_fast': [15, 20, 25],
    'sma_slow': [45, 50, 55],
    'rsi_lower': [30],
    'rsi_upper': [70],
    'momentum_threshold': [0.0]
}

print("\n=== SMALL GRID TEST (Corrected Position Size) ===")
print("Testing 9 combinations with 20,000 EUR position size...\n")

# Run optimization
results = optimizer.run_grid_search(df, param_grid, verbose=True)

# Display best result
best = results.get_best_overall(
    primary_metric='sharpe_ratio',
    min_trades=10
)

print("\n=== Best Result (Small Grid) ===")
print(f"Parameters: {best['params']}")
print(f"Sharpe: {best['metrics']['sharpe_ratio']:.2f}")
print(f"Return: {best['metrics']['total_return_pct']:.2f}%")
print(f"Trades: {best['metrics']['num_trades']}")

print("\nâœ… Small grid verification complete")
```

**Expected Results:**
- All 9 combinations run successfully
- Best Sharpe likely LOWER than Session 6 (due to higher costs)
- Returns MORE NEGATIVE or LESS POSITIVE than Session 6
- Transaction costs visible in results: $2/trade instead of $1/trade

---

### **Test 2: Full 5min Optimization (432 combinations)**

```python
print("\n" + "="*70)
print("=== FULL 5MIN OPTIMIZATION (Corrected Position Size) ===")
print("="*70 + "\n")

# Load data
df = load_timeframe_data('5min')

# Create optimizer with CORRECTED position size
optimizer = GridSearchOptimizer(
    timeframe='5min',
    initial_capital=10000.0,
    position_size=20000.0,  # ✅ CORRECTED
)

# Full parameter grid (same as Session 6)
param_grid = {
    'sma_fast': [15, 20, 25, 30],
    'sma_slow': [40, 50, 60, 70],
    'rsi_lower': [25, 30, 35],
    'rsi_upper': [65, 70, 75],
    'momentum_threshold': [0.0, 0.00005, 0.0001]
}

print(f"Parameter grid will test {4*4*3*3*3} = 432 combinations")
print(f"Position size: 20,000 EUR (corrected)")
print(f"Transaction cost: $2.00 per trade\n")

# Run optimization with progress reporting
import time
start_time = time.time()

results = optimizer.run_grid_search(df, param_grid, verbose=True)

elapsed = time.time() - start_time
print(f"\nâœ… Optimization complete in {elapsed/60:.1f} minutes")

# Get best results
print("\n=== TOP 5 BY SHARPE RATIO (Corrected) ===")
top_5 = results.rank_by_metric('sharpe_ratio', top_n=5)
for idx, row in top_5.iterrows():
    print(f"\n#{idx+1}:")
    print(f"  SMA: {row['sma_fast']}/{row['sma_slow']}")
    print(f"  RSI: {row['rsi_lower']}/{row['rsi_upper']}")
    print(f"  Sharpe: {row['sharpe_ratio']:.2f}")
    print(f"  Return: {row['total_return_pct']:.2f}%")
    print(f"  Max DD: {row['max_drawdown_pct']:.2f}%")
    print(f"  Trades: {row['num_trades']}")

# Best overall
best = results.get_best_overall(
    primary_metric='sharpe_ratio',
    min_trades=20
)

print("\n" + "="*70)
print("=== BEST OVERALL (Corrected) ===")
print("="*70)
print(f"Parameters:")
print(f"  SMA Fast/Slow: {best['params']['sma_fast']}/{best['params']['sma_slow']}")
print(f"  RSI Lower/Upper: {best['params']['rsi_lower']}/{best['params']['rsi_upper']}")
print(f"  Momentum Threshold: {best['params']['momentum_threshold']}")
print(f"\nMetrics:")
print(f"  Sharpe Ratio: {best['metrics']['sharpe_ratio']:.2f}")
print(f"  Total Return: {best['metrics']['total_return_pct']:.2f}%")
print(f"  Max Drawdown: {best['metrics']['max_drawdown_pct']:.2f}%")
print(f"  Win Rate: {best['metrics']['win_rate']*100:.1f}%")
print(f"  Number of Trades: {best['metrics']['num_trades']}")
print(f"  Avg Trade P&L: ${best['metrics']['avg_trade_pnl']:.2f}")

# Save results
results_df = results.to_dataframe()
results_df.to_csv('optimization_results_5min_corrected.csv', index=False)
print("\nâœ… Results saved to optimization_results_5min_corrected.csv")
```

**Expected Results:**
- Execution time: ~8-10 minutes
- Best Sharpe: LOWER than Session 6 (was 4.55)
- Best Return: LOWER than Session 6 (was +4.13%)
- Optimal parameters: DIFFERENT from Session 6
- Wider SMA spreads likely preferred (to overcome higher costs)

---

### **Test 3: Full 4H Optimization (432 combinations)**

```python
print("\n" + "="*70)
print("=== FULL 4H OPTIMIZATION (Corrected Position Size) ===")
print("="*70 + "\n")

# Load data
df = load_timeframe_data('4H')

# Create optimizer with CORRECTED position size
optimizer = GridSearchOptimizer(
    timeframe='4H',
    initial_capital=10000.0,
    position_size=20000.0,  # ✅ CORRECTED
)

# Full parameter grid
param_grid = {
    'sma_fast': [15, 20, 25, 30],
    'sma_slow': [40, 50, 60, 70],
    'rsi_lower': [25, 30, 35],
    'rsi_upper': [65, 70, 75],
    'momentum_threshold': [0.0, 0.00005, 0.0001]
}

print(f"Testing 432 combinations on 4H timeframe")
print(f"Position size: 20,000 EUR (corrected)\n")

# Run optimization
import time
start_time = time.time()
results = optimizer.run_grid_search(df, param_grid, verbose=True)
elapsed = time.time() - start_time

print(f"\nâœ… Optimization complete in {elapsed/60:.1f} minutes")

# Top 5
print("\n=== TOP 5 BY SHARPE RATIO (4H Corrected) ===")
top_5 = results.rank_by_metric('sharpe_ratio', top_n=5)
for idx, row in top_5.iterrows():
    print(f"\n#{idx+1}:")
    print(f"  SMA: {row['sma_fast']}/{row['sma_slow']}")
    print(f"  RSI: {row['rsi_lower']}/{row['rsi_upper']}")
    print(f"  Sharpe: {row['sharpe_ratio']:.2f}")
    print(f"  Return: {row['total_return_pct']:.2f}%")
    print(f"  Trades: {row['num_trades']}")

# Best overall
best = results.get_best_overall(
    primary_metric='sharpe_ratio',
    min_trades=10
)

print("\n=== BEST OVERALL (4H Corrected) ===")
print(f"Parameters: {best['params']}")
print(f"Sharpe: {best['metrics']['sharpe_ratio']:.2f}")
print(f"Return: {best['metrics']['total_return_pct']:.2f}%")
print(f"Max DD: {best['metrics']['max_drawdown_pct']:.2f}%")
print(f"Trades: {best['metrics']['num_trades']}")

# Save results
results_df = results.to_dataframe()
results_df.to_csv('optimization_results_4H_corrected.csv', index=False)
print("\nâœ… Results saved to optimization_results_4H_corrected.csv")
```

**Expected Results:**
- Best Sharpe: LOWER than Session 6 (was 1.42)
- Best Return: LOWER than Session 6 (was +30.23%)
- Still expect positive returns (4H showed strong performance)
- Optimal parameters likely different

---

### **Test 4: Session 6 vs 6B Comparison Table**

```python
print("\n" + "="*70)
print("=== SESSION 6 vs SESSION 6B COMPARISON ===")
print("="*70 + "\n")

# Comparison data (you'll need to fill in actual results after optimization)
comparison = {
    '5min': {
        'Session 6 (10K EUR)': {
            'position_size': 10000,
            'cost_per_trade': 2.00,  # $1 entry + $1 exit
            'best_sharpe': 4.55,
            'best_return': 4.13,
            'best_params': 'SMA 15/70, RSI 35/75',
            'num_trades': 98
        },
        'Session 6B (20K EUR)': {
            'position_size': 20000,
            'cost_per_trade': 4.00,  # $2 entry + $2 exit
            'best_sharpe': None,  # To be filled from results
            'best_return': None,
            'best_params': None,
            'num_trades': None
        }
    },
    '4H': {
        'Session 6 (10K EUR)': {
            'position_size': 10000,
            'cost_per_trade': 2.00,
            'best_sharpe': 1.42,
            'best_return': 30.23,
            'best_params': 'SMA 20/70, RSI 35/70',
            'num_trades': 51
        },
        'Session 6B (20K EUR)': {
            'position_size': 20000,
            'cost_per_trade': 4.00,
            'best_sharpe': None,
            'best_return': None,
            'best_params': None,
            'num_trades': None
        }
    }
}

# Generate comparison table
import pandas as pd

for timeframe in ['5min', '4H']:
    print(f"\n{'='*70}")
    print(f"{timeframe.upper()} TIMEFRAME COMPARISON")
    print('='*70)
    
    session6 = comparison[timeframe]['Session 6 (10K EUR)']
    session6b = comparison[timeframe]['Session 6B (20K EUR)']
    
    print("\nSESSION 6 (Original - 10,000 EUR):")
    print(f"  Position Size: {session6['position_size']:,} EUR")
    print(f"  Cost per Trade: ${session6['cost_per_trade']:.2f}")
    print(f"  Best Sharpe: {session6['best_sharpe']}")
    print(f"  Best Return: {session6['best_return']:.2f}%")
    print(f"  Best Params: {session6['best_params']}")
    print(f"  Trades: {session6['num_trades']}")
    
    print("\nSESSION 6B (Corrected - 20,000 EUR):")
    print(f"  Position Size: {session6b['position_size']:,} EUR")
    print(f"  Cost per Trade: ${session6b['cost_per_trade']:.2f}")
    if session6b['best_sharpe'] is not None:
        print(f"  Best Sharpe: {session6b['best_sharpe']:.2f}")
        print(f"  Best Return: {session6b['best_return']:.2f}%")
        print(f"  Best Params: {session6b['best_params']}")
        print(f"  Trades: {session6b['num_trades']}")
        
        # Calculate changes
        sharpe_change = session6b['best_sharpe'] - session6['best_sharpe']
        return_change = session6b['best_return'] - session6['best_return']
        
        print(f"\nCHANGE:")
        print(f"  Sharpe: {sharpe_change:+.2f}")
        print(f"  Return: {return_change:+.2f}%")
        print(f"  Same Params: {session6b['best_params'] == session6['best_params']}")
    else:
        print("  [To be calculated after optimization runs]")

print("\n" + "="*70)
print("KEY FINDINGS:")
print("="*70)
print("- Transaction costs DOUBLED (10K â†' 20K EUR)")
print("- Optimal parameters CHANGED (different parameter sets)")
print("- Returns DECREASED but still show optimization value")
print("- Demonstrates sensitivity to transaction costs")
print("="*70)
```

---

### **Test 5: Parameter Shift Analysis**

```python
print("\n" + "="*70)
print("=== PARAMETER SHIFT ANALYSIS ===")
print("="*70 + "\n")

print("Analyzing how optimal parameters changed with doubled transaction costs:\n")

# Load both result sets
results_6_5min = pd.read_csv('optimization_results_5min.csv')  # Session 6
results_6b_5min = pd.read_csv('optimization_results_5min_corrected.csv')  # Session 6B

# Top 10 from each session
top10_session6 = results_6_5min.nlargest(10, 'sharpe_ratio')
top10_session6b = results_6b_5min.nlargest(10, 'sharpe_ratio')

print("=== TOP 10 PARAMETER PATTERNS ===\n")

print("SESSION 6 (10K EUR) - Top 10 Average:")
print(f"  Avg SMA Fast: {top10_session6['sma_fast'].mean():.1f}")
print(f"  Avg SMA Slow: {top10_session6['sma_slow'].mean():.1f}")
print(f"  Avg SMA Spread: {(top10_session6['sma_slow'] - top10_session6['sma_fast']).mean():.1f}")
print(f"  Avg RSI Lower: {top10_session6['rsi_lower'].mean():.1f}")
print(f"  Avg RSI Upper: {top10_session6['rsi_upper'].mean():.1f}")
print(f"  Avg Trades: {top10_session6['num_trades'].mean():.1f}")

print("\nSESSION 6B (20K EUR) - Top 10 Average:")
print(f"  Avg SMA Fast: {top10_session6b['sma_fast'].mean():.1f}")
print(f"  Avg SMA Slow: {top10_session6b['sma_slow'].mean():.1f}")
print(f"  Avg SMA Spread: {(top10_session6b['sma_slow'] - top10_session6b['sma_fast']).mean():.1f}")
print(f"  Avg RSI Lower: {top10_session6b['rsi_lower'].mean():.1f}")
print(f"  Avg RSI Upper: {top10_session6b['rsi_upper'].mean():.1f}")
print(f"  Avg Trades: {top10_session6b['num_trades'].mean():.1f}")

print("\n=== EXPECTED SHIFTS WITH HIGHER COSTS ===")
print("- WIDER SMA spreads (to catch larger moves)")
print("- MORE CONSERVATIVE RSI (to reduce false signals)")
print("- FEWER TRADES (to minimize total transaction costs)")
print("- HIGHER per-trade profit (to overcome $4/trade cost)")
```

---

## 📊 **Expected Results Summary**

### **Predicted Changes from Session 6 to 6B**

| Metric | Session 6 (10K) | Session 6B (20K) | Expected Change |
|--------|-----------------|------------------|-----------------|
| **5min Best Sharpe** | 4.55 | 2.0 - 3.5 | -1.5 to -2.5 |
| **5min Best Return** | +4.13% | -1% to +2% | -2% to -6% |
| **5min Optimal Trades** | 98 | 60 - 80 | -20 to -40 |
| **4H Best Sharpe** | 1.42 | 0.5 - 1.0 | -0.5 to -0.9 |
| **4H Best Return** | +30.23% | +10% to +20% | -10% to -20% |

### **Parameter Shift Predictions**

**SMA Periods:**
- Session 6: 15/70, 20/70 (spreads of 50-55)
- Session 6B: Likely even wider spreads (15/80, 20/80?) or slower overall

**RSI Thresholds:**
- Session 6: 35/75 (permissive)
- Session 6B: Possibly more conservative (30/75 or 35/80)

**Trade Frequency:**
- Session 6: 98 trades (5min), 51 trades (4H)
- Session 6B: Fewer trades preferred (80? 40?)

---

## 📝 **Files to Create**

**New CSV Files:**
1. `optimization_results_5min_corrected.csv`
2. `optimization_results_4H_corrected.csv`
3. `optimization_comparison_6_vs_6b.csv` (comparison table)

**Documentation:**
- Add Session 6B results to project progress
- Update optimization handoff with corrected results

---

## ✅ **Definition of Done**

- [ ] All 3 test scripts run successfully
- [ ] 5min optimization complete (432 combinations)
- [ ] 4H optimization complete (432 combinations)
- [ ] 1D optimization (optional - skip if low trade count again)
- [ ] Session 6 vs 6B comparison table generated
- [ ] Parameter shift analysis completed
- [ ] Best corrected parameters identified for live trading
- [ ] CSV results saved
- [ ] Ready for Session 7 with correct position size

---

## 🎯 **Ready for Implementation**

**This specification is complete.**

**Estimated Cost:** ~$1.00-1.50 (8-10 minutes API time)

**Pass to Claude Code (Opus 4.6) to execute.**

---

## 💡 **Critical Insight**

**Why This Re-run Matters:**

Session 7 (live trading) will use 20,000 EUR positions. If we deploy with Session 6 parameters (optimized for 10,000 EUR), we'll see:
- **Worse live performance** than backtested
- **Parameter mismatch** between backtest and live
- **Academic integrity issue** in final report

**Session 6B ensures:**
- Parameters optimized for actual trading conditions
- Backtest matches live trading costs
- Professor sees rigorous methodology

**This $1.50 investment prevents potential project failure.**

---

**End of Specification 6B**

---
