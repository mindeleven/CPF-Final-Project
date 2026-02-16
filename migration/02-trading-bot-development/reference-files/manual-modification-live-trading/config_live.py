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
IB_CLIENT_ID = 3  # Unique client ID (change if running multiple bots)

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
RUN_DURATION = "4h"  # Start with 1-hour test

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
# POSITION SIZING
# =============================================================================

# Position size in EUR (IBKR minimum for forex: 20,000 EUR)
POSITION_SIZE = 20000

# Initial capital for P&L tracking (USD)
INITIAL_CAPITAL = 20000.0

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
    RSI_PERIOD = 21
    RSI_LOWER = 35
    RSI_UPPER = 70
    MOMENTUM_PERIOD = 14
    MOMENTUM_THRESHOLD = 0.0

else:
    raise ValueError(f"Invalid timeframe: {TIMEFRAME}. Must be '5min' or '4H'")
