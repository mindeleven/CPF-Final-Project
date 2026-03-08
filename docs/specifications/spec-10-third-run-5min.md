# Specification: Third Live Run — 5-Minute Timeframe with Maintenance Window Pause

**Store as:** `docs/specifications/spec-10-third-run-5min.md`
**Relates to:** `deployment/trading_bot.py`, `deployment/config_live.py`
**Notebook sections affected (if run is included):** 7.6, 9.2, 9.3, 10.4

---

## Context

This specification covers two things: (1) the code changes required before the third
live run, and (2) the log analysis instructions after the run completes. The third run
is a 5-minute timeframe deployment with a configurable maintenance window pause added
to eliminate the reconciliation noise that affected the February 23–27 run, during
which 7 of 11 trades were closed by reconciliation rather than strategy signals.

The decision whether to include the third run results in the notebook remains open
until after Claude Code has analysed the logs. If included, notebook changes are
limited to: one new paragraph in Section 9.2, one addition to Section 9.3, and a
brief mention in Section 7.6. Section 10.4 will mention the maintenance window as a
codebase improvement regardless of whether the results are included.

---

## Part 1: Code Changes

### 1.1 config_live.py — Add Maintenance Window Parameters

Add the following two parameters to `config_live.py`. They must be the authoritative
source of truth; no times should be hardcoded in `trading_bot.py`.

```python
# Maintenance window — bot pauses signal checking and order placement during this
# window to avoid IB Gateway nightly reboot disruptions. Open positions remain open.
# Format: "HH:MM" in CET (Central European Time).
MAINTENANCE_WINDOW_START = "23:30"
MAINTENANCE_WINDOW_END = "06:00"
```

### 1.2 trading_bot.py — Maintenance Window Pause Logic

At the top of each main loop iteration, before any signal check or order logic, add
a check against the maintenance window. The implementation must:

- Parse `MAINTENANCE_WINDOW_START` and `MAINTENANCE_WINDOW_END` from config at
  startup (not on every iteration).
- Use CET (Europe/Zurich or Europe/Berlin) as the timezone for the check.
- Handle the overnight crossing correctly: the window from 23:30 to 06:00 spans
  midnight, so the condition is `time >= 23:30 OR time < 06:00`.
- During the pause, sleep in 60-second cycles and log a single "Maintenance window
  active — resuming at 06:00 CET" message at entry. Do not repeat the log message
  on every sleep cycle.
- Do NOT close any open positions when entering the pause window.
- On exit from the pause window at `MAINTENANCE_WINDOW_END`, reload warmup bars via
  `load_historical_warmup()` before the first signal check. Log "Maintenance window
  ended — reloading warmup bars before resuming."

### 1.3 trading_bot.py — Daily P&L Snapshot

One minute before `MAINTENANCE_WINDOW_START` (i.e. at 23:29 CET), append a
`DAILY_SNAPSHOT` row to the trade CSV. This captures the cumulative P&L at the end
of the active trading day before the pause begins.

The row should use the same columns as existing trade rows, with:
- `trade_type` = `"DAILY_SNAPSHOT"` (or equivalent column name already in use)
- `pnl_eur` and `pnl_usd` = cumulative net P&L at that moment
- All other trade-specific columns (entry price, exit price, etc.) = empty or null

The existing log analysis script must filter out `DAILY_SNAPSHOT` rows before
calculating trade statistics (win rate, average P&L, etc.) so they do not skew
results. Confirm this filter is in place before the run starts.

### 1.4 Git Commit

Commit all changes before starting the run. Use a descriptive commit message, for
example:

```
Add configurable maintenance window pause (23:30-06:00 CET) to trading_bot.py

- MAINTENANCE_WINDOW_START and MAINTENANCE_WINDOW_END added to config_live.py
- Main loop pauses signal checking during window; open positions remain open
- Warmup bars reloaded on window exit before first signal check
- DAILY_SNAPSHOT row appended to trade CSV at 23:29 CET each night
```

### 1.5 Pre-Run Checklist

Before starting the container:
- Confirm EUR/USD balance situation is clean (sufficient USD available, no leftover
  virtual FX positions from prior currency conversions)
- Confirm the baseline position snapshot logic is still active (it was added for the
  4H run and should remain in place)
- Confirm `TIMEFRAME = "5min"` and `RUN_DURATION = "5d"` in config_live.py
- Confirm optimised 5-minute parameters are set: SMA 15/70, RSI 14 (35/75),
  Momentum 10 (threshold 0.0)
- Confirm `MAINTENANCE_WINDOW_START = "23:30"` and `MAINTENANCE_WINDOW_END = "06:00"`
- Run the container with a distinct name, e.g. `trading-bot-5min-r3`

---

## Part 2: Log Analysis

Run this after the five-day run completes and logs have been downloaded to
`deployment/logs/`. The relevant files will have `5min` and the run start date as
part of the filename.

Produce a structured summary saved as `docs/handoffs/session-10-live-results-5min-r3.md`.

### Preliminary Checks

Before extracting trade data, confirm from the startup log:

- Optimised parameters logged correctly: SMA 15/70, RSI 14 (35/75), Momentum 10
  (threshold 0.0)
- Baseline position snapshot logged at startup (confirm what it shows — ideally
  an empty set if the account is clean)
- `MAINTENANCE_WINDOW_START = 23:30` and `MAINTENANCE_WINDOW_END = 06:00` confirmed
  in config log

### 1. Run Metadata

- Confirmed start and end timestamps from the log
- Total wall-clock duration in hours
- Number of active trading days (days where the maintenance window was entered and
  exited cleanly)
- Confirm maintenance window was entered and exited correctly each night — log the
  exact entry and exit times for each day

### 2. Trade Summary

Follow the same structure as `docs/handoffs/session-09-live-results-5min.md`.

- Total number of trades executed (excluding DAILY_SNAPSHOT rows)
- Number of long trades and short trades
- Number of winning trades and losing trades
- Win rate (%)
- Total net P&L in EUR
- Average P&L per trade
- Largest single winning trade and largest single losing trade
- For each trade, note whether it was closed by a strategy signal or by
  reconciliation. Given the maintenance window, reconciliation-closed trades should
  be rare or absent — flag any that do occur and explain the circumstances.

### 3. Daily P&L Snapshots

Extract the DAILY_SNAPSHOT rows from the trade CSV and present them as a table:

| Date | Cumulative P&L (EUR) | Trades that day |
|------|---------------------|-----------------|

This provides a day-by-day equity progression that was not available from the
February run.

### 4. Infrastructure Events

- List any connectivity events that occurred outside the maintenance window (these
  would be unexpected)
- Confirm whether the maintenance window suppressed the nightly reboot disruptions
  as intended — i.e. confirm that no Error 1100/1102 events appear in the active
  trading hours (06:00–23:30 CET)
- Any Error 201 occurrences
- Any unexpected errors

### 5. Sharpe Ratio

Calculate an annualised Sharpe ratio from per-trade P&L if sufficient trades exist.
Note clearly that this is indicative only given the five-day sample. If fewer than
10 trades were executed, state that the sample is too small for a meaningful
calculation.

### 6. Comparison to February Run

Provide a brief comparison table against the February 23–27 run:

| Metric | Feb 23–27 run | Third run |
|--------|--------------|-----------|
| Trades executed | 11 | — |
| Trades closed by reconciliation | 7 (63.6%) | — |
| Trades closed by signal | 4 (36.4%) | — |
| Net P&L (EUR) | −10.24 | — |
| Win rate | 36.4% | — |
| Error 201 occurrences | 3 | — |

This comparison is the primary analytical value of the third run. Fill in the right
column from the log analysis.

### 7. Raw Data Appendix

- Full trade log as a table (timestamp, direction, entry price, exit price, P&L EUR,
  close reason: signal or reconciliation)
- Daily snapshot table (from Section 3 above)

---

Do not infer or estimate values that are not in the logs. Where data is missing or
ambiguous, flag it explicitly. The output will be used to decide whether to include
the third run in the notebook and, if so, to write the additional content for
Sections 7.6, 9.2, and 9.3.

For structural reference, follow the same format as
`docs/handoffs/session-09-live-results-5min.md`.
