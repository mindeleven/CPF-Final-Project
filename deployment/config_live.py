"""
Live Trading Configuration

Author: Juergen Kober + Claude Code Opus 4.6
Date: February 2026
Session: 7

Configuration for live trading bot with Session 6B optimized parameters.
"""

# =============================================================================
# IB GATEWAY CONNECTION
# =============================================================================

IB_HOST = "localhost"  # IB Gateway running on same machine (Docker host mode)
IB_PORT = 4002  # Paper trading port (4001 for live)
IB_CLIENT_ID = 753  # Unique client ID (change if running multiple bots)

# =============================================================================
# TIMEFRAME SELECTION
# =============================================================================

# Choose timeframe: '5min' or '4H'
TIMEFRAME = "5min"  # Change to '4H' for 4-hour trading

# =============================================================================
# RUNTIME CONFIGURATION
# =============================================================================

# How long should the bot run?
# Format: "Xh" for hours, "Xd" for days, "Xm" for minutes
# Examples: "1h", "8h", "5d"
RUN_DURATION = "5d"  # 5-day test (Monday-Friday)

# How often to check for new data (seconds)
# 5min timeframe: check every 60 seconds
# 4H timeframe: check every 300 seconds (5 minutes)
CHECK_FREQUENCY = 60 if TIMEFRAME == "5min" else 300

# =============================================================================
# WEEKEND MANAGEMENT
# =============================================================================

# Close positions before weekend?
CLOSE_BEFORE_WEEKEND = True

# What time Friday to close? (local timezone, 24-hour format "HH:MM")
WEEKEND_CLOSE_TIME = "16:00"  # 4:00 PM

# =============================================================================
# MAINTENANCE WINDOW
# =============================================================================
# Bot pauses signal checking and order placement during this window to avoid
# IB Gateway nightly reboot disruptions. Open positions remain open.
# Format: "HH:MM" in CET (Central European Time).
#
# NOTE: IB Gateway hard disconnect occurs at 23:45 UTC = 00:45 CET.
# The current code implication is based on CET not UTC.
# Soft reboot (Error 1100/1102) occurs between approximately 05:22–05:49 UTC
# = 06:22–06:49 CET. Times below are in CET; add 1 hour to convert to UTC.
# To take the UTC/CET mistake into account and cover the full maintenance window:
# Start at 00:30 CET to catch the 00:45 CET hard disconnect with 15 min buffer.
# End at 06:45 CET to clear the soft reboot window with a safe margin.
MAINTENANCE_WINDOW_START = "00:30"
MAINTENANCE_WINDOW_END = "06:45"

# =============================================================================
# POSITION SIZING
# =============================================================================

# Position size in EUR (IBKR minimum for forex: 20,000 EUR)
POSITION_SIZE = 20000

# Initial capital for P&L tracking (EUR)
# NOTE: Overridden at startup by actual EUR balance from IB account
INITIAL_CAPITAL = 10000.0

# Minimum EUR balance required to trade
# Bot will abort startup if EUR balance is below this threshold
MIN_EUR_BALANCE = 20000

# =============================================================================
# STRATEGY PARAMETERS - SESSION 6B OPTIMIZED
# =============================================================================

if TIMEFRAME == "5min":
    # 5-minute optimized parameters (Session 6B)
    SMA_FAST = 15
    SMA_SLOW = 70
    RSI_PERIOD = 14
    RSI_LOWER = 35
    RSI_UPPER = 75
    MOMENTUM_PERIOD = 10
    MOMENTUM_THRESHOLD = 0.0

elif TIMEFRAME == "4H":
    # 4-hour optimized parameters (Session 6B)
    SMA_FAST = 20
    SMA_SLOW = 70
    RSI_PERIOD = 14
    RSI_LOWER = 35
    RSI_UPPER = 70
    MOMENTUM_PERIOD = 10
    MOMENTUM_THRESHOLD = 0.0

else:
    raise ValueError(f"Invalid timeframe: {TIMEFRAME}. Must be '5min' or '4H'")
