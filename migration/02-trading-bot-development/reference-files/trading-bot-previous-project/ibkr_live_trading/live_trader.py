"""
Live Trading Bot
Main orchestrator for live paper trading with Interactive Brokers.
"""

import sys
import time
from datetime import datetime, timedelta
from ib_async import *
import pandas as pd
import signal as sys_signal

# Import our modules
from config_live import *
from position_manager import PositionManager
from stream_processor import StreamProcessor
from trade_logger import TradeLogger


class LiveTrader:
    """Main live trading bot."""
    
    def __init__(self):
        """Initialize live trader."""
        self.ib = None
        self.position_manager = None
        self.stream_processor = None
        self.logger = None
        
        self.is_running = False
        self.start_time = None
        self.end_time = None
        
        # Signal handlers for graceful shutdown
        sys_signal.signal(sys_signal.SIGINT, self._signal_handler)
        sys_signal.signal(sys_signal.SIGTERM, self._signal_handler)
    
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\n\n🛑 Shutdown signal received...")
        self.stop("User interrupt")
    
    
    def start(self):
        """Start the live trading bot."""
        print("\n" + "="*70)
        print("  EUR/USD LIVE PAPER TRADING BOT")
        print("="*70)
        print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Print configuration
        print_config()
        
        # Calculate run duration
        run_seconds = get_run_duration_seconds()
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(seconds=run_seconds)
        
        print(f"\n⏱️  Bot will run until: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   (Duration: {RUN_DURATION})\n")
        
        # Initialize components
        if not self._initialize():
            print("\n✗ Initialization failed")
            return False
        
        # Start trading loop
        self.is_running = True
        self._trading_loop()
        
        return True
    
    
    def _initialize(self):
        """Initialize all components."""
        print("\n" + "="*70)
        print("  INITIALIZATION")
        print("="*70)
        
        # 1. Initialize logger
        print("\n📝 Step 1: Initialize Logger")
        self.logger = TradeLogger(
            log_dir=LOG_DIR,
            trade_log_name=TRADE_LOG_FILE,
            detail_log_name=DETAIL_LOG_FILE
        )
        
        # 2. Connect to IB
        print("\n📡 Step 2: Connect to IB Gateway")
        try:
            util.startLoop()
            self.ib = IB()
            self.ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID)
            
            if not self.ib.isConnected():
                self.logger.log_error("Failed to connect to IB Gateway")
                return False
            
            self.logger.log_info(f"Connected to IB Gateway at {IB_HOST}:{IB_PORT}")
            
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False
        
        # 3. Initialize Position Manager
        print("\n💼 Step 3: Initialize Position Manager")
        self.position_manager = PositionManager(
            self.ib,
            symbol=SYMBOL,
            currency=CURRENCY,
            contract_size=CONTRACT_SIZE,
            logger=self.logger
        )
        
        # 4. Check USD balance
        print("\n💰 Step 4: Check Account Balance")
        has_funds, balance = self.position_manager.check_usd_balance(MIN_USD_BALANCE)
        
        if not has_funds:
            self.logger.log_error(f"Insufficient funds: ${balance:,.2f} < ${MIN_USD_BALANCE:,.2f}")
            return False
        
        self.logger.log_info(f"Account balance: ${balance:,.2f}")
        
        # 5. Close any open positions (clean slate)
        print("\n🧹 Step 5: Close Any Open Positions (Clean Slate)")
        # success, close_pnl = self.position_manager.close_position()
        # if not success:
        #     self.logger.log_warning("Failed to close position - continuing anyway")  
        print("\n🧹 Step 5: Close Any Open Positions (Clean Slate)")
        success, close_pnl = self.position_manager.close_position()
        if close_pnl != 0:
            self.logger.log_info(f"Closed pre-existing position: P&L = ${close_pnl:+,.2f}")
        if not success:
            self.logger.log_warning("Failed to close position - continuing anyway")

        # 6. Initialize Stream Processor
        print("\n📊 Step 6: Initialize Stream Processor")
        self.stream_processor = StreamProcessor(
            lookback_bars=LOOKBACK_BARS,
            ma_short=MA_SHORT_PERIOD,
            ma_long=MA_LONG_PERIOD,
            rsi_period=RSI_PERIOD,
            momentum_period=MOMENTUM_PERIOD
        )
        
        # 7. Fetch historical bars for warmup
        print("\n📈 Step 7: Fetch Historical Bars for Warmup")
        contract = Forex(SYMBOL + CURRENCY)
        
        try:
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr='1 D',  # 1 day of history
                barSizeSetting=BAR_SIZE,
                whatToShow='MIDPOINT',
                useRTH=False,
                formatDate=1
            )
            
            # Convert to list of dicts
            historical_bars = []
            for bar in bars:
                historical_bars.append({
                    'date': bar.date,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close
                })
            
            self.stream_processor.load_historical_bars(historical_bars)
            self.logger.log_info(f"Loaded {len(historical_bars)} historical bars for warmup")
            
        except Exception as e:
            self.logger.log_error(f"Failed to fetch historical data: {e}")
            return False
        
        # 8. Subscribe to real-time bars
        print("\n📡 Step 8: Subscribe to Real-Time Bars")
        try:
            self.bars_subscription = self.ib.reqRealTimeBars(
                contract,
                barSize=5,  # 5 seconds
                whatToShow='MIDPOINT',
                useRTH=False
            )
            
            self.logger.log_info(f"Subscribed to real-time {BAR_SIZE} bars")
            
        except Exception as e:
            self.logger.log_error(f"Failed to subscribe to real-time bars: {e}")
            return False
        
        print("\n" + "="*70)
        print("  ✓ INITIALIZATION COMPLETE")
        print("="*70)
        
        return True
    
    
    def _trading_loop(self):
        """Main trading loop."""
        self.logger.log_info("="*70)
        self.logger.log_info("TRADING LOOP STARTED")
        self.logger.log_info("="*70)
        
        print("\n🤖 Trading bot is now LIVE...")
        print("   Press CTRL+C to stop\n")
        
        last_bar_time = None
        reconnect_attempts = 0
        max_reconnect_attempts = 5
        
        try:
            while self.is_running:
                # Check if run duration exceeded
                if datetime.now() >= self.end_time:
                    self.logger.log_info(f"Run duration ({RUN_DURATION}) reached")
                    break
                
                try:
                    # Process pending IB events
                    self.ib.sleep(1)
                    
                    # Check connection
                    if not self.ib.isConnected():
                        raise ConnectionError("IB Gateway disconnected")
                    
                    # Reset reconnect counter on successful iteration
                    reconnect_attempts = 0
                    
                    # Check for new 5-minute bar
                    bars = self.bars_subscription
                    
                    if bars and len(bars) > 0:
                        latest_bar = bars[-1]
                        bar_time = latest_bar.time
                        
                        # Only process if it's a new bar
                        if bar_time != last_bar_time:
                            last_bar_time = bar_time
                            
                            # Convert to dict
                            bar_dict = {
                                'date': bar_time,
                                'open': latest_bar.open_,
                                'high': latest_bar.high,
                                'low': latest_bar.low,
                                'close': latest_bar.close
                            }
                            
                            # Process bar
                            self._process_new_bar(bar_dict)
                    
                    # Show progress
                    remaining = (self.end_time - datetime.now()).total_seconds()
                    if int(remaining) % 60 == 0:  # Every minute
                        mins_left = int(remaining / 60)
                        print(f"⏱️  {mins_left} minutes remaining...")
                
                except (ConnectionError, OSError) as conn_error:
                    # Connection lost - try to reconnect
                    reconnect_attempts += 1
                    
                    if reconnect_attempts > max_reconnect_attempts:
                        self.logger.log_error(f"Max reconnect attempts ({max_reconnect_attempts}) reached")
                        raise
                    
                    self.logger.log_warning(f"Connection lost: {conn_error}")
                    self.logger.log_info(f"Attempting to reconnect ({reconnect_attempts}/{max_reconnect_attempts})...")
                    print(f"\n⚠️  Connection lost! Reconnecting... (attempt {reconnect_attempts}/{max_reconnect_attempts})")
                    
                    # Try to reconnect
                    if self._reconnect():
                        self.logger.log_info("Reconnection successful - resuming trading")
                        print("✓ Reconnected successfully!\n")
                    else:
                        self.logger.log_error("Reconnection failed")
                        # Wait a bit before retrying
                        time.sleep(5)
        
        except KeyboardInterrupt:
            self.logger.log_info("Keyboard interrupt received")
            raise
        except Exception as e:
            self.logger.log_error(f"Error in trading loop: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.stop("Run duration complete")
    
    
    def _reconnect(self):
        """
        Attempt to reconnect to IB Gateway.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Disconnect if still connected
            if self.ib.isConnected():
                self.ib.disconnect()
            
            # Wait a moment
            time.sleep(2)
            
            # Reconnect
            self.ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID)
            
            if not self.ib.isConnected():
                return False
            
            # Resubscribe to real-time bars
            contract = Forex(SYMBOL + CURRENCY)
            self.bars_subscription = self.ib.reqRealTimeBars(
                contract,
                barSize=5,
                whatToShow='MIDPOINT',
                useRTH=False
            )
            
            return True
            
        except Exception as e:
            self.logger.log_error(f"Reconnection error: {e}")
            return False
    
    
    def _process_new_bar(self, bar):
        """
        Process a new 5-minute bar.
        
        Args:
            bar: Dict with bar data
        """
        # Process bar through stream processor
        result = self.stream_processor.process_bar(bar)
        
        if result is None:
            # Still warming up
            return
        
        # Log bar to console if enabled
        if LOG_BARS_TO_CONSOLE:
            print(f"\n📊 New Bar: {bar['date']}")
            print(f"   Close: {bar['close']:.5f} | SMA20: {result['sma_20']:.5f} | "
                  f"SMA50: {result['sma_50']:.5f} | RSI: {result['rsi']:.1f}")
        
        # Log to file
        self.logger.log_bar(bar, result)
        
        # Generate signal
        signal, reason = self.stream_processor.generate_signal(
            result,
            rsi_neutral_low=RSI_NEUTRAL_LOW,
            rsi_neutral_high=RSI_NEUTRAL_HIGH,
            rsi_buy_threshold=RSI_BUY_THRESHOLD,
            rsi_sell_threshold=RSI_SELL_THRESHOLD,
            momentum_buy_threshold=MOMENTUM_BUY_THRESHOLD,
            momentum_sell_threshold=MOMENTUM_SELL_THRESHOLD
        )
        
        signal_type = {1: 'BUY', -1: 'SELL', 0: 'HOLD'}[signal]
        
        # Log signal
        self.logger.log_signal(signal, signal_type, reason)
        
        if signal != 0:
            print(f"   🎯 Signal: {signal_type} - {reason}")
        
        # Execute trade if signal is not HOLD
        if signal != 0:
            success, action, fill_price, close_pnl = self.position_manager.execute_trade(
                signal,
                current_price=bar['close']
            )
            
            if success and action != 'HOLD':
                # Use the P&L from closing previous position
                trade_pnl = close_pnl
                
                # Log the trade
                position_str = {1: 'LONG', -1: 'SHORT', 0: 'FLAT'}[signal]
                
                self.logger.log_trade(
                    action=action,
                    position=position_str,
                    quantity=CONTRACT_SIZE,
                    price=fill_price,
                    bar_time=bar['date'],
                    indicators=result,
                    signal=signal,
                    reason=reason,
                    slippage_pips=0.0,
                    trade_pnl=trade_pnl
                )
    
    
    def stop(self, reason="Normal shutdown"):
        """
        Stop the trading bot.
        
        Args:
            reason: Reason for stopping
        """
        if not self.is_running:
            return
        
        self.is_running = False
        
        print("\n" + "="*70)
        print(f"  SHUTTING DOWN: {reason}")
        print("="*70)
        
        # Close positions if configured
        if CLOSE_POSITIONS_ON_EXIT and self.position_manager:
            print("\n🧹 Closing open positions...")
            self.position_manager.close_position()
        
        # Save final summary
        if self.logger:
            print("\n📊 Saving final summary...")
            summary = self.logger.get_trade_summary()
            
            print(f"\n📈 TRADING SESSION SUMMARY:")
            print(f"   Total Trades: {summary['total_trades']}")
            print(f"   Win Rate: {summary['win_rate']*100:.1f}%")
            print(f"   Total P&L: ${summary['total_pnl']:+,.2f}")
            
            self.logger.save_final_summary()
            self.logger.log_shutdown(reason)
        
        # Disconnect from IB
        if self.ib and self.ib.isConnected():
            print("\n📡 Disconnecting from IB Gateway...")
            self.ib.disconnect()
        
        print("\n✓ Shutdown complete")
        print(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


def main():
    """Main entry point."""
    trader = LiveTrader()
    
    try:
        trader.start()
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt received")
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if trader.is_running:
            trader.stop("Unexpected exit")


if __name__ == "__main__":
    main()
