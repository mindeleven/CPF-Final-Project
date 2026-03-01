# Session 09C: 4H Live Trading Deployment Preparation

**Date:** March 1, 2026 (Saturday)
**Model:** Claude Opus 4.6
**Status:** Complete — Ready for Monday deployment
**Next session:** Monday, March 2, 2026 (4H live run starts)

---

## Summary

Fixed three critical bugs preventing 4H live trading:
1. **Wrong strategy parameters** in `config_live.py` (RSI_PERIOD=21, MOMENTUM_PERIOD=14 should be 14, 10)
2. **Hardcoded 5-minute bar size strings** in `trading_bot.py` (two methods affected)
3. **Configuration values** for 4H run (TIMEFRAME, RUN_DURATION)

All fixes verified by code review. No local testing possible (market closed, Docker build on server only).

**Risk:** Changes are unverified by execution. First validation will occur when bot starts Monday morning.

---

## Files Modified

### 1. deployment/config_live.py

**Changes made:**

| Line | Parameter | Old Value | New Value | Reason |
|------|-----------|-----------|-----------|--------|
| 24 | TIMEFRAME | `"5min"` | `"4H"` | Select 4-hour strategy |
| 33 | RUN_DURATION | `"1h"` | `"5d"` | Full trading week (Mon-Fri) |
| 83 | RSI_PERIOD | `21` | `14` | Correct Session 6B optimized value |
| 86 | MOMENTUM_PERIOD | `14` | `10` | Correct Session 6B optimized value |

**Complete 4H parameter block (lines 79-87):**
```python
elif TIMEFRAME == "4H":
    # 4-hour optimized parameters (Session 6B)
    SMA_FAST = 20
    SMA_SLOW = 70
    RSI_PERIOD = 14      # ✓ Corrected from 21
    RSI_LOWER = 35
    RSI_UPPER = 70
    MOMENTUM_PERIOD = 10 # ✓ Corrected from 14
    MOMENTUM_THRESHOLD = 0.0
```

**Historical note:** The wrong values (RSI 21, Momentum 14) appeared in three locations:
1. `CLAUDE.md` line 127 (fixed in Session 09, commit `967bcc3`)
2. Notebook Cell 190 comment (identified but not yet fixed in notebook source)
3. `config_live.py` lines 83, 86 (fixed in this session)

All three stem from an early hypothesis (pre-Session 6) that 4H might benefit from longer periods. This hypothesis was never validated. Session 6B grid search always used config defaults (14/10) and those produced optimal Sharpe 1.42.

---

### 2. deployment/trading_bot.py

**Changes made:**

#### Import Section (line 41)
**Added:**
```python
from modules.config import get_timeframe_config
```

This import provides access to `TIMEFRAME_CONFIGS` dictionary with correct IB bar size strings.

#### load_historical_warmup() Method (lines 534-594)

**Before (hardcoded 5-minute):**
```python
# Convert bars to duration string (bars * 5 minutes, in seconds)
duration_seconds = bars_needed * 5 * 60
duration_str = f"{duration_seconds} S"

self.logger.info(
    f"Loading {bars_needed} historical 5-min bars for warmup..."
)

bars = await self.ib.reqHistoricalDataAsync(
    self.contract,
    endDateTime="",
    durationStr=duration_str,
    barSizeSetting="5 mins",  # ❌ Hardcoded
    whatToShow="MIDPOINT",
    useRTH=False,
    formatDate=1,
)
```

**After (timeframe-aware):**
```python
# Get timeframe configuration
tf_config = get_timeframe_config(TIMEFRAME)
ib_bar_size = tf_config["ib_bar_size"]

# Calculate duration based on timeframe
bars_needed = max(SMA_SLOW, RSI_PERIOD + 1, MOMENTUM_PERIOD + 1) + 10

if TIMEFRAME == "5min":
    bar_duration_seconds = 5 * 60  # 5 minutes
elif TIMEFRAME == "4H":
    bar_duration_seconds = 4 * 60 * 60  # 4 hours
else:
    raise ValueError(f"Unsupported timeframe: {TIMEFRAME}")

duration_seconds = bars_needed * bar_duration_seconds
duration_str = f"{duration_seconds} S"

self.logger.info(
    f"Loading {bars_needed} historical {TIMEFRAME} bars for warmup..."
)

bars = await self.ib.reqHistoricalDataAsync(
    self.contract,
    endDateTime="",
    durationStr=duration_str,
    barSizeSetting=ib_bar_size,  # ✓ Dynamic from config
    whatToShow="MIDPOINT",
    useRTH=False,
    formatDate=1,
)
```

**Key changes:**
- `ib_bar_size` comes from `TIMEFRAME_CONFIGS[TIMEFRAME]["ib_bar_size"]`
- Bar duration calculated dynamically: 5 min (300s) or 4 hours (14400s)
- Log message shows actual timeframe: "5min" or "4H"

#### fetch_latest_bar() Method (lines 596-640)

**Before (hardcoded 5-minute):**
```python
bars = await self.ib.reqHistoricalDataAsync(
    self.contract,
    endDateTime="",
    durationStr="300 S",      # ❌ Hardcoded 5 minutes
    barSizeSetting="5 mins",  # ❌ Hardcoded
    whatToShow="MIDPOINT",
    useRTH=False,
    formatDate=1,
)
```

**After (timeframe-aware):**
```python
# Get timeframe configuration
tf_config = get_timeframe_config(TIMEFRAME)
ib_bar_size = tf_config["ib_bar_size"]

# Set duration based on timeframe
if TIMEFRAME == "5min":
    duration_str = "300 S"  # 5 minutes
elif TIMEFRAME == "4H":
    duration_str = "14400 S"  # 4 hours
else:
    raise ValueError(f"Unsupported timeframe: {TIMEFRAME}")

bars = await self.ib.reqHistoricalDataAsync(
    self.contract,
    endDateTime="",
    durationStr=duration_str,       # ✓ Dynamic
    barSizeSetting=ib_bar_size,     # ✓ Dynamic
    whatToShow="MIDPOINT",
    useRTH=False,
    formatDate=1,
)
```

**Key changes:**
- Duration string: "300 S" (5min) or "14400 S" (4H)
- Bar size setting from config (same as warmup method)

---

## Verified 4H Configuration

**Strategy parameters (Session 6B optimized):**
- SMA Fast/Slow: 20 / 70
- RSI Period: 14
- RSI Lower/Upper: 35 / 70
- Momentum Period: 10
- Momentum Threshold: 0.0

**Runtime configuration:**
- TIMEFRAME: "4H"
- RUN_DURATION: "5d" (Monday-Friday)
- CHECK_FREQUENCY: 300 seconds (5 minutes) — auto-set by config_live.py line 38
- POSITION_SIZE: 20,000 EUR
- MIN_EUR_BALANCE: 20,000 EUR

**IB Gateway bar size:**
- 5min: `"5 mins"` (from `TIMEFRAME_CONFIGS["5min"]["ib_bar_size"]`)
- 4H: `"4 hours"` (from `TIMEFRAME_CONFIGS["4H"]["ib_bar_size"]`)

---

## Expected Bot Behavior on Monday Startup

### Startup Sequence (with 4H config)

1. **Connection:**
   ```
   Connecting to IB Gateway at localhost:4002...
   Connected successfully
   Qualified contract: Forex('EURUSD', exchange='IDEALPRO')
   ```

2. **Balance Check:**
   ```
   Checking EUR balance...
   EUR balance: XXX,XXX.XX EUR
   Status: Sufficient
   ```

3. **Position Reconciliation:**
   ```
   Reconciling position state with IB...
   IB position: 0 EUR (FLAT)
   Bot position: 0 (FLAT)
   Reconciliation complete: positions match
   ```

4. **Historical Warmup (KEY VERIFICATION POINT):**
   ```
   Loading 80 historical 4H bars for warmup...
   Warmup complete: loaded 80 bars (need 80 for signals)
   ```

   **NOT:**
   ```
   Loading 80 historical 5-min bars for warmup...  ❌
   ```

5. **Main Loop:**
   ```
   Checking for new bars every 300 seconds
   Connection monitoring enabled (handles IB Gateway reboots)
   Bot will run for 432000 seconds (5.0 days)
   Expected end time: 2026-03-06 XX:XX:XX
   ```

### During Run

**Correct bar fetching:**
```
[Iteration N] Fetching latest bar...
Bar date: 2026-03-02 XX:00:00
```

Each bar should be 4 hours apart, not 5 minutes apart.

**Signal generation:**
```
Signal: [0/1/-1] | Position: [0/1/-1] | SMA: [fast]/[slow] | RSI: [value] | Momentum: [value]
```

Values should match 4H data, not 5-min data.

---

## Verification Checklist

### Before Deployment (Saturday, March 1)
- [x] Specification document written
- [x] config_live.py: TIMEFRAME = "4H"
- [x] config_live.py: RUN_DURATION = "5d"
- [x] config_live.py: RSI_PERIOD = 14 (not 21)
- [x] config_live.py: MOMENTUM_PERIOD = 10 (not 14)
- [x] trading_bot.py: Import get_timeframe_config
- [x] trading_bot.py: load_historical_warmup() uses dynamic bar size
- [x] trading_bot.py: fetch_latest_bar() uses dynamic bar size
- [x] Handoff document written
- [x] All changes committed

### Before Starting Bot (Monday, March 2)
- [ ] Copy updated `config_live.py` to droplet
- [ ] Copy updated `trading_bot.py` to droplet
- [ ] Rebuild Docker image on server: `docker build -f deployment/Dockerfile -t trading-bot:latest .`
- [ ] Verify IB Gateway running on port 4002
- [ ] Verify EUR→USD currency conversion completed (see `docs/ib-currency-conversion-guide.md`)
- [ ] Start bot: `docker run -d --network host -v $(pwd)/deployment/logs:/app/logs --name trading-bot-4h trading-bot:latest`

### After Bot Starts (Monday, March 2, first 5 minutes)
- [ ] Check logs for "Loading N historical **4H** bars for warmup" (not "5-min")
- [ ] Verify warmup loaded ~80 bars (SMA_SLOW=70 + 10 buffer)
- [ ] Check first bar date — should be 4 hours prior to current time, not 5 minutes
- [ ] Verify no Error 201 rejections (currency leverage) — should be resolved by EUR→USD conversion
- [ ] Confirm bot logs "Bot will run for 432000 seconds (5.0 days)"

### If Wrong Bar Size Detected
1. Stop bot: `docker stop trading-bot-4h && docker rm trading-bot-4h`
2. Check config_live.py: Verify TIMEFRAME = "4H" (not "5min")
3. Rebuild image: `docker build -f deployment/Dockerfile -t trading-bot:latest .`
4. Restart bot

---

## Open Risks

### Risk 1: Unverified Code Changes
**Status:** No local testing possible (market closed, server-only Docker build)
**Mitigation:** Code review confirmed correct parameter values and timeframe-aware logic
**Fallback:** If bot fails at startup, logs will show error immediately; stop and debug

### Risk 2: EUR→USD Conversion Not Completed
**Status:** Manual conversion step required this weekend (see `docs/ib-currency-conversion-guide.md`)
**Mitigation:** Follow guide to convert 500K EUR to USD via IB Gateway currency converter
**Fallback:** If Error 201 occurs, stop bot, complete conversion, restart

### Risk 3: IB Gateway 4H Bar Data Availability
**Status:** Unknown if paper trading account provides 4H bars
**Mitigation:** If warmup fails, bot will log error and attempt real-time collection
**Fallback:** If 4H bars unavailable, switch back to 5min timeframe

### Risk 4: 4H Strategy Diverges from Backtest
**Status:** Backtest showed Sharpe 1.42 for 4H with these parameters
**Mitigation:** Monitor first few trades closely; if P&L diverges significantly from backtest expectations, investigate data/signal mismatch
**Fallback:** Stop bot and analyze logs/trade data before continuing

---

## Next Actions

### Sunday, March 1 (Today)
1. ✓ Complete all code fixes (this session)
2. ✓ Commit changes to git
3. Execute EUR→USD currency conversion via IB Gateway (see guide)
4. Verify conversion: Check account balances show ~500K EUR + ~590K USD

### Monday, March 2 (Market Open)
1. SSH to droplet: `ssh root@157.230.113.17`
2. Pull latest code: `cd CPF-Final-Project && git pull origin main`
3. Rebuild Docker image: `docker build -f deployment/Dockerfile -t trading-bot:latest .`
4. Start 4H bot: `docker run -d --network host -v $(pwd)/deployment/logs:/app/logs --name trading-bot-4h trading-bot:latest`
5. Monitor startup logs: `docker logs -f trading-bot-4h`
6. Verify "Loading N historical 4H bars for warmup" appears
7. Confirm no Error 201 rejections
8. Let bot run through Friday, March 6

### Friday, March 6 (Market Close)
1. Download logs from droplet: `deployment/logs/trading_bot_4H_5d_*.log` and `trades_4H_5d_*.csv`
2. Run analysis script (similar to Session 09 for 5min run)
3. Write Session 09D handoff document with 4H live results
4. Compare 4H live results to backtest (Sharpe 1.42, Return +30.23%, 45 trades over 3 years)

---

## References

- Session 6B optimization results: `data/optimization/optimization_results_4H_corrected.csv`
- TIMEFRAME_CONFIGS: `modules/config/timeframes.py` lines 60-80
- Session 09 (5min live results): `docs/handoffs/session-09-live-results-5min.md`
- Currency conversion guide: `docs/ib-currency-conversion-guide.md`
- Specification for this session: `docs/specifications/spec-4h-deployment-fixes.md`

---

**End of Session 09C**
**Status:** All fixes complete, ready for Monday deployment
**Next:** Execute currency conversion, then start 4H live run Monday morning
