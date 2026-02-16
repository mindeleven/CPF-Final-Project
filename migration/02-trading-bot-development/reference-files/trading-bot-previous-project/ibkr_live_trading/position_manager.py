"""
Position Manager Module
Handles account balance checks, position tracking, and order execution.
"""

from ib_async import *
import time


class PositionManager:
    """Manages trading positions and account balance."""
    
    def __init__(self, ib, symbol='EUR', currency='USD', contract_size=20000, logger=None):
        """
        Initialize position manager.
        
        Args:
            ib: Active IB connection
            symbol: Base currency
            currency: Quote currency
            contract_size: Size of each trade
            logger: Optional trade logger for file logging
        """
        self.ib = ib
        self.symbol = symbol
        self.currency = currency
        self.contract_size = contract_size
        self.logger = logger
        
        # Create forex contract
        self.contract = Forex(symbol + currency)
        
        # Position tracking
        self.current_position = 0  # 0=FLAT, 1=LONG, -1=SHORT
        self.entry_price = None
        self.position_size = 0
        
        print(f"\n✓ Position Manager initialized")
        print(f"  Instrument: {symbol}/{currency}")
        print(f"  Contract size: {contract_size:,} {symbol}")
    
    
    def check_usd_balance(self, min_balance=25000):
        """
        Check if account has sufficient USD balance.
        
        Args:
            min_balance: Minimum required USD balance
        
        Returns:
            Tuple of (has_sufficient_funds, current_balance)
        """
        print(f"\n💰 Checking USD balance...")
        
        # Request account summary
        account_values = self.ib.accountSummary()
        
        # Find USD balance
        usd_balance = None
        
        for item in account_values:
            # Try TotalCashBalance first (more reliable for USD)
            if item.tag == 'TotalCashBalance' and item.currency == 'USD':
                usd_balance = float(item.value)
                break
            # Fallback to CashBalance
            elif item.tag == 'CashBalance' and item.currency == 'USD':
                usd_balance = float(item.value)
                break

        if usd_balance is None:
            print(f"  ⚠ Could not determine USD balance")
            return False, 0
        
        has_sufficient = usd_balance >= min_balance
        
        print(f"  Current USD balance: ${usd_balance:,.2f}")
        print(f"  Required: ${min_balance:,.2f}")
        print(f"  Status: {'✓ Sufficient' if has_sufficient else '✗ Insufficient'}")
        
        return has_sufficient, usd_balance
    
    
    def get_current_position(self):
        """
        Get current position from IB.
        
        Returns:
            Position: 1=LONG, -1=SHORT, 0=FLAT
        """
        print(f"\n📊 Checking current position...")
        if self.logger:
            self.logger.log_info(f"get_current_position() called - current entry_price: {self.entry_price}")
        
        positions = self.ib.positions()
        
        for pos in positions:
            if pos.contract.symbol == self.symbol and pos.contract.currency == self.currency:
                size = pos.position
                avg_cost = pos.avgCost
                
                if self.logger:
                    self.logger.log_info(f"IB position found: size={size}, avgCost={avg_cost:.5f}, our entry={self.entry_price}")
                
                if size > 0:
                    self.current_position = 1
                    self.position_size = size
                    # Only update entry_price if we don't have one
                    if self.entry_price is None:
                        self.entry_price = avg_cost
                        print(f"  Position: LONG {size:,} {self.symbol} @ {avg_cost:.5f}")
                        if self.logger:
                            self.logger.log_info(f"entry_price set to IB avgCost: {avg_cost:.5f}")
                    else:
                        print(f"  Position: LONG {size:,} {self.symbol} @ {self.entry_price:.5f} (IB reports: {avg_cost:.5f})")
                        if self.logger:
                            self.logger.log_info(f"Keeping our entry_price: {self.entry_price:.5f} (IB avgCost: {avg_cost:.5f})")
                    return 1
                elif size < 0:
                    self.current_position = -1
                    self.position_size = abs(size)
                    # Only update entry_price if we don't have one
                    if self.entry_price is None:
                        self.entry_price = avg_cost
                        print(f"  Position: SHORT {abs(size):,} {self.symbol} @ {avg_cost:.5f}")
                        if self.logger:
                            self.logger.log_info(f"entry_price set to IB avgCost: {avg_cost:.5f}")
                    else:
                        print(f"  Position: SHORT {abs(size):,} {self.symbol} @ {self.entry_price:.5f} (IB reports: {avg_cost:.5f})")
                        if self.logger:
                            self.logger.log_info(f"Keeping our entry_price: {self.entry_price:.5f} (IB avgCost: {avg_cost:.5f})")
                    return -1
        
        # No position found
        self.current_position = 0
        self.position_size = 0
        self.entry_price = None
        print(f"  Position: FLAT (no open positions)")
        if self.logger:
            self.logger.log_info("No position found - entry_price set to None")
        return 0
    
    
    def close_position(self):
        """
        Close current position if any exists.
        
        Returns:
            Tuple of (success, pnl)
        """
        current = self.get_current_position()
        
        if current == 0:
            print(f"  ✓ No position to close")
            return True, 0.0
        
        print(f"\n🔄 Closing position...")

         # Determine order action
        if current == 1:
            # Close LONG by selling
            action = 'SELL'
        else:
            # Close SHORT by buying
            action = 'BUY'
        
        # Create market order to close
        order = MarketOrder(action, self.position_size)
        order.tif = 'GTC'  # Required for 24/5 forex markets
        
        print(f"  Action: {action} {self.position_size:,} {self.symbol}/{self.currency}")
        
        # Place order
        trade = self.ib.placeOrder(self.contract, order)
        
        # Wait for fill
        timeout = 30  # seconds
        elapsed = 0
        while not trade.isDone() and elapsed < timeout:
            self.ib.sleep(0.5)
            elapsed += 0.5
        
        if trade.isDone():
            fill_price = trade.orderStatus.avgFillPrice
            print(f"  ✓ Position closed at {fill_price:.5f}")
            
            # Calculate P&L
            if self.entry_price and fill_price > 0:
                if self.logger:
                    self.logger.log_info(f"P&L calculation: entry={self.entry_price:.5f}, exit={fill_price:.5f}, size={self.position_size}")
                
                if current == 1:
                    # LONG position
                    pnl = (fill_price - self.entry_price) * self.position_size
                else:
                    # SHORT position
                    pnl = (self.entry_price - fill_price) * self.position_size
                
                print(f"  P&L: ${pnl:+,.2f}")
                if self.logger:
                    self.logger.log_info(f"Calculated P&L: ${pnl:+,.2f}")
                
                # Reset position tracking
                self.current_position = 0
                self.position_size = 0
                self.entry_price = None
                
                return True, pnl
            else:
                # Reset position tracking
                self.current_position = 0
                self.position_size = 0
                self.entry_price = None
                
                return True, 0.0
        else:
            print(f"  ✗ Failed to close position (timeout)")
            return False, 0.0
    
    
    def execute_trade(self, signal, current_price=None):
        """
        Execute trade based on signal.
        
        Args:
            signal: 1=BUY, -1=SELL, 0=HOLD
            current_price: Current market price (for logging)
        
        Returns:
            Tuple of (success, action_taken, fill_price, close_pnl)
        """
        if signal == 0:
            # HOLD - no action
            return True, 'HOLD', None, 0.0
    
        # Check if we need to trade
        if signal == self.current_position:
            # Already in desired position
            return True, 'HOLD', None, 0.0
        
        print(f"\n🔔 EXECUTING TRADE")
        print(f"  Signal: {'BUY' if signal == 1 else 'SELL'}")
        print(f"  Current position: {self._position_str(self.current_position)}")
        print(f"  Target position: {self._position_str(signal)}")
        
        # If we have a position, close it first
        close_pnl = 0.0
        if self.current_position != 0:
            print(f"\n  Step 1: Closing current position...")
            success, close_pnl = self.close_position()
            if not success:
                return False, 'ERROR', None, 0.0
            # Wait a moment for settlement
            self.ib.sleep(1)
        
        # Now open new position
        print(f"\n  Step 2: Opening new position...")
        
        if signal == 1:
            action = 'BUY'
        else:
            action = 'SELL'
        
        # Create market order
        order = MarketOrder(action, self.contract_size)
        order.tif = 'GTC'  # Required for 24/5 forex markets
        
        print(f"  Placing order: {action} {self.contract_size:,} {self.symbol}/{self.currency}")
        
        # Place order
        trade = self.ib.placeOrder(self.contract, order)
        
        # Wait for fill
        timeout = 30  # seconds
        elapsed = 0
        while not trade.isDone() and elapsed < timeout:
            self.ib.sleep(0.5)
            elapsed += 0.5
        
        if trade.isDone():
            fill_price = trade.orderStatus.avgFillPrice
            
            print(f"  ✓ Order filled at {fill_price:.5f}")
            
            if current_price:
                slippage_pips = abs(fill_price - current_price) * 10000
                print(f"  Slippage: {slippage_pips:.1f} pips")
            
            # Update position tracking
            self.current_position = signal
            self.position_size = self.contract_size
            self.entry_price = fill_price
            print(f"  Entry price recorded: {self.entry_price:.5f}")
            if self.logger:
                self.logger.log_info(f"New position opened: entry_price set to {self.entry_price:.5f}")
            
            return True, action, fill_price, close_pnl
        else:
            print(f"  ✗ Order failed or timed out")
            return False, 'ERROR', None, 0.0
    
    
    def _position_str(self, position):
        """Convert position code to string."""
        if position == 1:
            return 'LONG'
        elif position == -1:
            return 'SHORT'
        else:
            return 'FLAT'
    
    
    def get_position_pnl(self, current_price):
        """
        Calculate current position P&L.
        
        Args:
            current_price: Current market price
        
        Returns:
            Current P&L in USD (0 if flat)
        """
        if self.current_position == 0 or not self.entry_price:
            return 0.0
        
        if self.current_position == 1:
            # LONG position
            pnl = (current_price - self.entry_price) * self.position_size
        else:
            # SHORT position
            pnl = (self.entry_price - current_price) * self.position_size
        
        return pnl


# Test functions
def test_balance_check(ib):
    """Test USD balance check."""
    pm = PositionManager(ib)
    has_funds, balance = pm.check_usd_balance(min_balance=25000)
    return has_funds


def test_position_check(ib):
    """Test position retrieval."""
    pm = PositionManager(ib)
    position = pm.get_current_position()
    return position


def test_close_position(ib):
    """Test closing open position."""
    pm = PositionManager(ib)
    success, pnl = pm.close_position()
    return success


if __name__ == "__main__":
    print("Position Manager Test")
    print("="*70)
    print("\nThis module should be imported, not run directly.")
    print("Use live_trader.py to run the live trading bot.")
