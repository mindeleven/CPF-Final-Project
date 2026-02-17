---

# **Specification 7F: Record P&L on Reconciliation-Detected Position Loss**

**Project:** CPF Final Project - Automated Trading System
**Module:** Trading Bot - Position Reconciliation Enhancement
**Session:** 7F
**Date:** February 17, 2026
**Priority:** MEDIUM - Data integrity for test results
**Prerequisites:** Session 7E Complete, 14-hour production test completed

---

## Problem

During the 14-hour production test (Feb 16-17, 2026), the bot opened a SHORT position at 23:00 UTC. At 23:45, the IB Gateway performed its nightly reboot. After reconnection, `reconcile_positions()` found that IB reported position = 0 while the bot expected SHORT @ 1.18508. Reconciliation correctly updated the bot state to FLAT, but **no P&L was recorded for the vanished position**. The trade is absent from the trade log, distorting the session's total P&L.

**Log evidence:**

```
23:00:13 - OPENED: SELL 20,000 EUR @ 1.18508 (slippage: 0.1 pips)
23:00:13 - Entry price recorded: 1.18508
...
23:45:00 - Peer closed connection.
23:45:32 - Reconnected successfully on attempt 2
23:45:32 - Position mismatch detected!
23:45:32 -   Bot thought: SHORT @ 1.1851
23:45:32 -   IB shows: FLAT (no position)
23:45:32 - Updated bot state to match IB: FLAT
```

No trade record, no P&L calculation, no CSV entry for this position.

---

## Root Cause

`reconcile_positions()` resets `self.position`, `self.entry_price`, and `self.entry_time` to match IB's state, but does not record the implicit close of the position that disappeared. The method was designed to sync state, not to track P&L.

---

## Research Summary

Investigation into IB paper account behavior confirmed:

- IB positions are server-side and should persist across Gateway restarts
- Paper accounts are more fragile: maintenance windows, account resets, and transient session states can cause positions to appear absent from the API
- No officially documented "reboot clears positions" behavior, but multiple community reports of positions vanishing in paper accounts during overnight maintenance
- For production code, defensive P&L tracking is recommended regardless of the cause

---

## Proposed Fix

### Scope

One method modified: `reconcile_positions()` in `deployment/trading_bot.py`.

No new files, no config changes, no new dependencies.

### Change Description

When `reconcile_positions()` detects that the bot had an open position (`self.position != 0`) but IB reports FLAT, it should:

1. **Estimate the exit price** using the last known close price from `self.price_history`
2. **Calculate P&L** using the same formula as `close_position()`
3. **Record the trade** in `self.trades` and the CSV log, with direction marked as `"LONG (IB reconcile)"` or `"SHORT (IB reconcile)"` to distinguish it from bot-initiated closes
4. **Update `self.current_capital`** so cumulative P&L stays accurate
5. **Log a WARNING** with the estimated P&L and exit price

### Exit Price Accuracy

The last price in `self.price_history` is at most one bar (5 minutes) before the disconnect. For the observed case, disconnect was at 23:45:00 and the last bar was 18:40 EST (23:40 UTC) — a 5-minute gap. This is an acceptable approximation for an edge case that should rarely occur.

### Pseudocode

```python
# In reconcile_positions(), where bot had position but IB shows FLAT:
if old_position != 0:
    # Estimate exit price from last known bar
    if len(self.price_history) > 0:
        exit_price = self.price_history["close"].iloc[-1]
    else:
        exit_price = old_entry  # fallback: P&L = 0

    # Calculate P&L (same formula as close_position)
    gross_pnl = old_position * (exit_price - old_entry) * POSITION_SIZE
    spread_cost = 2 * 0.0001 * POSITION_SIZE
    net_pnl = gross_pnl - spread_cost
    net_pnl_eur = net_pnl / exit_price if exit_price > 0 else net_pnl
    self.current_capital += net_pnl_eur

    # Record trade with reconciliation marker
    trade_record = {
        "entry_time": self.entry_time,
        "exit_time": datetime.now(),
        "direction": f"{self._position_name(old_position)} (IB reconcile)",
        "entry_price": old_entry,
        "exit_price": exit_price,
        "size": POSITION_SIZE,
        "gross_pnl": gross_pnl,
        "costs": spread_cost,
        "net_pnl": net_pnl,
        "net_pnl_eur": net_pnl_eur,
        "capital_eur": self.current_capital,
    }
    self.trades.append(trade_record)
    self._save_trade(trade_record)

    self.logger.warning(
        f"Position closed by IB (reboot/reset). "
        f"Estimated exit: {exit_price:.5f}, "
        f"P&L: EUR {net_pnl_eur:.2f} (USD {net_pnl:.2f})"
    )
```

---

## What This Does NOT Change

- The bot still trusts IB as the source of truth for position state (correct behavior)
- No persistence of position state to disk (unnecessary complexity for this project)
- No additional API calls during reconciliation (uses existing price_history data)
- No changes to `close_position()`, `open_position()`, or `execute_order()`
- No changes to `config_live.py`

---

## Verification

After implementation, verify by reviewing the existing 14-hour test log:

- Confirm that the reconciliation code path now includes P&L logging
- The estimated P&L for the vanished SHORT (entry 1.18508, estimated exit ~1.18497 from last bar) would have been approximately EUR +0.93 (a small gain, since prices dropped slightly before disconnect)
- The trade CSV would have shown 3 trades instead of 2

For live verification, the scenario cannot be reliably reproduced (requires Gateway reboot during an open position), but the code path is testable by inspection.

---

## Estimated Impact

- ~20 lines added to `reconcile_positions()`
- No risk to existing functionality (change is in a branch that only executes when a mismatch is detected)
- Ensures complete P&L records regardless of IB-side position changes

---

**End of Specification 7F**

---
