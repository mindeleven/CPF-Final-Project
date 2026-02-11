---

# **Specification 5B: Position Size Correction**

**Project:** CPF Final Project - Automated Trading System  
**Module:** `modules/backtest/`  
**Session:** 5B (Correction to Session 5)  
**Date:** February 11, 2026  
**Prerequisites:** Session 5 Complete ✅

---

## **🚨 Critical Issue Discovered**

**Problem:** Session 5 used incorrect position size for EUR/USD backtesting.

**Incorrect (Session 5):**
- Position size: 10,000 EUR
- Spread cost per trade: 1 pip × 0.0001 × 10,000 = **$1.00**

**Correct (IBKR Reality):**
- Position size: 20,000 EUR (IBKR minimum for EUR/USD)
- Spread cost per trade: 1 pip × 0.0001 × 20,000 = **$2.00**

**Impact:**
- All transaction costs DOUBLED
- All backtest returns significantly overstated
- Must re-run ALL backtests with corrected position size

---

## **📋 Objective**

**Re-run Session 5 backtest with corrected position size:**

1. Update `position_size` parameter from 10,000 to 20,000 EUR
2. Keep ALL other code identical (no changes to logic)
3. Re-run all three timeframes (5min, 4H, 1D)
4. Document corrected results
5. Verify transaction cost impact is now accurate

**NO CODE CHANGES** - only parameter update in test scripts.

---

## **🔧 What Needs to Change**

### **Test Scripts Only**

**Before (Session 5):**
```python
engine = BacktestEngine(
    initial_capital=10000.0,
    position_size=10000.0,  # ❌ INCORRECT
    transaction_costs=costs
)
```

**After (Session 5B):**
```python
engine = BacktestEngine(
    initial_capital=10000.0,
    position_size=20000.0,  # ✅ CORRECT (IBKR minimum)
    transaction_costs=costs
)
```

**NO changes to:**
- `modules/backtest/engine.py` 
- `modules/backtest/transaction_costs.py`
- `modules/backtest/metrics.py`
- `modules/backtest/__init__.py`

**The code is correct - only the test parameter was wrong.**

---

## **🧪 Testing Protocol**

### **Test 1: Verify Corrected Transaction Costs**

```python
from modules.backtest import TransactionCosts

# Create transaction cost model
costs = TransactionCosts(spread_pips=1.0, commission_pct=0.0)

# Calculate spread cost for CORRECT position size
entry_price = 1.0365
position_size = 20000.0  # ✅ Corrected from 10,000
direction = 1

spread_cost = costs.calculate_spread_cost(entry_price, position_size, direction)
print(f"Spread cost per trade: ${spread_cost:.2f}")
# Expected: $2.00 (was $1.00 in Session 5)

# Verify formula
manual_cost = 1.0 * 0.0001 * 20000  # spread_pips * pip_value * size
print(f"Manual verification: ${manual_cost:.2f}")
assert abs(spread_cost - manual_cost) < 0.01, "Cost calculation mismatch!"
```

**Expected Output:**
```
Spread cost per trade: $2.00
Manual verification: $2.00
```

---

### **Test 2: Re-run 5min Backtest (Corrected)**

```python
from modules.data import load_timeframe_data
from modules.strategy import MARSIMomentumStrategy
from modules.backtest import BacktestEngine, TransactionCosts

# Load data
df = load_timeframe_data('5min')
print(f"Loaded {len(df)} bars of 5min data")

# Generate signals
strategy = MARSIMomentumStrategy(timeframe='5min')
signals = strategy.generate_signals(df)
print(f"Generated {(signals['signal'] != 0).sum()} signals")

# Configure backtest with CORRECTED position size
costs = TransactionCosts(spread_pips=1.0, commission_pct=0.0)
engine = BacktestEngine(
    initial_capital=10000.0,
    position_size=20000.0,  # ✅ CORRECTED from 10,000
    transaction_costs=costs
)

# Run backtest
results = engine.run(df, signals)

# Display results
print("\n=== CORRECTED Backtest Results (5min) ===")
print(f"Total Return: {results['metrics']['total_return_pct']:.2f}%")
print(f"Sharpe Ratio: {results['metrics']['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['metrics']['max_drawdown_pct']:.2f}%")
print(f"Win Rate: {results['metrics']['win_rate']*100:.1f}%")
print(f"Profit Factor: {results['metrics']['profit_factor']:.2f}")
print(f"Number of Trades: {results['metrics']['num_trades']}")
print(f"Avg Trade P&L: ${results['metrics']['avg_trade_pnl']:.2f}")
print(f"Final Capital: ${results['final_capital']:.2f}")

# Save results for documentation
trades_df = results['trades']
trades_df.to_csv('backtest_results_5min_corrected.csv', index=False)
print(f"\nTrades saved to backtest_results_5min_corrected.csv")
```

**Expected Results (Approximate):**
- **Total Return:** -6% to -8% (was -3.11% with wrong position size)
- **Transaction Cost Impact:** ~$278 total (139 trades × $2.00 per trade)
- **Sharpe Ratio:** More negative than Session 5
- **Number of Trades:** Same (139 trades)

---

### **Test 3: Re-run All Timeframes (Corrected)**

```python
print("\n=== RE-RUNNING ALL TIMEFRAMES WITH CORRECTED POSITION SIZE ===\n")

results_summary = []

for tf in ['5min', '4H', '1D']:
    print(f"\n--- {tf} Backtest (Corrected) ---")
    
    # Load and generate signals
    df = load_timeframe_data(tf)
    strategy = MARSIMomentumStrategy(timeframe=tf)
    signals = strategy.generate_signals(df)
    
    # Run backtest with CORRECTED position size
    costs = TransactionCosts(spread_pips=1.0)
    engine = BacktestEngine(
        initial_capital=10000.0,
        position_size=20000.0,  # ✅ CORRECTED
        transaction_costs=costs
    )
    results = engine.run(df, signals)
    
    # Display
    metrics = results['metrics']
    print(f"Bars: {len(df)}")
    print(f"Signals: {(signals['signal'] != 0).sum()}")
    print(f"Trades: {metrics['num_trades']}")
    print(f"Return: {metrics['total_return_pct']:.2f}%")
    print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
    print(f"Max DD: {metrics['max_drawdown_pct']:.2f}%")
    print(f"Win Rate: {metrics['win_rate']*100:.1f}%")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    
    # Save to summary
    results_summary.append({
        'Timeframe': tf,
        'Bars': len(df),
        'Signals': (signals['signal'] != 0).sum(),
        'Trades': metrics['num_trades'],
        'Return (%)': metrics['total_return_pct'],
        'Sharpe': metrics['sharpe_ratio'],
        'Max DD (%)': metrics['max_drawdown_pct'],
        'Win Rate (%)': metrics['win_rate'] * 100,
        'Profit Factor': metrics['profit_factor']
    })

# Create comparison table
import pandas as pd
summary_df = pd.DataFrame(results_summary)
print("\n=== CORRECTED BACKTEST SUMMARY ===")
print(summary_df.to_string(index=False))

# Save summary
summary_df.to_csv('backtest_summary_corrected.csv', index=False)
print("\nSummary saved to backtest_summary_corrected.csv")
```

**Expected Output:**
```
=== CORRECTED BACKTEST SUMMARY ===
Timeframe  Bars  Signals  Trades  Return (%)  Sharpe  Max DD (%)  Win Rate (%)  Profit Factor
     5min  8372      139     139       -6.50   -4.20       -8.00          33.8           0.65
       4H  5421       76      76      -35.00   -1.20      -40.00          38.2           0.45
       1D   776        3       3      -40.00   -1.50      -42.00           0.0           0.00
```

*(Actual numbers will vary slightly - these are estimates)*

---

### **Test 4: Transaction Cost Impact Analysis (Corrected)**

```python
print("\n=== TRANSACTION COST IMPACT (Corrected Position Size) ===\n")

df = load_timeframe_data('5min')
strategy = MARSIMomentumStrategy(timeframe='5min')
signals = strategy.generate_signals(df)

# Test different spread levels
spreads = [0.0, 1.0, 3.0]
cost_impact = []

for spread in spreads:
    costs = TransactionCosts(spread_pips=spread)
    engine = BacktestEngine(
        initial_capital=10000.0,
        position_size=20000.0,  # ✅ CORRECTED
        transaction_costs=costs
    )
    results = engine.run(df, signals)
    
    return_pct = results['metrics']['total_return_pct']
    num_trades = results['metrics']['num_trades']
    total_cost = spread * 0.0001 * 20000 * num_trades * 2  # 2x for entry+exit
    
    cost_impact.append({
        'Spread (pips)': spread,
        'Return (%)': return_pct,
        'Total Cost ($)': total_cost,
        'Cost per Trade ($)': spread * 0.0001 * 20000 * 2
    })
    
    print(f"{spread} pips: Return = {return_pct:.2f}%, "
          f"Total Cost = ${total_cost:.2f}")

# Create comparison
cost_df = pd.DataFrame(cost_impact)
print("\n=== COST IMPACT TABLE ===")
print(cost_df.to_string(index=False))
```

**Expected Output:**
```
=== TRANSACTION COST IMPACT (Corrected Position Size) ===

0.0 pips: Return = -0.50%, Total Cost = $0.00
1.0 pips: Return = -6.50%, Total Cost = $556.00
3.0 pips: Return = -18.00%, Total Cost = $1668.00

=== COST IMPACT TABLE ===
Spread (pips)  Return (%)  Total Cost ($)  Cost per Trade ($)
          0.0       -0.50            0.00                 0.00
          1.0       -6.50          556.00                 4.00
          3.0      -18.00         1668.00                12.00
```

**Key Finding:** 
- With 139 trades and 20,000 EUR position size:
- 1 pip spread costs: **$4.00 per round-trip** (entry $2 + exit $2)
- Total cost for 139 trades: **$556** (was $139 in Session 5)

---

### **Test 5: Manual P&L Verification (Corrected)**

```python
print("\n=== MANUAL P&L VERIFICATION ===\n")

# Re-run 5min backtest
df = load_timeframe_data('5min')
strategy = MARSIMomentumStrategy(timeframe='5min')
signals = strategy.generate_signals(df)

costs = TransactionCosts(spread_pips=1.0)
engine = BacktestEngine(
    initial_capital=10000.0,
    position_size=20000.0,  # ✅ CORRECTED
    transaction_costs=costs
)
results = engine.run(df, signals)

# Get first trade
first_trade = results['trades'].iloc[0]

print("First Trade Details:")
print(f"Direction: {first_trade['direction']}")
print(f"Entry: {first_trade['entry_price']:.4f}")
print(f"Exit: {first_trade['exit_price']:.4f}")
print(f"Size: 20,000 EUR")

# Manual calculation
entry_price = first_trade['entry_price']
exit_price = first_trade['exit_price']
direction = 1 if first_trade['direction'] == 'LONG' else -1
size = 20000.0  # ✅ CORRECTED

# Gross P&L
gross_pnl = direction * (exit_price - entry_price) * size
print(f"\nGross P&L: ${gross_pnl:.2f}")

# Transaction costs
entry_cost = 1.0 * 0.0001 * 20000  # $2.00
exit_cost = 1.0 * 0.0001 * 20000   # $2.00
total_cost = entry_cost + exit_cost
print(f"Entry cost: ${entry_cost:.2f}")
print(f"Exit cost: ${exit_cost:.2f}")
print(f"Total cost: ${total_cost:.2f}")

# Net P&L
net_pnl = gross_pnl - total_cost
print(f"\nNet P&L (manual): ${net_pnl:.2f}")
print(f"Net P&L (engine): ${first_trade['net_pnl']:.2f}")

# Verify match
match = abs(net_pnl - first_trade['net_pnl']) < 0.01
print(f"\nVerification: {'✅ PASS' if match else '❌ FAIL'}")
assert match, "P&L calculation mismatch!"
```

**Expected Output:**
```
=== MANUAL P&L VERIFICATION ===

First Trade Details:
Direction: LONG
Entry: 1.0365
Exit: 1.0352
Size: 20,000 EUR

Gross P&L: $-26.00
Entry cost: $2.00
Exit cost: $2.00
Total cost: $4.00

Net P&L (manual): $-30.00
Net P&L (engine): $-30.00

Verification: ✅ PASS
```

---

## **📊 Expected Results Comparison**

### **Session 5 (INCORRECT) vs Session 5B (CORRECTED)**

| Metric | Session 5 (10K EUR) | Session 5B (20K EUR) | Change |
|--------|---------------------|----------------------|--------|
| **5min Return** | -3.11% | -6.50% | -3.39% |
| **5min Sharpe** | -3.36 | -4.20 | -0.84 |
| **5min Max DD** | -4.15% | -8.00% | -3.85% |
| **Cost per Trade** | $2.00 | $4.00 | +100% |
| **Total 5min Cost** | $278 | $556 | +100% |

**4H Timeframe:**
| Metric | Session 5 | Session 5B | Change |
|--------|-----------|------------|--------|
| Return | -20.79% | -35.00% | -14.21% |
| Sharpe | -0.93 | -1.20 | -0.27 |
| Max DD | -24.57% | -40.00% | -15.43% |

**1D Timeframe:**
| Metric | Session 5 | Session 5B | Change |
|--------|-----------|------------|--------|
| Return | -20.78% | -40.00% | -19.22% |

**Key Finding:** Transaction costs doubled, returns roughly halved (more negative).

---

## **📝 Documentation Updates Needed**

After Session 5B completion, update:

1. **Session 5 handoff document** - note correction
2. **Project progress** - update backtest results
3. **Main notebook** - use Session 5B results
4. **Session 6 optimization** - may need to re-run with corrected position size

---

## **✅ Definition of Done**

- [ ] All test scripts updated with position_size=20000.0
- [ ] All 3 timeframes re-run (5min, 4H, 1D)
- [ ] Transaction cost verification confirms $2.00/trade
- [ ] Manual P&L verification passes
- [ ] Results saved to CSV files
- [ ] Comparison table created (Session 5 vs 5B)
- [ ] Session 5 handoff updated with correction note
- [ ] Ready for Session 6 optimization (with corrected position size)

---

## **🎯 Implementation Steps for Claude Code**

1. **Run Test 1:** Verify corrected transaction costs ($2.00/trade)
2. **Run Test 2:** Complete 5min backtest with corrected size
3. **Run Test 3:** All three timeframes with corrected size
4. **Run Test 4:** Cost impact analysis
5. **Run Test 5:** Manual P&L verification
6. **Generate comparison table:** Session 5 vs 5B results
7. **Save all outputs:** CSVs for documentation

**NO CODE MODIFICATIONS** - only parameter changes in test scripts.

---

## **⚠️ Critical Note**

**This correction is essential for academic integrity.**

Using the wrong position size would mean:
- Overstating backtest performance by ~100%
- Live trading results would NOT match backtest
- Loss of credibility with professor/reviewers

**Better to correct now than explain discrepancy later.**

---

## **💰 Estimated Cost**

- **API Time:** ~3-5 minutes (simple parameter change + re-run tests)
- **Cost:** ~$0.30-0.50
- **Value:** Fixes fundamental error in entire project

---

## **📌 After Session 5B**

**Next Session (6) Decision:**

- **Option A:** Re-run Session 6 optimization with corrected position size
- **Option B:** Proceed to Session 7 (live trading) with corrected position size
- **Recommendation:** Re-run Session 6 (quick, ensures optimization is valid)

---

## **🎯 Ready for Implementation**

**This specification is complete and ready for Claude Code.**

**Pass this spec to Claude Code (Opus 4.6) to execute the correction.**

---

**End of Specification 5B**

---
