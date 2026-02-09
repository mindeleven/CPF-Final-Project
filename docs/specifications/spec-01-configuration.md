===================================================================================
CPF FINAL PROJECT - SPECIFICATION 1: CONFIGURATION SYSTEM
===================================================================================

PROJECT CONTEXT:
You are implementing a parametric multi-timeframe trading system for the CPF 
(Certificate in Python for Finance) final project. This is an academic 
certification project requiring professional-grade code quality.

The system implements a trend-following strategy for EUR/USD forex trading using:
- Moving Average Crossover (primary trend identification)
- RSI Filter (momentum confirmation)
- Momentum Filter (directional validation)

The strategy operates across THREE timeframes with literature-backed parameters:
- 5-minute bars: Day trading/scalping (SMA 20/50)
- 4-hour bars: Day trading (SMA 20/50)
- Daily bars: Swing trading (SMA 50/200)

===================================================================================
YOUR TASK:
===================================================================================

Create the configuration system that defines ALL parameters for the three 
timeframes. This is the foundation that all other modules will reference.

CREATE TWO FILES:

1. modules/config/timeframes.py
   - Define TIMEFRAME_CONFIGS dictionary with all three timeframes
   - Include SMA periods, RSI parameters, Momentum lookback
   - Include metadata (bar duration, typical trade count, style)

2. modules/config/constants.py
   - Global constants (instrument, transaction costs, IB Gateway settings)
   - Data paths
   - General trading parameters

===================================================================================
REQUIREMENTS:
===================================================================================

FILE STRUCTURE:
modules/
└── config/
    ├── __init__.py
    ├── timeframes.py
    └── constants.py

CODING STANDARDS:
- Use type hints on ALL functions and class methods
- Use Google-style docstrings
- Verbose error handling with logging
- Moderate logging level (info + warnings + errors)
- PEP 8 formatting (will be checked with black)
- File headers with project title and authors

FILE HEADER TEMPLATE (use for ALL files):
"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Jürgen Kober
Co-developed with: Claude Code (Opus 4.5)
Created: February 2026

Module: [module_path]
Purpose: [Brief description]

This module is part of a parametric multi-timeframe trading system for EUR/USD
forex trading, implementing a trend-following strategy with MA crossover, RSI, 
and Momentum confirmation filters.
"""

===================================================================================
DETAILED SPECIFICATIONS:
===================================================================================

FILE 1: modules/config/timeframes.py
----------------------------------------

Define a dictionary TIMEFRAME_CONFIGS with the following structure:

TIMEFRAME_CONFIGS = {
    '5min': {
        'name': '5-minute',
        'trading_style': 'Day Trading / Scalping',
        'bar_duration': '5 mins',
        'expected_trades_per_year': '500-2000',
        
        # SMA Parameters (from literature: Forex.in.rs 2022, FXOpen 2025)
        'sma_fast': 20,
        'sma_slow': 50,
        'sma_ratio': 2.5,
        
        # RSI Parameters (standard 14-period, thresholds to be optimized)
        'rsi_period': 14,
        'rsi_overbought': 70,
        'rsi_oversold': 30,
        'rsi_neutral_upper': 55,
        'rsi_neutral_lower': 45,
        
        # Momentum Parameters (time-proportional to SMA)
        'momentum_lookback': 10,  # Half of fast SMA
        
        # IB Gateway bar size string
        'ib_bar_size': '5 mins',
        'ib_duration': '30 D',  # Fetch 30 days for testing
    },
    
    '4H': {
        'name': '4-hour',
        'trading_style': 'Day Trading',
        'bar_duration': '4 hours',
        'expected_trades_per_year': '50-200',
        
        # SMA Parameters (from literature: Teo 2024, TopBrokers 2023)
        'sma_fast': 20,
        'sma_slow': 50,
        'sma_ratio': 2.5,
        
        # RSI Parameters
        'rsi_period': 14,
        'rsi_overbought': 70,
        'rsi_oversold': 30,
        'rsi_neutral_upper': 55,
        'rsi_neutral_lower': 45,
        
        # Momentum Parameters
        'momentum_lookback': 10,
        
        # IB Gateway bar size string
        'ib_bar_size': '4 hours',
        'ib_duration': '3 Y',  # Fetch 3 years (2023-2025)
    },
    
    '1D': {
        'name': 'Daily',
        'trading_style': 'Swing Trading',
        'bar_duration': '1 day',
        'expected_trades_per_year': '20-100',
        
        # SMA Parameters (from literature: Murphy 1999, Elder 1993)
        'sma_fast': 50,
        'sma_slow': 200,
        'sma_ratio': 4.0,
        
        # RSI Parameters
        'rsi_period': 14,
        'rsi_overbought': 70,
        'rsi_oversold': 30,
        'rsi_neutral_upper': 55,
        'rsi_neutral_lower': 45,
        
        # Momentum Parameters
        'momentum_lookback': 14,  # Standard for daily
        
        # IB Gateway bar size string
        'ib_bar_size': '1 day',
        'ib_duration': '3 Y',  # Fetch 3 years (2023-2025)
    }
}

Add helper functions:
- get_timeframe_config(timeframe: str) -> dict
  Returns config for specified timeframe, raises ValueError if invalid
  
- list_timeframes() -> list[str]
  Returns list of available timeframe keys

Add validation:
- Ensure all required keys present in each timeframe
- Validate ratio matches (sma_slow / sma_fast)

----------------------------------------

FILE 2: modules/config/constants.py
----------------------------------------

Define:

# Instrument
INSTRUMENT_SYMBOL = 'EUR.USD'
INSTRUMENT_CURRENCY = 'USD'
INSTRUMENT_EXCHANGE = 'IDEALPRO'

# IB Gateway Connection
IB_HOST = '127.0.0.1'  # localhost for local testing
IB_PORT = 4002         # Paper trading port
IB_CLIENT_ID = 100     # For data fetching (different from live trading)

# Transaction Costs (EUR/USD forex)
SPREAD_PIPS = 1         # Typical EUR/USD spread
PIP_VALUE = 0.0001      # EUR/USD pip definition
SPREAD_PERCENTAGE = 0.0085 / 100  # ~0.0085% per side
COMMISSION_PER_TRADE = 0.0  # IB forex commission minimal for retail

# Position Sizing
DEFAULT_POSITION_SIZE = 10000  # $10,000 notional
LEVERAGE = 1.0                 # No leverage (1:1)

# Data Paths
DATA_DIR = 'data/historical'
RESULTS_DIR = 'results'
LOGS_DIR = 'logs'

# Backtesting
TRAIN_TEST_SPLIT = 0.7  # 70% training, 30% testing
MIN_TRADES_FOR_SIGNIFICANCE = 20

# Date Range for Historical Data
DATA_START_DATE = '2023-01-01'
DATA_END_DATE = '2025-12-31'

Add helper functions:
- get_data_path(timeframe: str, filename: str = None) -> str
  Constructs full path to data files
  
- ensure_directories() -> None
  Creates required directories if they don't exist

----------------------------------------

FILE 3: modules/config/__init__.py
----------------------------------------

Make the config module importable:

from .timeframes import TIMEFRAME_CONFIGS, get_timeframe_config, list_timeframes
from .constants import (
    INSTRUMENT_SYMBOL,
    IB_HOST,
    IB_PORT,
    IB_CLIENT_ID,
    DATA_DIR,
    ensure_directories
)

__all__ = [
    'TIMEFRAME_CONFIGS',
    'get_timeframe_config',
    'list_timeframes',
    'INSTRUMENT_SYMBOL',
    'IB_HOST',
    'IB_PORT',
    'IB_CLIENT_ID',
    'DATA_DIR',
    'ensure_directories'
]

===================================================================================
TESTING & VERIFICATION:
===================================================================================

After creating the files, verify they work:

1. Import test:
   python -c "from modules.config import TIMEFRAME_CONFIGS; print(TIMEFRAME_CONFIGS.keys())"
   
   Expected output: dict_keys(['5min', '4H', '1D'])

2. Helper function test:
   python -c "from modules.config import get_timeframe_config; print(get_timeframe_config('4H')['sma_fast'])"
   
   Expected output: 20

3. Validation test:
   python -c "from modules.config import get_timeframe_config; get_timeframe_config('invalid')"
   
   Expected: ValueError exception

4. Directory creation:
   python -c "from modules.config import ensure_directories; ensure_directories()"
   
   Expected: Creates data/historical, results, logs directories

===================================================================================
DELIVERABLES:
===================================================================================

✅ modules/config/__init__.py (with proper imports and __all__)
✅ modules/config/timeframes.py (complete with validation)
✅ modules/config/constants.py (complete with helpers)
✅ All files have proper headers with Jürgen Kober's name
✅ All files are PEP 8 compliant
✅ All functions have type hints and Google-style docstrings
✅ Code passes the verification tests above

===================================================================================
NOTES:
===================================================================================

- These parameters are based on literature review documented in the notebook
- RSI thresholds will be optimized during backtesting (Phase 3)
- Momentum lookback periods are time-proportional to SMA periods
- IB Gateway bar sizes must match IB API specifications exactly
- All three timeframes share similar RSI/Momentum structure for consistency

===================================================================================
END OF SPECIFICATION
===================================================================================