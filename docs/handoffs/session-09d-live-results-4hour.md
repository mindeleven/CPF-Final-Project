# Session 09D: Live Trading Results Analysis — 4-Hour Timeframe

**Date:** March 6, 2026
**Trading Period:** March 1–6, 2026 (5 days)
**Model:** Claude Sonnet 4.6
**Status:** Complete

---

## Preliminary Checks

### Baseline Position Filtering

**Confirmed.** Line 40 of the log reads:

```
2026-03-01 23:38:25,169 - INFO - Baseline positions at startup: {('EUR', 'USD', -50000)}
```

This is the virtual FX position from a prior EUR→USD currency conversion. Lines 41–43 confirm the reconciliation logic correctly filtered it:

```
2026-03-01 23:38:25,169 - INFO - Reconciling position state with IB...
2026-03-01 23:38:25,169 - INFO - Position confirmed: FLAT (no open positions)
2026-03-01 23:38:25,169 - INFO - Reconciliation complete. Current state: FLAT
```

The -50,000 baseline was not treated as a bot-originated position.

### Parameter Confirmation

**Confirmed.** Lines 1–2 of the log:

```
2026-03-01 23:38:24,423 - INFO - Trading Bot initialized for 4H timeframe
2026-03-01 23:38:24,424 - INFO - Parameters: SMA 20/70, RSI 14 (35/70), Momentum 10 (threshold 0.0)
```

RSI period 14 and Momentum period 10 are confirmed. These are the corrected parameters (not the earlier erroneous values of 21 and 14).

---

## 1. Run Metadata

**Start time:** 2026-03-01 23:38:24 CET
**End time:** 2026-03-06 16:01:32 CET
**Total wall-clock duration:** 4 days, 16 hours, 23 minutes, 8 seconds (**112.4 hours**)

The bot stopped normally at 16:01 CET on Friday via the "Approaching weekend" shutdown logic. No manual intervention.

**Log statistics:**
- Total log lines: 772
- Bars collected: 120 (92 warmup bars loaded at startup + 28 bars during the live run)

**Market context at startup:**
EUR/USD opened the run at approximately 1.1760 after gapping sharply lower at the Sunday open following US/Israeli strikes on Iran over the preceding weekend. The first live bar (2026-03-01 19:00 ET) closed at 1.17593. By end of March 2 the rate had fallen to approximately 1.167, and by March 3 to approximately 1.159 — a ~200-pip decline in the first two trading days.

**IB connectivity type:**
The run was characterised by two distinct nightly event patterns:
1. **Hard disconnects** at 23:45 CET each night (Peer closed connection — Gateway process restart)
2. **Soft reboots** (Error 1100 → 1102 sequences) at ~05:22–05:49 CET each morning

This differs from the 5-minute run, which showed only soft reboots.

---

## 2. Trade Summary

**Total trades executed: 0**

The trade CSV contains only a header row. The session summary confirms:

```
Timeframe: 4H
Parameters: SMA 20/70, RSI 35/70, Mom 0.0
Duration: 4 days, 16:23:08.001248
Total Trades: 0
Final Capital: EUR 952,192.21
Return: 0.00%
```

No buy or sell orders were placed at any point during the run. The bot was always in a FLAT position state from startup to shutdown.

**Capital:**
The capital figure of EUR 952,192.21 reflects the account balance at startup — unchanged, as no trades were executed and no transaction costs were incurred.

---

## 3. Infrastructure Events

### Hard Disconnects (23:45 CET nightly)

A "Peer closed connection" event occurred at exactly 23:45:00 CET each night for all five nights of the run. These represent a full TCP disconnection of the IB Gateway process, requiring the bot to perform a complete reconnection sequence.

| Night | Disconnect time | "Connection lost" detected | Reconnected | Attempt | Notes |
|-------|----------------|---------------------------|-------------|---------|-------|
| Mar 1→2 | 23:45:01 | 23:48:26 (+3.4 min) | 23:48:29 | 1 | Detection delay: connection monitor poll lag |
| Mar 2→3 | 23:45:00 | 23:45:15 (+15 sec) | 23:45:30 | **4** | Attempts 1–3 failed (connection refused); exponential backoff |
| Mar 3→4 | 23:45:00 | 23:48:39 (+3.6 min) | 23:48:42 | 1 | Detection delay: connection monitor poll lag |
| Mar 4→5 | 23:45:00 | 23:45:55 (+55 sec) | 23:45:58 | 1 | |
| Mar 5→6 | 23:45:00 | 23:45:13 (+13 sec) | 23:45:29 | **4** | Attempts 1–3 failed (connection refused); exponential backoff |

The variable detection lag (13 seconds to 3.6 minutes) reflects the asynchronous connection monitoring loop. On two nights (March 2→3, March 5→6), the Gateway process had not yet restarted when the bot first attempted to reconnect, causing the first three attempts to be refused immediately. Exponential backoff (waiting 1s, 2s, 4s before attempts 1, 2, 3) meant the fourth attempt succeeded within 29–30 seconds of detection. All five reconnections completed successfully.

Each hard reconnect was followed by position reconciliation (see below).

### Soft Reboots (Error 1100 → 1102)

A separate set of five soft IB Gateway reboot events occurred each morning between 05:22 and 05:49 CET. These follow the same 1100/1102 pattern as the 5-minute run and are consistent with IB Gateway's documented daily reset window (~00:15–01:45 ET).

| Date | Error 1100 (first) | Error 1102 | Duration | Reconciliation ran |
|------|-------------------|------------|----------|-------------------|
| Mar 2 | 05:22:28 | 05:24:14 | ~2 min | 05:29:15 → FLAT ✓ |
| Mar 3 | 05:45:01 | 05:49:48 | ~5 min | 05:51:59 → FLAT ✓ |
| Mar 4 | 05:25:18 | 05:26:19 | ~1 min | 05:29:56 → FLAT ✓ |
| Mar 5 | 05:40:35 | 05:43:19 | ~3 min | 05:47:27 → FLAT ✓ |
| Mar 6 | 05:27:25 | 05:29:04 | ~2 min | 05:30:58 → FLAT ✓ |

All five reconciliations confirmed a FLAT position. No mismatches were detected.

### Reconciliation Summary

**Total reconciliations: 10** (5 post-hard-disconnect + 5 post-soft-reboot)
**Position mismatches detected: 0**
**All reconciliations found: FLAT**

Since no positions were ever opened, there were no positions for IB to close during any of the nightly resets. All reconciliations returned immediately with "Position confirmed: FLAT."

### Error 201 Occurrences

**None.** No order rejections of any kind were recorded. The account was manually rebalanced (EUR→USD conversion) before deployment, and no orders were placed in any case.

### Other Errors Noted

**Recurring `KeyError: 8521` (non-fatal):**
This error appears five times, once during each soft reboot cycle. It originates in `ib_async/wrapper.py:874` (contractDetails handler) when a contract details response arrives after the corresponding request has already been cleaned up during the reconnection sequence. The affected request ID is always 8521. This is a benign race condition in the ib_async library — it does not interrupt processing and the bot resumed normally after each occurrence.

**Error 162, reqId 8729 (once, March 5 16:59):**
"API historical data query cancelled." This occurred during a brief data farm connectivity blip. The bot logged "reqHistoricalData: Timeout" and "No bar data returned." The bot continued on the next check cycle without incident. This was the only occurrence of a missed bar data fetch.

**Error 366 (twice, March 3 and March 5):**
"No historical data query found for ticker id." Both occurred during soft reboot events when a `reqHistoricalData` call was in flight at the moment connectivity was lost. Non-fatal.

---

## 4. Execution Quality

**Fill timeouts:** None (no orders were placed).
**Order rejections:** None.
**Position mismatches:** None detected in any of the 10 reconciliations.
**Connectivity recovery:** All 10 events (5 hard + 5 soft) recovered successfully. No manual intervention required at any point.

---

## 5. Sharpe Ratio

**Not calculable.** Zero trades were executed during the run. No return series exists from which a Sharpe ratio could be derived.

---

## 6. Interpretation: Trade Count in Context

### Is zero trades consistent with the backtest rate?

Yes. The 4H backtest over approximately three years (Feb 2023 – Feb 2026) produced 45 trades, giving a rate of approximately 15 trades per year, or roughly one trade every 17 calendar days. Applied to a 5-day window, the expected number of trades is approximately 0.29. Under a Poisson process assumption, the probability of observing zero trades in any given 5-day window is:

P(0) = e^(−5/17) ≈ 0.74

Zero trades is therefore the single most likely outcome for any 5-day live run, with roughly a 74% probability. The observed result is entirely consistent with the backtest rate.

The 5-minute backtest (107 trades over 6 weeks, ~18 trades per week) makes a 5-day window feel productive; the 4-hour timeframe operates on a fundamentally different cadence. The comparison is misleading and should be avoided.

### Role of the geopolitical market event

The run began on Sunday March 1 at 23:38 CET into a market that had already repriced sharply following US/Israeli military strikes on Iran over the weekend. EUR/USD gapped approximately 100–150 pips lower at the Sunday open, continuing to fall to approximately 1.155 by March 3 before partially recovering.

Several mechanisms could contribute to suppressed signal generation in this environment:

1. **Indicator lag relative to the gap.** The slow SMA (70 bars × 4H = ~11.7 trading days of lookback) incorporates historical data that predates the geopolitical event. At startup the fast SMA (20 bars ≈ 3.3 trading days) was already adjusting downward toward the new price level, but the crossover geometry depends on both SMAs being well-positioned. If the fast SMA was already below the slow SMA when the bot started — reflecting the existing downtrend — the bot would need the fast SMA to cross back above the slow SMA for a long signal, or to deepen further below it for a short signal.

2. **RSI and momentum filter interaction.** The RSI lower threshold is 35. In a sharp downtrend, RSI can reach or overshoot 35 briefly and then recover without generating a persistent crossing that aligns with SMA and momentum conditions simultaneously. The momentum threshold of 0.0 (any non-zero momentum) is permissive, but the RSI filter may have prevented entries during brief recoveries.

3. **Ranging behaviour following the initial drop.** After the initial sharp decline on March 2, EUR/USD traded in a relatively narrow range (approximately 1.155–1.167) for the remainder of the week. The 70-bar slow SMA was lagging behind the new lower price regime, and the price action was not trending strongly enough in either direction to generate a clean SMA crossover with confirming RSI and momentum readings.

It is not possible to determine from the log alone which of these mechanisms dominated — doing so would require reconstructing the indicator values from the historical data at each bar, which was not logged. The key conclusion is that zero trades over five days is a statistically expected outcome for this timeframe, with or without the geopolitical context. The geopolitical event is a plausible contributing factor but is not necessary to explain the result.

---

## 7. Raw Data Appendix

### Trade Log

No trades were executed during this run. The trade log contains only the header row.

### EUR/USD Price Progression (sampled from bar log)

The following bars were processed by the bot during the live run. These are the bars on which the strategy evaluated signals; none produced a trade entry.

| Bar timestamp (ET) | Open | High | Low | Close |
|--------------------|------|------|-----|-------|
| 2026-03-01 19:00 | 1.17592 | 1.17619 | 1.17562 | 1.17593 |
| 2026-03-01 23:00 | 1.17888 | 1.17904 | 1.17887 | 1.17901 |
| 2026-03-02 03:00 | 1.17163 | 1.17234 | 1.17156 | 1.17179 |
| 2026-03-02 07:00 | 1.17333 | 1.17341 | 1.17301 | 1.17335 |
| 2026-03-02 11:00 | 1.16802 | 1.16810 | 1.16762 | 1.16780 |
| 2026-03-02 15:00 | 1.17111 | 1.17132 | 1.17074 | 1.17081 |
| 2026-03-02 17:15 | 1.16865 | 1.16873 | 1.16865 | 1.16868 |
| 2026-03-02 19:00 | 1.16947 | 1.16949 | 1.16935 | 1.16937 |
| 2026-03-02 23:00 | 1.16904 | 1.16909 | 1.16902 | 1.16903 |
| 2026-03-03 03:00 | 1.16437 | 1.16448 | 1.16412 | 1.16431 |
| 2026-03-03 07:00 | 1.15974 | 1.15976 | 1.15925 | 1.15928 |
| 2026-03-03 11:00 | 1.15728 | 1.15749 | 1.15715 | 1.15724 |
| 2026-03-03 15:00 | 1.16124 | 1.16162 | 1.16112 | 1.16135 |
| 2026-03-03 17:15 | 1.16142 | 1.16142 | 1.16104 | 1.16124 |
| 2026-03-03 19:00 | 1.16108 | 1.16111 | 1.16047 | 1.16066 |
| 2026-03-03 23:00 | 1.16085 | 1.16101 | 1.16084 | 1.16091 |
| 2026-03-04 03:00 | 1.16159 | 1.16165 | 1.16153 | 1.16162 |
| 2026-03-04 07:00 | 1.16352 | 1.16362 | 1.16345 | 1.16345 |
| 2026-03-04 11:00 | 1.16402 | 1.16410 | 1.16402 | 1.16406 |
| 2026-03-04 15:00 | 1.16398 | 1.16410 | 1.16398 | 1.16404 |
| 2026-03-04 17:15 | 1.16310 | 1.16335 | 1.16310 | 1.16329 |
| 2026-03-04 19:00 | 1.16349 | 1.16352 | 1.16332 | 1.16334 |
| 2026-03-04 23:00 | 1.16132 | 1.16132 | 1.16107 | 1.16108 |
| 2026-03-05 03:00 | 1.16050 | 1.16051 | 1.15975 | 1.15986 |
| 2026-03-05 07:00 | 1.16114 | 1.16126 | 1.16094 | 1.16105 |
| 2026-03-05 11:00 | 1.15831 | 1.15858 | 1.15804 | 1.15858 |
| 2026-03-05 15:00 | 1.15730 | 1.15734 | 1.15702 | 1.15708 |
| 2026-03-05 17:15 | 1.16073 | 1.16084 | 1.16071 | 1.16073 |
| 2026-03-05 19:00 | 1.16067 | 1.16074 | 1.16061 | 1.16074 |
| 2026-03-05 23:00 | 1.16200 | 1.16202 | 1.16195 | 1.16195 |
| 2026-03-06 03:00 | 1.16147 | 1.16147 | 1.16116 | 1.16138 |
| 2026-03-06 07:00 | 1.15626 | 1.15650 | 1.15626 | 1.15644 |

**Note:** Bar timestamps are in US Eastern Time (ET) as logged. The warmup bars (bars 1–92 covering the prior ~14 trading days) are not shown here as they were not part of the live run period.

---

## Notes for Section 9.2 of the Notebook

The following items need to be incorporated into the 4H subsection of Section 9.2:

- **Run period:** Sunday March 1, 2026 at 23:38 CET through Friday March 6, 2026 at 16:01 CET (112.4 hours)
- **Trade count:** 0
- **P&L:** EUR 0.00 (no trades, no costs incurred)
- **Infrastructure:** 10 connectivity events (5 hard disconnects at 23:45 CET + 5 soft reboots at ~05:25 CET); all recovered successfully; no position mismatches
- **Error 201:** None (account was pre-rebalanced; in any case no orders were placed)
- **Statistical context for zero trades:** A 74% probability outcome given the 4H backtest rate of ~15 trades/year. Not an anomaly.
- **Market context:** Strongly directional post-geopolitical environment (Iran strikes), EUR/USD ~200 pip decline in first two days. No signal was generated despite the trending character of the move — consistent with the strategy's slow SMA parameters requiring a sustained, clean crossover rather than a sharp single-direction gap.

---

**End of Session 09D Handoff**
