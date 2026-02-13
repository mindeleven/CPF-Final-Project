# Session 7E Specification: Critical Production Fixes
**Date:** February 13, 2026  
**Purpose:** Fix critical bugs discovered during 4-hour live test  
**Priority:** HIGH - Production blocker issues  
**Estimated Cost:** $2-3

---

## 🎯 Session Goals

1. Fix double position bug (CRITICAL safety issue)
2. Implement proper EUR account balance verification
3. Fix entry price tracking and P&L calculation
4. Implement proper 5-minute bar streaming with historical warmup
5. Fix order TIF errors
6. Improve logging and error handling

---

## 📋 Consolidated Requirements

### **Critical Fixes (Must Have - Priority 1)** 🔴

#### **1. Fix Double Position Bug**
**Problem:** Bot opened -40K EUR position (double SHORT) instead of -20K  
**Root Cause:** Close and open orders execute simultaneously without confirmation  
**Current Code Flow:**
```python
# BROKEN - Both orders fire immediately
if self.position != 0:
    await self.close_position(price)  # Order 1
await self.execute_order(signal, price)  # Order 2
```

**Fix Required:**
```python
# From old bot (position_manager.py lines 246-265)
if self.current_position != 0:
    success, close_pnl = self.close_position()
    if not success:
        return False, 'ERROR', None, 0.0
    # CRITICAL: Wait for settlement!
    self.ib.sleep(1)  # or await asyncio.sleep(1)

# Only NOW open new position
order = MarketOrder(action, self.contract_size)
```

**Implementation:**
- Wait for `trade.isDone()` confirmation before next step
- Add 1-second settlement delay between close and open
- Verify position state after close before opening new

**Testing:** Verify only one position exists after signal, check IB position size

---

#### **2. Implement EUR Account Balance Check**
**Problem:** "Error 201: FX trade would expose account to currency leverage"  
**Root Cause:** No balance verification, EUR account needs EUR balance check  
**Current Code:** No balance check, assumes sufficient funds

**Fix Required:**
```python
# Adapt from old bot (position_manager.py lines 42-70)
def check_eur_balance(self, min_balance=20000):
    """Check if account has sufficient EUR balance."""
    account_values = self.ib.accountSummary()
    
    eur_balance = None
    for item in account_values:
        if item.tag == 'TotalCashBalance' and item.currency == 'EUR':
            eur_balance = float(item.value)
            break
    
    if eur_balance is None:
        self.logger.error("Could not determine EUR balance")
        return False, 0
    
    has_sufficient = eur_balance >= min_balance
    
    if not has_sufficient:
        self.logger.error(f"Insufficient EUR: {eur_balance:.2f} < {min_balance:.2f}")
    
    return has_sufficient, eur_balance
```

**Implementation:**
- Call `check_eur_balance()` on bot startup
- Call before each trade execution
- Set `self.initial_capital` from actual EUR balance (not hardcoded $10K)
- Convert EUR balance to USD for P&L tracking if needed

**Config Change:**
```python
# Remove hardcoded INITIAL_CAPITAL
# Will be set dynamically from account query
```

**Testing:** Verify balance check runs, blocks trades if insufficient EUR

---

#### **3. Fix Entry Price Tracking**
**Problem:** P&L shows $0.00 during position, only correct at close  
**Root Cause:** `entry_price` never set from fill confirmation  
**Current Code:** Missing `entry_price` assignment after order fill

**Fix Required:**
```python
# From old bot (position_manager.py lines 292-300)
if trade.isDone():
    fill_price = trade.orderStatus.avgFillPrice
    
    # SET ENTRY PRICE FROM FILL
    self.entry_price = fill_price  # ✅
    self.position_size = self.contract_size
    self.current_position = signal
    
    self.logger.info(f"Entry price recorded: {self.entry_price:.5f}")
```

**Also in position reconciliation:**
```python
# From old bot (position_manager.py lines 102-126)
# Only update entry_price if we don't have one
if self.entry_price is None:
    self.entry_price = avg_cost  # Set from IB
else:
    # Keep our entry_price, don't overwrite!
    pass
```

**Implementation:**
- Set `entry_price` from `trade.orderStatus.avgFillPrice` after fill
- Preserve `entry_price` in reconciliation unless None
- Fix `calculate_unrealized_pnl()` to use `entry_price`

**Testing:** Verify P&L updates during position, not just at close

---

#### **4. Add Order TIF='GTC'**
**Problem:** "Error 10349: Order TIF was set to DAY" on every order  
**Root Cause:** Missing time-in-force specification for 24/5 forex  
**Current Code:** `order = MarketOrder(action, size)` (defaults to DAY)

**Fix Required:**
```python
# From old bot (position_manager.py lines 169, 260)
order = MarketOrder(action, self.contract_size)
order.tif = 'GTC'  # ✅ Good Till Canceled (24/5 markets)
```

**Implementation:**
- Add `order.tif = 'GTC'` to ALL MarketOrder creations
- Locations: `execute_order()`, `close_position()`, `open_position()`

**Testing:** Verify no more Error 10349 warnings

---

### **Important Fixes (Should Have - Priority 2)** 🟡

#### **5. Implement 5-Minute Bar Streaming**
**Problem:** Bot fetches 60-second spot prices, not 5-minute bars  
**Root Cause:** Using `reqMktData()` for spot prices instead of bar data  
**Impact:** Strategy behavior differs from backtest (which used 5-min bars)

**Current Flow:**
```python
# WRONG - Fetches spot price every 60 seconds
async def fetch_latest_price(self):
    ticker = self.ib.reqMktData(self.contract)
    await asyncio.sleep(2)
    return ticker.last
```

**Fix Required:**
```python
# Use reqHistoricalData for 5-minute bars
async def fetch_latest_bar(self):
    """Fetch most recent 5-minute bar."""
    bars = self.ib.reqHistoricalData(
        self.contract,
        endDateTime='',
        durationStr='1 D',
        barSizeSetting='5 mins',
        whatToShow='MIDPOINT',
        useRTH=False,
        keepUpToDate=True  # Subscribe to updates
    )
    
    if bars:
        latest = bars[-1]
        return {
            'date': latest.date,
            'open': latest.open,
            'high': latest.high,
            'low': latest.low,
            'close': latest.close
        }
    return None
```

**Alternative - Real-Time Bars:**
```python
# reqRealTimeBars for streaming (5-second updates that aggregate to 5-min)
self.ib.reqRealTimeBars(
    self.contract,
    barSize=5,  # 5-second bars
    whatToShow='MIDPOINT',
    useRTH=False
)
```

**Implementation:**
- Replace `fetch_latest_price()` with `fetch_latest_bar()`
- Store OHLC data, use `close` price for signals
- Update frequency: Check every 60s, but only process new 5-min bars
- Handle bar completion detection

**Testing:** Verify bot waits for 5-minute bar completion before processing

---

#### **6. Add Historical Data Warmup**
**Problem:** Bot needs 70 minutes to collect 70 bars before first signal  
**Root Cause:** No historical data fetch on startup  
**Impact:** Can't trade immediately, wastes time

**Fix Required:**
```python
async def load_historical_warmup(self):
    """Load historical bars for indicator warmup."""
    # Calculate bars needed: max(SMA_LONG, RSI_PERIOD, MOMENTUM_PERIOD)
    bars_needed = max(SMA_LONG, RSI_PERIOD + 1, MOMENTUM_PERIOD + 1)
    
    # Fetch extra for safety
    bars_to_fetch = bars_needed + 10
    
    self.logger.info(f"Fetching {bars_to_fetch} historical bars for warmup...")
    
    bars = self.ib.reqHistoricalData(
        self.contract,
        endDateTime='',
        durationStr='1 D',
        barSizeSetting='5 mins',
        whatToShow='MIDPOINT',
        useRTH=False
    )
    
    # Load into price_history
    for bar in bars[-bars_to_fetch:]:
        self.price_history.append(bar.close)
    
    self.logger.info(f"✅ Warmup complete: {len(self.price_history)} bars loaded")
```

**Implementation:**
- Call `load_historical_warmup()` after connection, before main loop
- Verify sufficient bars loaded (70 for SMA, 15 for RSI, 11 for Momentum)
- Can generate signals immediately with first live bar

**Testing:** Verify signals generated within 5 minutes of startup

---

#### **7. Improve Logfile Naming**
**Problem:** Logfiles named `trading_bot_20260212_132823.log` - hard to identify  
**Suggestion:** Include timeframe, runtime in filename

**Fix Required:**
```python
# In __init__() or setup_logging()
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
runtime_str = RUN_DURATION.replace(' ', '').replace('h', 'hr').replace('min', 'm')
timeframe_str = TIMEFRAME.replace(' ', '')

log_filename = f"trading_bot_{timeframe_str}_{runtime_str}_{timestamp}.log"
# Example: trading_bot_5min_4hr_20260213_233522.log
```

**Implementation:**
- Add timeframe to log filename
- Add runtime duration to filename
- Makes identification easier when downloading multiple logs

**Testing:** Verify log filename is descriptive

---

#### **8. Track P&L in EUR**
**Problem:** P&L tracked in USD, but account is EUR  
**Reason:** More accurate for EUR account holders

**Fix Required:**
```python
# Option 1: Track in EUR directly
pnl_eur = (exit_price - entry_price) * position_size  # Already in EUR

# Option 2: Convert USD P&L to EUR
pnl_usd = (exit_price - entry_price) * position_size
pnl_eur = pnl_usd / current_eurusd_rate

# Option 3: Get from IB realized P&L (in account currency)
# CommissionReport has realizedPNL in account currency
```

**Implementation:**
- Display P&L in EUR in logs
- Convert to USD only if needed for comparison
- Use `commissionReport.realizedPNL` for actual account impact

**Testing:** Verify P&L matches IB account currency

---

### **Nice to Have (Priority 3)** 🟢

#### **9. Better Error Handling for Rejected Orders**
**Current:** Orders fail silently or with generic errors  
**Improvement:** 
- Catch specific error codes (201, 10349, etc.)
- Log detailed error messages
- Implement retry logic for transient failures
- Alert on persistent failures

#### **10. Verify Contract Qualification**
**Current:** Assumes `qualifyContractsAsync()` succeeds  
**Improvement:**
```python
qualified = await self.ib.qualifyContractsAsync(self.contract)
if not qualified:
    self.logger.error("Contract qualification failed")
    return False

self.contract = qualified[0]

# Verify conId populated
if not self.contract.conId:
    self.logger.error("Contract has no conId after qualification")
    return False

self.logger.info(f"Contract qualified: {self.contract.symbol} (conId: {self.contract.conId})")
```

---

## 🔄 Architectural Decisions

### **Async Pattern Commitment**
**Issue:** Mixing sync (`self.ib.sleep()`) and async (`await asyncio.sleep()`)  
**Resolution:** Use async throughout:
- `await asyncio.sleep()` for delays
- `await self.ib.qualifyContractsAsync()` for qualification
- All main methods are `async def`

**Old Bot Lesson:**
- Old bot was fully synchronous (simpler but blocking)
- New bot must be fully async (more complex but non-blocking)
- Don't mix patterns - pick one and stick to it

---

## 🧪 Testing Strategy

### **Phase 1: Local Testing (No Docker)**
```bash
# Setup SSH tunnel
ssh -L 4002:localhost:4002 root@157.230.113.17

# Or edit config for direct connection
IB_HOST = '157.230.113.17'

# Run locally
cd ~/Projects/.../CPF-Final-Project
python deployment/trading_bot.py
```

**Tests:**
1. Startup with balance check
2. Historical warmup completes
3. First signal generates within 5 minutes
4. Single position opened (not double)
5. P&L updates during position
6. Proper close on exit

### **Phase 2: Short Docker Test (1 hour)**
```bash
# On droplet
cd /root/trading_bot
docker build --no-cache -f deployment/Dockerfile -t trading-bot:latest .
docker run -d --name trading-bot-test --network host \
  -v /root/trading_bot/deployment/logs:/app/logs trading-bot:latest

# Monitor
docker logs -f trading-bot-test
```

**Verify:**
- No double position errors
- No TIF warnings
- P&L tracking works
- Logs named correctly

### **Phase 3: Extended Test (8-24 hours)**
- Run overnight with 8-hour runtime
- Verify midnight reconnection
- Check cumulative P&L accuracy
- Download and analyze all logs

---

## 📝 Implementation Checklist

- [ ] Fix double position bug (wait for confirmation)
- [ ] Add EUR balance check function
- [ ] Call balance check on startup and before trades
- [ ] Set entry_price from fill confirmation
- [ ] Preserve entry_price in reconciliation
- [ ] Add order.tif = 'GTC' to all orders
- [ ] Replace spot price fetching with 5-min bars
- [ ] Implement historical warmup function
- [ ] Call warmup after connection
- [ ] Update logfile naming convention
- [ ] Track P&L in EUR
- [ ] Test locally without Docker
- [ ] Test with Docker (1-hour)
- [ ] Extended test (8+ hours)

---

## 💰 Budget Estimate

- Implementation: 1.5-2 hours → $1.50-2.00
- Testing: 0.5-1 hour → $0.50-1.00
- **Total:** $2.00-3.00

**Remaining after 7E:** ~$10-11

---

## 📚 Reference Files

### **Old Bot (Working Example)**
- `/mnt/user-data/uploads/position_manager.py` - Shows correct patterns:
  - TIF='GTC' on line 169, 260
  - Wait for trade.isDone() on line 177-182, 268-273
  - Settlement sleep on line 251
  - Entry price from fill on line 297
  - Entry price preservation on line 102-126
  - EUR balance check on line 42-70 (adapt from USD)

### **Current Bot (Needs Fixing)**
- `/root/trading_bot/deployment/trading_bot.py` - Main bot file
- Lines with issues documented in critical-bugs-analysis.md

---

## 🎯 Success Criteria

**Session 7E is complete when:**
1. ✅ No double position errors in 4+ hour test
2. ✅ EUR balance checked before trading
3. ✅ P&L updates correctly during positions
4. ✅ No Order TIF warnings
5. ✅ Bot uses 5-minute bars (not 60s prices)
6. ✅ Signals generate within 5 minutes of startup
7. ✅ 8-hour test completes without errors
8. ✅ Logs are clearly named and accessible

---

**Priority Order for Implementation:**
1. Order TIF (quick win, 5 minutes)
2. Entry price tracking (moderate, 20 minutes)
3. Double position fix (critical, 30 minutes)
4. EUR balance check (moderate, 30 minutes)
5. Historical warmup (moderate, 30 minutes)
6. 5-minute bars (complex, 60 minutes)
7. Logfile naming (quick, 10 minutes)
8. P&L in EUR (quick, 15 minutes)

**Estimated total implementation:** 3-4 hours coding + 2-3 hours testing

---

**Next Steps:**
1. Review this specification
2. Start new chat with "Continue CPF Final Project - Session 7E Implementation"
3. Reference this file and other handoff documents
4. Begin with quick wins (TIF, entry_price)
5. Then tackle critical fixes (double position, balance check)
6. Test locally first, then Docker deploy
