"""
Stream Processor Module
Processes real-time 5-min bars and calculates indicators.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from collections import deque


class StreamProcessor:
    """Processes streaming bars and calculates indicators in real-time."""
    
    def __init__(self, lookback_bars=100, ma_short=20, ma_long=50, rsi_period=14, momentum_period=5):
        """
        Initialize stream processor.
        
        Args:
            lookback_bars: Number of historical bars to maintain
            ma_short: Short MA period
            ma_long: Long MA period
            rsi_period: RSI period
            momentum_period: Momentum period
        """
        self.lookback_bars = lookback_bars
        self.ma_short = ma_short
        self.ma_long = ma_long
        self.rsi_period = rsi_period
        self.momentum_period = momentum_period
        
        # Store bars as deque for efficiency
        self.bars = deque(maxlen=lookback_bars)
        
        # Warmup period (max of all indicator periods)
        self.warmup_period = max(ma_long, rsi_period, momentum_period)
        self.is_warmed_up = False
        
        print(f"\n✓ Stream Processor initialized")
        print(f"  Lookback bars: {lookback_bars}")
        print(f"  Indicators: MA({ma_short}/{ma_long}), RSI({rsi_period}), Momentum({momentum_period})")
        print(f"  Warmup period: {self.warmup_period} bars")
    
    
    def load_historical_bars(self, bars):
        """
        Load historical bars for warmup.
        
        Args:
            bars: List or DataFrame of historical bars
        """
        print(f"\n📊 Loading historical bars for warmup...")
        
        if isinstance(bars, pd.DataFrame):
            # Convert DataFrame to list of dicts
            bars = bars.to_dict('records')
        
        for bar in bars:
            self.bars.append(bar)
        
        # Check if warmed up
        if len(self.bars) >= self.warmup_period:
            self.is_warmed_up = True
            print(f"  ✓ Loaded {len(self.bars)} bars")
            print(f"  ✓ Warmup complete (need {self.warmup_period} bars)")
        else:
            print(f"  ⚠ Loaded {len(self.bars)} bars (need {self.warmup_period} for warmup)")
    
    
    def process_bar(self, bar):
        """
        Process a new bar and calculate indicators.
        
        Args:
            bar: New bar dict with keys: date, open, high, low, close
        
        Returns:
            Dict with bar data + calculated indicators, or None if not warmed up
        """
        # Add bar to history
        self.bars.append(bar)
        
        # Check warmup
        if not self.is_warmed_up:
            if len(self.bars) >= self.warmup_period:
                self.is_warmed_up = True
                print(f"  ✓ Warmup complete ({len(self.bars)} bars)")
            else:
                print(f"  ⏳ Warming up... ({len(self.bars)}/{self.warmup_period} bars)")
                return None
        
        # Calculate indicators
        indicators = self._calculate_indicators()
        
        # Combine bar data with indicators
        result = bar.copy()
        result.update(indicators)
        
        return result
    
    
    def _calculate_indicators(self):
        """
        Calculate all indicators from current bar history.
        
        Returns:
            Dict with indicator values
        """
        # Convert bars to arrays
        closes = np.array([b['close'] for b in self.bars])
        
        # Calculate returns
        returns = np.diff(closes) / closes[:-1]
        current_return = returns[-1] if len(returns) > 0 else 0.0
        
        # Moving Averages
        sma_short = closes[-self.ma_short:].mean()
        sma_long = closes[-self.ma_long:].mean()
        ma_cross = 1 if sma_short > sma_long else 0
        
        # RSI
        rsi = self._calculate_rsi(closes)
        
        # Momentum
        if len(closes) > self.momentum_period:
            momentum = closes[-1] - closes[-(self.momentum_period + 1)]
        else:
            momentum = 0.0
        
        return {
            'returns': current_return,
            'sma_20': sma_short,
            'sma_50': sma_long,
            'ma_cross': ma_cross,
            'rsi': rsi,
            'momentum': momentum
        }
    
    
    def _calculate_rsi(self, closes):
        """
        Calculate RSI from price array.
        
        Args:
            closes: Array of close prices
        
        Returns:
            RSI value (0-100)
        """
        if len(closes) < self.rsi_period + 1:
            return 50.0  # Neutral default
        
        # Calculate price changes
        deltas = np.diff(closes)
        
        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gains and losses
        avg_gains = gains[-(self.rsi_period):].mean()
        avg_losses = losses[-(self.rsi_period):].mean()
        
        if avg_losses == 0:
            return 100.0
        
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    
    def generate_signal(self, indicators, 
                       rsi_neutral_low=45, rsi_neutral_high=55,
                       rsi_buy_threshold=55, rsi_sell_threshold=45,
                       momentum_buy_threshold=0.00003, momentum_sell_threshold=-0.00003):
        """
        Generate trading signal from indicators.
        
        Args:
            indicators: Dict with indicator values
            rsi_neutral_low: Lower RSI neutral zone
            rsi_neutral_high: Upper RSI neutral zone
            rsi_buy_threshold: RSI buy threshold
            rsi_sell_threshold: RSI sell threshold
            momentum_buy_threshold: Momentum buy threshold
            momentum_sell_threshold: Momentum sell threshold
        
        Returns:
            Tuple of (signal, reason)
            signal: 1=BUY, -1=SELL, 0=HOLD
            reason: Text explanation
        """
        sma_20 = indicators['sma_20']
        sma_50 = indicators['sma_50']
        rsi = indicators['rsi']
        momentum = indicators['momentum']
        
        # Check RSI neutral zone
        in_neutral_zone = (rsi >= rsi_neutral_low) and (rsi <= rsi_neutral_high)
        
        if in_neutral_zone:
            return 0, f"RSI in neutral zone ({rsi:.1f})"
        
        # BUY signal logic
        if (sma_20 > sma_50 and 
            not in_neutral_zone and 
            (rsi < rsi_buy_threshold or momentum > momentum_buy_threshold)):
            
            reason = f"MA bullish (SMA20={sma_20:.5f} > SMA50={sma_50:.5f}), RSI={rsi:.1f}, Momentum={momentum:.6f}"
            return 1, reason
        
        # SELL signal logic
        if (sma_20 < sma_50 and 
            not in_neutral_zone and 
            (rsi > rsi_sell_threshold or momentum < momentum_sell_threshold)):
            
            reason = f"MA bearish (SMA20={sma_20:.5f} < SMA50={sma_50:.5f}), RSI={rsi:.1f}, Momentum={momentum:.6f}"
            return -1, reason
        
        # HOLD
        reason = f"No clear signal (SMA20={sma_20:.5f}, SMA50={sma_50:.5f}, RSI={rsi:.1f})"
        return 0, reason
    
    
    def get_current_state(self):
        """
        Get current state of the processor.
        
        Returns:
            Dict with current state info
        """
        return {
            'total_bars': len(self.bars),
            'is_warmed_up': self.is_warmed_up,
            'warmup_progress': f"{len(self.bars)}/{self.warmup_period}",
            'latest_bar': self.bars[-1] if self.bars else None
        }


# Test functions
def test_stream_processor():
    """Test stream processor with sample data."""
    print("Testing StreamProcessor...")
    print("="*70)
    
    # Create processor
    processor = StreamProcessor(lookback_bars=100, ma_short=20, ma_long=50)
    
    # Generate sample historical data
    print("\nGenerating sample data...")
    dates = pd.date_range('2026-01-01', periods=60, freq='5min')
    prices = 1.17 + np.random.randn(60) * 0.001
    
    historical_bars = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        bar = {
            'date': date,
            'open': price,
            'high': price + 0.0001,
            'low': price - 0.0001,
            'close': price
        }
        historical_bars.append(bar)
    
    # Load historical bars
    processor.load_historical_bars(historical_bars)
    
    # Process a few new bars
    print("\nProcessing new bars...")
    for i in range(5):
        new_bar = {
            'date': dates[-1] + pd.Timedelta(minutes=5*(i+1)),
            'open': prices[-1] + np.random.randn() * 0.0005,
            'high': prices[-1] + 0.0001,
            'low': prices[-1] - 0.0001,
            'close': prices[-1] + np.random.randn() * 0.0005
        }
        
        result = processor.process_bar(new_bar)
        
        if result:
            print(f"\n  Bar {i+1}:")
            print(f"    Close: {result['close']:.5f}")
            print(f"    SMA20: {result['sma_20']:.5f}")
            print(f"    SMA50: {result['sma_50']:.5f}")
            print(f"    RSI: {result['rsi']:.2f}")
            print(f"    Momentum: {result['momentum']:.6f}")
            
            # Generate signal
            signal, reason = processor.generate_signal(result)
            signal_str = {1: 'BUY', -1: 'SELL', 0: 'HOLD'}[signal]
            print(f"    Signal: {signal_str} - {reason}")
    
    print("\n✓ Test complete")


if __name__ == "__main__":
    test_stream_processor()
