"""
Live Trading Configuration
Configure all parameters for live paper trading bot.
"""

from datetime import datetime

# ============================================================================
# IB CONNECTION SETTINGS
# ============================================================================

IB_HOST = '127.0.0.1'   # IB Gateway host
IB_PORT = 4002          # Paper trading port (4001 for live)
IB_CLIENT_ID = 753      # Unique client ID (different from backtest)

# ============================================================================
# TRADING INSTRUMENT
# ============================================================================

SYMBOL = 'EUR'          # Base currency
CURRENCY = 'USD'        # Quote currency
CONTRACT_SIZE = 20000   # Minimum contract size for EUR/USD

# ============================================================================
# DATA STREAMING SETTINGS
# ============================================================================

BAR_SIZE = '5 mins'     # Bar size for streaming
LOOKBACK_BARS = 100     # Number of historical bars to fetch on startup

# ============================================================================
# TECHNICAL INDICATOR SETTINGS (Same as backtest)
# ============================================================================

MA_SHORT_PERIOD = 20
MA_LONG_PERIOD = 50
RSI_PERIOD = 14
MOMENTUM_PERIOD = 5

# ============================================================================
# SIGNAL GENERATION SETTINGS (Same as backtest)
# ============================================================================

RSI_NEUTRAL_LOW = 45
RSI_NEUTRAL_HIGH = 55
RSI_BUY_THRESHOLD = 55
RSI_SELL_THRESHOLD = 45
MOMENTUM_BUY_THRESHOLD = 0.00003
MOMENTUM_SELL_THRESHOLD = -0.00003

# ============================================================================
# RUN DURATION SETTINGS
# ============================================================================

# How long should the bot run before auto-shutdown?
# Format: "10 min", "1 h", "8 h", "30 min", etc.
# For testing: "10 min" or "30 min"
# For assignment: "8 h"
RUN_DURATION = "10 min"

# Close positions at end of run? (Recommended: True for clean slate)
CLOSE_POSITIONS_ON_EXIT = True

# ============================================================================
# SAFETY LIMITS (Optional - Disabled by default for assignment)
# ============================================================================

# Enable safety limits?
ENABLE_SAFETY_LIMITS = False

# Maximum daily loss (USD) - stops trading if reached
MAX_DAILY_LOSS = 500

# Maximum loss per trade (USD) - closes position if reached
MAX_LOSS_PER_TRADE = 200

# Trading hours restriction (ET timezone)
# None = trade 24/5, or specify hours like (9, 17) for 9am-5pm ET
TRADING_HOURS = None  # (9, 17) to restrict to business hours

# ============================================================================
# ACCOUNT SETTINGS
# ============================================================================

# Minimum USD balance required to trade
MIN_USD_BALANCE = 25000

# Check balance before each trade?
CHECK_BALANCE_BEFORE_TRADE = True

# ============================================================================
# LOGGING SETTINGS
# ============================================================================

# Log directory
LOG_DIR = 'logs'

# Trade log CSV filename (auto-appends timestamp)
TRADE_LOG_FILE = 'trades'  # Will become: trades_20260114_130000.csv

# Detailed log filename (auto-appends timestamp)
DETAIL_LOG_FILE = 'trading_bot'  # Will become: trading_bot_20260114_130000.log

# Console output verbosity
# 0 = Minimal (trades only)
# 1 = Normal (bars + signals + trades)
# 2 = Detailed (all calculations)
CONSOLE_VERBOSITY = 1

# Log every bar to console?
LOG_BARS_TO_CONSOLE = True

# ============================================================================
# PERFORMANCE TRACKING
# ============================================================================

# Track performance metrics in real-time?
ENABLE_PERFORMANCE_TRACKING = True

# Save performance snapshot every N minutes
PERFORMANCE_SNAPSHOT_INTERVAL = 15  # minutes

# ============================================================================
# STRATEGY DESCRIPTION
# ============================================================================

STRATEGY_DESCRIPTION = """
Live Trading: MA(20/50) + RSI(14) + Momentum(5)

Entry Logic (same as backtest):
- BUY: SMA(20) > SMA(50) AND RSI outside neutral AND conditions met
- SELL: SMA(20) < SMA(50) AND RSI outside neutral AND conditions met  
- HOLD: RSI in neutral zone (45-55)

Position Management:
- Always in market (LONG or SHORT)
- 20,000 EUR contract size
- Close positions at start and end of run
"""


def parse_duration(duration_str):
    """
    Parse duration string to seconds.
    
    Args:
        duration_str: String like "10 min", "1 h", "8 h", "30 min"
    
    Returns:
        Duration in seconds
    """
    parts = duration_str.strip().split()
    if len(parts) != 2:
        raise ValueError(f"Invalid duration format: {duration_str}. Use '10 min' or '1 h'")
    
    value = int(parts[0])
    unit = parts[1].lower()
    
    if unit in ['min', 'mins', 'minute', 'minutes']:
        return value * 60
    elif unit in ['h', 'hr', 'hour', 'hours']:
        return value * 3600
    else:
        raise ValueError(f"Invalid time unit: {unit}. Use 'min' or 'h'")


def get_run_duration_seconds():
    """Get run duration in seconds."""
    return parse_duration(RUN_DURATION)


def print_config():
    """Print current live trading configuration."""
    print("\n" + "="*70)
    print("  LIVE TRADING CONFIGURATION")
    print("="*70)
    
    print("\n📡 IB CONNECTION:")
    print(f"  Host: {IB_HOST}")
    print(f"  Port: {IB_PORT} (Paper Trading)")
    print(f"  Client ID: {IB_CLIENT_ID}")
    
    print("\n💱 TRADING:")
    print(f"  Instrument: {SYMBOL}/{CURRENCY}")
    print(f"  Contract Size: {CONTRACT_SIZE:,} {SYMBOL}")
    print(f"  Bar Size: {BAR_SIZE}")
    
    print("\n📈 INDICATORS:")
    print(f"  MA Periods: {MA_SHORT_PERIOD}/{MA_LONG_PERIOD}")
    print(f"  RSI Period: {RSI_PERIOD}")
    print(f"  Momentum Period: {MOMENTUM_PERIOD}")
    
    print("\n⏱️  RUN SETTINGS:")
    print(f"  Duration: {RUN_DURATION} ({get_run_duration_seconds()} seconds)")
    print(f"  Close positions on exit: {CLOSE_POSITIONS_ON_EXIT}")
    
    print("\n💰 ACCOUNT:")
    print(f"  Min USD balance: ${MIN_USD_BALANCE:,}")
    print(f"  Check balance before trade: {CHECK_BALANCE_BEFORE_TRADE}")
    
    print("\n🛡️  SAFETY LIMITS:")
    if ENABLE_SAFETY_LIMITS:
        print(f"  ENABLED")
        print(f"  Max daily loss: ${MAX_DAILY_LOSS}")
        print(f"  Max loss per trade: ${MAX_LOSS_PER_TRADE}")
        print(f"  Trading hours: {TRADING_HOURS if TRADING_HOURS else '24/5'}")
    else:
        print(f"  DISABLED (running without limits)")
    
    print("\n📝 LOGGING:")
    print(f"  Trade log: {TRADE_LOG_FILE}_[timestamp].csv")
    print(f"  Detail log: {DETAIL_LOG_FILE}_[timestamp].log")
    print(f"  Console verbosity: {CONSOLE_VERBOSITY}")
    print(f"  Log bars to console: {LOG_BARS_TO_CONSOLE}")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    print_config()
    print(STRATEGY_DESCRIPTION)
