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

### Bot Architecture

```
run()
  connect() → qualifyContractsAsync() + register _on_error (Error 1102 handler)
  check_eur_balance() → abort if < MIN_EUR_BALANCE
  reconcile_positions() → sync with IB reality, preserve fill-based entry_price
  load_historical_warmup() → reqHistoricalDataAsync, ~80 bars in ~4 seconds
  main loop:
    connection health check → reconnect + reconcile if disconnected
    _needs_reconciliation check → reconcile after soft connectivity restore (1102)
    fetch_latest_bar() → reqHistoricalDataAsync, 5-min bars
    deduplicate by bar timestamp (self.last_bar_time)
    calculate_indicators() → generate_signal()
    execute_order():
      _get_ib_eur_position() → reconcile if mismatch (pre-trade safety net)
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

---

## Notebook Status (as of 2026-02-27)

Current state: `migration/03-final-deliverable/03b-current-nb-20260227/ALGORITHMIC-TRADING-FINAL-PROJECT.md`
- Total: 4,936 lines, 10 main sections + Abstract + References

### Section Structure

| Section | Title | Status | Key Content |
|---------|-------|--------|-------------|
| Abstract | — | Placeholder | Awaiting live results ([X]% return, Sharpe [X]) |
| 1 | Project Setup | Complete | IBKR selection, DigitalOcean setup, Docker, IB Gateway deployment, VNC config |
| 2 | Strategic Decisions | Complete | EUR/USD rationale, timeframe selection, MA/RSI/Momentum parameter reasoning |
| 3 | Data Preparation | Complete | Load 3 timeframes, visualizations, quality checks |
| 4 | Technical Indicator Calculation | Complete | SMA, RSI, Momentum implementation + validation |
| 5 | Signal Generation and Position Management | Complete | Strategy logic, signal→position conversion, validation |
| 6 | Backtest Implementation | Complete | Results tables, heatmaps, optimal params (SMA 15/70, 20/70) |
| 7 | Live Trading Implementation | Complete | Requirements, architecture, challenges (8 bugs), testing history |
| 8 | Cloud Deployment | Complete | Docker containerization, deployment process, monitoring, lifecycle mgmt |
| 9 | Results from Cloud Trading Run | **PENDING** | 9.1 has placeholder text, 9.2-9.3 empty |
| 10 | Conclusion | **PENDING** | All subsections empty (10.1-10.5) |
| References | — | Complete | 16 sources (academic + practitioner) |

### Section 9 Placeholders (awaiting live data)

**9.1 Test Period Specification:**
- Shows Feb 23-28 for 5min, Mar 1-5 for 4H (dates are placeholders)
- Infrastructure events placeholder: "[N] scheduled IB Gateway infrastructure events"

**9.2 Performance Summary:** Empty (needs trade CSV analysis)

**9.3 Lessons Learned:** Empty (needs reflection on live run vs backtest)

### Section 10 Structure (all empty)

- 10.1 Key Achievements
- 10.2 Strategy Performance Analysis
- 10.3 Technical Lessons Learned
- 10.4 Future Directions (has one bullet point on Sortino ratio as placeholder)
- 10.5 Final Reflections

### Key Parameters Confirmed

**Optimization results shown in Section 6:**
- 5min: SMA 15/70, RSI 14 (35/75), Momentum 10 (0.0) → Sharpe 4.55, +4.13%, 107 trades
- 4H: SMA 20/70, RSI 14 (35/70), Momentum 10 (0.0) → Sharpe 1.42, +30.23%, 45 trades
- Both use config defaults: `rsi_period=14, momentum_period=10`

**Critical note:** Section 6 optimization tables and heatmaps show correct Sharpe values (4.55/1.42). The earlier Sharpe discrepancy (0.37 vs 1.42 for 4H) was resolved by fixing wrong RSI/Momentum periods in CLAUDE.md table.
