# Session 11 — Third Run Results (5-minute, Run 3)

**Log files:** `deployment/logs/trading_bot_5min_5d_20260308_225504.log` and `trades_5min_5d_20260308_225504.csv`
**Container:** `trading-bot-5min-2nd`
**Analysis date:** March 13, 2026

---

## Run Summary

The third production run of the 5-minute strategy ran from 2026-03-08 22:55:04 UTC to
2026-03-13 16:00:23 UTC — a wall-clock duration of 4 days, 17 hours, and 5 minutes. The run
ended 6 hours 55 minutes short of the 5-day RUN_DURATION target because the `CLOSE_BEFORE_WEEKEND`
flag triggered at Friday 16:00 local time (log line: "Approaching weekend. Stopping."). Strategy
parameters were confirmed in the startup log: SMA 15/70, RSI 14 (thresholds 35/75), Momentum 10
(threshold 0.0). The account started with a EUR 953,293.75 balance, which satisfied the
MIN_EUR_BALANCE check. Baseline positions at startup: empty set (no pre-existing FX positions).

Nine trades were executed. Five were profitable and four were not, giving a win rate of 55.6% and
a total net P&L of +EUR 47.52. Capital at shutdown was EUR 953,341.27 (return reported as 0.00%
due to the rounding of the 5-significant-figure percentage against a large account balance). Four
trades were closed by the IB Gateway paper trading nightly reset and recorded via reconciliation;
four were closed by strategy signals; one was closed by the weekend-shutdown routine.

---

## Trade Log

| # | Direction | Entry time (UTC) | Exit time (UTC) | Entry price | Exit price | Net P&L (EUR) | Close type |
|---|-----------|-----------------|----------------|-------------|------------|---------------|------------|
| 1 | SHORT | 2026-03-09 09:00:44 | 2026-03-09 10:00:59 | 1.15357 | 1.15539 | −34.97 | Strategy signal |
| 2 | LONG | 2026-03-09 10:01:00 | 2026-03-09 19:00:15 | 1.15538 | 1.15757 | +34.38 | Strategy signal |
| 3 | SHORT | 2026-03-09 19:00:17 | 2026-03-09 19:20:22 | 1.15758 | 1.16095 | −61.50 | Strategy signal |
| 4 | LONG | 2026-03-09 19:20:23 | 2026-03-09 23:45:32 | 1.16061 | 1.16301 | +37.92 | IB reconciliation |
| 5 | LONG | 2026-03-10 06:06:04 | 2026-03-10 18:31:00 | 1.16224 | 1.16334 | +15.47 | Strategy signal |
| 6 | SHORT | 2026-03-10 18:31:01 | 2026-03-10 23:45:34 | 1.16334 | 1.16106 | +35.83 | IB reconciliation |
| 7 | SHORT | 2026-03-11 07:50:32 | 2026-03-11 23:45:34 | 1.16209 | 1.15465 | +125.41 | IB reconciliation |
| 8 | LONG | 2026-03-12 06:25:09 | 2026-03-12 23:45:31 | 1.15469 | 1.15156 | −57.83 | IB reconciliation |
| 9 | LONG | 2026-03-13 12:00:26 | 2026-03-13 16:00:23 | 1.14683 | 1.14433 | −47.19 | Weekend shutdown |

Exit prices for trades 4, 6, 7, and 8 are estimated: the reconciliation logic records the last
known price at the time of the mismatch detection, not the actual IB fill price from the paper
trading reset.

**Long trades:** 5 (trades 2, 4, 5, 8, 9)
**Short trades:** 4 (trades 1, 3, 6, 7)
**Winning trades:** 5 (trades 2, 4, 5, 6, 7)
**Losing trades:** 4 (trades 1, 3, 8, 9)
**Largest win:** +EUR 125.41 (trade 7)
**Largest loss:** −EUR 61.50 (trade 3)
**Average P&L per trade:** +EUR 5.28

---

## Reconciliation Analysis

| Close type | Count | Percentage |
|------------|-------|------------|
| Strategy signal | 4 | 44.4% |
| IB reconciliation (nightly reset) | 4 | 44.4% |
| Weekend shutdown | 1 | 11.1% |

### Comparison to February 23–27 run

| Metric | Feb 23–27 run | Third run (Mar 8–13) |
|--------|--------------|----------------------|
| Total trades | 11 | 9 |
| Closed by strategy signal | 4 (36.4%) | 4 (44.4%) |
| Closed by IB reconciliation | 7 (63.6%) | 4 (44.4%) |
| Closed by other (shutdown) | 0 | 1 (11.1%) |
| Net P&L (EUR) | −10.24 | +47.52 |
| Win rate | 36.4% | 55.6% |
| Error 201 occurrences | 3 | 0 |

The maintenance window reduced the reconciliation-close rate from 63.6% to 44.4%, a real but
partial improvement. The remaining four reconciliation closes all followed the same pattern: a
position was opened during the trading day, remained open when the maintenance window started at
23:30 CET, and was then closed by IB's paper trading nightly reset at 00:45 CET. The maintenance
window prevents the bot from opening new positions during the risky window but cannot protect
positions that were already open when the pause began. This is a structural limitation of paper
trading accounts, not a code deficiency — the behaviour does not occur on live accounts.

The four strategy-signal closes in the third run are identical in count to the February run (also
4), suggesting the strategy's signal generation rate was broadly comparable across both weeks. The
improvement in win rate (36.4% → 55.6%) and P&L (−10.24 → +47.52 EUR) is real but arises from a
sample of 9 trades and carries no statistical weight.

---

## Infrastructure Events by Night

**Night 1 — Mar 8→9:**
- Maintenance window entered: 2026-03-08 23:30:14 UTC (23:30 UTC = 00:30 CET ✓)
- Position going into window: FLAT
- Hard disconnect (Peer closed connection): 2026-03-08 23:45:01 UTC
- Reconnection: 4 attempts, success at ~23:45:30 UTC (~29 seconds of downtime)
- Soft reboot (Error 1100 sequence): 2026-03-09 04:16:35–04:17:01 UTC (6 × Error 1100, then Error 1102 at 04:17:01)
- Reconciliation after Error 1102 (04:17:45): FLAT confirmed — no mismatch
- Maintenance window exited: 2026-03-09 05:45:49 UTC (05:45 UTC = 06:45 CET ✓), warmup reloaded
- Position mismatch: None (bot was FLAT going into the window)

**Night 2 — Mar 9→10:**
- Maintenance window entered: 2026-03-09 23:30:28 UTC
- Position going into window: LONG @ 1.16061 (trade 4, opened at 19:20 UTC)
- Hard disconnect: 2026-03-09 23:45:00 UTC
- Reconnection: 1 attempt, success at 23:45:32 UTC (~32 seconds of downtime)
- Position mismatch detected: 2026-03-09 23:45:32 UTC — bot LONG, IB FLAT
- Reconciliation close recorded: exit @ 1.16301, P&L +EUR 37.92 (estimated)
- Soft reboot: 2026-03-10 04:26:40–04:30:50 UTC (14 × Error 1100, then Error 1102 at 04:30:50)
- Reconciliation after Error 1102 (04:31:49): FLAT confirmed
- Maintenance window exited: 2026-03-10 05:45:52 UTC, warmup reloaded

**Night 3 — Mar 10→11:**
- Maintenance window entered: 2026-03-10 23:30:25 UTC
- Position going into window: SHORT @ 1.16334 (trade 6, opened at 18:31 UTC)
- Hard disconnect: 2026-03-10 23:45:01 UTC; second error at 23:45:28 UTC ("clientId 753 already in use?")
- Reconnection: 2 attempts, success at 23:45:34 UTC (~33 seconds of downtime)
- Position mismatch detected: 2026-03-10 23:45:34 UTC — bot SHORT, IB FLAT
- Reconciliation close recorded: exit @ 1.16106, P&L +EUR 35.83 (estimated)
- Soft reboot: 2026-03-11 04:22:11–04:23:54 UTC (10 × Error 1100, then Error 1102 at 04:23:54)
- Reconciliation after Error 1102 (04:24:50): FLAT confirmed
- Maintenance window exited: 2026-03-11 05:45:54 UTC, warmup reloaded

**Night 4 — Mar 11→12:**
- Maintenance window entered: 2026-03-11 23:30:25 UTC
- Position going into window: SHORT @ 1.16209 (trade 7, opened at 07:50 UTC)
- Hard disconnect: 2026-03-11 23:45:00 UTC; second error at 23:45:27 UTC ("clientId 753 already in use?")
- Reconnection: 2 attempts, success at 23:45:34 UTC (~34 seconds of downtime)
- Position mismatch detected: 2026-03-11 23:45:34 UTC — bot SHORT, IB FLAT
- Reconciliation close recorded: exit @ 1.15465, P&L +EUR 125.41 (estimated)
- Soft reboot: 2026-03-12 04:24:29–04:26:06 UTC (10 × Error 1100, then Error 1102 at 04:26:06)
- Reconciliation after Error 1102 (04:26:49): FLAT confirmed
- Maintenance window exited: 2026-03-12 05:45:53 UTC, warmup reloaded

**Night 5 — Mar 12→13:**
- Maintenance window entered: 2026-03-12 23:30:28 UTC
- Position going into window: LONG @ 1.15469 (trade 8, opened at 06:25 UTC)
- Hard disconnect: 2026-03-12 23:45:00 UTC
- Reconnection: 1 attempt, success at 23:45:31 UTC (~31 seconds of downtime)
- Position mismatch detected: 2026-03-12 23:45:31 UTC — bot LONG, IB FLAT
- Reconciliation close recorded: exit @ 1.15156, P&L −EUR 57.83 (estimated)
- Soft reboot: 2026-03-13 04:21:41–04:23:21 UTC (10 × Error 1100, then Error 1102 at 04:23:21)
- Reconciliation after Error 1102 (04:23:46): FLAT confirmed
- Maintenance window exited: 2026-03-13 05:45:50 UTC, warmup reloaded

**Run end — Mar 13:**
- Trade 9 (LONG) opened at 12:00:26 UTC, held until 16:00:23 UTC
- "Approaching weekend. Stopping." logged at 16:00:23 UTC (CLOSE_BEFORE_WEEKEND = True, Friday)
- Position closed, session summary written, disconnected

**Infrastructure summary:**
- Maintenance window: entered and exited correctly on all 5 nights ✓
- Hard disconnects: 5 (all at 23:45 UTC ±1 second) — all recovered within 1–4 reconnection attempts ✓
- "clientId already in use" warning: 2 occurrences (nights 3 and 4) — recovered on attempt 2 ✓
- Soft reboots (Error 1100 → 1102): 5 (all between 04:16–04:30 UTC each morning) — all recovered ✓
- Non-fatal `KeyError` in ib_async contractDetails handler: 5 occurrences (one per soft reboot), identical to 4H run ✓
- Error 201 (order rejections): 0 ✓
- Unhandled exceptions or crashes: 0 ✓
- Connectivity events outside active trading hours: 0 ✓

---

## Position State at Hard Disconnect

| Night | Position at window entry | Closed by IB reset? | Mismatch detected? | Estimated P&L recorded |
|-------|------------------------|---------------------|-------------------|------------------------|
| Mar 8→9 | FLAT | N/A | No | N/A |
| Mar 9→10 | LONG @ 1.16061 | Yes | Yes | +EUR 37.92 |
| Mar 10→11 | SHORT @ 1.16334 | Yes | Yes | +EUR 35.83 |
| Mar 11→12 | SHORT @ 1.16209 | Yes | Yes | +EUR 125.41 |
| Mar 12→13 | LONG @ 1.15469 | Yes | Yes | −EUR 57.83 |

Night 1 is the only night where no mismatch occurred; the bot had not yet executed any trades
when the maintenance window started. On all four subsequent nights, a position was open when the
window began and was closed by the IB paper trading reset at 00:45 CET. All four mismatches were
detected correctly on reconnection.

---

## Daily P&L Snapshots

The `_save_daily_snapshot()` routine appended a DAILY_SNAPSHOT row to the trade CSV at 23:29 CET
each night for the first four active trading nights. No snapshot was recorded on night 5 (March
12→13) because the run ended on March 13 at 16:00 UTC, before the 23:29 CET trigger. All four
rows carry the cumulative net P&L at the moment of snapshot, not the final day's result, as trades
4, 6, 7, and 8 were still open at snapshot time and closed during the subsequent reset.

| Date (CET) | Cumulative P&L at 23:29 (EUR) | Capital (EUR) | Trades completed that day |
|-----------|-------------------------------|---------------|--------------------------|
| Mar 9 | −62.09 | 953,231.66 | 3 (all closed by signal) |
| Mar 10 | −8.69 | 953,285.06 | 1 (closed by signal) |
| Mar 11 | +27.14 | 953,320.89 | 0 (trade 7 still open) |
| Mar 12 | +152.54 | 953,446.29 | 0 (trade 8 still open) |

The jump from −62.09 to −8.69 reflects the reconciliation gain from trade 4 (+37.92) and the
strategy win from trade 5 (+15.47). The jump to +27.14 reflects the reconciliation gain from
trade 6 (+35.83). The snapshot at +152.54 on March 12 reflects the reconciliation gain from trade
7 (+125.41). The final P&L of +47.52 is lower because trades 8 (−57.83) and 9 (−47.19) closed
after the last snapshot.

---

## Run Duration and Completion

- **Start:** 2026-03-08 22:55:04 UTC
- **End:** 2026-03-13 16:00:23 UTC
- **Duration:** 4 days, 17 hours, 5 minutes, 19 seconds
- **Completion:** Normal. The run ended via `CLOSE_BEFORE_WEEKEND` on Friday March 13 at 16:00
  local time, approximately 6 hours 55 minutes before the 5-day RUN_DURATION would have expired.
  This is expected behaviour. The position open at that time (trade 9, LONG) was closed cleanly
  before shutdown.

---

## Sharpe Ratio

With 9 trades executed, the sample falls below the 10-trade threshold specified in the analysis
protocol. No Sharpe ratio is calculated. The result is noted as directionally positive (+EUR 47.52,
55.6% win rate) but carries no statistical weight over a 4.7-day window.

---

## Inclusion Recommendation

**INCLUDE**

The third run adds one specific piece of knowledge not available from the February run: a
quantified reduction in reconciliation-closed trades (63.6% → 44.4%) that confirms the maintenance
window works as designed while also documenting its limitation — positions already open at window
entry remain exposed to the paper trading nightly reset. The P&L and win-rate improvement
(−10.24 EUR / 36.4% → +47.52 EUR / 55.6%) is directionally positive but the sample is too small
to draw strategy conclusions from. The infrastructure performed identically to the 4H run: all
connectivity events recovered autonomously, no Error 201, no crashes. No finding in these results
contradicts the existing narrative in Sections 9 or 10; the result fits naturally into the
established framing of infrastructure resilience and paper-trading limitations.

Permitted notebook changes: one additional paragraph in Section 9.2, one addition to Section 9.3
(already covers reconciliation noise), brief mention in Section 7.6. No structural changes
required.

---

## Suggested Notebook Text

### Addition to Section 9.2 (after the February 5-minute subsection)

A third production run was conducted from 8 March to 13 March 2026 using identical parameters,
with the addition of the configurable maintenance window described in Section 7.6. Nine trades
were executed over 4 days and 17 hours, producing a net P&L of +EUR 47.52 (win rate 55.6%,
average trade +EUR 5.28). The primary purpose of this run was to assess whether the maintenance
window reduced the proportion of trades closed by IB's paper trading nightly reset, which had
accounted for 63.6% of all trade closures in the February run. Four of the nine trades were closed
by reconciliation (44.4%), down from 63.6%, confirming a meaningful but partial improvement. The
remaining four reconciliation closes followed a consistent pattern: a position was opened during
the trading day, was held open when the maintenance window began at 00:30 CET, and was
subsequently closed by IB's nightly reset at 00:45 CET. The maintenance window prevents the bot
from placing new orders during the reset window but does not close existing positions on entry,
as doing so would impose arbitrary exits on live-account deployments where the nightly reset does
not occur. The run ended at Friday 16:00 local time via the weekend-close routine, six hours
before the five-day timer would have expired. Infrastructure performance was consistent with
previous runs: all five hard disconnects and five soft reboots recovered autonomously, and no
order rejections were recorded.

### Addition to Section 9.3 (Lessons Learned)

The third run confirmed that the maintenance window addresses the proximate cause of
reconciliation noise — the bot attempting to manage positions through the Gateway reboot sequence —
but cannot eliminate it entirely on a paper trading account. Any position held open at the start
of the maintenance window at 00:30 CET remains vulnerable to closure by IB's paper trading reset
at 00:45 CET. On a live account this distinction is irrelevant, as the nightly reset does not
close positions; the maintenance window would then serve purely as a circuit-breaker to prevent
order attempts during Gateway downtime.
