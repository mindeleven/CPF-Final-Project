"""
CPF Final Project: End-to-End Cloud Deployment of Automated Trading Strategies
Author: Juergen Kober
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
import time
from pathlib import Path

import pandas as pd
from ib_async import IB, Forex, util

from modules.config import (
    DATA_DIR,
    IB_CLIENT_ID,
    IB_HOST,
    IB_PORT,
    INSTRUMENT_SYMBOL,
    TIMEFRAME_CONFIGS,
)
from modules.config.constants import INSTRUMENT_CURRENCY, INSTRUMENT_EXCHANGE

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_RETRIES: int = 3
RETRY_DELAY_SECONDS: int = 5
IB_PACING_DELAY_SECONDS: int = 2
REQUIRED_COLUMNS: list[str] = ["date", "open", "high", "low", "close", "volume"]
MIN_BARS: int = 100


# ---------------------------------------------------------------------------
# IB Gateway connection
# ---------------------------------------------------------------------------
def connect_ib_gateway(
    host: str = IB_HOST,
    port: int = IB_PORT,
    client_id: int = IB_CLIENT_ID,
    timeout: int = 10,
) -> IB:
    """Connect to IB Gateway with retry logic.

    Attempts connection up to ``MAX_RETRIES`` times with a delay between
    attempts.

    Args:
        host: IB Gateway host address.
        port: IB Gateway port.
        client_id: Unique client identifier.
        timeout: Connection timeout in seconds.

    Returns:
        Connected IB instance.

    Raises:
        ConnectionError: If connection fails after all retries.
    """
    ib = IB()
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                "Connection attempt %d/%d to %s:%d (clientId=%d)",
                attempt,
                MAX_RETRIES,
                host,
                port,
                client_id,
            )
            ib.connect(host, port, clientId=client_id, timeout=timeout)
            return ib
        except Exception as exc:
            last_error = exc
            logger.warning("Connection attempt %d failed: %s", attempt, exc)
            if attempt < MAX_RETRIES:
                logger.info("Retrying in %d seconds...", RETRY_DELAY_SECONDS)
                time.sleep(RETRY_DELAY_SECONDS)

    raise ConnectionError(
        f"Failed to connect to IB Gateway at {host}:{port} "
        f"after {MAX_RETRIES} attempts. Last error: {last_error}"
    )


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------
def fetch_timeframe_data(
    ib: IB,
    timeframe: str,
    config: dict,
) -> pd.DataFrame:
    """Fetch historical data for a specific timeframe.

    Creates a EUR/USD Forex contract and requests historical bars from IB
    Gateway using the bar size and duration specified in *config*.

    Args:
        ib: Connected IB instance.
        timeframe: Timeframe key (e.g. '5min', '4H', '1D').
        config: Timeframe configuration from ``TIMEFRAME_CONFIGS``.

    Returns:
        DataFrame with columns: date, open, high, low, close, volume.

    Raises:
        ValueError: If no data received or data is empty.
    """
    symbol = INSTRUMENT_SYMBOL.split(".")[0]  # 'EUR'
    contract = Forex(
        symbol=symbol,
        currency=INSTRUMENT_CURRENCY,
        exchange=INSTRUMENT_EXCHANGE,
    )

    logger.info(
        "Requesting %s bars  (barSize=%s, duration=%s)",
        timeframe,
        config["ib_bar_size"],
        config["ib_duration"],
    )

    bars = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr=config["ib_duration"],
        barSizeSetting=config["ib_bar_size"],
        whatToShow="MIDPOINT",
        useRTH=False,
        formatDate=1,
        keepUpToDate=False,
    )

    if not bars:
        raise ValueError(
            f"No data received for {timeframe} "
            f"(barSize={config['ib_bar_size']}, duration={config['ib_duration']})"
        )

    df = util.df(bars)
    logger.info("Received %d bars for %s", len(df), timeframe)

    # Keep only the required columns
    df = df.rename(columns={"date": "date"})
    available = [c for c in REQUIRED_COLUMNS if c in df.columns]
    df = df[available]

    return df


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_data(df: pd.DataFrame, timeframe: str) -> bool:
    """Validate fetched data for quality issues.

    Checks OHLC price relationships, duplicate timestamps, missing values,
    and minimum row count.

    Args:
        df: DataFrame to validate.
        timeframe: Timeframe key (for logging context).

    Returns:
        ``True`` if data passes all checks.

    Raises:
        ValueError: If critical issues are found.
    """
    # Minimum row count
    if len(df) < MIN_BARS:
        raise ValueError(
            f"{timeframe}: Only {len(df)} bars received (minimum {MIN_BARS})"
        )

    # NaN in OHLC columns
    ohlc = ["open", "high", "low", "close"]
    nan_counts = df[ohlc].isna().sum()
    if nan_counts.any():
        raise ValueError(
            f"{timeframe}: NaN values found in OHLC data:\n{nan_counts[nan_counts > 0]}"
        )

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

    # Duplicate timestamps
    n_dupes = df["date"].duplicated().sum()
    if n_dupes > 0:
        logger.warning(
            "%s: Found %d duplicate timestamps — removing duplicates",
            timeframe,
            n_dupes,
        )
        df.drop_duplicates(subset="date", keep="last", inplace=True)

    # Volume warnings (NaN volume is acceptable for forex midpoint data)
    if "volume" in df.columns and df["volume"].isna().any():
        logger.warning(
            "%s: %d rows with missing volume (expected for forex MIDPOINT)",
            timeframe,
            df["volume"].isna().sum(),
        )

    logger.info("%s: All validation checks passed (%d bars)", timeframe, len(df))
    return True


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------
def save_to_csv(
    df: pd.DataFrame,
    timeframe: str,
    base_dir: str = DATA_DIR,
) -> Path:
    """Save DataFrame to CSV with standardised naming.

    Creates the target directory if it does not exist and writes data using
    the naming convention ``EUR_USD_{timeframe}_{start}_{end}.csv``.

    Args:
        df: DataFrame with OHLCV data.
        timeframe: Timeframe key.
        base_dir: Base data directory.

    Returns:
        Path to saved CSV file.
    """
    tf_dir = Path(base_dir) / timeframe
    tf_dir.mkdir(parents=True, exist_ok=True)

    # Derive date range from data
    dates = pd.to_datetime(df["date"])
    start_str = dates.min().strftime("%Y%m%d")
    end_str = dates.max().strftime("%Y%m%d")

    filename = f"EUR_USD_{timeframe}_{start_str}_{end_str}.csv"
    filepath = tf_dir / filename

    df.to_csv(filepath, index=False)
    logger.info("Saved %d bars to %s", len(df), filepath)

    return filepath


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    """Main execution function."""
    logger.info("Starting historical data fetch from IB Gateway")
    logger.info("Target directory: %s", DATA_DIR)

    ib: IB | None = None
    try:
        ib = connect_ib_gateway()
        logger.info("Connected to IB Gateway at %s:%d", IB_HOST, IB_PORT)

        for idx, (timeframe, config) in enumerate(TIMEFRAME_CONFIGS.items()):
            logger.info("Fetching %s data...", timeframe)

            df = fetch_timeframe_data(ib, timeframe, config)
            validate_data(df, timeframe)
            filepath = save_to_csv(df, timeframe)

            logger.info("Saved %d bars to %s", len(df), filepath)

            # Respect IB pacing rules between requests
            if idx < len(TIMEFRAME_CONFIGS) - 1:
                time.sleep(IB_PACING_DELAY_SECONDS)

        logger.info("All data fetched successfully!")

    except Exception as exc:
        logger.error("Error during data fetch: %s", exc)
        raise

    finally:
        if ib is not None and ib.isConnected():
            ib.disconnect()
            logger.info("Disconnected from IB Gateway")


if __name__ == "__main__":
    main()
