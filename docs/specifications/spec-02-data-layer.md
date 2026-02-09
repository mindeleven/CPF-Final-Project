===================================================================================
CPF FINAL PROJECT - SPECIFICATION 2: DATA LAYER
===================================================================================

PROJECT CONTEXT:
You are continuing work on a parametric multi-timeframe trading system for the 
CPF (Certificate in Python for Finance) final project.

SESSION 1 COMPLETED:
✅ Configuration system (modules/config/) is complete and tested
✅ TIMEFRAME_CONFIGS defines parameters for 5min, 4H, and 1D timeframes
✅ Directory structure created (data/historical/, results/, logs/)

CURRENT TASK:
Build the data layer that fetches EUR/USD historical data from Interactive Brokers 
Gateway and provides clean CSV loading for the Jupyter notebook.

===================================================================================
YOUR TASK:
===================================================================================

Create THREE components:

1. scripts/fetch_historical_data.py
   - Standalone script to fetch data from IB Gateway
   - Connects, downloads, saves to CSV, disconnects cleanly
   - Run ONCE to populate data/historical/ directory

2. modules/data/loader.py
   - Load CSV files for notebook/backtesting use
   - Validate OHLCV structure
   - Handle missing data

3. modules/data/__init__.py
   - Package initialization
   - Export key functions

===================================================================================
REQUIREMENTS:
===================================================================================

FILE STRUCTURE:
scripts/
└── fetch_historical_data.py

modules/
└── data/
    ├── __init__.py
    └── loader.py

CODING STANDARDS (same as Session 1):
- Use type hints on ALL functions
- Google-style docstrings
- Verbose error handling with logging
- Moderate logging level (info + warnings + errors)
- PEP 8 formatting (black)
- File headers with: Jürgen Kober + Claude Code (Opus 4.6)

===================================================================================
DETAILED SPECIFICATIONS:
===================================================================================

FILE 1: scripts/fetch_historical_data.py
----------------------------------------

PURPOSE:
One-time script to fetch historical EUR/USD data from IB Gateway and save to CSV.
This script is run ONCE locally, then the CSV files are committed to GitHub.

REQUIREMENTS:

1. **IB Gateway Connection**
   - Host: 127.0.0.1 (localhost)
   - Port: 4002 (paper trading)
   - ClientId: 100 (different from live trading)
   - CRITICAL: Always disconnect() in finally block
   
2. **Data Fetching**
   - Instrument: EUR/USD forex contract
   - Symbol: EUR.USD, Currency: USD, Exchange: IDEALPRO
   - Timeframes: Use TIMEFRAME_CONFIGS from modules.config
   
3. **Fetch Parameters per Timeframe**
   From modules.config.timeframes:
   - 5min: ib_bar_size='5 mins', ib_duration='30 D'
   - 4H: ib_bar_size='4 hours', ib_duration='3 Y'
   - 1D: ib_bar_size='1 day', ib_duration='3 Y'
   
4. **CSV Output**
   - Directory: data/historical/{timeframe}/
   - Filename: EUR_USD_{timeframe}_{start_date}_{end_date}.csv
   - Example: data/historical/5min/EUR_USD_5min_20260109_20260208.csv
   
5. **CSV Columns**
   - date (ISO format: YYYY-MM-DD HH:MM:SS)
   - open
   - high
   - low
   - close
   - volume
   
6. **Error Handling**
   - Check IB Gateway connection before fetching
   - Retry logic if connection fails (3 attempts)
   - Validate data received (no NaN, no duplicates)
   - Log all operations (info, warnings, errors)
   
7. **Progress Reporting**
   - Print which timeframe is being fetched
   - Show number of bars received
   - Confirm file saved successfully

EXAMPLE STRUCTURE:
```python
"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Jürgen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: scripts.fetch_historical_data
Purpose: Fetch historical EUR/USD data from IB Gateway and save to CSV files.

This script connects to Interactive Brokers Gateway, downloads historical OHLCV
data for three timeframes (5min, 4H, 1D), and saves them as CSV files for
reproducible backtesting.

Usage:
    python scripts/fetch_historical_data.py
    
Requirements:
    - IB Gateway running on localhost:4002
    - Network connection to IB servers
    - Sufficient disk space for CSV files (~50MB total)
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import pandas as pd
from ib_async import IB, Forex, util

from modules.config import (
    TIMEFRAME_CONFIGS,
    INSTRUMENT_SYMBOL,
    IB_HOST,
    IB_PORT,
    IB_CLIENT_ID,
    DATA_DIR
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def connect_ib_gateway(
    host: str = IB_HOST,
    port: int = IB_PORT,
    client_id: int = IB_CLIENT_ID,
    timeout: int = 10
) -> IB:
    """
    Connect to IB Gateway with retry logic.
    
    Args:
        host: IB Gateway host address
        port: IB Gateway port
        client_id: Unique client identifier
        timeout: Connection timeout in seconds
        
    Returns:
        Connected IB instance
        
    Raises:
        ConnectionError: If connection fails after retries
    """
    # Implementation here
    pass


def fetch_timeframe_data(
    ib: IB,
    timeframe: str,
    config: dict
) -> pd.DataFrame:
    """
    Fetch historical data for a specific timeframe.
    
    Args:
        ib: Connected IB instance
        timeframe: Timeframe key (e.g., '5min', '4H', '1D')
        config: Timeframe configuration from TIMEFRAME_CONFIGS
        
    Returns:
        DataFrame with columns: date, open, high, low, close, volume
        
    Raises:
        ValueError: If no data received or data is invalid
    """
    # Implementation here
    pass


def save_to_csv(
    df: pd.DataFrame,
    timeframe: str,
    base_dir: str = DATA_DIR
) -> Path:
    """
    Save DataFrame to CSV with standardized naming.
    
    Args:
        df: DataFrame with OHLCV data
        timeframe: Timeframe key
        base_dir: Base data directory
        
    Returns:
        Path to saved CSV file
    """
    # Implementation here
    pass


def validate_data(df: pd.DataFrame, timeframe: str) -> bool:
    """
    Validate fetched data for quality issues.
    
    Args:
        df: DataFrame to validate
        timeframe: Timeframe key (for logging)
        
    Returns:
        True if data is valid
        
    Raises:
        ValueError: If critical issues found
    """
    # Check for:
    # - No NaN values in OHLC
    # - High >= Low
    # - High >= Open, Close
    # - Low <= Open, Close
    # - No duplicate timestamps
    # - Minimum number of rows (e.g., >100 bars)
    pass


def main():
    """Main execution function."""
    logger.info("Starting historical data fetch from IB Gateway")
    logger.info(f"Target directory: {DATA_DIR}")
    
    ib = None
    try:
        # Connect to IB Gateway
        ib = connect_ib_gateway()
        logger.info(f"Connected to IB Gateway at {IB_HOST}:{IB_PORT}")
        
        # Fetch data for each timeframe
        for timeframe, config in TIMEFRAME_CONFIGS.items():
            logger.info(f"\nFetching {timeframe} data...")
            
            # Fetch data
            df = fetch_timeframe_data(ib, timeframe, config)
            
            # Validate
            validate_data(df, timeframe)
            
            # Save to CSV
            filepath = save_to_csv(df, timeframe)
            logger.info(f"✓ Saved {len(df)} bars to {filepath}")
        
        logger.info("\n✓ All data fetched successfully!")
        
    except Exception as e:
        logger.error(f"Error during data fetch: {e}")
        raise
    
    finally:
        # CRITICAL: Always disconnect
        if ib is not None and ib.isConnected():
            ib.disconnect()
            logger.info("Disconnected from IB Gateway")


if __name__ == "__main__":
    main()
```

IMPORTANT NOTES:
- Use ib_async.Forex() to create EUR/USD contract
- Use ib.reqHistoricalData() for fetching
- keepUpToDate=False (we want historical snapshot, not streaming)
- useRTH=False (forex trades 24/5, include all hours)
- Always call ib.disconnect() even if errors occur

----------------------------------------

FILE 2: modules/data/loader.py
----------------------------------------

PURPOSE:
Load CSV files for use in Jupyter notebook and backtesting. Provides clean,
validated DataFrames with proper datetime indexing.

REQUIREMENTS:

1. **Load Functions**
   - load_timeframe_data(timeframe: str) -> pd.DataFrame
   - load_all_timeframes() -> dict[str, pd.DataFrame]
   
2. **CSV Reading**
   - Read from data/historical/{timeframe}/*.csv
   - Parse 'date' column as datetime
   - Set datetime as index
   - Sort by date ascending
   
3. **Data Validation**
   - Check all required columns present
   - Verify OHLCV relationships (High >= Low, etc.)
   - Check for missing values
   - Remove duplicates if any
   
4. **Error Handling**
   - Raise FileNotFoundError if CSV doesn't exist
   - Provide helpful error messages
   - Log warnings for data quality issues

EXAMPLE STRUCTURE:
```python
"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Jürgen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.data.loader
Purpose: Load and validate historical data from CSV files.

Provides functions to load pre-fetched EUR/USD data for backtesting and analysis.
All data is validated for quality and returned as pandas DataFrames with datetime
indexing.
"""

import logging
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

from modules.config import DATA_DIR, list_timeframes

logger = logging.getLogger(__name__)


def find_csv_file(timeframe: str, data_dir: str = DATA_DIR) -> Path:
    """
    Find CSV file for given timeframe.
    
    Args:
        timeframe: Timeframe key (e.g., '5min', '4H', '1D')
        data_dir: Base data directory
        
    Returns:
        Path to CSV file
        
    Raises:
        FileNotFoundError: If no CSV file found for timeframe
    """
    # Look in data/historical/{timeframe}/ for EUR_USD_*.csv
    # Return first match (should only be one)
    pass


def validate_dataframe(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """
    Validate and clean loaded DataFrame.
    
    Args:
        df: Raw DataFrame from CSV
        timeframe: Timeframe key (for logging)
        
    Returns:
        Validated and cleaned DataFrame
        
    Raises:
        ValueError: If critical validation fails
    """
    # Check required columns
    # Check OHLCV relationships
    # Remove duplicates
    # Check for missing values
    # Sort by date
    pass


def load_timeframe_data(
    timeframe: str,
    data_dir: str = DATA_DIR
) -> pd.DataFrame:
    """
    Load historical data for a specific timeframe.
    
    Args:
        timeframe: Timeframe key (e.g., '5min', '4H', '1D')
        data_dir: Base data directory
        
    Returns:
        DataFrame with datetime index and columns: open, high, low, close, volume
        
    Raises:
        FileNotFoundError: If CSV file not found
        ValueError: If data validation fails
        
    Example:
        >>> df = load_timeframe_data('4H')
        >>> print(df.head())
                            open    high     low   close  volume
        date
        2023-01-01 00:00:00  1.0650  1.0665  1.0645  1.0660  12500
        ...
    """
    # Implementation here
    pass


def load_all_timeframes(data_dir: str = DATA_DIR) -> Dict[str, pd.DataFrame]:
    """
    Load data for all configured timeframes.
    
    Args:
        data_dir: Base data directory
        
    Returns:
        Dictionary mapping timeframe keys to DataFrames
        
    Example:
        >>> data = load_all_timeframes()
        >>> print(data.keys())
        dict_keys(['5min', '4H', '1D'])
    """
    # Load data for each timeframe in TIMEFRAME_CONFIGS
    pass


def get_date_range(df: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    """
    Get start and end dates from DataFrame.
    
    Args:
        df: DataFrame with datetime index
        
    Returns:
        Tuple of (start_date, end_date)
    """
    return df.index.min(), df.index.max()
```

----------------------------------------

FILE 3: modules/data/__init__.py
----------------------------------------
```python
"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Jürgen Kober
Co-developed with: Claude Code (Opus 4.6)
Created: February 2026

Module: modules.data
Purpose: Data fetching and loading functionality.

This package provides tools for acquiring and loading historical forex data
for backtesting and analysis.
"""

from .loader import (
    load_timeframe_data,
    load_all_timeframes,
    get_date_range
)

__all__ = [
    'load_timeframe_data',
    'load_all_timeframes',
    'get_date_range'
]
```

===================================================================================
TESTING & VERIFICATION:
===================================================================================

STEP 1: Run the fetch script
------------------------------
```bash
python scripts/fetch_historical_data.py
```

Expected output:
```
2026-02-09 12:00:00 - INFO - Starting historical data fetch from IB Gateway
2026-02-09 12:00:00 - INFO - Target directory: data/historical
2026-02-09 12:00:01 - INFO - Connected to IB Gateway at 127.0.0.1:4002

2026-02-09 12:00:01 - INFO - Fetching 5min data...
2026-02-09 12:00:05 - INFO - ✓ Saved 8640 bars to data/historical/5min/EUR_USD_5min_...
2026-02-09 12:00:05 - INFO - Fetching 4H data...
2026-02-09 12:00:10 - INFO - ✓ Saved 6570 bars to data/historical/4H/EUR_USD_4H_...
2026-02-09 12:00:10 - INFO - Fetching 1D data...
2026-02-09 12:00:12 - INFO - ✓ Saved 756 bars to data/historical/1D/EUR_USD_1D_...

2026-02-09 12:00:12 - INFO - ✓ All data fetched successfully!
2026-02-09 12:00:12 - INFO - Disconnected from IB Gateway
```

STEP 2: Verify CSV files exist
-------------------------------
```bash
ls -lh data/historical/5min/
ls -lh data/historical/4H/
ls -lh data/historical/1D/
```

Each directory should have one EUR_USD_*.csv file.

STEP 3: Test data loader
-------------------------
```bash
python -c "from modules.data import load_timeframe_data; df = load_timeframe_data('4H'); print(f'Loaded {len(df)} bars'); print(df.head())"
```

Expected output:
```
Loaded 6570 bars
                         open      high       low     close  volume
date                                                                
2023-01-02 00:00:00  1.065123  1.067234  1.064012  1.066543   15234
2023-01-02 04:00:00  1.066543  1.068123  1.065432  1.067234   14567
...
```

STEP 4: Test load all timeframes
---------------------------------
```bash
python -c "from modules.data import load_all_timeframes; data = load_all_timeframes(); print({k: len(v) for k, v in data.items()})"
```

Expected output:
```
{'5min': 8640, '4H': 6570, '1D': 756}
```

STEP 5: Verify data quality
----------------------------
```bash
python -c "
from modules.data import load_timeframe_data
df = load_timeframe_data('4H')
# Check no NaN
assert df.isna().sum().sum() == 0, 'Found NaN values'
# Check OHLC relationships
assert (df['high'] >= df['low']).all(), 'High < Low violation'
assert (df['high'] >= df['open']).all(), 'High < Open violation'
assert (df['high'] >= df['close']).all(), 'High < Close violation'
assert (df['low'] <= df['open']).all(), 'Low > Open violation'
assert (df['low'] <= df['close']).all(), 'Low > Close violation'
print('✓ All data quality checks passed')
"
```

===================================================================================
DELIVERABLES:
===================================================================================

✅ scripts/fetch_historical_data.py
   - Connects to IB Gateway (localhost:4002, clientId 100)
   - Fetches EUR/USD for 5min (30 days), 4H (3 years), 1D (3 years)
   - Saves to CSV with proper formatting
   - ALWAYS disconnects from IB Gateway (even on errors)
   - Comprehensive logging

✅ modules/data/loader.py
   - load_timeframe_data() function
   - load_all_timeframes() function
   - Data validation (OHLCV checks, no NaN, no duplicates)
   - Datetime indexing

✅ modules/data/__init__.py
   - Proper package initialization
   - Clean exports

✅ All files have proper headers (Jürgen Kober + Claude Code Opus 4.6)
✅ All files are PEP 8 compliant
✅ All functions have type hints and Google-style docstrings
✅ All verification tests pass

===================================================================================
NOTES:
===================================================================================

IB GATEWAY CONNECTION:
- The script assumes IB Gateway is running locally on port 4002
- If IB Gateway is on the cloud server (157.230.113.17), you have two options:
  1. Run the script on the cloud server via SSH
  2. Create an SSH tunnel: ssh -L 4002:localhost:4002 root@157.230.113.17
  
- ClientId 100 is different from live trading (which might use 753 or other)
- Always disconnect to avoid "clientId already in use" errors

DATA SIZES:
- 5min, 30 days: ~8,640 bars (~2-3 MB CSV)
- 4H, 3 years: ~6,570 bars (~1-2 MB CSV)
- 1D, 3 years: ~756 bars (~100 KB CSV)
- Total: ~5-8 MB (easily fits in GitHub)

CSV FORMAT:
- Must be plain CSV (not compressed)
- UTF-8 encoding
- Standard datetime format: YYYY-MM-DD HH:MM:SS
- No timezone info in CSV (assume UTC)

ERROR HANDLING:
- If IB Gateway connection fails, provide clear error message
- If data fetch returns 0 bars, raise ValueError
- If CSV write fails, raise IOError with details

===================================================================================
END OF SPECIFICATION
===================================================================================