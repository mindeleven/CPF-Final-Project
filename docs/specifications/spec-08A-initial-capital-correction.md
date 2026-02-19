---

# **Specification 8A: Correct Initial Capital to 20,000 EUR (No Leverage)**

**Project:** CPF Final Project - Automated Trading System
**Module:** Optimization, Backtest, Notebook
**Session:** 8A
**Date:** February 19, 2026
**Priority:** HIGH - Numbers in final deliverable must be consistent

---

## Problem

All backtest and optimization results were computed with `initial_capital=10000` and `position_size=20000`, implying 2x leverage. The project design intent is **no leverage**: initial capital equals position size at 20,000 EUR.

This inconsistency affects:

1. **Optimization CSV files** — contain metrics computed with 10K initial capital
2. **Notebook section 6** — code and descriptive text reference 10K initial capital
3. **Backtest CSV files** — Session 5B default-parameter results based on 10K

### Why simple mathematical scaling is insufficient

Changing initial_capital from 10K to 20K while keeping position_size at 20K does not affect absolute dollar P&L (which depends only on position_size). However, two key metrics involve **dividing by equity levels**, which change non-linearly:

- **Sharpe ratio:** Computed from `equity_curve.pct_change()`. Each bar's return is `PnL(t) / equity(t-1)`, where `equity(t-1) = initial_capital + cumPnL(t-1)`. The denominator shifts by a non-constant amount as cumPnL varies over time, so mean and std of returns do not scale by a constant factor.

- **Max drawdown %:** Computed as `(equity - running_max) / running_max`. The peak equity differs (10K+peak_pnl vs 20K+peak_pnl), so percentage drawdown changes non-linearly.

For the 4H strategy with +60.46% return on 10K (cumPnL = $6,046), the non-linear effects are significant. The only correct approach is to **re-run the grid search** with `initial_capital=20000`.

---

## Solution

### Step 1: Regenerate optimization CSV files

Re-run the Session 6B grid search for both timeframes with corrected parameters:

```python
optimizer = GridSearchOptimizer(
    timeframe="5min",
    initial_capital=20000.0,   # was 10000.0
    position_size=20000.0,     # unchanged
    transaction_costs=TransactionCosts(spread_pips=1.0),
)
```

This produces new versions of:

- `data/optimization/optimization_results_5min_corrected.csv` (432 rows)
- `data/optimization/optimization_results_4H_corrected.csv` (432 rows)
- `data/optimization/optimization_comparison_6_vs_6b.csv` (regenerate as comparison table)

### Step 2: Regenerate backtest CSV files

Re-run the Session 5B default-parameter backtests with `initial_capital=20000`:

- `data/backtest/backtest_results_5min_corrected.csv` (trade log)
- `data/backtest/backtest_summary_corrected.csv` (all-timeframe summary)

### Step 3: Update notebook section 6

The file `migration/03-final-deliverable/04-claude-code-files/section-06-backtest-implementation.md` needs targeted edits (not a complete rewrite — the structure, analysis flow, and most prose are sound):

| Section | Change required |
|---------|----------------|
| 6.2 | Change `initial_capital=10000.0` to `20000.0` in engine initialization |
| 6.4 | Change `INITIAL_CAPITAL = 10000.0` to `20000.0`. Remove leverage line (`Leverage: 2.0x`). Update prose about leverage. |
| 6.5 | `INITIAL_CAPITAL` already references the variable — no change needed |
| 6.6 | `INITIAL_CAPITAL` variable reference — no change needed |
| 6.9 | Buy-and-hold comparison uses `INITIAL_CAPITAL` variable — no change needed, but the example output block (the formatted table showing `Final Capital ($) 9,377.10`) must be removed or updated since it implies 10K base |
| 6.10 | CSV `pd.read_csv()` paths need updating to `data/optimization/...` |
| 6.11 | Update the Session 6B results summary table: return percentages change (5min: ~4.1% instead of 8.25%, 4H: ~30.2% instead of 60.46%). Sharpe ratios will change slightly (re-read from new CSVs). Update descriptive text accordingly. |

### Step 4: Update CSV paths in notebook section 6

The `pd.read_csv()` calls currently reference root-relative paths. Update to:

```python
# Old
opt_5min_df = pd.read_csv("optimization_results_5min_corrected.csv")
opt_4h_df = pd.read_csv("optimization_results_4H_corrected.csv")

# New
opt_5min_df = pd.read_csv("data/optimization/optimization_results_5min_corrected.csv")
opt_4h_df = pd.read_csv("data/optimization/optimization_results_4H_corrected.csv")
```

### Step 5: Update CLAUDE.md and MEMORY.md

Update the Session 6B optimization results section with corrected numbers (new Sharpe ratios, return percentages, etc.) once the regeneration is complete.

---

## Files affected

| File | Action |
|------|--------|
| `data/optimization/optimization_results_5min_corrected.csv` | Regenerate with 20K initial |
| `data/optimization/optimization_results_4H_corrected.csv` | Regenerate with 20K initial |
| `data/optimization/optimization_comparison_6_vs_6b.csv` | Regenerate |
| `data/backtest/backtest_results_5min_corrected.csv` | Regenerate with 20K initial |
| `data/backtest/backtest_summary_corrected.csv` | Regenerate with 20K initial |
| `migration/.../section-06-backtest-implementation.md` | Edit sections 6.2, 6.4, 6.9, 6.10, 6.11 |
| `CLAUDE.md` | Update Session 6B results after regeneration |

---

## Expected impact on key results

Based on the non-linear relationship, the exact new numbers will come from the regeneration, but the directional impact is:

- **Sharpe ratios:** Will decrease slightly (returns shrink relative to capital, reducing mean return more than std scales)
- **Total returns:** Will approximately halve (5min: ~4.1%, 4H: ~30.2%)
- **Max drawdown %:** Will approximately halve (smaller percentage of larger capital base)
- **Win rate, profit factor, num_trades, avg_trade_pnl:** Unchanged (depend only on dollar P&L)
- **Best parameter combinations:** May shift slightly due to Sharpe ratio changes, though likely remain the same since the ranking is dominated by large differences

---

**End of Specification 8A**

---
