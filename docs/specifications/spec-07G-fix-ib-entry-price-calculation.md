---

# **Specification 7G: Fix IB Entry Price Calculation in Reconciliation**

**Project:** CPF Final Project - Automated Trading System
**Module:** Trading Bot - Position Reconciliation
**Session:** 7G
**Date:** February 17, 2026
**Priority:** HIGH - Causes incorrect P&L on inherited positions

---

## Problem

In `reconcile_positions()`, the entry price from IB is calculated as:

```python
ib_entry = abs(ib_avg_cost / ib_size)
```

This assumes `avgCost` is a total cost (price * quantity). For IB forex contracts, `avgCost` is already the per-unit price (the EUR/USD exchange rate). Dividing by position size produces a value ~20,000x too small (e.g., 0.00006 instead of 1.18459).

**Impact:** Any position inherited via reconciliation will have a wrong entry price, causing massively incorrect P&L when closed.

## Fix

Change `abs(ib_avg_cost / ib_size)` to `abs(ib_avg_cost)` in `reconcile_positions()`. One line, two occurrences (LONG and SHORT branches).

---

**End of Specification 7G**

---
