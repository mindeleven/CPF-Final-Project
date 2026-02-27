"""
Analyze live trading bot logs from 5-minute paper trading run.

Extracts key events, errors, trades, and infrastructure events from the bot log
and trade CSV to produce a structured summary for the final project notebook.

Usage:
    python scripts/analyze_live_run.py
"""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

# Log file paths
LOG_FILE = Path("deployment/logs/trading_bot_5min_5d_20260223_072007.log")
TRADE_FILE = Path("deployment/logs/trades_5min_5min_5d_20260223_072007.csv")

# Alternative trade file naming (check both)
if not TRADE_FILE.exists():
    TRADE_FILE = Path("deployment/logs/trades_5min_5d_20260223_072007.csv")


def parse_log_timestamp(line: str) -> datetime:
    """Extract timestamp from log line."""
    # Format: 2026-02-23 07:20:08,123 - INFO - ...
    match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
    return None


def analyze_log_file(log_path: Path) -> Dict:
    """Parse log file and extract key events."""
    print(f"Analyzing log file: {log_path}")
    print(f"File size: {log_path.stat().st_size / 1024:.1f} KB\n")

    with open(log_path, "r") as f:
        lines = f.readlines()

    print(f"Total log lines: {len(lines)}\n")

    # Extract metadata
    first_line = lines[0]
    last_line = lines[-1]
    start_ts = parse_log_timestamp(first_line)
    end_ts = parse_log_timestamp(last_line)

    if start_ts and end_ts:
        duration = end_ts - start_ts
        print(f"Run period: {start_ts} to {end_ts}")
        print(f"Duration: {duration} ({duration.total_seconds() / 3600:.2f} hours)\n")

    # Event counters
    events = {
        "error_1100": [],  # Connection lost
        "error_1102": [],  # Connection restored
        "error_10349": [],  # TIF error
        "error_201": [],  # Currency leverage error
        "other_errors": [],
        "reconnections": [],
        "reconciliations": [],
        "position_mismatches": [],
        "opened_positions": [],
        "closed_positions": [],
        "fill_timeouts": [],
        "order_rejections": [],
    }

    # Parse line by line
    for i, line in enumerate(lines):
        ts = parse_log_timestamp(line)

        # Error 1100 (connection lost)
        if "ERROR 1100" in line or "Connectivity between IBKR" in line:
            events["error_1100"].append((ts, line.strip()))

        # Error 1102 (connection restored)
        if "ERROR 1102" in line or "Connectivity restored" in line:
            events["error_1102"].append((ts, line.strip()))

        # Error 10349 (TIF error)
        if "ERROR 10349" in line or "Order TIF was set to DAY" in line:
            events["error_10349"].append((ts, line.strip()))

        # Error 201 (currency leverage)
        if "Error 201" in line or "currency leverage" in line:
            events["error_201"].append((ts, line.strip()))

        # Other errors (not 1100, 1102, 10349, 201, 2104, 2106, 2158)
        if (
            "ERROR" in line
            and "ERROR 1100" not in line
            and "ERROR 1102" not in line
            and "ERROR 10349" not in line
            and "Error 201" not in line
            and "Error 2104" not in line  # Market data farm connection OK
            and "Error 2106" not in line  # HMDS data farm connection OK
            and "Error 2158" not in line  # Sec-def data farm connection OK
        ):
            events["other_errors"].append((ts, line.strip()))

        # Reconnections
        if "Reconnected successfully" in line:
            events["reconnections"].append((ts, line.strip()))

        # Reconciliations
        if "Reconciling position state" in line:
            events["reconciliations"].append((ts, line.strip()))

        # Position mismatches
        if "Position mismatch detected" in line:
            events["position_mismatches"].append((ts, line.strip()))

        # Opened positions
        if "OPENED:" in line:
            events["opened_positions"].append((ts, line.strip()))

        # Closed positions
        if "CLOSED:" in line:
            events["closed_positions"].append((ts, line.strip()))

        # Fill timeouts
        if "Order not filled within" in line:
            events["fill_timeouts"].append((ts, line.strip()))

        # Order rejections (explicit rejection messages)
        if "Order rejected" in line or "OrderStatus: Inactive" in line:
            events["order_rejections"].append((ts, line.strip()))

    return {
        "start_time": start_ts,
        "end_time": end_ts,
        "duration_hours": duration.total_seconds() / 3600 if start_ts and end_ts else None,
        "total_lines": len(lines),
        "events": events,
    }


def analyze_trade_csv(csv_path: Path) -> Dict:
    """Parse trade CSV and compute summary statistics."""
    if not csv_path.exists():
        print(f"WARNING: Trade CSV not found at {csv_path}")
        return None

    print(f"\nAnalyzing trade CSV: {csv_path}\n")

    try:
        trades = pd.read_csv(csv_path)
    except Exception as e:
        print(f"ERROR reading CSV: {e}")
        return None

    print(f"Columns: {list(trades.columns)}")
    print(f"Total trades: {len(trades)}\n")

    if len(trades) == 0:
        print("No trades in CSV.")
        return {"num_trades": 0}

    # Compute statistics
    summary = {
        "num_trades": len(trades),
        "num_long": (trades["direction"].str.contains("LONG")).sum() if "direction" in trades.columns else None,
        "num_short": (trades["direction"].str.contains("SHORT")).sum() if "direction" in trades.columns else None,
    }

    # P&L statistics (prefer EUR if available)
    if "net_pnl_eur" in trades.columns:
        pnl_col = "net_pnl_eur"
        currency = "EUR"
    elif "net_pnl" in trades.columns:
        pnl_col = "net_pnl"
        currency = "USD"
    else:
        print("WARNING: No P&L column found in CSV")
        return summary

    summary["currency"] = currency
    summary["num_winning"] = (trades[pnl_col] > 0).sum()
    summary["num_losing"] = (trades[pnl_col] < 0).sum()
    summary["win_rate"] = summary["num_winning"] / len(trades) * 100 if len(trades) > 0 else 0.0
    summary["total_pnl"] = trades[pnl_col].sum()
    summary["avg_pnl"] = trades[pnl_col].mean()
    summary["max_win"] = trades[pnl_col].max()
    summary["max_loss"] = trades[pnl_col].min()

    # Sharpe ratio (indicative, from trade returns)
    if len(trades) > 2:
        # Assume position size 20,000 EUR
        position_size = 20000.0
        trade_returns = trades[pnl_col] / position_size
        mean_ret = trade_returns.mean()
        std_ret = trade_returns.std()
        # Annualize: assume ~15 trades/year from backtesting (45 trades / 3 years)
        # But this is a 5-day sample, so use number of trades as proxy
        # Sharpe = mean / std * sqrt(trades_per_year)
        # Very rough estimate: 252 trading days, if we have N trades in 5 days -> ~50*N per year
        trades_per_year_estimate = len(trades) * (252 / 5.0)
        sharpe = (mean_ret / std_ret) * (trades_per_year_estimate**0.5) if std_ret > 0 else 0.0
        summary["sharpe_indicative"] = sharpe
        summary["trades_per_year_estimate"] = trades_per_year_estimate
    else:
        summary["sharpe_indicative"] = None
        summary["trades_per_year_estimate"] = None

    summary["trades_df"] = trades

    return summary


def print_summary(log_analysis: Dict, trade_analysis: Dict):
    """Print structured summary."""
    print("\n" + "=" * 80)
    print("LIVE TRADING RUN SUMMARY — 5-MINUTE TIMEFRAME")
    print("=" * 80)

    # Metadata
    print("\n1. RUN METADATA")
    print("-" * 80)
    print(f"Start time:    {log_analysis['start_time']}")
    print(f"End time:      {log_analysis['end_time']}")
    print(f"Duration:      {log_analysis['duration_hours']:.2f} hours")
    print(f"Log lines:     {log_analysis['total_lines']:,}")

    # Infrastructure events
    print("\n2. INFRASTRUCTURE EVENTS")
    print("-" * 80)
    print(f"Error 1100 (connection lost):      {len(log_analysis['events']['error_1100'])}")
    print(f"Error 1102 (connection restored):  {len(log_analysis['events']['error_1102'])}")
    print(f"Reconnections completed:           {len(log_analysis['events']['reconnections'])}")
    print(f"Position reconciliations:          {len(log_analysis['events']['reconciliations'])}")
    print(f"Position mismatches detected:      {len(log_analysis['events']['position_mismatches'])}")

    # Nightly reboot sequences
    num_reboots = min(len(log_analysis["events"]["error_1100"]), len(log_analysis["events"]["error_1102"]))
    print(f"\nNightly reboot cycles (1100→1102): {num_reboots}")

    # Other errors
    print("\n3. ERRORS AND WARNINGS")
    print("-" * 80)
    print(f"Error 10349 (TIF error):           {len(log_analysis['events']['error_10349'])}")
    print(f"Error 201 (currency leverage):     {len(log_analysis['events']['error_201'])}")
    print(f"Other errors:                      {len(log_analysis['events']['other_errors'])}")
    print(f"Fill timeouts:                     {len(log_analysis['events']['fill_timeouts'])}")
    print(f"Order rejections:                  {len(log_analysis['events']['order_rejections'])}")

    # Trade summary
    if trade_analysis:
        print("\n4. TRADE SUMMARY")
        print("-" * 80)
        print(f"Total trades:     {trade_analysis['num_trades']}")
        if trade_analysis["num_trades"] > 0:
            print(f"Long trades:      {trade_analysis['num_long']}")
            print(f"Short trades:     {trade_analysis['num_short']}")
            print(f"Winning trades:   {trade_analysis['num_winning']}")
            print(f"Losing trades:    {trade_analysis['num_losing']}")
            print(f"Win rate:         {trade_analysis['win_rate']:.1f}%")
            print(f"Total P&L:        {trade_analysis['total_pnl']:.2f} {trade_analysis['currency']}")
            print(f"Average P&L:      {trade_analysis['avg_pnl']:.2f} {trade_analysis['currency']}")
            print(f"Largest win:      {trade_analysis['max_win']:.2f} {trade_analysis['currency']}")
            print(f"Largest loss:     {trade_analysis['max_loss']:.2f} {trade_analysis['currency']}")

            if trade_analysis["sharpe_indicative"]:
                print(f"\nSharpe (indicative): {trade_analysis['sharpe_indicative']:.2f}")
                print(f"  (Based on {trade_analysis['num_trades']} trades over 5 days)")
                print(f"  (Annualized assuming ~{trade_analysis['trades_per_year_estimate']:.0f} trades/year)")
                print("  WARNING: 5-day sample insufficient for reliable Sharpe calculation")


if __name__ == "__main__":
    print("=" * 80)
    print("LIVE TRADING LOG ANALYSIS — 5-MINUTE TIMEFRAME")
    print("=" * 80)

    # Analyze log file
    log_analysis = analyze_log_file(LOG_FILE)

    # Analyze trade CSV
    trade_analysis = analyze_trade_csv(TRADE_FILE)

    # Print summary
    print_summary(log_analysis, trade_analysis)

    # Write detailed event logs
    print("\n" + "=" * 80)
    print("DETAILED EVENT LOGS")
    print("=" * 80)

    events = log_analysis["events"]

    if events["error_1100"]:
        print("\nError 1100 events (connection lost):")
        for ts, line in events["error_1100"]:
            print(f"  {ts}: {line}")

    if events["error_1102"]:
        print("\nError 1102 events (connection restored):")
        for ts, line in events["error_1102"]:
            print(f"  {ts}: {line}")

    if events["error_201"]:
        print("\nError 201 events (currency leverage):")
        for ts, line in events["error_201"]:
            print(f"  {ts}: {line}")

    if events["other_errors"]:
        print(f"\nOther errors ({len(events['other_errors'])} total):")
        for ts, line in events["other_errors"][:10]:  # Show first 10
            print(f"  {ts}: {line}")
        if len(events["other_errors"]) > 10:
            print(f"  ... and {len(events['other_errors']) - 10} more")

    if events["position_mismatches"]:
        print("\nPosition mismatches:")
        for ts, line in events["position_mismatches"]:
            print(f"  {ts}: {line}")

    # Trade log table
    if trade_analysis and trade_analysis["num_trades"] > 0:
        print("\n" + "=" * 80)
        print("TRADE LOG TABLE")
        print("=" * 80)
        trades = trade_analysis["trades_df"]
        print(trades.to_string(index=False))

    print("\n" + "=" * 80)
    print("END OF ANALYSIS")
    print("=" * 80)
