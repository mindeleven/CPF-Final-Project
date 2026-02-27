# IB Gateway Currency Conversion Guide

**Purpose:** Convert EUR to USD in paper trading account to enable bidirectional EUR/USD forex trading

**Context:** The live trading bot trades EUR.USD forex pairs, which requires BOTH currencies:
- **BUY EUR.USD** = buy EUR base currency using USD quote currency (requires USD balance)
- **SELL EUR.USD** = sell EUR base currency receiving USD quote currency (requires EUR balance)

**Current problem:** Paper trading account is EUR-denominated (~1M EUR, insufficient USD), causing Error 201 rejections when bot attempts BUY orders.

---

## Prerequisites

- Access to IB Gateway Web Portal or TWS (Trader Workstation)
- Paper trading account credentials
- Account must have EUR balance available for conversion

---

## Method 1: IB Gateway Web Portal (Recommended)

### Step 1: Log into IB Account Management
1. Navigate to: https://www.interactivebrokers.com/portal
2. Log in with paper trading account credentials
3. Select "Paper Trading" account mode

### Step 2: Access Currency Converter
1. Click on "Transfer & Pay" in top menu
2. Select "Currency Converter" or "Convert Currency"
3. Or navigate directly to: Account Management → Transfer & Pay → Currency Converter

### Step 3: Execute Currency Conversion
1. **From Currency:** EUR
2. **To Currency:** USD
3. **Amount:** 500,000 EUR (recommended for balanced holdings)
4. Review conversion rate (should be ~1.18 EUR/USD, giving ~590,000 USD)
5. Click "Convert" or "Submit"
6. Confirm the transaction

### Step 4: Verify Conversion
1. Navigate to "Account" → "Account Value"
2. Check "Cash Balances" section
3. Verify you now have:
   - ~500,000 EUR remaining
   - ~590,000 USD available

---

## Method 2: TWS (Trader Workstation)

### Step 1: Open Currency Converter
1. Launch TWS with paper trading account
2. Click "Account" menu → "Currency Converter"
3. Or use shortcut: Press Ctrl+Shift+C (Windows/Linux) or Cmd+Shift+C (Mac)

### Step 2: Configure Conversion
1. In the Currency Converter window:
   - **From:** EUR
   - **To:** USD
   - **Amount:** 500,000
2. Click "Preview" to see estimated conversion
3. Review exchange rate and resulting USD amount

### Step 3: Submit Conversion
1. Click "Submit" to execute
2. Check "Order Status" window for confirmation
3. Wait for conversion to complete (typically instant for paper trading)

### Step 4: Verify in Account Window
1. Open "Account" window (Ctrl+U or Cmd+U)
2. Check "Market Value" section
3. Expand "Cash" to see EUR and USD balances

---

## Method 3: Manual Forex Trade (Alternative)

If currency converter is unavailable, you can execute a manual forex trade:

### Step 1: Create EUR.USD Contract
1. In TWS, go to "Symbol" search
2. Enter: **EUR.USD**
3. Select "Forex" as security type
4. Exchange: **IDEALPRO**

### Step 2: Place SELL Order
1. Right-click on EUR.USD contract
2. Select "Sell" (selling EUR to receive USD)
3. Order type: **Market**
4. Quantity: **500,000** (EUR amount to convert)
5. Time in Force: **GTC**
6. Submit order

### Step 3: Verify Execution
1. Check "Trades" window for fill confirmation
2. Verify entry price (should be ~1.18)
3. Check account balance for USD increase

**Note:** This method creates a forex trade entry in your history, unlike the currency converter which is a pure transfer.

---

## Recommended Conversion Amount

**Recommended:** Convert **500,000 EUR** to USD

**Rationale:**
- Account has ~1,000,000 EUR total
- Bot trades 20,000 EUR position size per trade
- Expected ~24,000 USD needed per BUY trade (at 1.18 rate)
- 500K EUR → ~590K USD gives ~24 BUY trades worth of buffer
- Leaves 500K EUR for ~25 SELL trades worth of buffer
- Provides balanced capacity for bidirectional trading

**Alternative amounts:**
- **Conservative:** 400,000 EUR → ~472,000 USD (maintains higher EUR reserve)
- **Aggressive:** 600,000 EUR → ~708,000 USD (more USD capacity for BUY-heavy strategies)

---

## Verification Checklist

After conversion, verify:

- [ ] EUR balance reduced by conversion amount
- [ ] USD balance increased by ~1.18× conversion amount
- [ ] Total account value unchanged (excluding small spread cost)
- [ ] No error messages or failed transactions
- [ ] Both currencies show in "Cash Balances" section

---

## Timeline for 4H Test (March 2, 2026)

**Deadline:** Sunday, March 1, 2026 (before market open Monday)

**Recommended schedule:**
1. **Friday evening (Feb 27):** Review this guide
2. **Saturday (Feb 28):** Execute currency conversion
3. **Sunday (Mar 1):** Verify balances and test bot startup (dry run)
4. **Monday (Mar 2):** Launch 4H test with balanced currency holdings

---

## Troubleshooting

### Issue: Currency Converter not available in paper trading
**Solution:** Use Method 3 (manual forex trade via SELL EUR.USD order)

### Issue: "Insufficient funds" error
**Solution:** Reduce conversion amount. Check current EUR balance first.

### Issue: Conversion shows 0 USD received
**Solution:** Ensure "To Currency" is set to USD (not another currency)

### Issue: Paper trading account doesn't show currency converter
**Solution:** Paper trading accounts may have limited features. Contact IB support or use manual forex trade method.

---

## Post-Conversion: Bot Configuration

**No code changes needed** — currency conversion is account-level, not bot-level.

The bot will automatically detect and use available USD for BUY orders and EUR for SELL orders. The existing `check_eur_balance()` will still work for SELL orders. Error 201 should no longer occur for BUY orders.

---

## Long-Term Code Fix (Optional)

For future bot versions, implement direction-aware balance checking:

```python
def check_balance_for_order(self, direction: int) -> bool:
    """
    Check if account has sufficient balance for the order direction.

    Args:
        direction: 1 for BUY (needs USD), -1 for SELL (needs EUR)

    Returns:
        True if sufficient balance, False otherwise
    """
    if direction == 1:  # BUY signal
        # Need USD to buy EUR
        return self._check_usd_balance()
    elif direction == -1:  # SELL signal
        # Need EUR to sell for USD
        return self._check_eur_balance()
    return False
```

This would make the bot currency-aware and prevent Error 201 without manual conversions.

---

**Document created:** February 27, 2026
**For:** CPF Final Project — Session 09 Error 201 Resolution
**Next action:** Execute currency conversion this weekend before Monday's 4H test
