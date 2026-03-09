# CPF Final Project — Claude Code Instructions

## Self-Maintenance Rule

**At the end of every coding session — or at what appears to be the end (i.e., after a commit) — update this file with any new durable facts learned during the session.** This includes new modules, API patterns, bug fixes, architectural decisions, and any corrections to existing entries. Remove or update entries that have become wrong or outdated. This file must stay accurate and current.

---

## Project Overview

- **What:** Parametric multi-timeframe EUR/USD trading system with live deployment
- **Author:** Juergen Kober, co-developed with Claude Code
- **Program:** Certificate in Python for Finance (CPF), The Python Quants Group
- **Deadline:** March 31, 2026
- **Account currency:** EUR (not USD)
- **Header convention:** "Opus 4.5" in Session 1 files, "Opus 4.6" in Session 2+

## Coding Standards

- Type hints on all function signatures
- Google-style docstrings
- PEP 8 formatting via `black`
- Logging levels: INFO, WARNING, ERROR (no DEBUG in production code)
- No emojis in code or log output
- Handoff documents go in `docs/handoffs/` with naming: `session-XX-description.md`

---

## Project Structure

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
│   ├── config_live.py # Runtime config + Session 6B optimized params
│   ├── Dockerfile     # Build context is project root
│   ├── requirements.txt
│   ├── .dockerignore
│   └── logs/          # Runtime output (gitignored)
├── scripts/
│   └── fetch_historical_data.py  # IB Gateway historical fetch
├── data/historical/   # CSV data: {5min,4H,1D}/
├── docs/handoffs/     # Session handoff documents
├── notebooks/         # Jupyter analysis (Session 8, pending)
└── tests/             # Unit tests
```

---

## Module APIs

### Config (`modules/config`)

**Exports from `__init__.py`:** `TIMEFRAME_CONFIGS`, `get_timeframe_config`, `list_timeframes`, `INSTRUMENT_SYMBOL`, `IB_HOST`, `IB_PORT`, `IB_CLIENT_ID`, `DATA_DIR`, `ensure_directories`

**Not exported** (in `constants.py` only): `INSTRUMENT_CURRENCY`, `INSTRUMENT_EXCHANGE`

| Constant | Value |
|----------|-------|
| `INSTRUMENT_SYMBOL` | `"EUR.USD"` |
| `INSTRUMENT_CURRENCY` | `"USD"` |
| `INSTRUMENT_EXCHANGE` | `"IDEALPRO"` |
| `IB_HOST` | `"127.0.0.1"` |
| `IB_PORT` | `4002` |
| `IB_CLIENT_ID` | `100` |
| `DATA_DIR` | `"data/historical"` (relative) |

**TIMEFRAME_CONFIGS keys:** `5min`, `4H`, `1D` — each has `ib_bar_size`, `ib_duration`, and strategy default params (including `momentum_lookback`, not `momentum_period`).

### Data (`modules/data`)

- CSV naming convention: `EUR_USD_{timeframe}_{YYYYMMDD}_{YYYYMMDD}.csv`
- Directories: `data/historical/{5min,4H,1D}/`
- Output DataFrames use lowercase column names: `open`, `high`, `low`, `close`, `volume`

### Indicators (`modules/indicators`)

**Exports:** `Indicator` (ABC), `SMA`, `RSI`, `Momentum`

- All expect a DataFrame with a `'close'` column (not a Series)
- Callable shorthand: `sma(df)` is equivalent to `sma.calculate(df)`
- `SMA`: rolling mean, `period >= 2`, NaN for first `(period-1)` rows
- `RSI`: EMA-smoothed, `period >= 2`, bounded [0, 100], 1 NaN row (from diff)
- `Momentum`: price diff, `period >= 1`, NaN for first `period` rows

### Strategy (`modules/strategy`)

**Exports:** `Strategy` (ABC), `MARSIMomentumStrategy`

- Signals: `1` = BUY, `-1` = SELL, `0` = HOLD
- Positions: `1` = LONG, `-1` = SHORT, `0` = FLAT (forward-filled until opposite signal)
- Works on a copy of the input DataFrame (does not mutate original)
- Output columns: `sma_fast`, `sma_slow`, `rsi`, `momentum`, `signal`, `position`

### Backtest (`modules/backtest`)

**Exports:** `BacktestEngine`, `TransactionCosts`, `metrics`

- Signal at bar `t` executes at bar `t+1` open (no look-ahead bias)
- Transaction costs at both entry and exit
- Periods per year: 72,000 (5min), 2,080 (4H), 252 (1D) — auto-detected
- `metrics` module: pure functions (`calculate_returns`, `calculate_sharpe_ratio`, `calculate_max_drawdown`, `calculate_win_rate`, `calculate_profit_factor`, `calculate_total_return`, `calculate_all_metrics`)

### Optimization (`modules/optimization`)

**Exports:** `GridSearchOptimizer`, `OptimizationResults`

- Skips invalid combos: `sma_fast >= sma_slow`, `rsi_lower >= rsi_upper`
- `get_best_overall()` filters by `min_trades`, ranks by primary + secondary metric

---

## Optimized Strategy Parameters (Session 8A — corrected)

Initial capital: 20,000 EUR. Position size: 20,000 EUR. No leverage (1:1).

| Timeframe | SMA Fast/Slow | RSI Period | RSI Lower/Upper | Mom Period | Mom Threshold | Sharpe | Return | Trades |
|-----------|---------------|------------|-----------------|------------|---------------|--------|--------|--------|
| 5min | 15 / 70 | 14 | 35 / 75 | 10 | 0.0 | 4.55 | +4.13% | 107 |
| 4H | 20 / 70 | 14 | 35 / 70 | 10 | 0.0 | 1.42 | +30.23% | 45 |

CSV files: `data/optimization/optimization_results_{5min,4H}_corrected.csv`

---

## Live Trading Bot (`deployment/trading_bot.py`)

### ib_async Patterns (CRITICAL)

These patterns were learned from production bugs. Do not regress:

| Pattern | Correct | Wrong |
|---------|---------|-------|
| Contract qualification | `await self.ib.qualifyContractsAsync(self.contract)` | `self.ib.qualifyContracts()` (blocks event loop) |
| Account summary | `await self.ib.accountSummaryAsync()` | `self.ib.accountSummary()` (blocks event loop) |
| Position query | `self.ib.positions()` (sync OK, returns cache) | — |
| Historical data | `await self.ib.reqHistoricalDataAsync(...)` | `self.ib.reqMktData()` (gives spot ticks, not bars) |
| Forex contract | `Forex("EURUSD")` | `Stock("EUR", "USD", ...)` |
| Contract `pair` | `pos.contract.pair()` (method call) | `pos.contract.pair` (not a property) |
| IB `avgCost` (forex) | `abs(ib_avg_cost)` (already per-unit rate) | `avgCost / position_size` (that's for stocks) |
| Order TIF | `order.tif = "GTC"` (forex is 24/5) | Default DAY (causes Error 10349) |
| Fill waiting | 30s loop with `trade.isDone()` | `await self.ib.sleep(2)` (unreliable) |
| Soft reconnect | Reconcile on Error 1102 via `_needs_reconciliation` flag | Ignoring Error 1102 (causes stale position state) |
| Pre-trade verify | `_get_ib_eur_position()` before close-then-open | Trusting bot state without IB check |
| IB duration limit | Use "D" (days) for 4H bars, "S" (seconds) for 5min | Duration > 86400s with "S" causes Error 321 |
| Baseline positions | Snapshot at startup, filter from reconciliation | Pre-existing positions confuse reconciliation logic |

### Bot Architecture

```
run()
  connect() → qualifyContractsAsync() + register _on_error (Error 1102 handler)
  check_eur_balance() → abort if < MIN_EUR_BALANCE
  capture baseline_positions → snapshot existing positions (e.g., EUR→USD conversion)
  reconcile_positions() → sync with IB reality, filter baseline, preserve fill-based entry_price
  load_historical_warmup() → reqHistoricalDataAsync, 80 bars, uses "D" for 4H (IB duration limit)
  main loop:
    connection health check → reconnect + reconcile if disconnected
    _needs_reconciliation check → reconcile after soft connectivity restore (1102)
    fetch_latest_bar() → reqHistoricalDataAsync, timeframe-aware bar size
    deduplicate by bar timestamp (self.last_bar_time)
    calculate_indicators() → generate_signal()
    execute_order():
      _get_ib_eur_position() → reconcile if mismatch (pre-trade safety net), filters baseline
      check_eur_balance() before every trade
      close_position() → GTC, 30s wait, returns bool
      sleep(1) settlement delay
      verify position == 0 (double position guard)
      open_position() → GTC, 30s wait, entry_price from avgFillPrice
  shutdown: close position, print summary, disconnect
```

### Config (`deployment/config_live.py`)

| Setting | Value | Notes |
|---------|-------|-------|
| `IB_HOST` | `"localhost"` | Docker host mode |
| `IB_PORT` | `4002` | Paper trading |
| `IB_CLIENT_ID` | `3` | Unique per bot instance |
| `POSITION_SIZE` | `20000` | EUR, IBKR minimum for forex |
| `INITIAL_CAPITAL` | `10000.0` | Overridden by actual EUR balance at startup |
| `MIN_EUR_BALANCE` | `20000` | Bot aborts if below this |
| `RUN_DURATION` | `"1h"` | Format: "Xh", "Xd", "Xm" |
| `CHECK_FREQUENCY` | `60` (5min) / `300` (4H) | Seconds between bar checks |

### P&L Calculation

- Gross PnL (USD): `direction * (exit_price - entry_price) * position_size`
- Costs (USD): `2 * 0.0001 * position_size` (1 pip spread, entry + exit)
- Net PnL (EUR): `net_pnl_usd / fill_price`
- Capital tracking is EUR-denominated

### Docker Deployment

- Build from project root: `docker build -f deployment/Dockerfile -t trading-bot:latest .`
- Run: `docker run -d --network host -v .../logs:/app/logs trading-bot:latest`
- Cloud: DigitalOcean droplet at `root@157.230.113.17`

### Log File Naming

- Bot log: `trading_bot_{timeframe}_{duration}_{YYYYMMDD_HHMMSS}.log`
- Trade CSV: `trades_{timeframe}_{duration}_{YYYYMMDD_HHMMSS}.csv`
- Trade CSV columns: `entry_time, exit_time, direction, entry_price, exit_price, size, gross_pnl, costs, net_pnl, net_pnl_eur, capital_eur`

---

## Session History

| Session | What | Key Outcome |
|---------|------|-------------|
| 1 | Config module | Constants, timeframes, validation |
| 2 | Data layer + IB fetch | CSV loader, historical data script |
| 3 | Indicators | SMA, RSI, Momentum with ABC |
| 4 | Strategy | MARSIMomentumStrategy |
| 5/5B | Backtesting | BacktestEngine, position size correction |
| 6/6B | Optimization | Grid search, position size re-optimization |
| 7 | Live bot + Docker | LiveTradingBot, Dockerfile, deployment guide |
| 7B | Reconnection | Exponential backoff, handles Gateway reboots |
| 7C | Reconciliation | Position sync with IB after reconnect |
| 7D | Contract fixes | qualifyContracts, event loop fix |
| 7E | Production fixes | 8 bugs fixed, async API, warmup, bar streaming |
| 7F | Reconciliation P&L | Record estimated P&L when position vanishes |
| 7G | Entry price fix | avgCost is per-unit for forex, not total cost |
| 7H | Connectivity reconciliation | Reconcile on Error 1102 + pre-trade IB position verify |
| 8A | Initial capital correction | 20K initial capital, regenerated all CSVs, updated notebook |
| 09 | 5min live results | 11 trades over 5 days, -10 EUR P&L, Error 201 analysis |
| 09B | Error 201 fix | EUR→USD conversion guide, corrected root cause |
| 09C | 4H deployment prep | Correct params, timeframe-aware bars, baseline positions, IB duration fix |
| 09D | 4H live run analysis | 0 trades, 112.4 hours, 10 connectivity events all handled; section 9.2 drafted |
| 10 | Maintenance window + 3rd run prep | Configurable 23:30–06:00 CET pause added; DAILY_SNAPSHOT row; spec stored |

---

## Notebook Status (as of 2026-03-06)

Current state: `migration/03-final-deliverable/03d-current-nb-20260306/ALGORITHMIC-TRADING-FINAL-PROJECT.md`
- Total: 4,947 lines, 10 main sections + Abstract + References
- Images directory: same folder as the .md file (ignore any subdirectory paths in image refs)

### Section Line Numbers (03d version)

| Section | Start Line |
|---------|-----------|
| Abstract | 11 |
| 1. Project Setup | 42 |
| 2. Strategic Decisions | 387 |
| 3. Data Preparation | 715 |
| 4. Technical Indicator Calculation | 1340 |
| 5. Signal Generation and Position Management | 2250 |
| 6. Backtest Implementation | 2700 |
| 7. Live Trading Implementation | 4149 |
| 8. Cloud Deployment | 4366 |
| 9. Results from Cloud Trading Run | 4802 |
| 10. Conclusion | 4849 |
| References | 4908 |

### Section Structure

| Section | Title | Status | Key Content |
|---------|-------|--------|-------------|
| Abstract | — | Complete | Full abstract including 5min and 4H results summary |
| 1 | Project Setup | Complete | IBKR selection, DigitalOcean setup, Docker, IB Gateway deployment, VNC config |
| 2 | Strategic Decisions | Complete | EUR/USD rationale, timeframe selection, MA/RSI/Momentum parameter reasoning |
| 3 | Data Preparation | Complete | Load 3 timeframes, visualizations, quality checks, data limitations |
| 4 | Technical Indicator Calculation | Complete | SMA, RSI, Momentum implementation + validation |
| 5 | Signal Generation and Position Management | Complete | Strategy logic, signal→position conversion, validation |
| 6 | Backtest Implementation | Complete | Results tables, heatmaps, optimal params (SMA 15/70, 20/70) |
| 7 | Live Trading Implementation | Complete | Requirements, architecture, 8 challenges, testing history (3 runs) |
| 8 | Cloud Deployment | Complete | Docker containerization, deployment process, monitoring, lifecycle mgmt |
| 9 | Results from Cloud Trading Run | **PARTIAL** | 9.1 complete, 9.2 has 5min results + 4H draft ready, 9.3 complete |
| 10 | Conclusion | Complete | All subsections 10.1–10.5 written |
| References | — | Complete | 16 sources (academic + practitioner) |

### Section 9 — Current State

**9.1 Test Period Specification:** Complete. 4H run confirmed as March 1, 2026 23:38 CET – March 6, 2026 16:01 CET.

**9.2 Performance Summary:**
- 5min subsection: Complete (11 trades, −10.24 EUR, 36.4% win rate, 4 reconcile-closed trades)
- 4H subsection: Draft written, awaiting manual insertion into notebook. File: `migration/03-final-deliverable/04-claude-code-files/section-0902-4-Hour-Timeframe-Run.md`
- 4H result: 0 trades, EUR 0.00 P&L, 112.4 hours, 10 connectivity events all resolved correctly

**9.3 Lessons Learned:** Complete (infrastructure resilience, reconciliation noise in paper trading, USD balance requirement).

### Section 10 — Complete Summary

- 10.1 Key Achievements: Complete
- 10.2 Strategy Performance Analysis: Complete
- 10.3 Technical Lessons Learned: Complete (GTC, fill polling, avgCost, currency management, reconciliation)
- 10.4 Future Directions: Complete (pagination, train/test split, Sortino, programmatic FX conversion, second strategy, regime filter)
- 10.5 Personal Reflection: Complete

### Key Parameters Confirmed

**Optimization results shown in Section 6:**
- 5min: SMA 15/70, RSI 14 (35/75), Momentum 10 (0.0) → Sharpe 4.55, +4.13%, 107 trades
- 4H: SMA 20/70, RSI 14 (35/70), Momentum 10 (0.0) → Sharpe 1.42, +30.23%, 45 trades
- Both use config defaults: `rsi_period=14, momentum_period=10`

---

## Third Live Run (5min) — Pending

**Status:** Code changes committed (session 10). Run not yet started.
**Spec:** `docs/specifications/spec-10-third-run-5min.md`
**Pre-run checklist (manual steps before starting container):**
- Set `TIMEFRAME = "5min"` and `RUN_DURATION = "5d"` in `config_live.py`
- Confirm USD balance is sufficient (Error 201 root cause from first run)
- Confirm baseline position snapshot in place (carried over from 4H run)
- Confirm 5min params: SMA 15/70, RSI 14 (35/75), Momentum 10 (0.0)
- Container name: `trading-bot-5min-r3`

**Maintenance window implementation (added in session 10):**
- `MAINTENANCE_WINDOW_START = "00:30"` and `MAINTENANCE_WINDOW_END = "06:45"` in `config_live.py` (corrected in session 10B — see known issue below)
- Main loop checks `_in_maintenance_window()` before any signal/order logic
- Window spans midnight: condition is `time >= 00:30 OR time < 06:45`
- Uses `pytz.timezone("Europe/Berlin")` for CET/CEST-aware checks (never bare `datetime.now()`)
- On entry: sets `_mw_active = True`, logs single message, sleeps in 60s cycles
- On exit: sets `_mw_active = False`, calls `load_historical_warmup()`, logs resumption
- `_save_daily_snapshot()` fires at 23:29 CET (guarded by `_snapshot_date` to avoid duplicates)
- DAILY_SNAPSHOT row uses `direction` column (no schema change); `net_pnl_eur` = cumulative P&L
- `self.trades` never receives snapshot rows → summary stats unaffected

**Known issue — UTC/CET timezone confusion in maintenance window (fix deferred):**
The DigitalOcean server runs UTC by default, so all log timestamps are in UTC, not CET.
IB Gateway events occur at:
- Hard disconnect: 23:45 UTC = 00:45 CET
- Soft reboot (Error 1100/1102): ~05:22–05:49 UTC = ~06:22–06:49 CET

The original spec assumed the log timestamps were CET and set the window to 23:30–06:00 CET — which was too early and too short. The parameters were corrected manually to 00:30–06:45 CET (which the code interprets via pytz Europe/Berlin correctly). The underlying code logic is sound, but the parameter semantics are confusing: the config values are in CET, the log timestamps are in UTC, and these are currently not documented clearly together. A future improvement should either accept the window times in UTC, or add explicit inline documentation linking the UTC event times to the CET parameter values.

**Log analysis (after run completes):**
- Save as: `docs/handoffs/session-10-live-results-5min-r3.md`
- Key comparison metric: trades closed by reconciliation (was 7/11 = 63.6% in Feb run; should be near zero with window active)
- Filter `direction == "DAILY_SNAPSHOT"` before computing win rate / average P&L

---

## 4H Live Run — Confirmed Results (Session 09D)

**Log files:** `deployment/logs/trading_bot_4H_5d_20260301_233824.log` and `trades_4H_5d_20260301_233824.csv`
**Full analysis:** `docs/handoffs/session-09d-live-results-4hour.md`

**Result:** 0 trades, EUR 0.00 P&L, capital unchanged at EUR 952,192.21.

**Infrastructure:** 10 connectivity events total — 5 hard disconnects ("Peer closed connection") at exactly 23:45 CET each night, and 5 soft reboots (Error 1100 → 1102) each morning at ~05:22–05:49 CET. All 10 recovered autonomously. Two nights (Mar 2→3, Mar 5→6) required exponential backoff (4 attempts) due to Gateway not yet restarted on first attempt. All 10 reconciliations confirmed FLAT position.

**Notable errors:** Recurring `KeyError: 8521` in ib_async contractDetails handler (once per soft reboot, non-fatal). Error 162 once (cancelled historical data query during connectivity blip, non-fatal).

**Error 201:** None. Account was pre-rebalanced before deployment.

**Statistical context:** 0 trades is a ~74% probability outcome given the backtest rate of ~15 trades/year. Not an anomaly.

**Market context:** EUR/USD gapped ~100–150 pips lower at Sunday open (US/Israeli strikes on Iran). Rate fell from ~1.177 to ~1.155 by mid-week, then partially recovered to ~1.162. No signal conditions were satisfied despite the directional move.
