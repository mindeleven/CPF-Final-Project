# End-to-End Cloud Deployment of Automated Trading Strategies with IBKR

## Developing an EUR/USD Algorithmic Trading System

A production-grade automated forex trading system implementing a multi-indicator trend-following strategy with cloud deployment infrastructure.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Interactive Brokers](https://img.shields.io/badge/broker-Interactive%20Brokers-green.svg)](https://www.interactivebrokers.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Project Overview

This project implements a complete algorithmic trading system for EUR/USD forex trading, from strategy development and backtesting to live deployment on cloud infrastructure. The system combines a trend-following approach (SMA crossovers) with momentum exhaustion filters (RSI and momentum indicators), and includes production infrastructure covering Docker containerisation, cloud deployment, automatic reconnection handling, and position reconciliation.

**Key Features:**
- Multi-indicator trend-following strategy with configurable parameters
- Comprehensive backtesting framework with transaction cost modelling
- Grid search optimisation for parameter tuning
- Live trading via Interactive Brokers API
- Cloud deployment on DigitalOcean with Docker containers
- Configurable maintenance window pause to avoid IB Gateway nightly reboot disruptions
- Automatic reconnection handling with exponential backoff
- Position reconciliation and error recovery
- Complete logging and trade tracking

**Final Project:** This is the capstone project for the Python Quants' Certificate in Python for Finance, demonstrating the complete lifecycle from research to production deployment.

---

## Project Structure

```
CPF-Final-Project/
├── README.md                                # This file
├── ALGORITHMIC-TRADING-FINAL-PROJECT.ipynb  # Final deliverable notebook
├── LICENSE
├── requirements.txt                         # Python dependencies
│
├── data/                                    # Market data and results storage
│   ├── historical/                          # Historical price data from IB
│   │   ├── 5min/                            # 5-minute bars
│   │   ├── 4H/                              # 4-hour bars
│   │   └── 1D/                              # Daily bars
│   ├── backtest/                            # Backtest result CSVs
│   └── optimization/                        # Grid search optimisation results
│
├── deployment/                              # Production deployment
│   ├── trading_bot.py                       # Live trading bot
│   ├── config_live.py                       # Runtime config with optimised params
│   ├── Dockerfile                           # Container build (context is project root)
│   ├── requirements.txt                     # Bot dependencies
│   ├── .dockerignore
│   ├── .env.example                         # Environment variables template
│   ├── logs/                                # Runtime logs
│   │                                        # (production run logs committed;
│   │                                        # development logs gitignored)
│   └── DEPLOYMENT_GUIDE.md                  # Cloud deployment instructions
│
├── docs/                                    # Project documentation
│   ├── handoffs/                            # Development session handoffs
│   ├── specifications/                      # Implementation specifications
│   ├── guides/                              # Implementation guides
│   └── project-progress.md                  # Development timeline
│
├── modules/                                 # Core implementation modules
│   ├── backtest/                            # Backtesting framework
│   │   ├── engine.py                        # BacktestEngine (t+1 execution)
│   │   ├── metrics.py                       # Sharpe, drawdown, win rate, etc.
│   │   └── transaction_costs.py             # Transaction cost modelling
│   ├── config/                              # Global configuration
│   │   ├── constants.py                     # System-wide constants
│   │   └── timeframes.py                    # Timeframe configurations
│   ├── data/                                # Data handling
│   │   └── loader.py                        # CSV loading with datetime indexing
│   ├── indicators/                          # Technical indicators
│   │   ├── base.py                          # Abstract Indicator base class
│   │   ├── momentum.py                      # Momentum indicator
│   │   ├── rsi.py                           # RSI indicator
│   │   └── sma.py                           # SMA indicator
│   ├── optimization/                        # Parameter optimisation
│   │   ├── grid_search.py                   # GridSearchOptimizer
│   │   └── results.py                       # OptimizationResults analysis
│   └── strategy/                            # Trading strategy
│       ├── base.py                          # Abstract Strategy base class
│       └── ma_rsi_momentum.py               # Multi-Indicator Trend-Following Strategy
│
└── scripts/                                 # Utility scripts
    ├── fetch_historical_data.py             # Download data from IB Gateway
    ├── optimize_parameters.py               # Run grid search optimisation
    └── regenerate_optimization_results.py   # Re-run optimisation with corrected capital
```

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Interactive Brokers account (live or paper trading)
- TWS or IB Gateway installed locally, or Docker for containerised IB Gateway deployment

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd CPF-Final-Project
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure IB connection — edit `deployment/config_live.py`:
```python
HOST = '127.0.0.1'  # localhost for local testing
PORT = 4002          # IB Gateway paper trading port
```

### Running the Notebook

Open `ALGORITHMIC-TRADING-FINAL-PROJECT.ipynb` in JupyterLab. All code cells can be run in sequence. Historical data and optimisation results are pre-computed and stored in `data/`.

### Running Optimisation

```bash
# Run grid search optimisation
python scripts/optimize_parameters.py --timeframe 5min
python scripts/optimize_parameters.py --timeframe 4H
```

### Live Trading (Local)

1. Start TWS or IB Gateway on your machine
2. Enable API connections (Port 4002 for IB Gateway paper trading)
3. Run the trading bot:
```bash
cd deployment
python trading_bot.py
```

The bot creates timestamped log files in `deployment/logs/`.

### Cloud Deployment

See `deployment/DEPLOYMENT_GUIDE.md` for complete cloud deployment instructions.

---

## Strategy Overview

### Multi-Indicator Trend-Following Strategy

The strategy combines three indicators operating at different analytical levels:

**1. Trend Identification — SMA Crossover:**
- Fast SMA crosses above Slow SMA: uptrend identified, consider LONG
- Fast SMA crosses below Slow SMA: downtrend identified, consider SHORT

**2. Entry Timing — RSI Momentum Exhaustion Filter:**
- For LONG entries: RSI below lower threshold (counter-trend momentum exhausted on the downside)
- For SHORT entries: RSI above upper threshold (counter-trend momentum exhausted on the upside)

**3. Directional Confirmation — Momentum Indicator:**
- For LONG entries: Momentum > 0 (upward directional pressure building)
- For SHORT entries: Momentum < 0 (downward directional pressure building)

The system holds one position at a time (LONG, SHORT, or FLAT) and reverses directly from LONG to SHORT and vice versa on a new crossover signal.

### Backtesting Results

**Initial Capital:** €20,000 | **Position Size:** €20,000 (1:1, no leverage)  
**Transaction Costs:** 1.0 pip spread, $4 round-trip per trade

**Optimised Parameters — 5-Minute Timeframe:**
```
Data period:        6 weeks (maximum retrievable via single IB request)
SMA Fast/Slow:      15 / 70
RSI Period:         14
RSI Lower/Upper:    35 / 75
Momentum Period:    10, Threshold: 0.0

Sharpe Ratio:       4.55
Total Return:       +4.13%
Total Trades:       107
Max Drawdown:       -1.37%
```

**Optimised Parameters — 4-Hour Timeframe:**
```
Data period:        ~3 years (February 2023 – February 2026)
SMA Fast/Slow:      20 / 70
RSI Period:         14
RSI Lower/Upper:    35 / 70
Momentum Period:    10, Threshold: 0.0

Sharpe Ratio:       1.42
Total Return:       +30.23%
Total Trades:       45
Max Drawdown:       -4.04%
```

Optimal parameters are invariant to position size and capital ratio. The same parameter combinations rank highest whether trading with €10,000, €20,000, or €50,000 capital.

---

## Configuration

### Trading Parameters

Edit `deployment/config_live.py` to switch between timeframes:

```python
# 5-Minute Timeframe (optimised)
STRATEGY_PARAMS = {
    'sma_fast': 15,
    'sma_slow': 70,
    'rsi_period': 14,
    'rsi_upper': 75,
    'rsi_lower': 35,
    'momentum_period': 10,
    'momentum_threshold': 0.0,
}

# 4-Hour Timeframe (optimised)
# STRATEGY_PARAMS = {
#     'sma_fast': 20,
#     'sma_slow': 70,
#     'rsi_period': 14,
#     'rsi_upper': 70,
#     'rsi_lower': 35,
#     'momentum_period': 10,
#     'momentum_threshold': 0.0,
# }

SYMBOL = 'EUR'
CURRENCY = 'USD'
EXCHANGE = 'IDEALPRO'
POSITION_SIZE = 20000   # EUR
INITIAL_CAPITAL = 20000  # EUR
```

### Maintenance Window

The bot pauses signal checking during the IB Gateway nightly reboot window. Times are specified in CET:

```python
# IB Gateway hard disconnect occurs at 23:45 UTC = 00:45 CET.
# Soft reboot (Error 1100/1102) occurs ~05:22–05:49 UTC = ~06:22–06:49 CET.
# Times below are in CET; the server runs UTC (add 1 hour to convert).
MAINTENANCE_WINDOW_START = "00:30"
MAINTENANCE_WINDOW_END = "06:45"
```

The bot does not close open positions when entering the maintenance window. Note that IB's paper trading environment closes all open positions during its nightly hard reset.

### IB Gateway Connection

```python
HOST = '127.0.0.1'   # localhost for local testing
PORT = 4002           # IB Gateway paper trading
CLIENT_ID = 1
```

---

## Production Monitoring

All trading activity is logged to timestamped files in `deployment/logs/`:

```bash
# View live logs
tail -f deployment/logs/trading_bot_*.log

# Monitor trade activity
tail -f deployment/logs/trades_*.csv
```

---

## Known Limitations

**IB Paper Trading Position Resets:** The IB Gateway performs a nightly hard reset on paper trading accounts at approximately 00:45 CET that closes all open positions. This behaviour does not occur on live accounts. During the production runs documented in the notebook, positions held overnight were closed by IB and recorded via the reconciliation logic rather than by strategy signals. This is a structural limitation of using paper trading to validate a continuously-traded 24/5 strategy.

**5-Minute Data Window:** The IB API limits a single historical data request for 5-minute bars to approximately 30 days. The 5-minute backtest uses a 6-week window, which covers a single market regime and limits the evidential weight of those results relative to the 4-hour backtest (approximately 3 years of data).

**USD Balance Requirement:** Trading EUR/USD on an EUR-denominated account requires sufficient USD holdings for BUY orders. An account holding only EUR can execute short-side trades but will exhaust its USD balance as long-side trades accumulate. The account should be manually rebalanced before each deployment. Programmatic currency conversion at startup is documented as a future improvement.

---

## Requirements

Key packages (see `requirements.txt` and `deployment/requirements.txt`):

```
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
ib_async==2.1.0    # Async IB API wrapper — specific version required
jupyter>=1.0.0
pytz==2024.1       # Timezone handling for maintenance window (CET/CEST)
```

**System Requirements:**

Local development: Python 3.11+, 4 GB RAM, IB TWS or IB Gateway, Linux/macOS/Windows

Cloud deployment (tested configuration):
- DigitalOcean droplet, Ubuntu 22.04.5 LTS, 2 GB RAM, 1 vCPU
- Docker 20.10+, stable internet connection

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

This software is for educational purposes only. It is not investment advice. Past performance does not guarantee future results. Trading forex involves substantial risk of loss. Only trade with capital you can afford to lose. The authors assume no liability for trading losses. This system was developed and tested using Interactive Brokers paper trading accounts. Live trading with real money is done entirely at your own risk.

---

## Acknowledgments

- **Interactive Brokers** for robust API access and paper trading environment
- **ib_async** (v2.1.0) by Ewald de Wit — async Python IB API wrapper
- **The Python Quants** — Certificate in Python for Finance programme
- **Claude (Anthropic)** — development assistance, code review, and debugging support
- **DigitalOcean** — cloud infrastructure (Frankfurt datacenter)
