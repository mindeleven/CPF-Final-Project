---

# **SESSION 7F HANDOFF: Record P&L on Reconciliation-Detected Position Loss**

**Date:** February 17, 2026
**Model:** Claude Code Opus 4.6
**Commit:** `c2276d2` ("Session 7F: Record estimated P&L when position vanishes during reconciliation")
**Status:** Complete, ready for deployment

---

## Context

During the 14-hour production test (Feb 16-17, 2026), the bot opened a SHORT position at 23:00 UTC. At 23:45, the IB Gateway performed its nightly reboot. After reconnection, `reconcile_positions()` found IB reported FLAT while the bot expected SHORT @ 1.18508. Reconciliation correctly updated the bot state, but **no P&L was recorded** for the vanished position — the trade was absent from the CSV log, distorting the session's total results.

Research confirmed this is a known paper account fragility: positions can vanish during IB maintenance windows without a closing trade. The fix ensures P&L is always tracked, regardless of how a position closes.

---

## File Modified

| File | Change |
|------|--------|
| `deployment/trading_bot.py` | +50 lines |

No config changes, no new files, no new dependencies.

---

## Implementation

### New Method: `_record_reconcile_close()`

```python
def _record_reconcile_close(self, old_position: int, old_entry: float) -> None:
```

Called when `reconcile_positions()` detects the bot had a position but IB shows FLAT. It:

1. **Estimates exit price** from the last close in `self.price_history` (at most one 5-minute bar before the disconnect; falls back to entry price if no history)
2. **Calculates P&L** using the same formula as `close_position()`: gross, spread cost, net, EUR conversion
3. **Records the trade** in `self.trades` and the CSV log with direction marked as `"LONG (IB reconcile)"` or `"SHORT (IB reconcile)"`
4. **Updates `self.current_capital`** so cumulative P&L stays accurate
5. **Logs a WARNING** with estimated exit price and P&L in both EUR and USD

### Call Sites

The method is called from two branches in `reconcile_positions()` where the bot transitions from a position to FLAT:

- **Line 330:** IB returns a position object with `size == 0` and bot had a position
- **Line 340:** No EUR/USD position found at IB and bot had a position

---

## Impact on the 14-Hour Test

Had this fix been in place, the vanished SHORT (entry 1.18508, last known bar close ~1.18497) would have produced:

- A third trade in the CSV: `SHORT (IB reconcile)` with estimated P&L ~EUR +0.93
- Session total: 3 trades instead of 2
- More accurate cumulative P&L

---

## Project Status

| Session | Component | Status |
|---------|-----------|--------|
| 1-6B | Config, Data, Indicators, Strategy, Backtest, Optimization | Complete |
| 7-7D | Live Bot, Reconnection, Reconciliation, Contract Fixes | Complete |
| 7E | Critical Production Fixes (8 bugs) | Complete |
| **7F** | **Reconciliation P&L Tracking** | **Complete** |
| 8 | Notebook Integration | Pending |

---

**End of Session 7F Handoff**

---
