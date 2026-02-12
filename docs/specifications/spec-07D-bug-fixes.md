---

# **Specification 7D: Fix Contract Qualification & Reconciliation Bugs**

**Project:** CPF Final Project - Automated Trading System  
**Module:** Trading Bot Bug Fixes  
**Session:** 7D (Critical Bug Fixes from Deployment)  
**Date:** February 12, 2026  
**Prerequisites:** Session 7C Complete ✅, Deployment attempted ✅

---

## 🐛 **Critical Bugs Discovered During Deployment**

### **Bug #1: Contract Not Qualified**

**Error Message:**
```
ERROR - Error fetching price: Contract Forex('EURUSD', exchange='IDEALPRO') 
can't be hashed because no 'conId' value exists. 
Qualify contract to populate 'conId'.
```

**Root Cause:**
- Forex contracts need a unique `conId` (contract identifier) from IB
- `conId` is obtained by calling `qualifyContracts()` after connection
- Without qualification, the contract can't be used for data requests

**Impact:**
- ❌ Price fetching fails
- ❌ No market data streams
- ❌ Bot can't generate signals
- ❌ Trading completely blocked

**Current Code (Broken):**
```python
async def connect(self) -> bool:
    await self.ib.connectAsync(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID)
    self.logger.info(f"Connected to IB Gateway at {IB_HOST}:{IB_PORT}")
    return True
    # Contract never qualified!
```

---

### **Bug #2: Event Loop Already Running in Reconciliation**

**Error Message:**
```
ERROR - Error during position reconciliation: This event loop is already running
ERROR - Continuing with current bot state (not updating)
```

**Root Cause:**
- `reconcile_positions()` calls `await self.ib.sleep(2)`
- But it's called from within an already-running async event loop
- `ib_async` doesn't allow nested event loop waits
- The sleep is actually unnecessary - positions() returns synchronously

**Impact:**
- ⚠️ Position reconciliation fails silently
- ⚠️ Bot continues with assumed state (FLAT)
- ⚠️ Position mismatches won't be detected
- ⚠️ Double position errors still possible

**Current Code (Broken):**
```python
async def reconcile_positions(self) -> None:
    positions = self.ib.positions()
    
    # Wait briefly for positions to populate
    await self.ib.sleep(2)  # <- THIS LINE CAUSES ERROR
    
    # Find EUR/USD position...
```

---

## 📋 **Objective**

Fix both bugs with minimal changes:

1. **Qualify Forex contract** after connection to populate `conId`
2. **Remove problematic sleep** from reconciliation (not needed)

**SINGLE file modification:** `deployment/trading_bot.py` only.

**No other changes needed** - both bugs have simple, surgical fixes.

---

## 🔧 **Implementation**

### **FIX #1: Qualify Contract After Connection**

**Location:** In `connect()` method (around line 127)

**FIND this code:**
```python
async def connect(self) -> bool:
    """
    Connect to IB Gateway.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        await self.ib.connectAsync(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID)
        self.logger.info(f"Connected to IB Gateway at {IB_HOST}:{IB_PORT}")
        self.logger.info("Connection monitoring active")
        return True
    except Exception as e:
        self.logger.error(f"Failed to connect to IB Gateway: {e}")
        return False
```

**REPLACE with:**
```python
async def connect(self) -> bool:
    """
    Connect to IB Gateway and qualify the Forex contract.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        await self.ib.connectAsync(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID)
        self.logger.info(f"Connected to IB Gateway at {IB_HOST}:{IB_PORT}")
        
        # ===== NEW: Qualify contract to get conId =====
        await self.ib.qualifyContracts(self.contract)
        self.logger.info(f"Contract qualified: {self.contract.symbol} (conId: {self.contract.conId})")
        # ===== END NEW CODE =====
        
        self.logger.info("Connection monitoring active")
        return True
    except Exception as e:
        self.logger.error(f"Failed to connect to IB Gateway: {e}")
        return False
```

**What This Does:**
- Calls IB's `qualifyContracts()` API after connection
- Populates `self.contract.conId` with unique contract ID
- Logs the conId for verification
- Contract can now be used for data requests and orders

**Why After Connection:**
- `qualifyContracts()` requires active IB connection
- Must be called before any data requests
- One-time operation per contract

---

### **FIX #2: Remove Event Loop Sleep from Reconciliation**

**Location:** In `reconcile_positions()` method (around line 240)

**FIND this code:**
```python
async def reconcile_positions(self) -> None:
    """
    Reconcile bot position state with Interactive Brokers reality.
    ...
    """
    try:
        self.logger.info("🔍 Reconciling position state with IB...")
        
        # Query IB for all positions
        positions = self.ib.positions()
        
        # Wait briefly for positions to populate
        await self.ib.sleep(2)
        
        # Find EUR/USD position
        eur_usd_position = None
```

**REPLACE with:**
```python
async def reconcile_positions(self) -> None:
    """
    Reconcile bot position state with Interactive Brokers reality.
    ...
    """
    try:
        self.logger.info("🔍 Reconciling position state with IB...")
        
        # Query IB for all positions
        positions = self.ib.positions()
        
        # ===== REMOVED: await self.ib.sleep(2) =====
        # positions() returns synchronously, no wait needed
        # ===== END REMOVAL =====
        
        # Find EUR/USD position
        eur_usd_position = None
```

**What This Does:**
- Removes the problematic `await self.ib.sleep(2)` line
- `positions()` call is synchronous - data is immediately available
- No wait needed - positions list is complete on return
- Eliminates event loop conflict

**Why This Works:**
- `self.ib.positions()` is a synchronous method
- Returns complete list immediately
- Does not need async wait
- Sleep was added as defensive programming but is unnecessary

---

## 📊 **Expected Changes**

**File Modified:**
- `deployment/trading_bot.py`

**Lines Changed:**
- **Fix #1:** +3 lines (contract qualification + log)
- **Fix #2:** -1 line (remove sleep)
- **Net change:** +2 lines

**Total Changes:** Minimal, surgical fixes only.

---

## ✅ **Expected Behavior After Fix**

### **Startup Logs (Fixed):**

```
INFO - Trading Bot initialized for 5min timeframe
INFO - Parameters: SMA 15/70, RSI 14 (35/75), Momentum 10 (threshold 0.0)
INFO - Position size: 20,000 EUR
INFO - Runtime: 1h
INFO - Bot will run until: 2026-02-12 13:13:40
INFO - Connecting to localhost:4002 with clientId 3...
INFO - Connected
INFO - Logged on to server version 178
INFO - API connection ready
INFO - Connected to IB Gateway at localhost:4002
INFO - Contract qualified: EURUSD (conId: 12087792)          ← NEW: Shows conId
INFO - Connection monitoring active
INFO - Trading bot started
INFO - 🔍 Reconciling position state with IB...
INFO - ✅ Position confirmed: FLAT (no open positions)        ← FIXED: No error
INFO - 🔍 Reconciliation complete. Current state: FLAT
INFO - Checking for signals every 60 seconds
INFO - Connection monitoring enabled (handles IB Gateway reboots)
```

**After 60 seconds:**
```
INFO - Status: Price=1.0428, Position=FLAT, P&L=$0.00...    ← FIXED: Price appears!
```

---

### **Before vs After**

**Before Session 7D:**
```
❌ ERROR - Error fetching price: Contract... can't be hashed
❌ ERROR - Error during position reconciliation: This event loop is already running
❌ No price data
❌ No trading possible
```

**After Session 7D:**
```
✅ Contract qualified: EURUSD (conId: 12087792)
✅ Position confirmed: FLAT
✅ Price data streaming: Price=1.0428
✅ Trading enabled
```

---

## 🧪 **Testing Strategy**

### **Test 1: Verify Deployment Fix**

**After implementing Session 7D:**

```bash
# 1. Stop current broken container
ssh root@157.230.113.17
docker stop trading-bot-5min
docker rm trading-bot-5min

# 2. Rebuild with fixes
cd /root/trading_bot
docker build -f deployment/Dockerfile -t trading-bot:latest .

# 3. Start fixed container
docker run -d \
  --name trading-bot-5min-fixed \
  --network host \
  -v /root/trading_bot/deployment/logs:/app/logs \
  trading-bot:latest

# 4. Monitor startup
docker logs -f trading-bot-5min-fixed
```

**Success Criteria:**
- ✅ "Contract qualified: EURUSD (conId: ...)" appears in logs
- ✅ "Position confirmed: FLAT" appears (no reconciliation error)
- ✅ After 60s: "Status: Price=..." appears with actual price
- ✅ No errors in logs

---

### **Test 2: Verify Price Data Streaming**

**Wait 2-3 minutes**, then:

```bash
# Check latest status updates
docker logs trading-bot-5min-fixed --tail 20 | grep "Status:"

# Expected:
# INFO - Status: Price=1.0428, Position=FLAT, P&L=$0.00, Time remaining=0.9h
# INFO - Status: Price=1.0429, Position=FLAT, P&L=$0.00, Time remaining=0.9h
```

**Success Criteria:**
- ✅ Price values appear (not errors)
- ✅ Prices update every 60 seconds
- ✅ Bot is monitoring market correctly

---

### **Test 3: Verify Position Reconciliation**

**If bot opens a position during test:**

```bash
# Watch for trade execution
docker logs -f trading-bot-5min-fixed | grep "TRADE EXECUTED"

# Then manually disconnect/reconnect
docker stop ibgateway && sleep 30 && docker start ibgateway

# Watch logs for reconciliation
docker logs -f trading-bot-5min-fixed
```

**Expected:**
```
⚠️ Connection lost detected!
Reconnection attempt 1/10...
✅ Reconnected successfully.
🔍 Reconciling position state with IB...
✅ Position confirmed: LONG @ 1.0425      ← FIXED: No error
🔍 Reconciliation complete. Current state: LONG
Position state verified. Resuming trading.
```

**Success Criteria:**
- ✅ Reconciliation runs without error
- ✅ Position state detected correctly
- ✅ Trading resumes normally

---

## 💰 **Estimated Cost**

**Implementation Time:** ~5 minutes (2 simple changes)  
**API Cost:** ~$0.10-0.20  
**Total Project After 7D:** ~$11.08-11.18 of $25.00

**Remaining Buffer:** ~$13.82-13.92

---

## 📝 **Files Modified**

**Single file update:**
```
deployment/trading_bot.py
```

**Changes:**
- Fix #1: Add contract qualification (3 lines)
- Fix #2: Remove sleep from reconciliation (1 line removed)
- Net: +2 lines

**No changes to:**
- config_live.py ✅
- Dockerfile ✅
- requirements.txt ✅
- All other files ✅

---

## 🎯 **After Implementation**

### **Immediate Actions:**

1. **Transfer updated file:**
   ```bash
   scp deployment/trading_bot.py root@157.230.113.17:/root/trading_bot/deployment/
   ```

2. **Rebuild and restart:**
   ```bash
   ssh root@157.230.113.17
   cd /root/trading_bot
   docker build -f deployment/Dockerfile -t trading-bot:latest .
   docker stop trading-bot-5min && docker rm trading-bot-5min
   docker run -d --name trading-bot-5min-fixed --network host \
     -v /root/trading_bot/deployment/logs:/app/logs trading-bot:latest
   ```

3. **Verify fix:**
   ```bash
   docker logs -f trading-bot-5min-fixed
   # Watch for: "Contract qualified" and "Position confirmed: FLAT"
   # Wait 60s for: "Status: Price=..."
   ```

4. **Continue original testing plan:**
   - 1-hour validation run
   - Manual disconnect test
   - Overnight test
   - Multi-day production run

---

## ✅ **Definition of Done**

- [ ] Contract qualification added to `connect()` method
- [ ] Event loop sleep removed from `reconcile_positions()`
- [ ] Syntax check passes
- [ ] Black formatting passes
- [ ] Container builds successfully
- [ ] Bot connects and qualifies contract
- [ ] Position reconciliation runs without error
- [ ] Price data streaming works
- [ ] Ready for 1-hour test run

---

## 🎓 **What We Learned**

### **Lesson 1: Contract Qualification Required**

**Discovery:**
- Forex contracts need `conId` before use
- Not mentioned in initial ib_async documentation review
- Only discovered during actual deployment

**Best Practice:**
- Always qualify contracts after connection
- Log the conId for verification
- Check contract is fully populated before use

**For CPF Report:**
> "Deployment testing revealed that ib_async Forex contracts require explicit qualification via `qualifyContracts()` to populate the contract identifier (`conId`) before they can be used for data requests or order placement. This step was not apparent from documentation review but became evident through runtime error messages."

---

### **Lesson 2: Async Event Loop Context Matters**

**Discovery:**
- `await self.ib.sleep()` fails when called from within running event loop
- `positions()` is actually synchronous - returns immediately
- Defensive wait was unnecessary and caused error

**Best Practice:**
- Check method signatures - don't assume async methods need waits
- Test event loop contexts during development
- Remove defensive code that causes problems

**For CPF Report:**
> "Position reconciliation initially included a defensive 2-second wait after querying positions, assuming data might need time to populate. Deployment testing revealed this caused an event loop conflict as `positions()` is synchronous and returns complete data immediately. The unnecessary wait was removed, eliminating the error."

---

### **Lesson 3: Deployment Finds What Testing Misses**

**Observation:**
- Both bugs only appeared during cloud deployment
- Local testing might have caught these (if you'd run it)
- Production environment often reveals edge cases

**Best Practice:**
- Test in target environment as early as possible
- Don't assume local == cloud
- Budget time for deployment debugging

**For Academic Value:**
> "This iteration demonstrates the value of early deployment testing. Both bugs were invisible during specification review and code generation but immediately apparent when running in the target environment. This validates the phased deployment strategy: quick iteration cycles with real environment feedback prevent accumulation of hidden issues."

---

## 🚀 **Ready for Implementation**

**This specification is complete and ready for Claude Code.**

**Key Points:**
- Two critical bugs blocking trading
- Simple, surgical fixes
- High confidence in solution (standard ib_async patterns)
- Minimal code changes
- Immediate validation possible

**After this fix:**
- Bot will stream price data ✅
- Position reconciliation will work ✅
- Trading will be enabled ✅
- Can proceed with full testing plan ✅

---

## 📊 **Success Criteria**

**Session 7D is successful when:**

1. ✅ Bot connects to IB Gateway
2. ✅ Contract qualification succeeds (conId logged)
3. ✅ Position reconciliation runs without error
4. ✅ Price data streams successfully
5. ✅ No errors in logs after 5 minutes
6. ✅ Bot generates signals (when conditions met)
7. ✅ Can proceed with 1-hour test run

---

**End of Specification 7D**

**Pass to Claude Code (Opus 4.6) to implement.**

**This should take ~5 minutes to fix both bugs.**

---
