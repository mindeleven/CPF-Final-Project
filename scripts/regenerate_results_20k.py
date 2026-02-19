"""
Regenerate optimization and backtest CSV files with initial_capital=20000.

Session 8A: Corrects the initial capital from 10K to 20K (no leverage).
Replaces files in data/optimization/ and data/backtest/.

Usage:
    python scripts/regenerate_results_20k.py
"""

import sys
import time
from pathlib import Path

import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from modules.backtest import BacktestEngine, TransactionCosts
from modules.data import load_timeframe_data
from modules.optimization import GridSearchOptimizer
from modules.strategy import MARSIMomentumStrategy

INITIAL_CAPITAL = 20000.0
POSITION_SIZE = 20000.0
SPREAD_PIPS = 1.0

costs = TransactionCosts(spread_pips=SPREAD_PIPS)

# The same param grid used in Session 6 / 6B
param_grid = {
    "sma_fast": [15, 20, 25, 30],
    "sma_slow": [40, 50, 60, 70],
    "rsi_lower": [25, 30, 35],
    "rsi_upper": [65, 70, 75],
    "momentum_threshold": [0.0, 0.00005, 0.0001],
}

output_dir_opt = project_root / "data" / "optimization"
output_dir_bt = project_root / "data" / "backtest"


def run_optimization(timeframe: str) -> pd.DataFrame:
    """Run grid search optimization for a timeframe."""
    print(f"\n{'='*60}")
    print(f"  OPTIMIZATION: {timeframe} (initial_capital={INITIAL_CAPITAL:,.0f})")
    print(f"{'='*60}\n")

    data = load_timeframe_data(timeframe)
    print(f"Loaded {len(data)} bars for {timeframe}")

    optimizer = GridSearchOptimizer(
        timeframe=timeframe,
        initial_capital=INITIAL_CAPITAL,
        position_size=POSITION_SIZE,
        transaction_costs=costs,
    )

    results = optimizer.run_grid_search(data, param_grid, verbose=True)
    df = results.to_dataframe()

    output_file = output_dir_opt / f"optimization_results_{timeframe}_corrected.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved {len(df)} results to {output_file}")

    # Print best result
    best = results.get_best_overall(primary_metric="sharpe_ratio", min_trades=20)
    if best:
        print(f"\nBest (Sharpe, min 20 trades):")
        print(f"  Params: SMA {best['params']['sma_fast']}/{best['params']['sma_slow']}, "
              f"RSI {best['params']['rsi_lower']}/{best['params']['rsi_upper']}, "
              f"Mom {best['params']['momentum_threshold']}")
        print(f"  Sharpe: {best['metrics']['sharpe_ratio']:.4f}")
        print(f"  Return: {best['metrics']['total_return_pct']:.2f}%")
        print(f"  Trades: {best['metrics']['num_trades']}")

    return df


def run_default_backtest(timeframe: str) -> dict:
    """Run backtest with default parameters for a timeframe."""
    print(f"\n  Default backtest: {timeframe}")

    data = load_timeframe_data(timeframe)
    strategy = MARSIMomentumStrategy(timeframe=timeframe)
    signals = strategy.generate_signals(data)

    engine = BacktestEngine(
        initial_capital=INITIAL_CAPITAL,
        position_size=POSITION_SIZE,
        transaction_costs=costs,
    )

    results = engine.run(data, signals)
    metrics = results["metrics"]

    print(f"    Bars: {len(data)}, Trades: {metrics['num_trades']}, "
          f"Return: {metrics['total_return_pct']:.2f}%, "
          f"Sharpe: {metrics['sharpe_ratio']:.2f}")

    return {
        "timeframe": timeframe,
        "data": data,
        "results": results,
        "metrics": metrics,
        "signals": signals,
    }


if __name__ == "__main__":
    start = time.time()

    # =========================================================================
    # Step 1: Optimization for 5min and 4H
    # =========================================================================
    opt_5min_df = run_optimization("5min")
    opt_4h_df = run_optimization("4H")

    # =========================================================================
    # Step 2: Comparison CSV
    # =========================================================================
    print(f"\n{'='*60}")
    print("  GENERATING COMPARISON TABLE")
    print(f"{'='*60}\n")

    # Best results from new optimization
    best_5min = opt_5min_df.nlargest(1, "sharpe_ratio").iloc[0]
    best_4h = opt_4h_df.nlargest(1, "sharpe_ratio").iloc[0]

    comparison = pd.DataFrame([
        {
            "Timeframe": "5min",
            "Session": "8A (20K capital)",
            "Initial_Capital": int(INITIAL_CAPITAL),
            "Position_Size": int(POSITION_SIZE),
            "Best_Sharpe": round(best_5min["sharpe_ratio"], 4),
            "Best_Return_Pct": round(best_5min["total_return_pct"], 2),
            "Best_SMA_Fast": int(best_5min["sma_fast"]),
            "Best_SMA_Slow": int(best_5min["sma_slow"]),
            "Best_RSI_Lower": int(best_5min["rsi_lower"]),
            "Best_RSI_Upper": int(best_5min["rsi_upper"]),
            "Best_Mom_Threshold": best_5min["momentum_threshold"],
            "Num_Trades": int(best_5min["num_trades"]),
        },
        {
            "Timeframe": "4H",
            "Session": "8A (20K capital)",
            "Initial_Capital": int(INITIAL_CAPITAL),
            "Position_Size": int(POSITION_SIZE),
            "Best_Sharpe": round(best_4h["sharpe_ratio"], 4),
            "Best_Return_Pct": round(best_4h["total_return_pct"], 2),
            "Best_SMA_Fast": int(best_4h["sma_fast"]),
            "Best_SMA_Slow": int(best_4h["sma_slow"]),
            "Best_RSI_Lower": int(best_4h["rsi_lower"]),
            "Best_RSI_Upper": int(best_4h["rsi_upper"]),
            "Best_Mom_Threshold": best_4h["momentum_threshold"],
            "Num_Trades": int(best_4h["num_trades"]),
        },
    ])

    comp_file = output_dir_opt / "optimization_comparison_6_vs_6b.csv"
    comparison.to_csv(comp_file, index=False)
    print(f"Saved comparison to {comp_file}")
    print(comparison.to_string(index=False))

    # =========================================================================
    # Step 3: Default-parameter backtests (all timeframes)
    # =========================================================================
    print(f"\n{'='*60}")
    print(f"  DEFAULT-PARAMETER BACKTESTS (initial_capital={INITIAL_CAPITAL:,.0f})")
    print(f"{'='*60}")

    bt_results = []
    for tf in ["5min", "4H", "1D"]:
        bt = run_default_backtest(tf)
        m = bt["metrics"]
        bt_results.append({
            "Timeframe": tf,
            "Bars": len(bt["data"]),
            "Signals": len(bt["signals"]),
            "Trades": m["num_trades"],
            "Return (%)": round(m["total_return_pct"], 2),
            "Sharpe": round(m["sharpe_ratio"], 2),
            "Max DD (%)": round(m["max_drawdown_pct"], 2),
            "Win Rate (%)": round(m["win_rate"] * 100, 1),
            "Profit Factor": round(m["profit_factor"], 2),
        })

        # Save 5min trade log
        if tf == "5min":
            trades_df = bt["results"]["trades"]
            trades_file = output_dir_bt / "backtest_results_5min_corrected.csv"
            trades_df.to_csv(trades_file, index=False)
            print(f"    Saved trade log: {trades_file}")

    summary_df = pd.DataFrame(bt_results)
    summary_file = output_dir_bt / "backtest_summary_corrected.csv"
    summary_df.to_csv(summary_file, index=False)
    print(f"\n  Saved summary: {summary_file}")
    print(f"\n{summary_df.to_string(index=False)}")

    # =========================================================================
    # Done
    # =========================================================================
    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  COMPLETE in {elapsed:.1f}s")
    print(f"{'='*60}")
