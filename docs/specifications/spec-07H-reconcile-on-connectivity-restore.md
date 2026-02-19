---

# **Specification 7H: Reconcile Positions on Connectivity Restore**

**Project:** CPF Final Project - Automated Trading System
**Module:** Trading Bot - Connection Management / Order Execution
**Session:** 7H
**Date:** February 19, 2026
**Priority:** HIGH - Stale position state causes accidental order opens and leverage rejections

---

## Problem

During a 3-day test run on 2026-02-18/19, IB Gateway experienced a "soft" connectivity loss (Error 1100) at ~05:23 UTC. During this disruption, IB silently closed the bot's SHORT position. When connectivity was restored (Error 1102 at 05:26), the bot did not reconcile and continued operating with stale state (thinking it was SHORT when IB was actually FLAT).

Two hours later at 06:20, a BUY signal triggered the close-then-open logic:

1. Bot sent BUY 20,000 to "close" the SHORT — but since IB was already FLAT, this **opened a new LONG +20,000**
2. Bot internally reset `self.position = 0` (thinking the close succeeded)
3. Bot sent another BUY 20,000 to open the intended LONG
4. IB **rejected** with Error 201: "FX trade would expose account to currency leverage" (already holding +20,000)
5. Bot is now stuck FLAT internally while IB has an orphaned, unmanaged LONG +20,000

**Root cause:** The bot only reconciles after a full disconnect/reconnect cycle (`is_connected()` returning `False`). Error 1100/1102 events are "soft" — the TCP connection stays alive, so `is_connected()` still returns `True`, and reconciliation never runs.

---

## Fix A: Reconcile After Error 1102 (Connectivity Restored)

Register an error handler that triggers position reconciliation when IB emits Error 1102 ("Connectivity between IBKR and Trader Workstation has been restored").

### Implementation

1. Add a flag `self._needs_reconciliation: bool = False` to `__init__`.

2. Add method `_on_error` and register it as IB's error callback in `connect()`:
   ```python
   self.ib.errorEvent += self._on_error
   ```

3. `_on_error(reqId, errorCode, errorString, contract)` checks for error code 1102. If matched, sets `self._needs_reconciliation = True` and logs a message.

4. In the main loop, after the connection health check and before fetching bars, check the flag:
   ```python
   if self._needs_reconciliation:
       self._needs_reconciliation = False
       await self.reconcile_positions()
   ```

### Why a flag instead of calling reconcile directly from the callback?

The error callback runs synchronously inside the ib_async event loop. Calling an async method (`reconcile_positions`) from a sync callback would require `asyncio.ensure_future()` or similar, which risks race conditions with the main trading loop. Using a flag keeps reconciliation in the main loop's sequential flow, where it's safe.

---

## Fix B: Verify IB Position Before Close Order

Before sending a close order, query the actual IB position and compare with bot state. If they differ, reconcile first. This is a safety net even if the Error 1102 handler is missed.

### Implementation

Add a pre-close verification step at the start of `execute_order()`, before the close-then-open logic:

```python
# Verify bot state matches IB before acting on a signal
if self.position != 0:
    positions = self.ib.positions()
    ib_pos = self._get_ib_eur_position(positions)
    if ib_pos != self.position:
        self.logger.warning(
            f"Pre-trade check: bot thinks {self._position_name(self.position)} "
            f"but IB shows {self._position_name(ib_pos)}. Reconciling..."
        )
        await self.reconcile_positions()
```

Extract the IB position lookup from `reconcile_positions()` into a small helper `_get_ib_eur_position(positions) -> int` that returns 1, -1, or 0 based on the EUR/USD position in the positions list. This avoids duplicating the contract-matching logic.

---

## Files Changed

- `deployment/trading_bot.py` — Both fixes, all in `LiveTradingBot` class

## Testing

Deploy updated bot to the DigitalOcean droplet and run a 3d test through Friday. Verify in logs that:

1. Error 1102 events trigger the `_needs_reconciliation` flag
2. Reconciliation runs in the main loop after the flag is set
3. Pre-trade position verification logs appear before close orders

---

**End of Specification 7H**

---
