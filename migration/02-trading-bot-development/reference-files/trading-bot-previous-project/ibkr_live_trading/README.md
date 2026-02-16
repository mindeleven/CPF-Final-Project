# EUR/USD Live Paper Trading Bot

Automated live paper trading system using Interactive Brokers for EUR/USD forex trading.

## 📁 Project Structure

```
live_trading/
├── live_trader.py           # Main orchestrator - RUN THIS
├── config_live.py          # Configuration (edit parameters here)
├── position_manager.py     # Account & order management
├── stream_processor.py     # Real-time bar processing & indicators
├── trade_logger.py         # CSV + log file logging
├── requirements.txt        # Python dependencies
└── README.md              # This file

logs/                       # Created automatically
├── trades_YYYYMMDD_HHMMSS.csv          # Trade history
├── trading_bot_YYYYMMDD_HHMMSS.log     # Detailed log
└── trades_YYYYMMDD_HHMMSS_summary.txt  # Final summary
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd live_trading
pip install -r requirements.txt
```

### 2. Configure Run Duration

Edit `config_live.py`:

```python
# For testing (10 minutes)
RUN_DURATION = "10 min"

# For assignment (8 hours)
RUN_DURATION = "8 h"
```

### 3. Make Sure IB Gateway is Running

Your IB Gateway Docker container should be running on port 4002 (paper trading).

```bash
# Check if IB Gateway is running
docker ps | grep ib-gateway
```

### 4. Run the Bot

```bash
python live_trader.py
```

That's it! The bot will:
- ✅ Connect to IB Gateway
- ✅ Check USD balance
- ✅ Close any open positions (clean slate)
- ✅ Start trading for configured duration
- ✅ Auto-close positions and exit when done

---

## ⚙️ Configuration

All settings are in `config_live.py`:

### Run Duration
```python
RUN_DURATION = "10 min"  # or "1 h", "8 h", "30 min", etc.
```

### Trading Parameters (Same as Backtest)
```python
MA_SHORT_PERIOD = 20
MA_LONG_PERIOD = 50
RSI_PERIOD = 14
RSI_NEUTRAL_LOW = 45
RSI_NEUTRAL_HIGH = 55
```

### Account Settings
```python
MIN_USD_BALANCE = 25000        # Minimum balance required
CONTRACT_SIZE = 20000          # EUR/USD contract size
```

### Logging
```python
LOG_BARS_TO_CONSOLE = True     # Print each bar to console
CONSOLE_VERBOSITY = 1          # 0=minimal, 1=normal, 2=detailed
```

---

## 📊 What Happens During a Run

### Initialization (30-60 seconds)
1. Connect to IB Gateway
2. Check USD balance (needs $25,000+)
3. Close any open positions
4. Fetch 1 day of historical bars for warmup
5. Subscribe to real-time 5-minute bars

### Trading Loop
Every 5 minutes:
1. Receive new bar from IB
2. Calculate indicators (MA, RSI, Momentum)
3. Generate signal (BUY/SELL/HOLD)
4. Execute trade if signal changed
5. Log to console + files

### Shutdown
1. Close any open positions (clean slate for next run)
2. Save trade summary
3. Disconnect from IB

---

## 📝 Output Files

After each run, find these in `logs/`:

### 1. Trade Log CSV
```csv
timestamp,bar_time,action,position,quantity,price,trade_pnl,cumulative_pnl,signal,sma_20,sma_50,rsi,momentum,reason
2026-01-14 13:05:00,2026-01-14 13:05:00,BUY,LONG,20000,1.0345,0.00,0.00,1,1.0341,1.0335,45.2,0.0001,MA bullish...
```

**Use this file for comparison with backtest!**

### 2. Detailed Log
```
2026-01-14 13:05:00 - INFO - New bar: O=1.0343 H=1.0347 L=1.0342 C=1.0345
2026-01-14 13:05:01 - INFO - SIGNAL: BUY (value=1) - MA bullish...
2026-01-14 13:05:02 - INFO - TRADE EXECUTED: BUY 20,000 @ 1.0345 -> LONG
```

### 3. Summary File
```
LIVE TRADING SESSION SUMMARY
Total Trades: 5
Winning Trades: 2
Losing Trades: 3
Win Rate: 40.0%
Total P&L: $-123.45
```

---

## 🎯 Typical Workflow

### Test Run (10 minutes)
```bash
# Edit config_live.py
RUN_DURATION = "10 min"

# Run bot
python live_trader.py

# Expected: 2-3 trades in 10 minutes
```

### Assignment Run (8 hours)
```bash
# Edit config_live.py
RUN_DURATION = "8 h"

# Run bot (best during active trading hours)
python live_trader.py

# Expected: 10-15 trades in 8 hours
```

---

## 📈 Console Output Example

```
======================================================================
  EUR/USD LIVE PAPER TRADING BOT
======================================================================

Started: 2026-01-14 13:00:00

⏱️  Bot will run until: 2026-01-14 13:10:00
   (Duration: 10 min)

💰 Checking USD balance...
  Current USD balance: $50,000.00
  Required: $25,000.00
  Status: ✓ Sufficient

🧹 Closing Any Open Positions (Clean Slate)
  ✓ No position to close

🤖 Trading bot is now LIVE...
   Press CTRL+C to stop

📊 New Bar: 2026-01-14 13:05:00
   Close: 1.03450 | SMA20: 1.03410 | SMA50: 1.03350 | RSI: 45.2
   🎯 Signal: BUY - MA bullish (SMA20=1.03410 > SMA50=1.03350), RSI=45.2

🔔 EXECUTING TRADE
  Signal: BUY
  Current position: FLAT
  Target position: LONG
  Step 2: Opening new position...
  Placing order: BUY 20,000 EUR/USD
  ✓ Order filled at 1.03451
  Slippage: 0.1 pips

⏱️  9 minutes remaining...
⏱️  8 minutes remaining...
```

---

## ⚠️ Important Notes

### IB Gateway Requirements
- **Paper trading account** (port 4002)
- **Minimum $25,000 virtual balance**
- Must be **logged in** before running bot

### Position Management
- Bot **closes positions at START** (clean slate)
- Bot **closes positions at END** (clean slate)
- Only **ONE position** at a time (IB limitation)
- **20,000 EUR minimum** contract size

### Trading Hours
- Forex trades **24/5** (Sunday 5pm - Friday 5pm ET)
- Bot will trade **any time IB Gateway is open**
- For best results: Run during **active hours** (7am-5pm ET)

### Data Quality
- Uses **5-minute bars** (same as backtest)
- Warmup needs **50 bars** (~4 hours of data)
- First signals appear after warmup complete

---

## 🛡️ Safety Features

### Clean Slate
- Closes positions at start AND end
- Each run is independent
- No leftover positions

### Account Protection
- Checks balance before starting
- Refuses to run if insufficient funds
- No automatic re-deposits

### Graceful Shutdown
- CTRL+C closes positions cleanly
- Auto-closes at end of duration
- Saves all logs before exit

### Optional Safety Limits (Disabled by Default)
```python
ENABLE_SAFETY_LIMITS = False  # Set to True to enable

# Then configure:
MAX_DAILY_LOSS = 500          # Stop if lose $500
MAX_LOSS_PER_TRADE = 200      # Close position if lose $200
TRADING_HOURS = (9, 17)       # Only trade 9am-5pm ET
```

**For assignment:** Keep safety limits **DISABLED** to avoid premature stops.

---

## 🔧 Troubleshooting

### "Connection refused" to IB Gateway
```bash
# Check IB Gateway is running
docker ps | grep ib-gateway

# Check port 4002 is exposed
docker port <ib-gateway-container-name>

# Try connecting manually
telnet localhost 4002
```

### "Insufficient funds"
- Paper account needs **$25,000+**
- Check paper account balance in TWS/IB Gateway
- Reset paper account if needed (IB website)

### "No bars received"
- IB Gateway might not be logged in
- Check IB Gateway logs: `docker logs <container-name>`
- Restart IB Gateway if needed

### "Warmup taking too long"
- Warmup needs 50 bars (~4 hours)
- Historical data fetch might have failed
- Check logs for fetch errors

---

## 📊 Comparing to Backtest

After your live run, compare results:

### Load Trade Logs
```python
import pandas as pd

# Load live trading results
live = pd.read_csv('logs/trades_YYYYMMDD_HHMMSS.csv')

# Load backtest results
backtest = pd.read_csv('../trading_bot/EUR_USD_backtest_results.csv')

# Compare
print("Live Win Rate:", (live['trade_pnl'] > 0).mean())
print("Backtest Win Rate:", 0.265)  # From your backtest

print("Live Total P&L:", live['cumulative_pnl'].iloc[-1])
print("Backtest Total P&L:", -44.82)  # From your backtest
```

### Expected Differences
- **Slippage:** Live has real slippage, backtest assumes none
- **Timing:** Live bars might differ from historical
- **Market conditions:** Different time period = different results
- **Fewer trades:** Live runs shorter, fewer opportunities

---

## 🎓 For Your Assignment

**Recommended workflow:**

1. **Test run (10 min):** Verify everything works
   ```bash
   RUN_DURATION = "10 min"
   python live_trader.py
   ```

2. **Assignment run (8 hours):** Monday 13:00-21:00
   ```bash
   RUN_DURATION = "8 h"
   python live_trader.py
   ```

3. **Analyze results:** Compare to backtest
   - Win rate
   - Total P&L
   - Number of trades
   - Average hold time

4. **Document findings:** Note differences between live and backtest

**Expected for 8-hour run:**
- ~10-15 trades
- Similar win rate to backtest (~25-30%)
- Similar loss pattern (transaction costs dominate)
- Clean CSV log for analysis

---

## 📞 Support

**IB Gateway issues:** Check Docker IB Gateway setup chat
**Strategy questions:** Review backtest notebook
**Code issues:** Check logs in `logs/` directory

---

## 📄 License

Educational project - not financial advice.
