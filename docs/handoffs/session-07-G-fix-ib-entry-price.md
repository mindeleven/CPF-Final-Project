---

# **SESSION 7G HANDOFF: Fix IB Entry Price Calculation**

**Date:** February 17, 2026
**Model:** Claude Code Opus 4.6
**Status:** Complete, ready for deployment

---

## Fix

`reconcile_positions()` calculated entry price from IB as `abs(avgCost / position_size)`, producing values ~20,000x too small (e.g., 0.00006 instead of 1.18459). For IB forex contracts, `avgCost` is already the per-unit exchange rate — no division needed.

**Before:** `ib_entry = abs(ib_avg_cost / ib_size)`
**After:** `ib_entry = abs(ib_avg_cost)`

One line changed in `deployment/trading_bot.py`.

---

## Discovery

Found during the 20-hour test when the new container inherited a LONG position from the previous container. The log showed `Entry price set from IB: 0.00006` — obviously wrong for a EUR/USD rate of ~1.18.

---

**End of Session 7G Handoff**

---
