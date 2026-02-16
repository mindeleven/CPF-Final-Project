# Critical Bugs Analysis - 4-Hour Live Test
**Test Date:** February 12-13, 2026 (23:35 - 03:35 UTC)  
**Test Duration:** 4 hours, 12 seconds  
**Bot Version:** Post-Session 7D (with qualifyContractsAsync fix)  
**Issues Found:** 6 critical, 3 warnings

---

## 🔴 Bug #1: Double Position Error (CRITICAL)

### **Severity:** CRITICAL - Violates IBKR constraints, wrong position size

### **What Happened:**
At 01:16:51, bot attempted to close LONG and open SHORT position:

```
01:16:51 - SELL Signal: SMA crossed below
01:16:51 - placeOrder: SELL 20,000 EUR (order 660)
01:16:52 - position: -20,000 (one SHORT) ✓
01:16:53 - placeOrder: SELL 20,000 EUR (order 661) 
01:16:53 - position: -40,000 (DOUBLE SHORT!) ✗
```

**Result:** Position of -40,000 EUR instead of expected -20,000 EUR

### **Root Cause:**
Bot logic executes two separate orders:
1. Close existing LONG → Opens SHORT of -20K
2. Open new SHORT → Adds another -20K SHORT
3. Total: -40K SHORT (double position)

**Code Flow:**
```python
# Somewhere in execute_order() or signal handling
if self.position != 0:
    await self.close_position(price)     # Order 1: SELL 20K
    
await self.open_position(signal, price)  # Order 2: SELL 20K
# Both execute! No confirmation wait between them
```

### **Why It's Dangerous:**
- IBKR forex rule: One position per currency pair
- Double position = 2x intended exposure
- Risk management broken
- P&L calculations incorrect

### **How Old Bot Prevents This:**
```python
# From position_manager.py (OLD BOT)
if self.current_position != 0:
    success, close_pnl = self.close_position()
    if not success:
        return False, 'ERROR', None, 0.0
    
    # CRITICAL: Wait for settlement
    self.ib.sleep(1)  # ← Prevents double position

# Only NOW open new position
order = MarketOrder(action, self.contract_size)
```

**And in close_position():**
```python
# Wait for fill CONFIRMATION
timeout = 30
while not trade.isDone() and elapsed < timeout:
    self.ib.sleep(0.5)
    elapsed += 0.5

if trade.isDone():  # ← Verified closed
    self.current_position = 0
    return True, pnl
```

### **Fix Required:**
1. Wait for `trade.isDone()` confirmation after close
2. Add 1-second settlement delay
3. Verify position = 0 before opening new
4. Consider single order to flip position (SELL 40K instead of SELL 20K + SELL 20K)

### **Testing:**
- After fix, run signal that requires position flip
- Verify only one order executes
- Check final position size = 20K (not 40K)

---

## 🔴 Bug #2: Entry Price Not Set (CRITICAL)

### **Severity:** CRITICAL - P&L tracking broken

### **What Happened:**
Throughout the 4-hour run, P&L showed $0.00 during positions:

```
01:00:19 - Status: Position=LONG, P&L=$0.00  ← Should show unrealized P&L
01:01:21 - Status: Position=LONG, P&L=$0.00  ← Still $0.00
...
01:16:53 - CLOSED: P&L=$-14.90  ← Only correct at close
```

**Only at close did P&L show correctly.**

### **Root Cause:**
`entry_price` never set from fill confirmation, so `calculate_unrealized_pnl()` returns 0:

```python
def calculate_unrealized_pnl(self, current_price):
    if self.position == 0 or not self.entry_price:  # ← entry_price is None
        return 0.0
    
    # Never reaches here
    if self.position == 1:
        return (current_price - self.entry_price) * POSITION_SIZE
```

### **Where Entry Price Should Be Set:**

**Location 1: After Order Fill**
```python
# execute_order() or open_position()
trade = self.ib.placeOrder(self.contract, order)

# Wait for fill...
if trade.isDone():
    fill_price = trade.orderStatus.avgFillPrice
    
    # MISSING THIS:
    self.entry_price = fill_price  # ← Never executed
    self.position = signal
```

**Location 2: In Position Reconciliation**
```python
# reconcile_positions() after reconnect
for pos in self.ib.positions():
    if pos.contract.symbol == 'EUR':
        avg_cost = pos.avgCost
        
        # MISSING THIS:
        if self.entry_price is None:
            self.entry_price = avg_cost  # ← Set from IB
```

### **How Old Bot Handles This:**
```python
# From position_manager.py
if trade.isDone():
    fill_price = trade.orderStatus.avgFillPrice
    
    # Always set entry price from fill
    self.entry_price = fill_price  # ✓
    self.current_position = signal
    self.position_size = self.contract_size
    
    self.logger.log_info(f"Entry price set to {self.entry_price:.5f}")
```

**And preserves it:**
```python
# In get_current_position() / reconcile
if self.entry_price is None:
    self.entry_price = avg_cost  # Set if missing
else:
    # Keep our entry_price, don't overwrite
    pass
```

### **Fix Required:**
1. Set `self.entry_price = trade.orderStatus.avgFillPrice` after fill
2. In reconciliation, set from `pos.avgCost` if `entry_price is None`
3. Don't overwrite `entry_price` if already set

### **Testing:**
- Open position, check P&L updates every minute
- Should show realistic unrealized P&L, not $0.00
- After reconnect, verify P&L still correct

---

## ⚠️ Bug #3: Order TIF Error (WARNING)

### **Severity:** WARNING - Orders execute but log errors

### **What Happened:**
Every single order generated Error 10349:

```
00:59:16 - ERROR 10349: Order TIF was set to DAY based on order preset
01:16:51 - ERROR 10349: Order TIF was set to DAY based on order preset
02:24:06 - ERROR 10349: Order TIF was set to DAY based on order preset
03:17:55 - ERROR 10349: Order TIF was set to DAY based on order preset
03:35:33 - ERROR 10349: Order TIF was set to DAY based on order preset
```

**Orders still filled, but warnings annoying and unprofessional.**

### **Root Cause:**
`MarketOrder()` defaults to TIF='DAY', but forex markets are 24/5.  
IBKR automatically converts to GTC but logs warning.

```python
# Current code
order = MarketOrder(action, POSITION_SIZE)
# order.tif defaults to 'DAY' ← Problem
```

### **Fix Required:**
```python
order = MarketOrder(action, POSITION_SIZE)
order.tif = 'GTC'  # Good Till Canceled (24/5 markets)
```

**Apply to ALL order creations:**
- `execute_order()`
- `open_position()`
- `close_position()`

### **Old Bot Has This:**
```python
# position_manager.py lines 169, 260
order = MarketOrder(action, self.position_size)
order.tif = 'GTC'  # ← Already there
```

### **Testing:**
- After fix, verify no Error 10349 warnings
- Orders should execute cleanly

---

## 🔴 Bug #4: Currency Leverage Error (CRITICAL)

### **Severity:** CRITICAL - First order rejected

### **What Happened:**
At 00:59:16, first BUY order was rejected:

```
00:59:15 - BUY Signal generated
00:59:16 - ERROR 201: Order rejected - FX trade would expose account to currency leverage
00:59:16 - Order status: Inactive
```

**But somehow position still opened as LONG?** Confusing order status chain.

### **Root Cause:**
No EUR account balance verification before trading.  
Account is EUR-based, needs EUR balance check (not USD).

**IBKR Requirements:**
- For EUR/USD trading from EUR account
- Need sufficient EUR balance
- Can't create "currency leverage" by borrowing base currency

### **Current Code:**
No balance check at all. Assumes sufficient funds.

### **Fix Required:**
```python
def check_eur_balance(self, min_balance=20000):
    """Check EUR balance before trading."""
    account_values = self.ib.accountSummary()
    
    for item in account_values:
        if item.tag == 'TotalCashBalance' and item.currency == 'EUR':
            eur_balance = float(item.value)
            
            if eur_balance < min_balance:
                self.logger.error(f"Insufficient EUR: {eur_balance:.2f}")
                return False, eur_balance
            
            return True, eur_balance
    
    self.logger.error("Could not determine EUR balance")
    return False, 0
```

**Call Before Trading:**
```python
# On startup
has_funds, balance = self.check_eur_balance()
if not has_funds:
    self.logger.error("Insufficient funds. Exiting.")
    return

# Before each trade
has_funds, balance = self.check_eur_balance(POSITION_SIZE)
if not has_funds:
    self.logger.warning("Skipping trade - insufficient EUR")
    return
```

### **Old Bot Has This:**
```python
# position_manager.py check_usd_balance() 
# (same logic, just change currency to EUR)
```

### **Also Fix INITIAL_CAPITAL:**
```python
# Instead of hardcoded
INITIAL_CAPITAL = 10000.0  # ← Wrong

# Query actual balance
self.initial_capital = balance  # From check_eur_balance()
```

### **Testing:**
- Verify balance check runs on startup
- Log actual EUR balance
- Verify no Error 201

---

## 🔴 Bug #5: Wrong Timeframe Data (CRITICAL)

### **Severity:** CRITICAL - Strategy behavior differs from backtest

### **What Happened:**
Bot fetches spot price every 60 seconds, not 5-minute bars:

```
23:35:25 - Status: Bars=1
23:36:27 - Status: Bars=2  (62 seconds later)
23:37:29 - Status: Bars=3  (62 seconds later)
```

**These are 60-second spot prices, not 5-minute OHLC bars.**

### **Root Cause:**
Current implementation:

```python
CHECK_FREQUENCY = 60  # Check every 60 seconds

async def fetch_latest_price(self):
    ticker = self.ib.reqMktData(self.contract)
    await asyncio.sleep(2)
    return ticker.last  # ← Spot price, not bar
```

### **Impact:**
- Backtest used 5-minute bar close prices
- Live bot uses 1-minute spot prices
- Indicators calculate on different data
- Strategy behavior diverges
- Results not comparable to backtest

### **Fix Required:**
```python
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

**And update frequency:**
```python
CHECK_FREQUENCY = 300  # 5 minutes = 300 seconds
# Or keep at 60 but only process when new 5-min bar completes
```

### **Testing:**
- Verify bars arrive every 5 minutes
- Check bar timestamps are 5 minutes apart
- Verify close prices match expected values

---

## ⚠️ Bug #6: No Historical Warmup (WARNING)

### **Severity:** WARNING - Wastes 70 minutes before first signal

### **What Happened:**
Bot starts with empty price history, needs to collect 70 bars:

```
23:35:25 - Bars=1
23:36:27 - Bars=2
...
00:46:51 - Bars=70  (71 minutes later)
00:59:15 - BUY Signal  (first signal, 84 minutes after start)
```

**Strategy requires SMA(70), so needs 70 bars before first signal.**

### **Root Cause:**
No historical data fetch on startup:

```python
def __init__(self):
    self.price_history = deque(maxlen=120)  # Starts empty
    # No historical fetch
```

### **Fix Required:**
```python
async def load_historical_warmup(self):
    """Load historical bars for immediate trading."""
    # Need 70 for SMA, 15 for RSI, 11 for Momentum
    bars_needed = max(SMA_LONG, RSI_PERIOD + 1, MOMENTUM_PERIOD + 1)
    bars_to_fetch = bars_needed + 10  # Safety margin
    
    self.logger.info(f"Fetching {bars_to_fetch} historical 5-min bars...")
    
    bars = self.ib.reqHistoricalData(
        self.contract,
        endDateTime='',
        durationStr='1 D',
        barSizeSetting='5 mins',
        whatToShow='MIDPOINT',
        useRTH=False
    )
    
    for bar in bars[-bars_to_fetch:]:
        self.price_history.append(bar.close)
    
    self.logger.info(f"✅ Warmup complete: {len(self.price_history)} bars")
```

**Call after connection:**
```python
async def run(self):
    await self.connect()
    await self.load_historical_warmup()  # ← Add this
    # Now can generate signals immediately
```

### **Testing:**
- Verify 70+ bars loaded on startup
- First signal should generate within 5 minutes
- No 70-minute wait

---

## 📊 Additional Observations

### **Reconnection Works! ✅**
```
23:45:00 - ERROR - Peer closed connection
23:45:43 - WARNING - Connection lost detected!
23:45:44 - INFO - Reconnection attempt 1/10...
23:45:45 - INFO - ✅ Reconnected successfully
23:45:46 - INFO - Contract re-qualified
23:45:46 - INFO - Position confirmed: FLAT
```

**Session 7B reconnection logic worked perfectly!**

---

### **Position Reconciliation Works! ✅**
```
23:45:46 - INFO - Reconciling position state with IB...
23:45:46 - INFO - Position confirmed: FLAT
23:45:46 - INFO - Reconciliation complete
```

**Session 7C position reconciliation worked after reconnect!**

---

### **Contract Qualification Works! ✅**
```
23:35:23 - INFO - Contract qualified: EUR (conId=12087792)
23:45:46 - INFO - Contract re-qualified: EUR
```

**Session 7D qualifyContractsAsync fix worked!**

---

### **Bars Capped at 120**
```
01:38:37 - Bars=120
01:39:39 - Bars=120
...
03:35:35 - Bars=120  (stayed at 120 rest of run)
```

**This is CORRECT behavior:**
```python
self.price_history = deque(maxlen=120)
```

After 120 bars, oldest drops off when new arrives. This is intentional.

---

## 🔧 Order Status Confusion

Throughout logs, order status sequences are confusing:

```
00:59:16 - ERROR 10349: Order TIF set to DAY
00:59:16 - Canceled order
00:59:16 - orderStatus: Inactive
00:59:16 - ERROR 201: Order rejected
00:59:17 - orderStatus: Inactive (may still fill)
01:00:19 - Status: Position=LONG  ← But order was rejected?
```

**Possible explanations:**
1. IBKR automatically retries with corrected TIF
2. "Inactive" doesn't mean failed
3. Multiple order status updates
4. Async status callbacks arriving out of sequence

**Needs investigation** - but orders did execute eventually.

---

## 📈 Performance Summary

**Trades Executed:** 4  
**Win Rate:** 0% (all losses)  
**Total P&L:** -$39.70  
**Average Trade:** -$9.93  
**Worst Trade:** -$14.90  
**Best Trade:** -$6.40

**Note:** Low volatility period, all losses expected. Strategy not designed for ranging markets.

---

## 🎯 Priority for Session 7E

### **Must Fix:**
1. 🔴 Double position bug (2x exposure, violates constraints)
2. 🔴 Entry price tracking (P&L monitoring broken)
3. 🔴 EUR balance check (prevents Error 201)
4. 🔴 5-minute bars (aligns with backtest)

### **Should Fix:**
5. ⚠️ Order TIF (professional appearance)
6. ⚠️ Historical warmup (faster startup)

### **Nice to Have:**
7. 🟢 Better error handling
8. 🟢 Logfile naming
9. 🟢 P&L in EUR

---

## 📝 Log Analysis Observations

### **Log File Mystery**
User reports: "I haven't found a logfile with this content when downloading them"

**Explanation:** Terminal output is from `docker logs` command (live container stdout), not from log files in `/root/trading_bot/deployment/logs/`.

**Fix:** Ensure logger writes to file, not just stdout:
```python
# Check logging configuration
logging.basicConfig(
    filename=log_file_path,  # ← Important!
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

---

## 🔍 Debugging Recommendations

### **For Session 7E Testing:**

1. **Enable detailed logging:**
   ```python
   logging.DEBUG  # Instead of INFO
   ```

2. **Log order status transitions:**
   ```python
   for log_entry in trade.log:
       self.logger.debug(f"Order {trade.order.orderId}: {log_entry.status}")
   ```

3. **Log entry_price updates:**
   ```python
   self.logger.info(f"entry_price: {self.entry_price} (was: {old_entry_price})")
   ```

4. **Log balance checks:**
   ```python
   self.logger.info(f"EUR balance: {balance:.2f}, required: {min_balance:.2f}")
   ```

---

**Summary:** 4 critical bugs, 2 warnings discovered. All fixable in Session 7E. Core functionality (reconnection, reconciliation, qualification) working correctly.

**Next Steps:** Implement Session 7E fixes, test locally first, then deploy to Docker for production testing.

---

**Document Created:** February 13, 2026, 08:40 UTC  
**Test Data:** February 12-13, 2026, 4-hour live run  
**Related Files:** session-7E-specification.md, project-progress.md, deployment-status.md
