
---

# **SESSION 8A HANDOFF: Initial Capital Correction (10K → 20K)**

**Date:** February 19, 2026
**Model:** Claude Code Opus 4.6
**Specification:** `docs/specifications/spec-08A-initial-capital-correction.md`
**Status:** Complete

---

## Problem

All optimization and backtest CSV files were generated with `initial_capital=10000`
and `position_size=20000`, implying 2x leverage. The project requirement is no
leverage: initial capital should equal position size at 20,000 EUR.

### Why Simple Scaling Fails

In Session 6B we discovered that changing **position_size** produces linear scaling
(Sharpe invariant, returns double). However, changing **initial_capital** is
different — it shifts the equity curve baseline, which affects:

- **`sharpe_ratio`**: computed from `equity_curve.pct_change()` — percentage
  changes depend on equity level (non-linear denominator)
- **`max_drawdown_pct`**: computed as `(equity - peak) / peak` — peak values
  shift with initial capital (non-linear denominator)

Columns that do scale exactly: `total_return_pct` halves, `final_capital` shifts
by +10000, `avg_trade_pnl` / `win_rate` / `profit_factor` / `num_trades` unchanged.

Conclusion: full grid search re-run required.

---

## What Changed

### 1. CSV Files Moved (committed separately in `a77d2a0`)

Five CSV files moved from project root to organized subdirectories:

| File | Destination |
|------|-------------|
| `backtest_results_5min_corrected.csv` | `data/backtest/` |
| `backtest_summary_corrected.csv` | `data/backtest/` |
| `optimization_results_5min_corrected.csv` | `data/optimization/` |
| `optimization_results_4H_corrected.csv` | `data/optimization/` |
| `optimization_comparison_6_vs_6b.csv` | `data/optimization/` |

### 2. Full Grid Search Re-run

Created `scripts/regenerate_results_20k.py` — runs optimization (432 combinations
each for 5min and 4H) and default-parameter backtests for all three timeframes.
Total runtime: ~242 seconds.

### 3. Regenerated Results

**Optimization (best by Sharpe):**

| Timeframe | SMA Fast/Slow | RSI Lower/Upper | Mom | Sharpe | Return | Trades |
|-----------|---------------|-----------------|-----|--------|--------|--------|
| 5min | 15 / 70 | 35 / 75 | 0.0 | 4.55 | +4.13% | 107 |
| 4H | 20 / 70 | 35 / 70 | 0.0 | 1.42 | +30.23% | 45 |

Optimal parameters are **identical** to Session 6B — only Sharpe and return
percentages changed as expected (returns halved from 2x leverage to 1x).

**Default-parameter backtests (all timeframes):**

| Timeframe | Bars | Trades | Return (%) | Sharpe | Max DD (%) | Win Rate (%) |
|-----------|------|--------|------------|--------|------------|--------------|
| 5min | 8372 | 139 | -3.11 | -3.36 | -4.15 | 33.8 |
| 4H | 5421 | 76 | -20.79 | -0.93 | -24.57 | 38.2 |
| 1D | 776 | 3 | -20.78 | -1.03 | -23.00 | 0.0 |

### 4. Notebook Section 6 Updated

File: `migration/03-final-deliverable/04-claude-code-files/section-06-backtest-implementation.md`
(gitignored — managed separately)

Sections updated:
- **6.2**: `initial_capital=10000.0` → `20000.0`
- **6.4**: `INITIAL_CAPITAL = 10000.0` → `20000.0`, removed leverage text
- **6.4 prose**: Replaced leverage explanation with no-leverage explanation
- **6.10**: CSV paths updated to `data/optimization/...`
- **6.11**: Sharpe 4.59→4.55, Return +8.25%→+4.13%, +60.46%→+30.23%
- **Closing paragraph**: Sharpe reference updated to 4.55

### 5. Project Documentation Updated

- **`CLAUDE.md`**: Updated optimization results table, added Session 8A to history
- **`MEMORY.md`**: Updated Session 6B/8A results section

---

## Files Created / Modified

| File | Action |
|------|--------|
| `scripts/regenerate_results_20k.py` | Created |
| `data/optimization/optimization_results_5min_corrected.csv` | Regenerated |
| `data/optimization/optimization_results_4H_corrected.csv` | Regenerated |
| `data/optimization/optimization_comparison_6_vs_6b.csv` | Regenerated |
| `data/backtest/backtest_summary_corrected.csv` | Regenerated |
| `data/backtest/backtest_results_5min_corrected.csv` | Unchanged (trade-level P&L unaffected) |
| `CLAUDE.md` | Updated |
| `docs/specifications/spec-08A-initial-capital-correction.md` | Created (prior commit) |

---

## Key Insight

Changing **position_size** with fixed initial_capital → linear scaling (Session 6B).
Changing **initial_capital** with fixed position_size → non-linear effect on Sharpe
and drawdown metrics. Both produce the same optimal parameters, but the numerical
values of risk-adjusted metrics differ and must be recomputed.

---

## Planned: Error 1100 Backend Disconnect Pause Flag

**Context:** IB Gateway performs a daily server reset (~00:15-01:45 ET, roughly
05:30-07:00 CET on our DigitalOcean droplet). This triggers Error 1100
("Connectivity between IBKR and Trader Workstation has been lost") followed
60-90 minutes later by Error 1102 (connectivity restored).

**Current state:** Session 7H added an Error 1102 handler that sets
`_needs_reconciliation = True`, consumed by the main loop to trigger
`reconcile_positions()`. The bot already survives the reset — failed
`fetch_latest_bar()` calls return `None` and the loop continues gracefully.
However, the bot does not explicitly detect Error 1100, so during the reset
window it keeps polling, generating noisy failed-request warnings in the log.

**Planned change (no code written yet):** Add an `is_backend_connected` flag
to `_on_error()`:

- **Error 1100 received:** set `self.is_backend_connected = False`, log once
  that the IB daily reset has started and trading is paused.
- **Error 1102 received:** set `self.is_backend_connected = True` (in addition
  to existing `_needs_reconciliation` flag).
- **Main loop:** check `is_backend_connected` early; if `False`, sleep and
  `continue` without attempting data fetches or order execution.

**Benefits:**
1. Eliminates repeated error logs during the 60-90 min reset window.
2. Prevents any possibility of order attempts during backend disconnect.
3. Produces a clean log narrative: "reset started -> paused -> reset ended ->
   reconciled -> resumed".
4. Demonstrates awareness of IB's daily maintenance cycle (useful for CPF report
   "Production Reliability" section).

**Implementation effort:** ~10 lines of code in `trading_bot.py`. To be done
in a future session when the bot code is next modified.

---

**End of Session 8A Handoff**
