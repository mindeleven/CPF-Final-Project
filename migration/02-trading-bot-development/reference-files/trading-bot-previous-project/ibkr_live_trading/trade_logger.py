"""
Trade Logger Module
Handles CSV trade logging and detailed log files.
"""

import pandas as pd
import os
from datetime import datetime
import logging


class TradeLogger:
    """Logs trades to CSV and detailed events to log file."""
    
    def __init__(self, log_dir='logs', trade_log_name='trades', detail_log_name='trading_bot'):
        """
        Initialize trade logger.
        
        Args:
            log_dir: Directory for log files
            trade_log_name: Base name for trade CSV
            detail_log_name: Base name for detail log
        """
        self.log_dir = log_dir
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Generate timestamped filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.trade_csv_path = os.path.join(log_dir, f'{trade_log_name}_{timestamp}.csv')
        self.detail_log_path = os.path.join(log_dir, f'{detail_log_name}_{timestamp}.log')
        
        # Initialize trade log CSV
        self.trade_columns = [
            'timestamp',
            'bar_time',
            'action',
            'position',
            'quantity',
            'price',
            'slippage_pips',
            'trade_pnl',
            'cumulative_pnl',
            'signal',
            'sma_20',
            'sma_50',
            'rsi',
            'momentum',
            'reason'
        ]
        
        # Create empty CSV with headers
        pd.DataFrame(columns=self.trade_columns).to_csv(self.trade_csv_path, index=False)
        
        # Initialize detailed logging
        self.logger = logging.getLogger('TradingBot')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(self.detail_log_path)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler (will be controlled by verbosity setting)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Tracking
        self.trades = []
        self.cumulative_pnl = 0.0
        
        self.logger.info("="*70)
        self.logger.info("TRADING BOT STARTED")
        self.logger.info("="*70)
        self.logger.info(f"Trade log: {self.trade_csv_path}")
        self.logger.info(f"Detail log: {self.detail_log_path}")
        self.logger.info("="*70)
    
    
    def log_trade(self, action, position, quantity, price, bar_time, indicators, 
                  signal, reason, slippage_pips=0.0, trade_pnl=0.0):
        """
        Log a trade to CSV.
        
        Args:
            action: 'BUY', 'SELL', 'HOLD'
            position: 'LONG', 'SHORT', 'FLAT'
            quantity: Trade size
            price: Execution price
            bar_time: Bar timestamp
            indicators: Dict with indicator values
            signal: Signal value (1, -1, 0)
            reason: Text description of why trade was taken
            slippage_pips: Slippage in pips
            trade_pnl: P&L from this trade
        """
        # Update cumulative P&L
        self.cumulative_pnl += trade_pnl
        
        # Create trade record
        trade = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'bar_time': bar_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(bar_time, 'strftime') else str(bar_time),
            'action': action,
            'position': position,
            'quantity': quantity,
            'price': price if price else 0.0,
            'slippage_pips': slippage_pips,
            'trade_pnl': trade_pnl,
            'cumulative_pnl': self.cumulative_pnl,
            'signal': signal,
            'sma_20': indicators.get('sma_20', 0),
            'sma_50': indicators.get('sma_50', 0),
            'rsi': indicators.get('rsi', 0),
            'momentum': indicators.get('momentum', 0),
            'reason': reason
        }
        
        self.trades.append(trade)
        
        # Append to CSV
        pd.DataFrame([trade]).to_csv(self.trade_csv_path, mode='a', header=False, index=False)
        
        # Log to detail log
        if action != 'HOLD':
            self.logger.info(f"TRADE EXECUTED: {action} {quantity:,} @ {price:.5f} -> {position}")
            self.logger.info(f"  Trade P&L: ${trade_pnl:+,.2f}")
            self.logger.info(f"  Cumulative P&L: ${self.cumulative_pnl:+,.2f}")
            self.logger.info(f"  Reason: {reason}")
    
    
    def log_bar(self, bar, indicators):
        """
        Log a new bar received.
        
        Args:
            bar: Bar data (date, open, high, low, close)
            indicators: Dict with calculated indicators
        """
        self.logger.debug(
            f"New bar: {bar['date']} | "
            f"O={bar['open']:.5f} H={bar['high']:.5f} L={bar['low']:.5f} C={bar['close']:.5f} | "
            f"SMA20={indicators.get('sma_20', 0):.5f} SMA50={indicators.get('sma_50', 0):.5f} | "
            f"RSI={indicators.get('rsi', 0):.2f} | "
            f"MOM={indicators.get('momentum', 0):.6f}"
        )
    
    
    def log_signal(self, signal, signal_type, reason):
        """
        Log a trading signal.
        
        Args:
            signal: Signal value (1, -1, 0)
            signal_type: 'BUY', 'SELL', 'HOLD'
            reason: Explanation of signal
        """
        self.logger.info(f"SIGNAL: {signal_type} (value={signal}) - {reason}")
    
    
    def log_info(self, message):
        """Log general information."""
        self.logger.info(message)
    
    
    def log_warning(self, message):
        """Log warning."""
        self.logger.warning(message)
    
    
    def log_error(self, message):
        """Log error."""
        self.logger.error(message)
    
    
    def log_shutdown(self, reason="Normal shutdown"):
        """Log bot shutdown."""
        self.logger.info("="*70)
        self.logger.info(f"TRADING BOT SHUTDOWN: {reason}")
        self.logger.info(f"Total trades: {len(self.trades)}")
        self.logger.info(f"Final cumulative P&L: ${self.cumulative_pnl:+,.2f}")
        self.logger.info("="*70)
    
    
    def get_trade_summary(self):
        """
        Get summary of all trades.
        
        Returns:
            Dict with trade statistics
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'win_rate': 0.0
            }
        
        df = pd.DataFrame(self.trades)
        
        # Filter actual trades (not HOLD)
        actual_trades = df[df['action'] != 'HOLD']
        
        if len(actual_trades) == 0:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': self.cumulative_pnl,
                'win_rate': 0.0
            }
        
        winning = actual_trades[actual_trades['trade_pnl'] > 0]
        losing = actual_trades[actual_trades['trade_pnl'] < 0]
        
        return {
            'total_trades': len(actual_trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'total_pnl': self.cumulative_pnl,
            'win_rate': len(winning) / len(actual_trades) if len(actual_trades) > 0 else 0.0,
            'avg_win': winning['trade_pnl'].mean() if len(winning) > 0 else 0.0,
            'avg_loss': losing['trade_pnl'].mean() if len(losing) > 0 else 0.0,
        }
    
    
    def save_final_summary(self):
        """Save final trading summary to file."""
        summary = self.get_trade_summary()
        
        summary_path = self.trade_csv_path.replace('.csv', '_summary.txt')
        
        with open(summary_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("LIVE TRADING SESSION SUMMARY\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Total Trades: {summary['total_trades']}\n")
            f.write(f"Winning Trades: {summary['winning_trades']}\n")
            f.write(f"Losing Trades: {summary['losing_trades']}\n")
            f.write(f"Win Rate: {summary['win_rate']*100:.1f}%\n\n")
            
            f.write(f"Total P&L: ${summary['total_pnl']:+,.2f}\n")
            
            if summary['winning_trades'] > 0:
                f.write(f"Average Win: ${summary['avg_win']:+,.2f}\n")
            if summary['losing_trades'] > 0:
                f.write(f"Average Loss: ${summary['avg_loss']:+,.2f}\n")
            
            f.write("\n" + "="*70 + "\n")
        
        self.logger.info(f"Summary saved: {summary_path}")
        
        return summary_path


if __name__ == "__main__":
    # Test the logger
    print("Testing TradeLogger...")
    
    logger = TradeLogger(log_dir='test_logs')
    
    # Test bar logging
    bar = {
        'date': datetime.now(),
        'open': 1.0340,
        'high': 1.0345,
        'low': 1.0338,
        'close': 1.0343
    }
    
    indicators = {
        'sma_20': 1.0341,
        'sma_50': 1.0335,
        'rsi': 45.2,
        'momentum': 0.0001
    }
    
    logger.log_bar(bar, indicators)
    logger.log_signal(1, 'BUY', 'MA cross bullish + RSI favorable')
    
    # Test trade logging
    logger.log_trade(
        action='BUY',
        position='LONG',
        quantity=20000,
        price=1.0343,
        bar_time=datetime.now(),
        indicators=indicators,
        signal=1,
        reason='MA cross bullish + RSI 45.2 + Momentum positive',
        slippage_pips=0.2,
        trade_pnl=0.0
    )
    
    logger.log_shutdown("Test complete")
    
    print("\n✓ Logger test complete")
    print(f"  Trade CSV: {logger.trade_csv_path}")
    print(f"  Detail log: {logger.detail_log_path}")
