# Specification: Third Run Log Analysis — Session 11
**Prepared for:** Claude Code  
**Date:** March 12, 2026  
**Run:** Production 5-minute run 3 (`trading-bot-5min-2nd`)  
**Output to save as:** `docs/handoffs/session-11-live-results-5min-r3.md`

---

## Run Parameters

- **Container:** `trading-bot-5min-2nd`
- **Droplet:** 157.230.113.17
- **Started:** 2026-03-08 22:55 UTC (23:55 CET)
- **Ends:** 2026-03-13 22:55 UTC (23:55 CET)
- **Timeframe:** 5-minute
- **Strategy parameters:** SMA 15/70, RSI 14 (thresholds 35/75), Momentum 10 (threshold 0.0)
- **Position size:** 20,000 EUR
- **Maintenance window:** 00:30–06:45 CET (covers hard disconnect at 00:45 CET and soft reboot finishing by ~06:24 CET)

---

## Log File Locations

```bash
# On the droplet:
deployment/logs/trades_5d-5min-2nd_*.csv
deployment/logs/trading_bot_5d-5min-2nd_*.log
```

Confirm exact filenames before running analysis.

---

## Analysis Tasks

### 1. Trade Summary

From the trades CSV, extract:
- Total number of trades
- Number of LONG trades vs SHORT trades
- Total net P&L in EUR
- Total net P&L in USD
- Win rate (% of trades with positive P&L)
- Largest winning trade (EUR)
- Largest losing trade (EUR)
- Average P&L per trade (EUR)

### 2. Reconciliation Analysis — Critical Metric

This is the primary comparison metric against the February run.

For each trade, determine whether it was closed by:
- **Strategy signal** — a SELL or BUY signal from the strategy logic
- **Reconciliation** — a position mismatch detected after reconnection (log line: `Position mismatch detected!`)
- **Maintenance window** — any other mechanism

Count and report:
- Trades closed by strategy signal: N (X%)
- Trades closed by reconciliation: N (X%)

**Comparison baseline:** February run had 7/11 trades (63.6%) closed by reconciliation.  
**Expected improvement:** The maintenance window should reduce this, but Night 1 already confirmed at least one reconciliation close (March 8–9), so it will not be zero.

### 3. Infrastructure Events

From the log file, identify and count:
- Hard disconnects (23:45 UTC each night — `Peer closed connection`)
- Soft reboots (Error 1100 → 1102 sequences)
- Maintenance window entries (`Maintenance window active`)
- Reconnection attempts and outcomes
- Any crashes or unhandled exceptions
- Any Error 201 occurrences (BUY order rejections)
- DAILY_SNAPSHOT rows in the CSV (should appear once per night at 23:29 CET)

Report for each night separately (Night 1: Mar 8–9, Night 2: Mar 9–10, Night 3: Mar 10–11, Night 4: Mar 11–12, Night 5: Mar 12–13).

### 4. Position State at Hard Disconnect

For each night's hard disconnect, record:
- Was a position open going into 00:45 CET? (LONG / SHORT / FLAT)
- Was it closed by IB during the reset?
- Did reconciliation detect a mismatch the following morning?
- Estimated exit P&L recorded (if applicable)

### 5. Run Duration and Completion

- Actual start time (first log entry)
- Actual end time (last log entry or shutdown message)
- Total hours of operation
- Did the run complete normally or was there any unplanned interruption?

---

## Inclusion Decision Framework

After completing the analysis, assess against these three criteria:

1. **Does this run add knowledge not already present in the February run?**  
   Specifically: did the maintenance window meaningfully reduce the reconciliation-close rate? Any new infrastructure findings?

2. **Are the notebook changes required limited in scope?**  
   Permitted changes if included: one new paragraph in 9.2, one addition to 9.3, brief mention in 7.6. No structural changes to the notebook.

3. **Is there anything in the results that contradicts or complicates the existing narrative in Sections 9 and 10?**

State clearly: **INCLUDE** or **EXCLUDE**, with one sentence of reasoning.

---

## Output Document Structure

Save results to `docs/handoffs/session-11-live-results-5min-r3.md` with the following sections:

```
# Session 11 — Third Run Results (5-minute, Run 3)

## Run Summary
[One paragraph: dates, trades, P&L, win rate]

## Reconciliation Analysis
[Table: trades by close type, comparison to February run]

## Infrastructure Events by Night
[Night-by-night breakdown]

## Position State at Hard Disconnect
[Table: one row per night]

## Inclusion Recommendation
[INCLUDE / EXCLUDE + reasoning]

## Suggested Notebook Text
[If INCLUDE: draft paragraph for 9.2 and any addition to 9.3]
[Keep to the style rules below]
```

---

## Style Rules for Any Drafted Notebook Text

- No bullet points in narrative cells — prose only
- British spelling throughout (modelling, optimisation, behaviour, etc.)
- No "Session X" references
- No "out-of-sample" language
- No "momentum strategy" or "MARSIMO"
- No "natural/naturally"
- No defensive or justifying tone in results sections
- Murphy (1999) and Elder (1993) as primary fallback sources if citations needed
- Academic register throughout — the notebook is written as a research paper
