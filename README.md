# End-to-End Cloud Deployment of Automated Trading Strategies with IBKR

## Developing an EUR/USD Algorithmic Trading System

A production-grade automated forex trading system implementing a multi-indicator trend-following strategy with cloud deployment infrastructure.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Interactive Brokers](https://img.shields.io/badge/broker-Interactive%20Brokers-green.svg)](https://www.interactivebrokers.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Project Overview

This project implements a complete algorithmic trading system for EUR/USD forex trading, from strategy development and backtesting to live deployment on cloud infrastructure. The system combines a trend-following approach (SMA crossovers) with momentum exhaustion filters (RSI and momentum indicators) for robust production infrastructure including Docker containerization, cloud deployment, and automated reconnection handling.

**Key Features:**
- Multi-indicator trend-following strategy with configurable parameters
- Comprehensive backtesting framework with transaction cost modeling
- Grid search optimization for parameter tuning
- Live trading via Interactive Brokers API
- Cloud deployment on DigitalOcean with Docker containers
- Automatic reconnection handling for IB maintenance windows
- Position reconciliation and error recovery
- Complete logging and trade tracking

**Final Project:** This is the capstone project for the Python Quants' Certificate in Python for Finance, demonstrating the complete lifecycle from research to production deployment.

---

## 📁 Project Structure

```
CPF-Final-Project/
├── README.md                                # This file
├── CLAUDE.md                                # Project instructions
├── ALGORITHMIC-TRADING-FINAL-PROJECT.ipynb  # Final deliverable
├── LICENSE                                  # License agreement
├── requirements.txt                         # Python dependencies
│
├── data/                                    # Market data and results storage
│   ├── historical/                          # Historical price data from IB
│   │   ├── 5min/                            # 5-minute bars
│   │   ├── 4H/                              # 4-hour bars
│   │   └── 1D/                              # Daily bars
│   ├── backtest/                            # Backtest result CSVs
│   └── optimization/                        # Grid search optimization results
│
├── deployment/                              # Production deployment
│   ├── trading_bot.py                       # Live trading bot
│   ├── config_live.py                       # Runtime config with optimized params
│   ├── Dockerfile                           # Container build (context is project root)
│   ├── requirements.txt                     # Bot dependencies
│   ├── .dockerignore
│   ├── .env.example                         # Environment variables template
│   ├── logs/                                # Runtime logs (gitignored)
│   │   ├── trading_bot_*.log
│   │   ├── trades_*.csv
│   │   └── equity_*.csv
│   └── DEPLOYMENT_GUIDE.md                  # Cloud deployment instructions
│
├── docs/                                    # Documentation
│   ├── handoffs/                            # Session handoff documents
│   ├── specifications/                      # Session specification documents
│   ├── guides/                              # Implementation guides
│   ├── project-progress.md                  # Documentation of development timeline
│   ├── decision-point-session-02.md         # Decision data fetching approach
│   └── ib-currency-conversion-guide.md      # Currency conversion
│
├── modules/                                 # Core implementation modules
│   ├── __init__.py
│   ├── backtest/                            # Backtesting framework
│   │   ├── __init__.py
│   │   ├── engine.py                        # BacktestEngine (t+1 execution)
│   │   ├── metrics.py                       # Sharpe, drawdown, win rate, etc.
│   │   └── transaction_costs.py             # Transaction cost modeling
│   ├── config/                              # Global configuration
│   │   ├── __init__.py
│   │   ├── constants.py                     # System-wide constants
│   │   ├── timeframes.py                    # Timeframe configurations
│   ├── data/                                # Data handling
│   │   ├── __init__.py
│   │   ├── loader.py                        # CSV loading with datetime indexing
│   ├── indicators/                          # Technical indicators
│   │   ├── __init__.py
│   │   ├── base.py                          # Abstract Indicator base class
│   │   ├── momentum.py                      # Momentum implementations
│   │   ├── rsi.py                           # RSI implementations
│   │   └── sma.py                           # SMA implementations
│   ├── optimization/                        # Parameter optimization
│   │   ├── __init__.py
│   │   ├── grid_search.py                   # GridSearchOptimizer
│   │   └── results.py                       # OptimizationResults analysis
│   └── strategy/                            # Trading strategy
│       ├── __init__.py
│       ├── base.py                          # Abstract Strategy base class
│       └── ma_rsi_momentum.py               # Multi-Indicator Trend-Following Strategy
│
└── scripts/                                 # Utility scripts
    ├── fetch_historical_data.py             # Download data from IB Gateway
    ├── optimize_parameters.py               # Run grid search optimization
    └── regenerate_results_20k.py            # Re-run optimization
```

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Interactive Brokers account (live or paper trading)
- TWS or IB Gateway installed locally, OR
- Docker for containerized IB Gateway deployment

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd CPF-Final-Project
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure IB connection:**
```bash
# For local testing with TWS/IB Gateway
# Edit deployment/config_live.py:
# HOST = '127.0.0.1'
# PORT = 4002  # Paper trading port

# For cloud deployment
# Edit deployment/config_live.py:
# HOST = 'XXX.XXX.XXX.XX'  # Your droplet IP
# PORT = 4002
```

### Running Backtests

```bash
# Run backtest with default parameters (5-minute timeframe)
python scripts/run_backtest.py --timeframe 5min

# Run with Session 8A optimized parameters
python scripts/run_backtest.py \
    --timeframe 5min \
    --sma-fast 15 \
    --sma-slow 70 \
    --rsi-lower 35 \
    --rsi-upper 75 \
    --initial-capital 20000

# Run grid search optimization
python scripts/optimize_parameters.py --timeframe 5min

# Regenerate Session 8A results with corrected capital
python scripts/regenerate_results_20k.py
```

### Live Trading (Local)

1. **Start TWS or IB Gateway** on your machine
2. **Enable API connections** in TWS settings:
   - Port 7497 for paper trading (TWS)
   - Port 4002 for paper trading (IB Gateway)
   - Port 7496 for live trading (TWS) - **use extreme caution**
3. **Run the trading bot:**
```bash
cd deployment
python trading_bot.py
```

**Note:** The bot will create timestamped log files in `deployment/logs/`

### Cloud Deployment

See `deployment/DEPLOYMENT_GUIDE.md` for complete cloud deployment instructions.

**Quick cloud deployment:**
```bash
# SSH into droplet
ssh root@XXX.XXX.XXX.XX

# Navigate to project
cd /path/to/CPF-Final-Project/deployment

# Start IB Gateway container
docker-compose up -d

# Start trading bot
python trading_bot.py
# OR run in Docker container (see DEPLOYMENT_GUIDE.md)
```

---

## Strategy Overview

### Multi-Indicator Trend-Following Strategy

A trend-following approach combining:
- Simple Moving Average crossovers (trend detection)
- RSI filters (entry timing via momentum exhaustion)
- Momentum indicator (directional confirmation)

**Implementation:** MARSIMomentumStrategy class in `modules/strategy/`

**Core Components:**

**1. Trend Identification (Primary Signal):**
- **SMA Crossover (15/70 or 20/70):** Detects trend direction changes
  - Fast SMA crosses above Slow SMA → **Uptrend identified**
  - Fast SMA crosses below Slow SMA → **Downtrend identified**

**2. Momentum Exhaustion Filter (Entry Timing):**
- **RSI (14):** Waits for counter-trend momentum exhaustion before entry
  - For LONG entries: RSI < 35 (oversold, downside momentum exhausted)
  - For SHORT entries: RSI > 70-75 (overbought, upside momentum exhausted)
  - **Note:** This is counter-trend logic - entering when momentum is exhausted, not when it's strong

**3. Directional Confirmation:**
- **Momentum Indicator (10):** Validates emerging directional pressure
  - For LONG entries: Momentum > 0 (upward pressure building)
  - For SHORT entries: Momentum < 0 (downward pressure building)

**Strategy Classification:** Trend-following with momentum filters (not a pure momentum strategy)

**Signal Generation Logic:**

**LONG Entry (BUY):**
- Fast SMA crosses above Slow SMA (bullish crossover = **trend signal**)
- RSI < 30-35 (oversold = **momentum exhausted on downside**)
- Momentum > 0 (upward pressure = **direction confirmed**)

**SHORT Entry (SELL):**
- Fast SMA crosses below Slow SMA (bearish crossover = **trend signal**)
- RSI > 70-75 (overbought = **momentum exhausted on upside**)
- Momentum < 0 (downward pressure = **direction confirmed**)

**Position Management:**
- One position at a time (LONG, SHORT, or FLAT)
- Signal-to-position conversion with forward-fill logic
- Automatic position reconciliation after connectivity loss

**Why This Works:**
The SMA crossover identifies the trend, while RSI and Momentum filters ensure entry occurs at favorable timing within that trend - specifically when counter-trend momentum has been exhausted and new directional momentum is building.

### Backtesting Results

**Initial Capital:** €20,000 (EUR account)  
**Position Size:** €20,000 (1:1 leverage, no margin)  
**Test Period:** 3 months (October 2025 - January 2026)  
**Transaction Costs:** 1.0 pip spread, $4 round-trip per trade

**Optimized Parameters - 5-Minute Timeframe:**
```
SMA Fast/Slow:     15 / 70
RSI Lower/Upper:   35 / 75
Momentum Period:   10
Momentum Threshold: 0.0

Results:
  Sharpe Ratio:    4.55
  Total Return:    +4.13%
  Total Trades:    107
  Win Rate:        ~48%
  Max Drawdown:    -2.84%
```

**Optimized Parameters - 4-Hour Timeframe:**
```
SMA Fast/Slow:     20 / 70
RSI Lower/Upper:   35 / 70
Momentum Period:   10
Momentum Threshold: 0.0

Results:
  Sharpe Ratio:    1.42
  Total Return:    +30.23%
  Total Trades:    45
  Win Rate:        ~52%
```

**Key Finding:** Optimal parameters are invariant to position size/capital ratio. The same parameter combinations rank highest whether trading with €10,000, €20,000, or €50,000 capital.

**Transaction Costs:**
- EUR/USD spread: 1.0 pip
- Round-trip cost: $4.00 per trade
- All results include full transaction cost modeling

### Live Testing Results

**Test 1: Initial Validation (Feb 12-13, 2026)**
- **Duration:** 4 hours
- **Purpose:** First autonomous run after Session 7D fixes
- **Trades:** 4 (all losses due to low-volatility period)
- **P&L:** -$39.70 (-0.2%)
- **Outcome:** Infrastructure validated, revealed 8 production bugs
- **Impact:** Led to Session 7E critical fixes

**Test 2: Post-Fix Validation (Feb 18-20, 2026)**
- **Duration:** ~3 days (5-minute timeframe)
- **Purpose:** Verify Session 7E fixes in production
- **Infrastructure Events:** Multiple IB Gateway daily resets handled successfully
- **Connectivity:** Automatic reconnection and position reconciliation working
- **Outcome:** Revealed stale state issue → fixed in Session 7H
- **Impact:** Production-ready status achieved

**Test 3: Extended Production Run (Feb 23-28, 2026)** 🔄 **IN PROGRESS**
- **Duration:** 5 days (Monday 9 AM - Friday 4 PM CET)
- **Purpose:** Final validation before project submission
- **Expected:** 6-8 trades, full production stress test
- **Monitoring:** Continuous logging, automated maintenance window handling
- **Results:** To be documented in final notebook Section 9

---

## 🔧 Configuration

### Trading Parameters

Edit `deployment/config_live.py`:

```python
# Strategy Parameters (Optimized for 5min)
STRATEGY_PARAMS = {
    'sma_fast': 15,
    'sma_slow': 70,
    'rsi_period': 14,
    'rsi_upper': 75,
    'rsi_lower': 35,
    'momentum_period': 10,
    'momentum_threshold': 0.0,
}

# Alternative: 4-Hour Timeframe Parameters
# STRATEGY_PARAMS = {
#     'sma_fast': 20,
#     'sma_slow': 70,
#     'rsi_period': 14,
#     'rsi_upper': 70,
#     'rsi_lower': 35,
#     'momentum_period': 10,
#     'momentum_threshold': 0.0,
# }

# Trading Configuration
SYMBOL = 'EUR'
CURRENCY = 'USD'
EXCHANGE = 'IDEALPRO'
POSITION_SIZE = 20000  # EUR (IBKR minimum for forex)

# Risk Management
INITIAL_CAPITAL = 20000  # EUR (matches position size, no leverage)
MAX_DAILY_LOSS = 500     # Maximum loss per day (USD)
MAX_POSITION_SIZE = 20000
```

### IB Gateway Configuration

```python
# Connection Settings
HOST = '127.0.0.1'      # localhost for local testing
# HOST = 'XXX.XXX.XXX.XX'  # DigitalOcean droplet IP for cloud deployment
PORT = 4002             # 4002 for IB Gateway paper trading
CLIENT_ID = 1           # Unique client identifier
```

**Note:** The account is EUR-based (not USD). Position size and initial capital are both in EUR.

---

## 📈 Performance Monitoring

### Log Files

All trading activity is logged to timestamped files in `logs/`:

```
logs/
├── trading_bot_5min_20260223_090000.log    # Main bot log
└── trades_5min_20260223_090000.csv         # Trade history
```

### Log Format

**Trading Bot Log:**
```
2026-02-23 09:15:00,123 - INFO - Connected to IB Gateway at 127.0.0.1:4002
2026-02-23 09:15:05,456 - INFO - Contract qualified: EUR.USD IDEALPRO
2026-02-23 09:15:10,789 - INFO - Current position: FLAT (0)
2026-02-23 09:20:00,012 - INFO - Signal generated: BUY (sma_cross=True, rsi=28.5, momentum=0.0012)
2026-02-23 09:20:01,234 - INFO - Order placed: BUY 20000 EUR.USD @ Market
2026-02-23 09:20:02,456 - INFO - Order filled: BUY 20000 @ 1.08945 (avgFillPrice)
```

**Trade Log (CSV):**
```csv
timestamp,direction,entry_price,exit_price,pnl_gross,pnl_net,position_size
2026-02-23 09:20:02,LONG,1.08945,1.09012,134.00,130.00,20000
```

### Real-Time Monitoring

**Check bot status:**
```bash
# View live logs
tail -f logs/trading_bot_*.log

# Monitor trade activity
tail -f logs/trades_*.csv

# Check current position
grep "Current position" logs/trading_bot_*.log | tail -1
```

---

## Development

### Code Style

The project follows PEP 8 style guidelines:

```bash
# Format code
black modules/ scripts/

# Check style
flake8 modules/ scripts/

# Type checking
mypy modules/
```

### Adding New Indicators

1. Create indicator class in `modules/indicators/indicators.py`
2. Inherit from `Indicator` base class
3. Implement `_calculate()` method
4. Add tests in `tests/test_indicators.py`

Example:
```python
from modules.indicators.base import Indicator

class MyIndicator(Indicator):
    """My custom indicator."""
    
    def __init__(self, period: int = 14):
        super().__init__(period=period)
    
    def _calculate(self, data: pd.DataFrame) -> pd.Series:
        """Calculate indicator values."""
        # Implementation here
        return result_series
```

---

## Docker Deployment

### IB Gateway Container

The project includes Docker configuration for running IB Gateway in a headless environment:

**Features:**
- Automated IB Gateway startup
- VNC access for initial configuration
- Persistent configuration storage
- Automatic restart on failure
- Network isolation

**Start IB Gateway:**
```bash
cd deployment
docker-compose up -d
```

**Access via VNC:**
```bash
# Local: VNC to localhost:5900
# Cloud: SSH tunnel + VNC to localhost:5900
ssh -L 5900:localhost:5900 root@YOUR_DROPLET_IP
```

**View logs:**
```bash
docker-compose logs -f ib-gateway
```

---

## Documentation

### Session Documentation

Complete development timeline tracked across 15 sessions (Jan-Feb 2026):

**Core Development (Sessions 1-4):**
- Session 1: Configuration module (constants, timeframes, validation)
- Session 2: Data layer (IB historical fetch, CSV loader, validation)
- Session 3: Technical indicators (SMA, RSI, Momentum with abstract base)
- Session 4: Strategy module (Strategy ABC + MARSIMomentumStrategy - trend-following)

**Backtesting & Optimization (Sessions 5-6):**
- Session 5/5B: BacktestEngine with transaction costs (fixed equity bug in 5B)
- Session 6/6B: GridSearchOptimizer with 432 parameter combinations

**Live Trading Development (Sessions 7A-7H):**
- Session 7: Initial live bot + Docker deployment
- Session 7B: Reconnection logic with exponential backoff
- Session 7C: Position reconciliation after connectivity loss
- Session 7D: Contract qualification fixes (async pattern)
- Session 7E: 8 critical production bugs fixed (see Production Bugs section)
- Session 7F: Reconciliation P&L tracking for vanished positions
- Session 7G: IB avgCost interpretation fix for forex
- Session 7H: Connectivity-based reconciliation triggers

**Refinement (Session 8A):**
- Session 8A: Initial capital correction (10k → 20k EUR), full re-optimization

Each session documented in `docs/handoffs/session-XX-*.md` with:
- Changes made
- Decisions and rationale  
- Code snippets
- Testing results
- Handoff to next session

---

## Production Bugs Resolved

The project encountered and resolved **8 critical production bugs** during live testing (Session 7E). These discoveries transformed the bot from a prototype to a production-ready system:

### Session 7E: Critical Fixes

1. **Order TIF Error (Error 10349)**
   - **Issue:** Orders with `tif='DAY'` rejected on forex (24/5 market)
   - **Fix:** Changed to `tif='GTC'` (Good-Till-Cancelled)

2. **Fill Confirmation**
   - **Issue:** Bot didn't wait for order fills, caused race conditions
   - **Fix:** Added 30-second timeout loop with `trade.isDone()`

3. **Entry Price Tracking**
   - **Issue:** Used current price instead of actual fill price
   - **Fix:** Capture `trade.orderStatus.avgFillPrice` on execution

4. **Double Position Prevention**
   - **Issue:** New order could execute while position still open
   - **Fix:** Return bool from `close_position()`, verify before opening

5. **EUR Balance Check (Error 201)**
   - **Issue:** Insufficient EUR balance not validated before trading
   - **Fix:** Added `check_eur_balance()` with 20,000 EUR minimum

6. **Historical Data Warmup**
   - **Issue:** Not enough bars for indicator calculation on startup
   - **Fix:** `load_historical_warmup()` fetches ~80 bars in 4 seconds

7. **Bar Streaming**
   - **Issue:** Real-time bar updates not working correctly
   - **Fix:** Proper `reqHistoricalData()` with 5-second bars

8. **Bar Deduplication**
   - **Issue:** Duplicate bars processed multiple times
   - **Fix:** Track `self.last_bar_time` and skip duplicates

### Additional Production Hardening

**Session 7F:** Position reconciliation P&L tracking  
**Session 7G:** IB `avgCost` interpretation fix for forex  
**Session 7H:** Connectivity-based reconciliation triggers  

**Result:** Bot now handles IB Gateway daily resets (midnight + 5:35 AM maintenance) automatically with full position/state recovery.

---

## Known Issues & Limitations

## Current Limitations & Future Work

### Interactive Brokers Connectivity

**Daily Maintenance Windows (Handled Automatically):**
- **~23:45 CET:** IB server reboot (~15 minutes)
- **~05:35 CET:** Maintenance window (~90 minutes)

**Current Status:** Fully handled with automatic reconnection and position reconciliation (Sessions 7B, 7H)

**Planned Enhancement (Not Yet Implemented):**
- Add `is_backend_connected` pause flag during Error 1100 → 1102 window
- Benefits: Cleaner logs, no order attempts during reset
- Effort: ~10 lines of code
- Documented in Session 8A handoff for future implementation

### Forex Market Hours

**Trading Hours:** Sunday 23:00 CET - Friday 23:00 CET  
**Bot Behavior:** 
- Runs continuously during trading week
- Automatically stops Friday afternoon (configurable)
- Avoids weekend gap exposure

**Recommendation:** Stop bot Friday 16:00 CET (7 hours before market close) for clean position closure

### Backtesting Limitations

- **Fill Assumptions:** Executes at bar close price (no slippage modeling)
- **Spread Model:** Static 1.0 pip spread (real spreads vary 0.5-2.0 pips)
- **No Partial Fills:** Assumes full position filled immediately
- **No Market Impact:** Suitable for 20,000 EUR positions only
- **Signal Timing:** Signal at bar t executes at bar t+1 open (prevents look-ahead bias)

**Note:** Live testing shows backtest assumptions are reasonable for EUR/USD at this position size

### Position Sizing Constraints

**IBKR Minimum:** €20,000 (or equivalent) for forex trades  
**Consequence:** Strategy requires minimum €20,000 capital to trade without leverage  
**Scalability:** Tested up to €50,000 - parameters remain optimal across this range

### Account Currency

**Important:** This system is designed for **EUR-based accounts**, not USD accounts.  
**Reason:** Position size (20,000 EUR) must be available in account base currency.  
**Conversion:** Adapting to USD account requires modifying position size logic.

---

## Academic Context

This project demonstrates:

**Technical Skills:**
- Python-based algorithmic trading system development
- Cloud infrastructure deployment (Linux, Docker, SSH)
- API integration (Interactive Brokers via `ib_async`)
- Backtesting methodology and parameter optimization

**Domain Knowledge:**
- Technical analysis: Trend-following strategies and momentum filters
- Forex market mechanics and transaction costs
- Risk management and position sizing
- Production trading system challenges

**Analytical Skills:**
- Strategy performance evaluation (Sharpe ratio, drawdown, win rate)
- Grid search optimization techniques
- Real-world testing and validation
- Critical analysis of backtest vs. live performance

---

## Requirements

### Python Dependencies

Key packages (see `requirements.txt` and `deployment/requirements.txt`):
```
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
ib_async==2.1.0          # Async IB API wrapper (specific version)
jupyter>=1.0.0
pytest>=7.4.0
```

**Important:** The project uses `ib_async` v2.1.0 specifically, which provides async/await patterns for IB API interaction.

### System Requirements

**Local Development:**
- Python 3.11+
- 4 GB RAM minimum
- Interactive Brokers TWS or IB Gateway
- Linux/macOS/Windows (tested on macOS and Ubuntu)

**Cloud Deployment (DigitalOcean Droplet):**
- **OS:** Ubuntu 22.04.5 LTS
- **RAM:** 2 GB minimum
- **CPU:** 1 vCPU sufficient
- **Storage:** 50 GB SSD
- **Network:** Stable internet connection required
- **Docker:** Version 20.10+
- **Docker Compose:** Version 2.0+

**Current Production Environment:**
- Droplet IP: XXX.XXX.XXX.XX (Frankfurt datacenter)
- IB Gateway: Running in Docker container
- Trading bot: Containerized with `--network host`

---

## Contributing

This is an academic project and is not actively seeking contributions. However, feedback and suggestions are welcome via issues.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

**IMPORTANT:** This software is for educational purposes only.

- This is NOT investment advice
- Past performance does not guarantee future results
- Trading forex involves substantial risk of loss
- Only trade with capital you can afford to lose
- The authors assume no liability for trading losses
- Always test thoroughly with paper trading before live deployment

**Paper Trading Recommended:** This system was developed and tested using Interactive Brokers paper trading accounts. Live trading with real money is done entirely at your own risk.

---

## Acknowledgments

- **Interactive Brokers** for robust API access and paper trading environment
- **ib_async library (v2.1.0)** by Ewald de Wit - essential async Python IB API wrapper
- **Certificate Programme in FinTech (CPF)** - University course providing project framework
- **Claude (Anthropic)** for development assistance, code review, and debugging support across 15 sessions
- **DigitalOcean** for reliable cloud infrastructure (Frankfurt datacenter)

**Special Thanks:** The 8 production bugs discovered in Session 7E were invaluable learning experiences that transformed this from an academic exercise into a truly production-ready system.

---

## Contact

For questions about this project:
- Create an issue in the repository
- See `project-progress.md` for development timeline and context

---

## Project Timeline

**Start Date:** Late-January 2026  
**Deadline:** March 31, 2026  
**Current Status:** ~95% Complete - Live bot production-ready, final notebook in progress

**Key Milestones:**
- Session 1-4: Core modules (config, data, indicators, strategy)
- Session 5-6: Backtesting framework and grid search optimization
- Session 7A-7H: Live trading bot with production fixes (8 critical bugs resolved)
- Session 8A: Initial capital correction and full re-optimization
- First live test: 4-hour run (Feb 12-13, 2026) - validation successful
- Second live test: 3-day run (Feb 18-20, 2026) - connectivity fixes verified
- Third live test: 5-day production run (Feb 23-28, 2026) - in progress
- Final documentation and notebook completion (Sections 7, 9, 10, Abstract)

See [`project-progress.md`](project-progress.md) for complete session-by-session development log.

---

**Last Updated:** February 23, 2026  
**Version:** 1.0.0  
**Status:** Production Testing Phase (5-day test run active)
