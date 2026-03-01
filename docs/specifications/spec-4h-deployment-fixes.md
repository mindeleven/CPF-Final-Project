# Specification: 4H Live Trading Deployment Fixes

**Date:** March 1, 2026
**Session:** 09C
**Author:** Juergen Kober + Claude Code Opus 4.6
**Purpose:** Fix configuration and bar size bugs before 4H paper trading run (March 2-6, 2026)

---

## Context

The 5-minute live trading run (Feb 23-27) revealed Error 201 currency leverage issues (now fixed via manual EUR→USD conversion). Preparing for the 4-hour live trading run uncovered two critical bugs that would prevent correct 4H operation:

1. **Wrong strategy parameters in `deployment/config_live.py`**
2. **Hardcoded 5-minute bar size strings in `deployment/trading_bot.py`**

Both must be fixed before Monday's deployment. No local testing is possible (market closed, Docker build on server only). Changes are verified by code review.

---

## Issue 1: Wrong Strategy Parameters in config_live.py

**Location:** `deployment/config_live.py` lines 83, 86

**Current (incorrect) code:**
```python
elif TIMEFRAME == "4H":
    # 4-hour optimized parameters (Session 6B)
    SMA_FAST = 20
    SMA_SLOW = 70
    RSI_PERIOD = 21      # ❌ WRONG
    RSI_LOWER = 35
    RSI_UPPER = 70
    MOMENTUM_PERIOD = 14 # ❌ WRONG
    MOMENTUM_THRESHOLD = 0.0
```

**Problem:**
- `RSI_PERIOD = 21` should be `14`
- `MOMENTUM_PERIOD = 14` should be `10`

**Root cause:**
Session 6B optimization did NOT vary `rsi_period` or `momentum_period` — these parameters always use config defaults from `TIMEFRAME_CONFIGS` (14 and 10 for all timeframes). The optimized parameters are only: `sma_fast`, `sma_slow`, `rsi_lower`, `rsi_upper`, `momentum_threshold`.

**Historical note:**
This is the **third location** where these stale values (RSI 21, Momentum 14) appeared:
1. `CLAUDE.md` line 127 (fixed in commit `967bcc3`, Session 09)
2. Notebook Cell 190 comment (identified but not yet fixed in notebook source)
3. `deployment/config_live.py` lines 83, 86 (discovered and fixed in this session)

All three instances stem from an early hypothesis (pre-Session 6) that 4H timeframe might benefit from longer periods, which was never validated. The grid search always used config defaults (14/10), and those produced the optimal Sharpe of 1.42.

**Correct values:**
```python
elif TIMEFRAME == "4H":
    # 4-hour optimized parameters (Session 6B)
    SMA_FAST = 20
    SMA_SLOW = 70
    RSI_PERIOD = 14      # ✓ Corrected
    RSI_LOWER = 35
    RSI_UPPER = 70
    MOMENTUM_PERIOD = 10 # ✓ Corrected
    MOMENTUM_THRESHOLD = 0.0
```

---

## Issue 2: Hardcoded Bar Size Strings in trading_bot.py

**Location:** `deployment/trading_bot.py`
- `load_historical_warmup()` method (lines ~541, 545, 553)
- `fetch_latest_bar()` method (lines ~593, 594)

**Problem:**
Both methods hardcode IB bar size strings for 5-minute bars:
- `barSizeSetting="5 mins"` in both methods
- `durationStr="300 S"` in `fetch_latest_bar()` (300 seconds = 5 minutes)
- Duration calculation `bars_needed * 5 * 60` in `load_historical_warmup()`

When `TIMEFRAME = "4H"`, these hardcoded strings cause the bot to:
- Fetch 5-minute bars instead of 4-hour bars
- Compute indicators on wrong timeframe data
- Generate signals that don't match backtest conditions

**Solution:**
Import `TIMEFRAME_CONFIGS` and `get_timeframe_config` from `modules.config`, then use the config values dynamically:

```python
from modules.config import TIMEFRAME_CONFIGS, get_timeframe_config

# In load_historical_warmup():
tf_config = get_timeframe_config(TIMEFRAME)
ib_bar_size = tf_config["ib_bar_size"]  # "5 mins" or "4 hours"

# Calculate duration based on bar size
if TIMEFRAME == "5min":
    bar_duration_seconds = 5 * 60
elif TIMEFRAME == "4H":
    bar_duration_seconds = 4 * 60 * 60
else:
    raise ValueError(f"Unsupported timeframe: {TIMEFRAME}")

duration_seconds = bars_needed * bar_duration_seconds
duration_str = f"{duration_seconds} S"

# In fetch_latest_bar():
tf_config = get_timeframe_config(TIMEFRAME)
ib_bar_size = tf_config["ib_bar_size"]

if TIMEFRAME == "5min":
    duration_str = "300 S"  # 5 minutes
elif TIMEFRAME == "4H":
    duration_str = "14400 S"  # 4 hours
else:
    raise ValueError(f"Unsupported timeframe: {TIMEFRAME}")
```

This approach:
- Uses the same `ib_bar_size` key that backtest and data fetching scripts use
- Eliminates all hardcoded timeframe-specific strings
- Makes the bot fully parametric across 5min and 4H timeframes

---

## Configuration Changes for 4H Run

**Location:** `deployment/config_live.py` lines 24, 33

**Changes:**
```python
TIMEFRAME = "4H"      # Was: "5min"
RUN_DURATION = "5d"   # Was: "1h"
```

**Rationale:**
- `TIMEFRAME = "4H"` activates 4-hour strategy parameters
- `RUN_DURATION = "5d"` runs Monday-Friday (full trading week)

---

## Issue 3: Baseline Position Snapshot

**Location:** `deployment/trading_bot.py` (added March 2, 2026)

**Problem:**
When the user performs manual EUR→USD currency conversion via IB Gateway (as recommended to fix Error 201 issues), the conversion may create positions visible to the bot's reconciliation logic. The bot could mistakenly interpret these pre-existing positions as trading positions that need to be managed or closed, leading to unintended trades or state corruption.

**Solution:**
Add a baseline position snapshot feature that captures all existing positions at startup, before any reconciliation or trading begins. The bot then filters out these baseline positions from all position queries, ensuring it only acts on positions it creates itself.

**Implementation:**

1. **In `__init__` (line 112):** Add `self.baseline_positions: set = set()`

2. **At startup (lines 1096-1102), after capital is set and before reconciliation:**
```python
# Capture baseline positions (e.g., from EUR→USD conversion)
existing = await self.ib.reqPositionsAsync()
self.baseline_positions = {
    (p.contract.symbol, p.contract.currency, round(p.position))
    for p in existing
}
self.logger.info(f"Baseline positions at startup: {self.baseline_positions}")
```

3. **In `reconcile_positions()` (lines 263-268):** Filter positions before reconciliation logic:
```python
# positions() is synchronous — returns complete list immediately
# Filter out baseline positions (e.g., EUR→USD conversion)
positions = [
    p for p in self.ib.positions()
    if (p.contract.symbol, p.contract.currency, round(p.position))
    not in self.baseline_positions
]
```

4. **In `_get_ib_eur_position()` (lines 422-427):** Filter positions before checking EUR/USD position:
```python
# Filter out baseline positions (e.g., EUR→USD conversion)
positions = [
    p for p in self.ib.positions()
    if (p.contract.symbol, p.contract.currency, round(p.position))
    not in self.baseline_positions
]
```

**Key design choices:**
- Tuple format `(symbol, currency, round(position))` uniquely identifies a position
- `round(position)` handles floating-point precision issues in position size matching
- Set lookup is O(1) for efficient filtering
- Snapshot taken early (after connect, before reconciliation) to capture true baseline
- Filtering applied in ALL position query locations for consistency

**Behavior:**
- If no pre-existing positions at startup: `baseline_positions = set()` (empty), no filtering effect
- If EUR→USD conversion position exists: Position is added to baseline set and ignored by all reconciliation logic
- Bot only sees and acts on positions it opens via `execute_order()`

**Risk mitigation:**
- Contained change: only 3 locations modified (init, reconcile, pre-trade check)
- No behavior change if account starts clean (current state)
- Activates only when conversion positions are present
- Log statement confirms baseline at startup for debugging

---

## Verification Method

**No local testing possible:**
- Market closed until Monday morning (March 2)
- Docker image built on server only (not local machine)
- Changes are unverified by execution

**Verification approach:**
- Code review of all modified sections
- Confirmation that TIMEFRAME_CONFIGS contains correct values
- Manual inspection of parameter values vs. Session 6B optimization results

**Risk mitigation:**
- First validation will occur when bot starts Monday morning
- Bot logs will immediately show bar size being fetched
- Startup warmup log will confirm number of bars loaded
- If wrong bar size is detected, stop bot and rebuild with corrected code

---

## Success Criteria

**On Monday startup, bot logs should show:**
```
Loading N historical 4-hour bars for warmup...
Successfully loaded N bars for indicator warmup
```

NOT:
```
Loading N historical 5-min bars for warmup...
```

**During run, fetch_latest_bar() should log:**
```
Fetching latest 4-hour bar...
```

NOT:
```
Fetching latest 5-minute bar...
```

---

## Files Modified

1. `deployment/config_live.py`
   - Lines 24, 33: TIMEFRAME and RUN_DURATION
   - Lines 83, 86: RSI_PERIOD and MOMENTUM_PERIOD

2. `deployment/trading_bot.py`
   - Import section: Add TIMEFRAME_CONFIGS, get_timeframe_config
   - `__init__()` method: Add baseline_positions set (line 112)
   - `run()` method: Populate baseline_positions at startup (lines 1096-1102)
   - `reconcile_positions()` method: Filter baseline positions (lines 263-268)
   - `_get_ib_eur_position()` method: Filter baseline positions (lines 422-427)
   - `load_historical_warmup()` method: Dynamic bar size and duration
   - `fetch_latest_bar()` method: Dynamic bar size and duration

---

## References

- Session 6B optimization results: `data/optimization/optimization_results_4H_corrected.csv`
- TIMEFRAME_CONFIGS: `modules/config/timeframes.py` lines 60-80
- Session 09 handoff: `docs/handoffs/session-09-live-results-5min.md`

---

**Status:** Specification complete, ready for implementation
**Next:** Apply fixes to code, write handoff document, commit changes
