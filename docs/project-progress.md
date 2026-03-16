# CPF Final Project - Progress Report
**Date:** March 16, 2026
**Status:** Complete — ready for submission
**Timeline:** 2 weeks to deadline (March 31, 2026)

---

## Project Overview

**Goal:** Automated EUR/USD forex trading system with optimized strategy
**Approach:** Data → Indicators → Strategy → Backtest → Optimize → Live Deploy
**Platform:** DigitalOcean droplet (157.230.113.17) with IB Gateway + Docker
**Account:** Paper trading EUR account (~900K EUR)
**Account currency:** EUR (not USD)
**Position size:** 20,000 EUR | **Initial capital:** 20,000 EUR (no leverage)

---

## Completed Sessions

### Session 1: Configuration Module
- Global configuration system (constants, timeframes, validation)
- `modules/config/`

### Session 2: Data Layer
- Historical data fetching from IB (`scripts/fetch_historical_data.py`)
- CSV loader, validation, datetime indexing (`modules/data/`)
- Data directories: `data/historical/{5min,4H,1D}/`

### Session 3: Indicators Module
- SMA, RSI, Momentum with abstract base class (`modules/indicators/`)
- All use lowercase column names: `close`

### Session 4: Strategy Module
- Strategy ABC + MARSIMomentumStrategy (`modules/strategy/`)
- SMA crossover + RSI filter + Momentum filter
- Signals: 1=BUY, -1=SELL, 0=HOLD | Positions forward-fill

### Session 5/5B: Backtesting
- BacktestEngine, TransactionCosts, metrics (`modules/backtest/`)
- Signal at bar t → execute at bar t+1 open (no look-ahead bias)
- Fixed equity tracking bug in 5B

### Session 6/6B: Optimization
- GridSearchOptimizer, OptimizationResults (`modules/optimization/`)
- 432 parameter combinations for 5min and 4H
- Discovered linear scaling property (Sharpe invariant to position size)

### Session 7: Live Trading Bot + Docker
- LiveTradingBot class (`deployment/trading_bot.py`)
- Forex("EURUSD") contract via ib_async
- Docker deployment, config_live.py with optimized params
- Time-based runtime, weekend closing, trade CSV logging

### Session 7B: Reconnection Logic
- Exponential backoff (1s → 2s → 4s → ... → 60s cap)
- Handles IB Gateway midnight reboots (2-5 min downtime)

### Session 7C: Position Reconciliation
- `reconcile_positions()` syncs bot state with IB reality after reconnect
- Contract matching via `pair()` method with symbol/currency fallback
- Entry price from IB: `abs(avgCost)` (per-unit rate for forex)

### Session 7D: Contract Fixes
- `qualifyContractsAsync()` (async, not sync)
- Removed problematic `self.ib.sleep()` calls

### Session 7E: Critical Production Fixes (8 bugs fixed)
- All orders use `order.tif = 'GTC'` (forex 24/5, DAY caused Error 10349)
- Proper fill waiting: 30s timeout loop with `trade.isDone()`
- Entry price from `trade.orderStatus.avgFillPrice`
- `close_position()` returns bool; double-position guard in `execute_order()`
- EUR balance verification (`check_eur_balance()`, MIN_EUR_BALANCE = 20000)
- `load_historical_warmup()`: ~80 bars in ~4 seconds on startup
- `fetch_latest_bar()`: proper 5-min bar streaming via `reqHistoricalData`
- Bar deduplication via `self.last_bar_time`
- P&L logging in EUR and USD

### Session 7F: Reconciliation P&L Tracking
- `_record_reconcile_close()`: records estimated P&L when position vanishes
- Uses last known price as exit estimate

### Session 7G: Entry Price Fix
- IB's `avgCost` for forex is already the per-unit exchange rate
- Fixed: `abs(avgCost)` instead of `avgCost / position_size`

### Session 7H: Connectivity Reconciliation
- Error 1102 handler (`_on_error()`) sets `_needs_reconciliation` flag
- Main loop checks flag and runs `reconcile_positions()`
- Pre-trade IB position verification (`_get_ib_eur_position()`)
- Prevents stale state from "soft" connectivity losses

### Session 8A: Initial Capital Correction
- Corrected initial_capital from 10,000 to 20,000 EUR (no leverage)
- Proved mathematical scaling insufficient (Sharpe, drawdown are non-linear)
- Full grid search re-run with `scripts/regenerate_results_20k.py`
- Moved CSV files to `data/backtest/` and `data/optimization/`
- Updated notebook section 6 and all project documentation

### Session 09: 5-Minute Live Trading Results
- Feb 23-27, 2026 (5 days): 11 trades, -10.24 EUR P&L
- Win rate: 36.4%, Sharpe -0.87 (not meaningful over 5 days)
- 4 nightly IB Gateway reboots handled successfully
- 7 trades closed by reconciliation (position vanished during nightly reset)
- Error 201 analysis: bot checks EUR but BUY orders require USD

### Session 09B: Error 201 Root Cause & Fix
- Root cause: BUY EUR.USD = buy EUR with USD (requires USD balance)
- Account EUR-denominated (~1M EUR, insufficient USD)
- Solution: Manual EUR→USD conversion via IB Gateway
- Created `docs/ib-currency-conversion-guide.md`
- Convert 500K EUR → ~590K USD for balanced holdings

### Session 09C: 4H Deployment Preparation (5 fixes)
1. **Config fixes:** TIMEFRAME="4H", RUN_DURATION="5d", RSI_PERIOD=14, MOMENTUM_PERIOD=10
2. **Timeframe-aware bar sizes:** Dynamic "S" or "D" suffix for IB historical requests
3. **Baseline position snapshot:** Ignore pre-existing conversion positions
4. **IB duration limit fix:** Use "14 D" for 4H bars (not "1152000 S")
5. **Documentation:** Updated handoff, specification, CLAUDE.md

### Session 09D: 4H Live Run Analysis
- 0 trades over 112.4 hours (March 1–6, 2026): EUR 0.00 P&L
- 10 connectivity events: 5 hard disconnects at 23:45 UTC + 5 soft reboots at ~05:22–05:49 UTC
- All 10 recovered autonomously; all reconciliations confirmed FLAT position
- 0 Error 201 (EUR→USD pre-conversion successful)
- Statistical context: 0 trades is ~74% probability outcome (~15 trades/year backtest rate)
- Section 9.2 4H content drafted

### Session 10: Maintenance Window + 3rd Run Preparation
- Configurable maintenance window pause added to `trading_bot.py` (23:30–06:00 CET per spec,
  corrected to 00:30–06:45 CET to cover actual IB Gateway event times)
- `MAINTENANCE_WINDOW_START` / `MAINTENANCE_WINDOW_END` in `config_live.py`
- Uses `pytz.timezone("Europe/Berlin")` for CET/CEST-aware checks
- DAILY_SNAPSHOT row appended to trade CSV at 23:29 CET each night
- Spec stored: `docs/specifications/spec-10-third-run-5min.md`

### Session 11: Third Run (5min) Log Analysis
- 9 trades, +EUR 47.52, 55.6% win rate; reconciliation closes 44.4% (down from 63.6%)
- INCLUDE recommended; suggested notebook text for 9.2 and 9.3 drafted in handoff

### Session 10B: README Verification and Correction
- Corrected script filenames (regenerate_results_20k.py, added analyze_live_run.py)
- Removed non-existent docs/guides/ from tree, removed non-existent optimize_parameters.py
- Fixed configuration examples to match actual config_live.py (flat vars, correct IB names)

### Session 12: Pre-Submission Consistency Check
- Full consistency check on notebook markdown export (migration/notebooks/markdown-2026-03-16/)
- Verified: 0 Session references, all log files committed, 4H backtest CSV correctly absent by design
- Removed non-existent deployment/.env.example from README structure tree
- All sections complete; notebook confirmed ready for submission

---

## Optimized Strategy Parameters (Session 8A — corrected)

Initial capital: 20,000 EUR. Position size: 20,000 EUR. No leverage (1:1).

| Timeframe | SMA Fast/Slow | RSI Lower/Upper | Mom Threshold | Sharpe | Return | Trades |
|-----------|---------------|-----------------|---------------|--------|--------|--------|
| 5min      | 15 / 70       | 35 / 75         | 0.0           | 4.55   | +4.13% | 107    |
| 4H        | 20 / 70       | 35 / 70         | 0.0           | 1.42   | +30.23%| 45     |

Optimal parameters are identical across all position size/capital combinations.

---

## Live Testing Results

### Early Tests (Feb 12-20, 2026)

**4H Test (Feb 12-13):** First autonomous run after Session 7D
- 4 trades, all losses (low-volatility period), P&L: -$39.70 (-0.2%)
- Successful reconnection after IB Gateway disconnect
- Revealed 8 bugs → fixed in Session 7E

**3-Day Test (Feb 18-20, post-7E):** 5min timeframe validation
- Bot ran autonomously through multiple IB Gateway daily resets
- Midnight reboot (Error 1100 → reconnect → reconcile): handled correctly
- Soft connectivity blip revealed stale state issue → fixed in Session 7H

### Production 5-Minute Test (Feb 23-27, 2026) — Session 09

**Duration:** 104.7 hours (Sunday 07:20 CET → Friday 16:00 CET)
**Trades:** 11 total (6 LONG, 5 SHORT)
**P&L:** -10.24 EUR (-0.001% of capital)
**Win rate:** 36.4% (4 wins, 7 losses)

**Infrastructure Performance:**
- 4 nightly IB Gateway reboots: handled automatically
- 9 position reconciliations: 7 detected mismatches, all resolved correctly
- 0 crashes, 0 manual interventions required

**Key Findings:**
1. **Error 201 (currency leverage):** 3 BUY orders rejected on Feb 27
   - Root cause: Bot checks EUR balance but BUY orders require USD
   - Account has ~1M EUR but insufficient USD (~23K USD needed per BUY trade)
   - Fix: Manual EUR→USD conversion (500K EUR → 590K USD)

2. **Reconciliation-closed trades:** 63.6% (7/11) closed by reconciliation vs. strategy signal
   - IB Gateway closes positions during nightly reset (paper trading behavior)
   - Reconciliation correctly detects and records estimated P&L

3. **Sample size:** 11 trades over 5 days insufficient for strategy evaluation
   - Backtest showed 107 trades over 3 years (~36 trades/year)
   - High variance expected in short samples

**Sharpe ratio:** -0.87 (indicative only, not meaningful over 5 days)

### Production 4-Hour Test (Mar 1–6, 2026) — Session 09D

**Duration:** 112.4 hours (March 1, 23:38 CET → March 6, 16:01 CET)
**Trades:** 0 | **P&L:** EUR 0.00 | **Capital:** EUR 952,192.21 (unchanged)

**Infrastructure Performance:**
- 5 hard disconnects at 23:45 UTC nightly: all recovered autonomously
- 5 soft reboots (Error 1100 → 1102) at ~05:22–05:49 UTC: all recovered, reconciliation confirmed FLAT
- Two nights required exponential backoff (4 attempts); 0 crashes, 0 manual interventions

**Key Finding:**
0 trades is a ~74% probability outcome given the 4H backtest rate of ~15 trades/year (Poisson model).
EUR/USD gapped ~100–150 pips lower at Sunday open (US/Israeli geopolitical event); no signal conditions
satisfied despite the directional move. Not an anomaly.

### Production 5-Minute Test (3rd Run, Mar 8–13, 2026) — Session 11

**Duration:** 4 days, 17 hours (2026-03-08 22:55 UTC → 2026-03-13 16:00 UTC; ended via CLOSE_BEFORE_WEEKEND)
**Trades:** 9 total (5 LONG, 4 SHORT) | **P&L:** +EUR 47.52 | **Win rate:** 55.6%

**Reconciliation analysis:**
- Closed by strategy signal: 4/9 (44.4%) — down from 4/11 (36.4%) in Feb run
- Closed by IB reconciliation: 4/9 (44.4%) — down from 7/11 (63.6%) in Feb run
- Closed by weekend shutdown: 1/9 (11.1%)

Maintenance window reduced reconciliation closes but did not eliminate them: positions open before
23:30 CET are still closed by IB's paper trading reset at 00:45 CET. Structural paper trading
limitation; irrelevant on live accounts.

**Infrastructure:** 5 hard disconnects + 5 soft reboots, all recovered. 0 Error 201. 0 crashes.
**Inclusion decision:** INCLUDE — adds quantified improvement; fits existing narrative without structural changes.

---

## Notebook Progress

The deliverable notebook is `ALGORITHMIC-TRADING-FINAL-PROJECT.ipynb` (project root).
Current state reference: `migration/03-final-deliverable/03d-current-nb-20260306/` (local only, not in repo).

| Section | Title | Status |
|---------|-------|--------|
| Abstract | — | Complete |
| 1 | Project Setup | Complete |
| 2 | Strategic Decisions | Complete |
| 3 | Data Preparation | Complete |
| 4 | Technical Indicator Calculation | Complete |
| 5 | Signal Generation and Position Management | Complete |
| 6 | Backtest Implementation | Complete |
| 7 | Live Trading Implementation | Complete |
| 8 | Cloud Deployment | Complete |
| 9 | Results from Cloud Trading Run | Complete |
| 10 | Conclusion | Complete |
| References | — | Complete |

---

## Deferred Features

### UTC/CET Maintenance Window Documentation
- Config values (`MAINTENANCE_WINDOW_START/END`) are in CET; log timestamps are UTC
- These are not yet documented together inline in config_live.py
- Future improvement: accept window times in UTC, or add clear inline mapping of UTC event times to CET params

### Error 1100 Granular Pause Flag
- A tighter pause flag (only between Error 1100 and 1102) would give cleaner logs vs. the broad maintenance window
- Not critical; the maintenance window already covers the relevant period

---

## Project File Structure

```
CPF-Final-Project/
├── modules/
│   ├── config/        # Constants, timeframe configs, validation
│   ├── data/          # CSV loader, validation, datetime indexing
│   ├── indicators/    # SMA, RSI, Momentum (abstract base class)
│   ├── strategy/      # Strategy ABC + MARSIMomentumStrategy
│   ├── backtest/      # BacktestEngine, TransactionCosts, metrics
│   └── optimization/  # GridSearchOptimizer, OptimizationResults
├── deployment/
│   ├── trading_bot.py # Live trading bot (async, ib_async)
│   ├── config_live.py # Runtime config + optimized params + maintenance window
│   ├── Dockerfile     # Build context is project root
│   ├── requirements.txt
│   ├── .dockerignore
│   └── logs/          # Runtime logs (production run logs committed; dev logs gitignored)
├── scripts/
│   ├── analyze_live_run.py        # Analyse live trading run logs
│   ├── fetch_historical_data.py   # IB Gateway historical fetch
│   └── regenerate_results_20k.py  # Session 8A CSV regeneration
├── data/
│   ├── historical/    # CSV data: {5min,4H,1D}/
│   ├── backtest/      # Backtest result CSVs
│   └── optimization/  # Optimization result CSVs
└── docs/
    ├── handoffs/      # Session handoff documents
    ├── specifications/# Session specification documents
    ├── ib-currency-conversion-guide.md  # EUR→USD conversion instructions
    └── project-progress.md  # This file
```

---

## Technical Environment

### DigitalOcean Droplet
- IP: 157.230.113.17
- OS: Ubuntu 22.04.5 LTS
- IB Gateway: Running, paper trading port 4002
- Docker: Trading bot containerized (`--network host`)

### Dependencies
- Python 3.11
- ib_async v2.1.0 (async IB API)
- pandas, numpy for data processing
- Docker for containerization

### Key IB Patterns (learned from production bugs)
- Contract: `Forex("EURUSD")`, qualify with `qualifyContractsAsync()`
- Orders: `order.tif = "GTC"` (not DAY), wait for fill with `trade.isDone()`
- Entry price: `trade.orderStatus.avgFillPrice` (not current price)
- IB `avgCost` for forex: already per-unit rate (`abs(avgCost)`)
- Account data: `accountSummaryAsync()` (async, not sync)
- Historical data: `reqHistoricalDataAsync()` (not `reqMktData`)

---

## Next Steps

1. **Submit** deliverable notebook `ALGORITHMIC-TRADING-FINAL-PROJECT.ipynb` by March 31, 2026

---

## Key Documents

| Document | Location |
|----------|----------|
| Project instructions | `CLAUDE.md` (project root) |
| Session handoffs | `docs/handoffs/session-XX-description.md` |
| Session specifications | `docs/specifications/spec-XXX-description.md` |
| Deployment guide | `deployment/DEPLOYMENT_GUIDE.md` |
| Deliverable notebook | `ALGORITHMIC-TRADING-FINAL-PROJECT.ipynb` (project root) |

---

**Last Updated:** March 16, 2026
**Next Action:** Submit deliverable notebook by March 31, 2026
