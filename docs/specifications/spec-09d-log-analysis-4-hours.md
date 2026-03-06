# Log Analysis Instructions — 4-Hour Live Trading Run

Analyse the live trading bot logs from the 4-hour paper trading run (March 2–6, 2026). 
The relevant files are in `deployment/logs/` and have `-5d-4H` as part of the filename. 
Produce a structured summary document saved as 
`docs/handoffs/session-09d-live-results-4hour.md` containing the following:

## Preliminary Checks

Before extracting trade data, confirm the following from the startup log:

- The baseline position `{('EUR', 'USD', -50000)}` appears at startup and is correctly
  filtered from reconciliation logic. This is a virtual FX position from a prior 
  EUR→USD currency conversion and should not be treated as a bot-originated trade.
- RSI_PERIOD=14 and MOMENTUM_PERIOD=10 appear in the startup config log, confirming 
  that the corrected parameters were deployed (not the earlier erroneous values of 21 
  and 14).

## 1. Run Metadata

- Confirmed start and end timestamps from the log
- Total wall-clock duration in hours
- Number of IB Gateway nightly reboot events (Error 1100 → 1102 sequences)

## 2. Trade Summary

- Total number of trades executed
- Number of long trades and short trades
- Number of winning trades and losing trades
- Win rate (%)
- Total net P&L in EUR (use EUR values where logged; note if only USD is available)
- Average P&L per trade
- Largest single winning trade and largest single losing trade
- For each trade, note whether it was closed by a strategy signal or by reconciliation
  (same distinction as in session-09-live-results-5min.md)

## 3. Infrastructure Events

- List each nightly reboot with timestamp and reconnection time
- Any other connectivity events (Error 1100/1102 outside scheduled window, or other 
  unexpected errors)
- Number of Error 201 occurrences (order rejections due to currency leverage), if any
- Confirm whether reconciliation ran after each reconnect and what state it found

## 4. Execution Quality

- Any fill timeouts (orders not filled within 30-second window)
- Any order rejections
- Any position mismatches detected by reconciliation

## 5. Sharpe Ratio

- If the trade CSV contains per-trade P&L, calculate an annualised Sharpe Ratio from 
  the trade returns. Note clearly that this is indicative only given the one-week sample.
- If insufficient trades exist for a meaningful calculation, state this explicitly.

## 6. Interpretation: Trade Count in Context

The 4-hour backtest over three years produced 45 trades — approximately 15 per year or 
roughly one trade every three to four weeks. A one-week live run would therefore be 
expected to produce 1–2 trades under normal conditions. In your interpretation, address 
the following:

- Is the observed trade count consistent with the backtest rate, or is it lower than 
  expected even for a one-week window?
- The run started on Sunday March 2 into a market that had already repriced sharply 
  following US/Israeli military strikes on Iran over the weekend. EUR/USD gapped lower 
  at the Sunday open, entering an unusual trending regime before the first bar. Consider 
  whether this event is likely to have suppressed signal generation (e.g. by causing the 
  strategy to enter immediately and hold, or by producing conflicting indicator readings), 
  or whether the low trade count is simply an expected outcome of the timeframe and 
  window length. This context is already acknowledged in Sections 10.1 and 10.4 of the 
  notebook.

## 7. Raw Data Appendix

- Include the full trade log as a table (timestamp, direction, entry price, exit price, 
  P&L EUR, P&L USD, close reason: signal or reconciliation)

---

Do not infer or estimate values that are not in the logs. Where data is missing or 
ambiguous, flag it explicitly rather than filling in a plausible value. The output will 
be used to write Section 9.2 and 9.3 of the final project notebook and must be accurate.

For structural reference and consistency, follow the same format as 
`docs/handoffs/session-09-live-results-5min.md`.