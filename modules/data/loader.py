"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
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
from typing import Dict

import pandas as pd

from modules.config import DATA_DIR, TIMEFRAME_CONFIGS, list_timeframes

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REQUIRED_COLUMNS: list[str] = ["open", "high", "low", "close", "volume"]


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------
def find_csv_file(timeframe: str, data_dir: str = DATA_DIR) -> Path:
    """Find the CSV file for a given timeframe.

    Searches the ``data/historical/{timeframe}/`` directory for a file
    matching the ``EUR_USD_*.csv`` pattern.

    Args:
        timeframe: Timeframe key (e.g. '5min', '4H', '1D').
        data_dir: Base data directory.

    Returns:
        Path to the CSV file.

    Raises:
        FileNotFoundError: If no CSV file is found for the timeframe.
        ValueError: If the timeframe key is not recognised.
    """
    available = list_timeframes()
    if timeframe not in available:
        raise ValueError(
            f"Unknown timeframe '{timeframe}'. "
            f"Available timeframes: {', '.join(available)}"
        )

    tf_dir = Path(data_dir) / timeframe
    if not tf_dir.exists():
        raise FileNotFoundError(
            f"Directory does not exist: {tf_dir}. "
            "Run scripts/fetch_historical_data.py first."
        )

    csv_files = sorted(tf_dir.glob("EUR_USD_*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No EUR_USD_*.csv files found in {tf_dir}. "
            "Run scripts/fetch_historical_data.py first."
        )

    if len(csv_files) > 1:
        logger.warning(
            "Multiple CSV files found in %s — using most recent: %s",
            tf_dir,
            csv_files[-1].name,
        )

    return csv_files[-1]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_dataframe(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Validate and clean a loaded DataFrame.

    Checks that all required columns are present, verifies OHLCV price
    relationships, removes duplicate timestamps, and sorts by date.

    Args:
        df: Raw DataFrame loaded from CSV.
        timeframe: Timeframe key (for logging context).

    Returns:
        Validated and cleaned DataFrame.

    Raises:
        ValueError: If critical validation fails (missing columns, OHLC
            violations).
    """
    # Check required columns
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"{timeframe}: Missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    # Remove duplicate timestamps
    n_dupes = df.index.duplicated().sum()
    if n_dupes > 0:
        logger.warning("%s: Removing %d duplicate timestamps", timeframe, n_dupes)
        df = df[~df.index.duplicated(keep="last")]

    # Sort by date
    df = df.sort_index()

    # Check for NaN in OHLC
    ohlc = ["open", "high", "low", "close"]
    nan_counts = df[ohlc].isna().sum()
    total_nans = nan_counts.sum()
    if total_nans > 0:
        logger.warning(
            "%s: Found %d NaN values in OHLC — dropping affected rows",
            timeframe,
            total_nans,
        )
        df = df.dropna(subset=ohlc)

    # OHLC relationships
    violations: list[str] = []
    if not (df["high"] >= df["low"]).all():
        violations.append("High < Low")
    if not (df["high"] >= df["open"]).all():
        violations.append("High < Open")
    if not (df["high"] >= df["close"]).all():
        violations.append("High < Close")
    if not (df["low"] <= df["open"]).all():
        violations.append("Low > Open")
    if not (df["low"] <= df["close"]).all():
        violations.append("Low > Close")

    if violations:
        raise ValueError(
            f"{timeframe}: OHLC relationship violations: {', '.join(violations)}"
        )

    # Volume NaN handling (forex midpoint data may have zero/NaN volume)
    if "volume" in df.columns and df["volume"].isna().any():
        logger.warning(
            "%s: Filling %d NaN volume values with 0",
            timeframe,
            df["volume"].isna().sum(),
        )
        df["volume"] = df["volume"].fillna(0)

    logger.info(
        "%s: Validation passed — %d bars, %s to %s",
        timeframe,
        len(df),
        df.index.min(),
        df.index.max(),
    )

    return df


# ---------------------------------------------------------------------------
# Loading functions
# ---------------------------------------------------------------------------
def load_timeframe_data(
    timeframe: str,
    data_dir: str = DATA_DIR,
) -> pd.DataFrame:
    """Load historical data for a specific timeframe.

    Reads the CSV file for the requested timeframe, parses dates, sets the
    datetime index, and validates data quality.

    Args:
        timeframe: Timeframe key (e.g. '5min', '4H', '1D').
        data_dir: Base data directory.

    Returns:
        DataFrame with datetime index and columns: open, high, low, close,
        volume.

    Raises:
        FileNotFoundError: If CSV file not found.
        ValueError: If data validation fails.

    Example:
        >>> df = load_timeframe_data('4H')
        >>> print(df.head())
                             open    high     low   close  volume
        date
        2023-01-01 00:00:00  1.0650  1.0665  1.0645  1.0660  12500
        ...
    """
    filepath = find_csv_file(timeframe, data_dir)
    logger.info("Loading %s data from %s", timeframe, filepath)

    df = pd.read_csv(filepath, parse_dates=["date"])
    df = df.set_index("date")

    df = validate_dataframe(df, timeframe)

    return df


def load_all_timeframes(data_dir: str = DATA_DIR) -> Dict[str, pd.DataFrame]:
    """Load data for all configured timeframes.

    Iterates over every timeframe defined in ``TIMEFRAME_CONFIGS`` and
    loads its historical CSV data.

    Args:
        data_dir: Base data directory.

    Returns:
        Dictionary mapping timeframe keys to DataFrames.

    Example:
        >>> data = load_all_timeframes()
        >>> print(data.keys())
        dict_keys(['5min', '4H', '1D'])
    """
    data: Dict[str, pd.DataFrame] = {}

    for timeframe in TIMEFRAME_CONFIGS:
        try:
            data[timeframe] = load_timeframe_data(timeframe, data_dir)
        except FileNotFoundError:
            logger.warning("No data file found for %s — skipping", timeframe)
        except ValueError as exc:
            logger.error("Validation failed for %s: %s — skipping", timeframe, exc)

    if not data:
        raise FileNotFoundError(
            "No data files found for any timeframe. "
            "Run scripts/fetch_historical_data.py first."
        )

    logger.info(
        "Loaded %d timeframes: %s",
        len(data),
        {k: len(v) for k, v in data.items()},
    )

    return data


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def get_date_range(df: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Get start and end dates from a DataFrame with a datetime index.

    Args:
        df: DataFrame with datetime index.

    Returns:
        Tuple of (start_date, end_date).
    """
    return df.index.min(), df.index.max()
