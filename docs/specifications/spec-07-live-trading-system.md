---

# **Specification 7: Live Trading System + Cloud Deployment**

**Project:** CPF Final Project - Automated Trading System  
**Module:** Live Trading Bot + Docker Deployment  
**Session:** 7  
**Date:** February 11, 2026  
**Prerequisites:** Session 6B Complete ✅ (optimized parameters with correct position size)

---

## 📋 **Overview**

Implement a live trading bot that:
1. Connects to Interactive Brokers via IB Gateway
2. Streams real-time EUR/USD price data
3. Generates signals using optimized parameters from Session 6B
4. Executes trades automatically via IB API
5. Logs all trades and P&L to CSV and console
6. Runs for specified duration (time-based)
7. Closes positions before weekend
8. Deploys to DigitalOcean via Docker

**Key Architecture Decision:** Standalone bot (imports existing modules) for simplicity and deployment ease.

---

## 🎯 **Success Criteria**

- ✅ Bot connects to IB Gateway successfully
- ✅ Real-time data streaming works (5min and 4H bars)
- ✅ Strategy signals generated correctly using Session 6B parameters
- ✅ Orders execute via IB API (paper trading account)
- ✅ Trade log captures every entry/exit with timestamps
- ✅ P&L tracking accurate (cumulative and per-trade)
- ✅ Weekend detection closes positions Friday 4pm EST
- ✅ Time-based runtime stops bot after specified duration
- ✅ Docker container builds and runs successfully
- ✅ Deployable to DigitalOcean with provided guide
- ✅ Type hints and docstrings throughout
- ✅ PEP 8 compliant, file headers present

---

## 📁 **Files to Create**

```
CPF-Final-Project/
├── deployment/
│   ├── trading_bot.py           # Main trading bot (300-400 lines)
│   ├── config_live.py            # Live trading configuration
│   ├── Dockerfile                # Container definition
│   ├── requirements.txt          # Python dependencies
│   ├── .dockerignore             # Build exclusions
│   └── DEPLOYMENT_GUIDE.md       # Step-by-step deployment instructions
```

---

## 1️⃣ **FILE: deployment/trading_bot.py**

### **Purpose**
Main executable for live trading. Connects to IB Gateway, streams data, generates signals, executes trades, and logs everything.

### **Architecture Overview**

```python
"""
Live Trading Bot for EUR/USD Forex

Author: Jürgen Kober + Claude Code Opus 4.6
Date: February 11, 2026

This bot implements the optimized MA+RSI+Momentum strategy from Session 6B
for live trading via Interactive Brokers API.

Key Features:
- Real-time data streaming
- Automated signal generation
- Order execution via IB API
- Trade and P&L logging
- Time-based runtime management
- Weekend position closing
- Error handling and reconnection
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from ib_async import IB, Stock, MarketOrder, util

# Import our modules
sys.path.append(str(Path(__file__).parent.parent))
from modules.indicators import SMA, RSI, Momentum
from config_live import (
    IB_HOST,
    IB_PORT,
    IB_CLIENT_ID,
    TIMEFRAME,
    RUN_DURATION,
    POSITION_SIZE,
    SMA_FAST,
    SMA_SLOW,
    RSI_PERIOD,
    RSI_LOWER,
    RSI_UPPER,
    MOMENTUM_PERIOD,
    MOMENTUM_THRESHOLD,
    CHECK_FREQUENCY,
    CLOSE_BEFORE_WEEKEND,
    WEEKEND_CLOSE_TIME
)
```

### **Class: `LiveTradingBot`**

```python
class LiveTradingBot:
    """
    Live trading bot for EUR/USD forex.
    
    Attributes:
        ib: IB API connection
        contract: EUR.USD contract
        position: Current position (1=LONG, -1=SHORT, 0=FLAT)
        entry_price: Entry price of current position
        trades: List of completed trades
        start_time: Bot start timestamp
        end_time: Bot end timestamp (based on RUN_DURATION)
        initial_capital: Starting capital
        current_capital: Current capital including P&L
    """
    
    def __init__(self):
        """Initialize trading bot with configuration from config_live.py"""
        self.ib = IB()
        self.contract = Stock('EUR', 'USD', 'IDEALPRO')
        
        # Position tracking
        self.position = 0  # 0=FLAT, 1=LONG, -1=SHORT
        self.entry_price = 0.0
        self.entry_time = None
        
        # Trade logging
        self.trades: List[Dict] = []
        self.trade_log_file = self._create_trade_log_file()
        
        # Runtime management
        self.start_time = datetime.now()
        self.end_time = self._calculate_end_time()
        
        # Capital tracking
        self.initial_capital = 10000.0
        self.current_capital = self.initial_capital
        
        # Price history for indicators
        self.price_history = pd.DataFrame(columns=['timestamp', 'close'])
        
        # Logging
        self._setup_logging()
        
        self.logger.info(f"Trading Bot initialized for {TIMEFRAME} timeframe")
        self.logger.info(f"Parameters: SMA {SMA_FAST}/{SMA_SLOW}, RSI {RSI_LOWER}/{RSI_UPPER}")
        self.logger.info(f"Position size: {POSITION_SIZE:,} EUR")
        self.logger.info(f"Runtime: {RUN_DURATION}")
        self.logger.info(f"Bot will run until: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
```

### **Key Methods**

**1. Connection Management**
```python
async def connect(self) -> bool:
    """
    Connect to IB Gateway.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        await self.ib.connectAsync(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID)
        self.logger.info(f"✅ Connected to IB Gateway at {IB_HOST}:{IB_PORT}")
        return True
    except Exception as e:
        self.logger.error(f"❌ Failed to connect to IB Gateway: {e}")
        return False

async def disconnect(self):
    """Disconnect from IB Gateway"""
    if self.ib.isConnected():
        self.ib.disconnect()
        self.logger.info("Disconnected from IB Gateway")
```

**2. Data Streaming**
```python
async def fetch_latest_price(self) -> Optional[float]:
    """
    Fetch current EUR/USD price.
    
    Returns:
        Current close price, or None if fetch fails
    """
    try:
        ticker = self.ib.reqMktData(self.contract)
        await self.ib.sleep(2)  # Wait for data
        
        if ticker.last:
            price = ticker.last
        elif ticker.close:
            price = ticker.close
        else:
            self.logger.warning("No price data available")
            return None
            
        self.ib.cancelMktData(self.contract)
        return price
        
    except Exception as e:
        self.logger.error(f"Error fetching price: {e}")
        return None

def update_price_history(self, price: float):
    """
    Add new price to history for indicator calculation.
    
    Args:
        price: Current close price
    """
    new_row = pd.DataFrame({
        'timestamp': [datetime.now()],
        'close': [price]
    })
    self.price_history = pd.concat([self.price_history, new_row], ignore_index=True)
    
    # Keep only necessary history (max SMA period + buffer)
    max_period = max(SMA_SLOW, RSI_PERIOD, MOMENTUM_PERIOD) + 50
    if len(self.price_history) > max_period:
        self.price_history = self.price_history.tail(max_period).reset_index(drop=True)
```

**3. Signal Generation**
```python
def calculate_indicators(self) -> Optional[Dict[str, pd.Series]]:
    """
    Calculate technical indicators on price history.
    
    Returns:
        Dict with indicator series, or None if insufficient data
    """
    if len(self.price_history) < SMA_SLOW + 10:
        return None
    
    try:
        # Calculate indicators using our modules
        sma_fast_indicator = SMA(period=SMA_FAST)
        sma_slow_indicator = SMA(period=SMA_SLOW)
        rsi_indicator = RSI(period=RSI_PERIOD)
        momentum_indicator = Momentum(period=MOMENTUM_PERIOD)
        
        sma_fast = sma_fast_indicator.calculate(self.price_history['close'])
        sma_slow = sma_slow_indicator.calculate(self.price_history['close'])
        rsi = rsi_indicator.calculate(self.price_history['close'])
        momentum = momentum_indicator.calculate(self.price_history['close'])
        
        return {
            'sma_fast': sma_fast,
            'sma_slow': sma_slow,
            'rsi': rsi,
            'momentum': momentum
        }
    except Exception as e:
        self.logger.error(f"Error calculating indicators: {e}")
        return None

def generate_signal(self, indicators: Dict[str, pd.Series]) -> int:
    """
    Generate trading signal based on indicators.
    
    Args:
        indicators: Dict of indicator series
        
    Returns:
        1 for BUY, -1 for SELL, 0 for HOLD
    """
    # Get latest values
    sma_fast = indicators['sma_fast'].iloc[-1]
    sma_slow = indicators['sma_slow'].iloc[-1]
    sma_fast_prev = indicators['sma_fast'].iloc[-2]
    sma_slow_prev = indicators['sma_slow'].iloc[-2]
    rsi = indicators['rsi'].iloc[-1]
    momentum = indicators['momentum'].iloc[-1]
    
    # Check for NaN
    if pd.isna(sma_fast) or pd.isna(sma_slow) or pd.isna(rsi) or pd.isna(momentum):
        return 0
    
    # BUY Signal: SMA crossover UP + RSI < 70 + Momentum > 0
    if (sma_fast_prev <= sma_slow_prev and  # Was below or equal
        sma_fast > sma_slow and              # Now above (crossover)
        rsi < RSI_UPPER and
        momentum > MOMENTUM_THRESHOLD):
        self.logger.info(f"📈 BUY Signal: SMA {sma_fast:.4f} crossed above {sma_slow:.4f}, "
                        f"RSI {rsi:.1f}, Momentum {momentum:.5f}")
        return 1
    
    # SELL Signal: SMA crossover DOWN + RSI > 30 + Momentum < 0
    if (sma_fast_prev >= sma_slow_prev and  # Was above or equal
        sma_fast < sma_slow and              # Now below (crossover)
        rsi > RSI_LOWER and
        momentum < -MOMENTUM_THRESHOLD):
        self.logger.info(f"📉 SELL Signal: SMA {sma_fast:.4f} crossed below {sma_slow:.4f}, "
                        f"RSI {rsi:.1f}, Momentum {momentum:.5f}")
        return -1
    
    return 0  # HOLD
```

**4. Order Execution**
```python
async def execute_order(self, signal: int, price: float):
    """
    Execute order based on signal.
    
    Args:
        signal: 1 for BUY, -1 for SELL
        price: Current market price
    """
    # Close existing position if signal is opposite
    if self.position != 0 and signal != self.position:
        await self.close_position(price)
    
    # Open new position if FLAT
    if self.position == 0 and signal != 0:
        await self.open_position(signal, price)

async def open_position(self, direction: int, price: float):
    """
    Open new position.
    
    Args:
        direction: 1 for LONG, -1 for SHORT
        price: Entry price
    """
    try:
        # Create order
        action = 'BUY' if direction == 1 else 'SELL'
        order = MarketOrder(action, POSITION_SIZE)
        
        # Place order
        trade = self.ib.placeOrder(self.contract, order)
        await self.ib.sleep(2)  # Wait for fill
        
        if trade.orderStatus.status == 'Filled':
            self.position = direction
            self.entry_price = price
            self.entry_time = datetime.now()
            
            self.logger.info(f"✅ TRADE EXECUTED: {action} {POSITION_SIZE:,} EUR @ {price:.4f}")
            self.logger.info(f"Position: {'LONG' if direction == 1 else 'SHORT'}")
        else:
            self.logger.error(f"❌ Order not filled: {trade.orderStatus.status}")
            
    except Exception as e:
        self.logger.error(f"Error executing order: {e}")

async def close_position(self, price: float):
    """
    Close current position and log trade.
    
    Args:
        price: Exit price
    """
    if self.position == 0:
        return
    
    try:
        # Create closing order
        action = 'SELL' if self.position == 1 else 'BUY'
        order = MarketOrder(action, POSITION_SIZE)
        
        # Place order
        trade = self.ib.placeOrder(self.contract, order)
        await self.ib.sleep(2)
        
        if trade.orderStatus.status == 'Filled':
            # Calculate P&L
            gross_pnl = self.position * (price - self.entry_price) * POSITION_SIZE
            # Transaction costs: 1 pip spread = 0.0001, at entry and exit
            spread_cost = 2 * 0.0001 * POSITION_SIZE  # $4.00 for 20K position
            net_pnl = gross_pnl - spread_cost
            
            # Update capital
            self.current_capital += net_pnl
            
            # Log trade
            trade_record = {
                'entry_time': self.entry_time,
                'exit_time': datetime.now(),
                'direction': 'LONG' if self.position == 1 else 'SHORT',
                'entry_price': self.entry_price,
                'exit_price': price,
                'size': POSITION_SIZE,
                'gross_pnl': gross_pnl,
                'costs': spread_cost,
                'net_pnl': net_pnl,
                'capital': self.current_capital
            }
            self.trades.append(trade_record)
            self._save_trade(trade_record)
            
            self.logger.info(f"✅ POSITION CLOSED: {action} {POSITION_SIZE:,} EUR @ {price:.4f}")
            self.logger.info(f"P&L: ${net_pnl:.2f} | Cumulative: ${self.current_capital - self.initial_capital:.2f}")
            
            # Reset position
            self.position = 0
            self.entry_price = 0.0
            self.entry_time = None
        else:
            self.logger.error(f"❌ Close order not filled: {trade.orderStatus.status}")
            
    except Exception as e:
        self.logger.error(f"Error closing position: {e}")
```

**5. Runtime Management**
```python
def should_continue_running(self) -> bool:
    """
    Check if bot should continue running.
    
    Returns:
        True if should continue, False if should stop
    """
    now = datetime.now()
    
    # Check if runtime expired
    if now >= self.end_time:
        self.logger.info(f"⏰ Runtime expired. Bot ran for {RUN_DURATION}")
        return False
    
    # Check if approaching weekend
    if CLOSE_BEFORE_WEEKEND and self.is_approaching_weekend():
        self.logger.info("⏰ Approaching weekend. Closing positions and stopping bot.")
        return False
    
    return True

def is_approaching_weekend(self) -> bool:
    """
    Check if it's Friday afternoon (4pm EST or later).
    
    Returns:
        True if should close for weekend
    """
    now = datetime.now()
    
    # Check if Friday
    if now.weekday() != 4:  # 0=Monday, 4=Friday
        return False
    
    # Parse weekend close time (format: "16:00")
    hour, minute = map(int, WEEKEND_CLOSE_TIME.split(':'))
    close_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    return now >= close_time

def is_forex_open(self) -> bool:
    """
    Check if forex market is open (Sunday 5pm EST - Friday 5pm EST).
    
    Returns:
        True if market is open
    """
    now = datetime.now()
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    
    # Market closed Saturday
    if weekday == 5:
        return False
    
    # Market closed most of Sunday (opens 5pm EST)
    if weekday == 6:
        return now.hour >= 17
    
    # Market closes Friday 5pm EST
    if weekday == 4:
        return now.hour < 17
    
    # Open Monday-Thursday
    return True

def _calculate_end_time(self) -> datetime:
    """
    Calculate when bot should stop based on RUN_DURATION.
    
    Returns:
        End datetime
    """
    duration_str = RUN_DURATION.strip()
    
    if duration_str.endswith('h'):
        hours = int(duration_str[:-1].strip())
        return self.start_time + timedelta(hours=hours)
    elif duration_str.endswith('d'):
        days = int(duration_str[:-1].strip())
        return self.start_time + timedelta(days=days)
    elif duration_str.endswith('m'):
        minutes = int(duration_str[:-1].strip())
        return self.start_time + timedelta(minutes=minutes)
    else:
        # Default: run for 8 hours
        return self.start_time + timedelta(hours=8)
```

**6. Main Loop**
```python
async def run(self):
    """
    Main trading loop.
    
    Runs continuously until:
    1. Runtime expires (RUN_DURATION)
    2. Weekend closing time reached
    3. Error forces stop
    """
    # Connect to IB Gateway
    if not await self.connect():
        self.logger.error("Failed to connect. Exiting.")
        return
    
    try:
        self.logger.info("🚀 Trading bot started")
        self.logger.info(f"Checking for signals every {CHECK_FREQUENCY} seconds")
        
        iteration = 0
        
        while self.should_continue_running():
            iteration += 1
            
            # Check if market is open
            if not self.is_forex_open():
                self.logger.info("Market closed. Waiting...")
                await asyncio.sleep(CHECK_FREQUENCY)
                continue
            
            # Fetch latest price
            price = await self.fetch_latest_price()
            if price is None:
                await asyncio.sleep(CHECK_FREQUENCY)
                continue
            
            # Update price history
            self.update_price_history(price)
            
            # Log current status every 10 iterations
            if iteration % 10 == 0:
                time_remaining = self.end_time - datetime.now()
                hours_remaining = time_remaining.total_seconds() / 3600
                self.logger.info(f"Status: Price={price:.4f}, Position={'LONG' if self.position==1 else 'SHORT' if self.position==-1 else 'FLAT'}, "
                               f"P&L=${self.current_capital - self.initial_capital:.2f}, "
                               f"Time remaining={hours_remaining:.1f}h")
            
            # Calculate indicators and generate signal
            indicators = self.calculate_indicators()
            if indicators is not None:
                signal = self.generate_signal(indicators)
                
                if signal != 0:
                    await self.execute_order(signal, price)
            
            # Wait before next check
            await asyncio.sleep(CHECK_FREQUENCY)
        
        # Close any open positions before stopping
        if self.position != 0:
            self.logger.info("Closing open position before shutdown...")
            price = await self.fetch_latest_price()
            if price:
                await self.close_position(price)
        
        # Final summary
        self._print_summary()
        
    except Exception as e:
        self.logger.error(f"Error in main loop: {e}")
    finally:
        await self.disconnect()
```

**7. Logging and File Management**
```python
def _setup_logging(self):
    """Setup logging to file and console"""
    timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
    log_file = Path(__file__).parent / 'logs' / f'trading_bot_{timestamp}.log'
    log_file.parent.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    self.logger = logging.getLogger(__name__)

def _create_trade_log_file(self) -> Path:
    """Create CSV file for trade logging"""
    timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
    log_file = Path(__file__).parent / 'logs' / f'trades_{timestamp}.csv'
    log_file.parent.mkdir(exist_ok=True)
    
    # Write header
    with open(log_file, 'w') as f:
        f.write('entry_time,exit_time,direction,entry_price,exit_price,size,gross_pnl,costs,net_pnl,capital\n')
    
    return log_file

def _save_trade(self, trade: Dict):
    """Append trade to CSV log"""
    with open(self.trade_log_file, 'a') as f:
        f.write(f"{trade['entry_time']},{trade['exit_time']},{trade['direction']},"
               f"{trade['entry_price']:.4f},{trade['exit_price']:.4f},{trade['size']},"
               f"{trade['gross_pnl']:.2f},{trade['costs']:.2f},{trade['net_pnl']:.2f},"
               f"{trade['capital']:.2f}\n")

def _print_summary(self):
    """Print final trading summary"""
    self.logger.info("\n" + "="*70)
    self.logger.info("TRADING SESSION SUMMARY")
    self.logger.info("="*70)
    self.logger.info(f"Timeframe: {TIMEFRAME}")
    self.logger.info(f"Duration: {self.end_time - self.start_time}")
    self.logger.info(f"Total Trades: {len(self.trades)}")
    
    if len(self.trades) > 0:
        net_pnls = [t['net_pnl'] for t in self.trades]
        winning_trades = [p for p in net_pnls if p > 0]
        losing_trades = [p for p in net_pnls if p < 0]
        
        self.logger.info(f"Winning Trades: {len(winning_trades)}")
        self.logger.info(f"Losing Trades: {len(losing_trades)}")
        self.logger.info(f"Win Rate: {len(winning_trades)/len(self.trades)*100:.1f}%")
        self.logger.info(f"Total P&L: ${sum(net_pnls):.2f}")
        self.logger.info(f"Avg Trade: ${np.mean(net_pnls):.2f}")
        self.logger.info(f"Best Trade: ${max(net_pnls):.2f}")
        self.logger.info(f"Worst Trade: ${min(net_pnls):.2f}")
    
    self.logger.info(f"Final Capital: ${self.current_capital:.2f}")
    self.logger.info(f"Return: {(self.current_capital/self.initial_capital - 1)*100:.2f}%")
    self.logger.info("="*70)
    
    # Save summary to file
    summary_file = self.trade_log_file.with_suffix('.txt').with_name(
        self.trade_log_file.stem + '_summary.txt'
    )
    with open(summary_file, 'w') as f:
        f.write(f"Trading Session Summary\n")
        f.write(f"Timeframe: {TIMEFRAME}\n")
        f.write(f"Total Trades: {len(self.trades)}\n")
        if len(self.trades) > 0:
            f.write(f"Win Rate: {len(winning_trades)/len(self.trades)*100:.1f}%\n")
            f.write(f"Total P&L: ${sum(net_pnls):.2f}\n")
        f.write(f"Final Capital: ${self.current_capital:.2f}\n")
```

**8. Entry Point**
```python
async def main():
    """Entry point for trading bot"""
    bot = LiveTradingBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 2️⃣ **FILE: deployment/config_live.py**

### **Purpose**
Configuration file for live trading parameters. Easily modified without rebuilding Docker image.

```python
"""
Live Trading Configuration

Author: Jürgen Kober + Claude Code Opus 4.6
Date: February 11, 2026

Configuration for live trading bot with Session 6B optimized parameters.
"""

# =============================================================================
# IB GATEWAY CONNECTION
# =============================================================================

IB_HOST = 'localhost'  # IB Gateway running on same machine (Docker host mode)
IB_PORT = 4002         # Paper trading port (4001 for live)
IB_CLIENT_ID = 3       # Unique client ID (change if running multiple bots)

# =============================================================================
# TIMEFRAME SELECTION
# =============================================================================

# Choose timeframe: '5min' or '4H'
TIMEFRAME = '5min'  # Change to '4H' for 4-hour trading

# =============================================================================
# RUNTIME CONFIGURATION
# =============================================================================

# How long should the bot run?
# Format: "X h" for hours, "X d" for days, "X m" for minutes
# Examples: "1 h", "8 h", "5 d"
RUN_DURATION = "1 h"  # Start with 1-hour test

# How often to check for new data (seconds)
# 5min timeframe: check every 60 seconds
# 4H timeframe: check every 300 seconds (5 minutes)
CHECK_FREQUENCY = 60 if TIMEFRAME == '5min' else 300

# =============================================================================
# WEEKEND MANAGEMENT
# =============================================================================

# Close positions before weekend?
CLOSE_BEFORE_WEEKEND = True

# What time Friday to close? (EST timezone)
# Format: "HH:MM" (24-hour)
WEEKEND_CLOSE_TIME = "16:00"  # 4:00 PM EST

# =============================================================================
# POSITION SIZING
# =============================================================================

# Position size in EUR (IBKR minimum: 20,000 EUR)
POSITION_SIZE = 20000

# =============================================================================
# STRATEGY PARAMETERS - SESSION 6B OPTIMIZED
# =============================================================================

if TIMEFRAME == '5min':
    # 5-minute optimized parameters (Session 6B)
    SMA_FAST = 15
    SMA_SLOW = 70
    RSI_PERIOD = 14
    RSI_LOWER = 35
    RSI_UPPER = 75
    MOMENTUM_PERIOD = 10
    MOMENTUM_THRESHOLD = 0.0
    
elif TIMEFRAME == '4H':
    # 4-hour optimized parameters (Session 6B)
    SMA_FAST = 20
    SMA_SLOW = 70
    RSI_PERIOD = 21
    RSI_LOWER = 35
    RSI_UPPER = 70
    MOMENTUM_PERIOD = 14
    MOMENTUM_THRESHOLD = 0.0

else:
    raise ValueError(f"Invalid timeframe: {TIMEFRAME}. Must be '5min' or '4H'")

# =============================================================================
# LOGGING
# =============================================================================

# Log directory (created automatically)
LOG_DIR = 'logs'
```

---

## 3️⃣ **FILE: deployment/Dockerfile**

### **Purpose**
Docker container definition for trading bot.

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy trading bot and configuration
COPY trading_bot.py .
COPY config_live.py .

# Copy modules from parent directory
COPY ../modules /app/modules

# Create logs directory
RUN mkdir -p /app/logs

# Run the trading bot
CMD ["python", "-u", "trading_bot.py"]
```

---

## 4️⃣ **FILE: deployment/requirements.txt**

### **Purpose**
Python dependencies for trading bot.

```
ib_async==2.1.0
pandas>=2.0.0
numpy>=1.24.0
```

---

## 5️⃣ **FILE: deployment/.dockerignore**

### **Purpose**
Exclude unnecessary files from Docker build.

```
__pycache__
*.pyc
*.pyo
*.log
logs/
.git
.gitignore
*.md
.DS_Store
*.csv
```

---

## 6️⃣ **FILE: deployment/DEPLOYMENT_GUIDE.md**

### **Purpose**
Complete step-by-step guide for deploying to DigitalOcean.

```markdown
# Trading Bot Deployment Guide

Complete guide for deploying the EUR/USD trading bot to DigitalOcean.

## Prerequisites

- ✅ DigitalOcean droplet running (157.230.113.17)
- ✅ IB Gateway running in Docker on droplet
- ✅ SSH access to droplet
- ✅ All files in `deployment/` directory

## Deployment Steps

### Step 1: Prepare Local Files [LOCAL]

Ensure all files are in the `deployment/` directory:
```bash
cd ~/Projects/Python-Quants-CPF-Program/_Final-Poject-Feb-2026/CPF-Final-Project/deployment

ls -la
# Should see:
# - trading_bot.py
# - config_live.py
# - Dockerfile
# - requirements.txt
# - .dockerignore
# - DEPLOYMENT_GUIDE.md
```

### Step 2: Transfer Files to Droplet [LOCAL]

```bash
# Create deployment directory on droplet
ssh root@157.230.113.17 "mkdir -p /root/trading_bot"

# Transfer deployment files
scp trading_bot.py config_live.py requirements.txt Dockerfile .dockerignore \
    root@157.230.113.17:/root/trading_bot/

# Transfer modules directory
scp -r ../modules root@157.230.113.17:/root/trading_bot/
```

### Step 3: Build Docker Image [CLOUD]

```bash
# Connect to droplet
ssh root@157.230.113.17

# Navigate to deployment directory
cd /root/trading_bot

# Build Docker image
docker build -t trading-bot:latest .

# Verify image created
docker images | grep trading-bot
```

### Step 4: Configure Trading Parameters [CLOUD]

Edit `config_live.py` on the droplet to set runtime duration:

```bash
# Still on droplet
nano /root/trading_bot/config_live.py

# Change these lines:
# TIMEFRAME = '5min'  # or '4H'
# RUN_DURATION = "1 h"  # Start with 1-hour test

# Save: Ctrl+X, Y, Enter
```

### Step 5: Run Trading Bot [CLOUD]

**For 5-minute timeframe:**
```bash
docker run -d \
  --name trading-bot-5min \
  --network host \
  --restart unless-stopped \
  -v /root/trading_bot/logs:/app/logs \
  -v /root/trading_bot/config_live.py:/app/config_live.py \
  trading-bot:latest
```

**For 4-hour timeframe:**
```bash
# First, update config_live.py to set TIMEFRAME = '4H'
nano /root/trading_bot/config_live.py

docker run -d \
  --name trading-bot-4h \
  --network host \
  --restart unless-stopped \
  -v /root/trading_bot/logs:/app/logs \
  -v /root/trading_bot/config_live.py:/app/config_live.py \
  trading-bot:latest
```

### Step 6: Verify Deployment [CLOUD]

```bash
# Check container is running
docker ps | grep trading-bot

# View live logs
docker logs -f trading-bot-5min

# Expected output:
# INFO - Trading Bot initialized for 5min timeframe
# INFO - Parameters: SMA 15/70, RSI 35/75
# INFO - Connected to IB Gateway at localhost:4002
# INFO - Trading bot started
```

## Monitoring Commands

### From Local Machine [LOCAL]

```bash
# Quick status
ssh root@157.230.113.17 "docker ps | grep trading-bot"

# View last 20 log lines
ssh root@157.230.113.17 "docker logs trading-bot-5min --tail 20"

# Live log stream
ssh root@157.230.113.17 "docker logs -f trading-bot-5min"

# Check latest P&L
ssh root@157.230.113.17 "docker logs trading-bot-5min 2>&1 | grep 'P&L:' | tail -1"

# Count trades executed
ssh root@157.230.113.17 "docker logs trading-bot-5min 2>&1 | grep 'TRADE EXECUTED' | wc -l"
```

### On Droplet [CLOUD]

```bash
# Container status
docker ps -a | grep trading-bot

# Full logs
docker logs trading-bot-5min

# Follow logs
docker logs -f trading-bot-5min

# Check if still running
docker inspect trading-bot-5min | grep Status
```

## Downloading Results

### After Bot Stops [LOCAL]

```bash
# Create local results directory
mkdir -p ~/trading_results_$(date +%Y%m%d)

# Download trade log CSV
scp 'root@157.230.113.17:/root/trading_bot/logs/trades_*.csv' ~/trading_results_$(date +%Y%m%d)/

# Download full log
scp 'root@157.230.113.17:/root/trading_bot/logs/trading_bot_*.log' ~/trading_results_$(date +%Y%m%d)/

# Download summary
scp 'root@157.230.113.17:/root/trading_bot/logs/trades_*_summary.txt' ~/trading_results_$(date +%Y%m%d)/
```

## Container Management

### Stopping the Bot [CLOUD]

```bash
ssh root@157.230.113.17
docker stop trading-bot-5min
exit
```

### Starting Stopped Container [CLOUD]

```bash
ssh root@157.230.113.17
docker start trading-bot-5min
exit
```

### Removing Container [CLOUD]

```bash
ssh root@157.230.113.17
docker stop trading-bot-5min
docker rm trading-bot-5min
exit
```

### Deploying New Instance [CLOUD]

```bash
ssh root@157.230.113.17

# Update configuration if needed
nano /root/trading_bot/config_live.py
# Change RUN_DURATION, TIMEFRAME, etc.

# Run new container with new name
docker run -d \
  --name trading-bot-8h \
  --network host \
  --restart unless-stopped \
  -v /root/trading_bot/logs:/app/logs \
  -v /root/trading_bot/config_live.py:/app/config_live.py \
  trading-bot:latest

exit
```

## Testing Protocol

### Phase 1: Initial Validation (Day 1)

**1.1 First 1-hour Run**
```bash
# Set RUN_DURATION = "1 h" in config_live.py
# Deploy and monitor for 1 hour
# Verify: connection, data fetching, logging
```

**1.2 Second 1-hour Run**
```bash
# If first run successful, repeat
# Verify: signal generation (if signals occur)
# Check for any errors in logs
```

**1.3 Third 1-hour Run**
```bash
# Final 1-hour validation
# Verify: trade execution (if signals occur)
# Confirm P&L tracking accurate
```

### Phase 2: Extended Test (Day 2)

**2.1 4-hour Run**
```bash
# Set RUN_DURATION = "4 h"
# Deploy for longer stability test
# Monitor for first hour, then check periodically
# Verify bot handles extended operation
```

### Phase 3: Week-Long Validation (Days 3-7)

**Option A: Daily 8-hour Runs**
```bash
# Set RUN_DURATION = "8 h"
# Deploy each morning for 5 trading days
# Ensures clean start each day
# Easier to debug if issues
```

**Option B: Continuous 5-day Run**
```bash
# Set RUN_DURATION = "5 d"
# Deploy once, let run for full week
# Bot handles weekends automatically
# More "production-like" testing
```

## Troubleshooting

### Bot Won't Connect to IB Gateway

```bash
# Check if IB Gateway is running
ssh root@157.230.113.17 "docker ps | grep ibgateway"

# Check IB Gateway logs
ssh root@157.230.113.17 "docker logs ibgateway | tail -50"

# Verify port 4002 is listening
ssh root@157.230.113.17 "netstat -tuln | grep 4002"
```

### Bot Crashes Immediately

```bash
# View crash logs
ssh root@157.230.113.17 "docker logs trading-bot-5min"

# Common issues:
# - Module import errors (check modules/ copied correctly)
# - Config syntax errors (verify config_live.py)
# - IB connection refused (check IB Gateway running)
```

### No Trades Executing

```bash
# Check if signals are being generated
ssh root@157.230.113.17 "docker logs trading-bot-5min | grep 'Signal'"

# Verify market is open
ssh root@157.230.113.17 "docker logs trading-bot-5min | grep 'Market closed'"

# Possible reasons:
# - Market closed (weekend/holiday)
# - No crossovers in current data
# - Not enough price history yet (wait for SMA_SLOW bars)
```

## Best Practices

1. **Always start with 1-hour tests** before longer runs
2. **Monitor first 30 minutes** of any new deployment
3. **Download results immediately** after bot stops
4. **Keep old containers** until results verified
5. **Document any parameter changes** in git commit messages

## Quick Reference

### Key File Locations

- **Droplet:** `/root/trading_bot/`
- **Logs:** `/root/trading_bot/logs/`
- **Config:** `/root/trading_bot/config_live.py`
- **Container:** `trading-bot-5min` or `trading-bot-4h`

### Key Commands

```bash
# Deploy
scp files... && ssh && docker build && docker run

# Monitor
docker logs -f trading-bot-5min

# Download
scp logs back to local

# Update config
nano config_live.py && docker stop && docker start
```
```

---

## 🧪 **Testing Protocol**

### **Phase 1: Initial Validation (Day 1)**

**Test 1.1: First 1-Hour Run**
```bash
# LOCAL: Set configuration
cd deployment/
nano config_live.py
# Set: TIMEFRAME = '5min', RUN_DURATION = "1 h"

# Deploy to droplet
[Follow DEPLOYMENT_GUIDE.md Steps 1-5]

# Monitor for full hour
ssh root@157.230.113.17 "docker logs -f trading-bot-5min"

# Expected outcomes:
# ✅ Bot connects to IB Gateway
# ✅ Price data fetched successfully
# ✅ Indicators calculated (after ~70 bars)
# ✅ Logs show status updates
# ✅ Bot stops after 1 hour
```

**Test 1.2: Second 1-Hour Run**
```bash
# Stop first container
ssh root@157.230.113.17 "docker stop trading-bot-5min && docker rm trading-bot-5min"

# Deploy again (same config)
[Repeat deployment]

# Monitor
# Expected outcomes:
# ✅ Clean restart
# ✅ Signal generation working (if crossovers occur)
# ✅ No errors in logs
```

**Test 1.3: Third 1-Hour Run**
```bash
# Repeat once more
# Expected outcomes:
# ✅ Trade execution (if signals occur)
# ✅ P&L tracking accurate
# ✅ CSV log created
# ✅ Position closed at end if open
```

### **Phase 2: Extended Test (Day 2)**

**Test 2.1: 4-Hour Stability Run**
```bash
# Update config
nano config_live.py
# Set: RUN_DURATION = "4 h"

# Deploy
[Follow deployment steps]

# Monitor first 30 minutes, then check hourly
# Expected outcomes:
# ✅ Bot runs for full 4 hours
# ✅ Handles multiple bars without crash
# ✅ Memory usage stable
# ✅ All trades logged correctly
```

### **Phase 3: Week-Long Validation**

**Option A: Daily 8-Hour Runs (Recommended)**
```bash
# Each trading day for 5 days:
# Set RUN_DURATION = "8 h"
# Deploy at market open
# Bot stops automatically after 8 hours
# Download results
# Clean container
# Repeat next day

# Advantages:
# - Clean start each day
# - Easier to debug
# - Clear daily results
```

**Option B: Continuous 5-Day Run (Advanced)**
```bash
# Set RUN_DURATION = "5 d"
# Deploy Monday morning
# Bot runs continuously
# Handles weekend automatically
# Stops Friday afternoon or after 5 days

# Advantages:
# - More "production-like"
# - Tests long-term stability
# - Minimal manual intervention
```

---

## 📊 **Expected Results**

### **5-Minute Timeframe (Session 6B Parameters)**

**Based on backtest performance:**
- Sharpe Ratio: ~4.59
- Expected Return: ~8.25% (on $10K capital with $20K positions)
- Trade Frequency: ~10-15 trades per week
- Average Trade: ~$0.77 profit per trade
- Win Rate: ~43%

**Live Reality Check:**
- Slippage may reduce returns slightly
- Network latency may miss some signals
- Market conditions may differ from backtest period

### **4-Hour Timeframe (Session 6B Parameters)**

**Based on backtest performance:**
- Sharpe Ratio: ~1.42
- Expected Return: ~60% (annualized)
- Trade Frequency: ~1-2 trades per week
- Average Trade: ~$134 profit per trade
- Win Rate: ~47%

**Live Reality Check:**
- Fewer trades = higher variance in weekly results
- 1-week test may show 0-3 trades only
- Performance more sensitive to individual trade outcomes

---

## ⚠️ **Critical Notes**

### **1. Paper Trading Only**
- All testing on IBKR paper trading account
- No real money at risk
- Results demonstrate system functionality, not guaranteed profitability

### **2. Transaction Costs**
- Bot assumes 1 pip spread ($2 per trade with 20K position)
- Real spreads may vary (0.5-2 pips depending on market conditions)
- Bot does NOT model slippage (market orders may fill at worse prices)

### **3. Market Conditions**
- Bot optimized on 2023-2025 EUR/USD data
- Current market may behave differently
- Trend-following struggles in ranging markets

### **4. Overfitting Risk**
- Parameters optimized to historical data
- No out-of-sample testing done
- Past performance ≠ future results

### **5. Network Dependencies**
- Bot requires stable connection to IB Gateway
- Any network interruption may miss signals
- Droplet must maintain connection to IBKR servers

---

## ✅ **Definition of Done**

- [ ] All 6 files created in `deployment/` directory
- [ ] `trading_bot.py` implements all required functionality
- [ ] `config_live.py` contains Session 6B optimized parameters
- [ ] `Dockerfile` builds successfully
- [ ] `DEPLOYMENT_GUIDE.md` provides complete instructions
- [ ] Testing protocol clearly defined
- [ ] Bot connects to IB Gateway successfully
- [ ] Real-time data streaming works
- [ ] Signal generation tested
- [ ] Order execution tested (if signals occur)
- [ ] Trade logging verified (CSV + console)
- [ ] P&L tracking accurate
- [ ] Weekend closing logic works
- [ ] Time-based runtime stops correctly
- [ ] Docker deployment successful
- [ ] Type hints and docstrings complete
- [ ] PEP 8 compliant (black formatted)
- [ ] File headers present

---

## 🎯 **Post-Implementation**

### **After Claude Code Completes:**

1. **Review all generated files**
2. **Test locally first** (if TWS running on Mac)
3. **Deploy to DigitalOcean** following guide
4. **Run Phase 1 tests** (3x 1-hour runs)
5. **Document any issues** encountered
6. **Run Phase 2 test** (4-hour stability)
7. **Begin Phase 3** (week-long validation)

### **Data Collection:**

For each test run, collect:
- Trade log CSV
- Full text log
- Summary file
- Any error messages
- Performance metrics

This data will be used in Session 8 (Notebook Integration) to:
- Compare backtest vs. live performance
- Analyze live trading behavior
- Document deployment process
- Show real-world results

---

## 💰 **Estimated Cost**

**Claude Code Implementation:** ~$1.50-2.00 (15-20 minutes)
**Total Project After Session 7:** ~$11-12 of $25 budget
**Remaining Buffer:** ~$13-14

---

## 🎯 **Ready for Implementation**

**This specification is complete and ready for Claude Code (Opus 4.6).**

**Key Features:**
- ✅ Complete standalone bot
- ✅ Reuses existing modules
- ✅ Session 6B optimized parameters
- ✅ Correct 20,000 EUR position size
- ✅ Time-based runtime
- ✅ Weekend management
- ✅ Docker deployment
- ✅ Comprehensive testing protocol
- ✅ Production-ready logging

---

**End of Specification 7**

---
