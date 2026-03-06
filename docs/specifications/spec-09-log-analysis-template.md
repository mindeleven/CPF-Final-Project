**Claude Code instructions for the logfile analysis**

Here is a prompt you can paste directly into the terminal session. It assumes the bot log and trade CSV are in the project's `deployment/logs/` directory.

---

Analyse the live trading bot logs from the 5-minute paper trading run (February 23–27, 2026). The relevant files are in `deployment/logs/`. Produce a structured summary document saved as `docs/handoffs/section-09-live-results-5min.md` containing the following:

**1. Run metadata**
- Confirmed start and end timestamps from the log
- Total wall-clock duration in hours
- Number of IB Gateway nightly reboot events (Error 1100 → 1102 sequences) — this fills the `[N]` placeholder in Section 9.1

**2. Trade summary**
- Total number of trades executed
- Number of long trades and short trades
- Number of winning trades and losing trades
- Win rate (%)
- Total net P&L in EUR (use EUR values where logged; note if only USD is available)
- Average P&L per trade
- Largest single winning trade and largest single losing trade

**3. Infrastructure events**
- List each nightly reboot with timestamp and reconnection time
- Any other connectivity events (Error 1100/1102 outside scheduled window, Error 10349, or other errors)
- Confirm whether reconciliation ran after each reconnect and what state it found

**4. Execution quality**
- Any fill timeouts (orders not filled within 30-second window)
- Any order rejections
- Any position mismatches detected by reconciliation

**5. Sharpe Ratio**
- If the trade CSV contains per-trade P&L, calculate an annualised Sharpe Ratio from the trade returns. Note clearly that this is indicative only given the five-day sample.
- If insufficient trades exist for a meaningful calculation, state this explicitly.

**6. Raw data appendix**
- Include the full trade log as a table (timestamp, direction, entry price, exit price, P&L EUR, P&L USD)

Do not infer or estimate values that are not in the logs. Where data is missing or ambiguous, flag it explicitly rather than filling in a plausible value. The output will be used to write Section 9 of the final project notebook and must be accurate.
