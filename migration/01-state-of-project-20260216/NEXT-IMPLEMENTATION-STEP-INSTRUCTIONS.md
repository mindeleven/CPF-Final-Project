# Instructions for Starting Next Implemetaion Step - Session 7E
**Date:** February 13, 2026  
**Current Status:** Session 7D complete, ready for Session 7E implementation  
**Context Window:** 4 comprehensive handoff documents created

---

Continue CPF Final Project - Session 7E Implementation

PROJECT CONTEXT:
I'm working on my CPF Final Project - an automated EUR/USD forex trading system. 
Sessions 1-7D are complete. The bot is deployed and functional but has 6 critical 
bugs discovered during a 4-hour live test.

CURRENT STATUS:
- Budget: ~ $10.00 used of $25.00 (will get stocked up)
- Timeline: 6 weeks to deadline (March 31, 2026)
- Deployment: DigitalOcean droplet 157.230.113.17
- Live test completed: 4 hours, 4 trades, bugs documented

IMMEDIATE TASK:
Implement Session 7E fixes for critical bugs:
1. Double position bug (opens -40K instead of -20K)
2. Entry price not set (P&L shows $0.00)
3. EUR balance check missing (Error 201)
4. Wrong timeframe (60s prices instead of 5min bars)
5. No historical warmup (70 min wait before signals)
6. Order TIF warnings (Error 10349)

HANDOFF DOCUMENTS:
Please read these files under migration/02-trading-bot-development I've created:
- project-progress.md (overall status)
- session-7E-specification.md (detailed fixes)
- deployment-status.md (current setup)
- critical-bugs-analysis.md (bug details)

These are in migration/02-trading-bot-development.

APPROACH FOR SESSION 7E:
1. Review handoff documents
2. Fix critical bugs (Priority 1) first
3. Test locally via SSH tunnel (NOT Docker initially)
4. Once stable, manual deployment to Docker will be my part, not the part of Claude Code
5. Run 1-hour validation test
6. I will run a 8-hour production test on the droplet after maunual deployment.

Under no circumstances Claude Code will generate a docker container or connect to the DigitalOcean.

Let's start by reviewing the handoff documents and confirming the implementation 
priority order.

### **Reference Files (From Previous Project):**
The reference project can be found under migration/02-trading-bot-development/reference-files/trading-bot-previous-project
The files that had a working trading bot implementation with simpler code are:
- `position_manager.py` (old working bot)
- `live_trader.py` (old working bot)
Both files avoided pitfalls which the current trading system does have.

They show correct patterns for:
- Order TIF = 'GTC'
- Entry price tracking
- Wait for trade.isDone()
- EUR balance check (adapt from USD)

### **Current Files to Provide:**
I had made manual fixes in two files on the server. These two files can be used as a reference and are stored under migration/02-trading-bot-development/reference-files/manual-modification-live-trading
- trading_bot.py (needs fixes)
- config_live.py (needs updates)

---

### 📄 Specification Documents Available
Specification documents which are documenting each planning stage of implementation are available under docs/specifications

### 📄 Handoff Documents Available
Handoff documents which are documenting each step of the successful implementation of a specification are available under docs/handoffs

### **1. project-progress.md** (~4K tokens)
Available under docs/
And available under migration/02-trading-bot-development
(docs/ will be part of the final deliverable, migration/ will be removed from the final deliverable)
Complete project status from Sessions 1-7D:
- What's been completed
- Budget tracking ~ $ 10.00 remaining, will be stocked up for remaining work
- Timeline (6 weeks to deadline)
- Academic justification points
- 4-hour live test results

### **2. session-7E-specification.md** (~6K tokens)
Available under docs/specifications
And available under migration/02-trading-bot-development
(docs/ will be part of the final deliverable, migration/ will be removed from the final deliverable)
Detailed implementation plan:
- 10 prioritized fixes (4 critical, 4 important, 2 nice-to-have)
- Code examples for each fix
- Testing strategy
- Implementation checklist
- Budget estimate ($2-3)

### **3. deployment-status.md** (~3K tokens)
Available under migration/02-trading-bot-development
Current deployment configuration:
- Server details (157.230.113.17)
- Directory structure
- Docker setup
- IB Gateway configuration
- Local testing options (SSH tunnel)
- Troubleshooting guide

### **4. critical-bugs-analysis.md** (~4K tokens)
Available under migration/02-trading-bot-development
Deep dive on 6 bugs from 4-hour test:
- Double position bug (CRITICAL)
- Entry price not set (CRITICAL)
- Order TIF error (WARNING)
- Currency leverage error (CRITICAL)
- Wrong timeframe data (CRITICAL)
- No historical warmup (WARNING)
- Detailed root causes and fixes

---

## 🔄 Workflow for Session 7E

### **Phase 1: Review & Plan (15 minutes)**
1. Claude reads 4 handoff documents
2. Confirms understanding of bugs
3. Discusses priority order with you
4. Confirms testing approach (local first)

### **Phase 2: Quick Wins (30 minutes)**
Fix simple issues first to build momentum:
1. Order TIF → 'GTC' (5 minutes, 1 line per order)
2. Logfile naming (10 minutes)
3. Entry price tracking (15 minutes)

### **Phase 3: Critical Fixes (90 minutes)**
1. Double position bug (30 minutes)
   - Wait for trade.isDone()
   - Add 1-second settlement delay
   - Test with position flip signal

2. EUR balance check (30 minutes)
   - Implement check_eur_balance()
   - Call on startup and before trades
   - Set INITIAL_CAPITAL from balance

3. Historical warmup (30 minutes)
   - Implement load_historical_warmup()
   - Fetch 70+ bars on startup
   - Verify immediate signal generation

### **Phase 4: Data Architecture (60 minutes)**
1. Replace spot price with 5-minute bars
   - Change fetch_latest_price() to fetch_latest_bar()
   - Handle OHLC data
   - Update to 5-minute frequency

### **Phase 5: Local Testing (60 minutes)**
1. Setup SSH tunnel
2. Run bot locally
3. Verify all fixes work
4. Check for new issues

### **Phase 6: Docker Deployment (30 minutes)**
1. Deploy to Docker
2. Run 1-hour validation
3. Check logs
4. Run 8-hour test if successful

**Total Estimated Time:** 4-5 hours coding + 9 hours testing

---

## 🚨 Important Reminders

### **Testing First**
- Claude Code does NOT deploy to Docker
- Test locally via SSH tunnel first
- Much faster iteration
- Easier debugging

### **Priority Order**
Start with Priority 1 (Critical) fixes:
1. Order TIF (quick win)
2. Entry price (moderate)
3. Double position (critical, complex)
4. EUR balance check (moderate)

Then Priority 2:
5. Historical warmup
6. 5-minute bars

### **Reference Old Bot**
The old `position_manager.py` has correct patterns:
- Lines 169, 260: `order.tif = 'GTC'`
- Lines 177-182, 268-273: Wait for `trade.isDone()`
- Line 251: Settlement `self.ib.sleep(1)`
- Line 297: `self.entry_price = fill_price`
- Lines 102-126: Entry price preservation
- Lines 42-70: Balance check (adapt from USD to EUR)

---

## 📱 Access Information

### **IB Gateway**
- Port: 4002 (localhost on droplet)
- Paper trading EUR account

### **SSH Tunnel for Local Testing**
The SSH tunnel is open and can be used for local testing. If there are connection issues, abort testrun and report the error.

---

## 🎓 Academic Considerations

When documenting Session 7E for academic submission:

### **Learning Outcomes**
- Discovered async/sync architecture considerations
- Learned importance of early deployment testing
- Understood broker-specific constraints (TIF, currency leverage)
- Experienced real-world vs backtest differences

### **Methodology Justification**
"Iterative deployment testing revealed issues invisible during specification and code review. The rapid iteration cycle (deploy → diagnose → fix → redeploy) prevents accumulation of hidden issues. Local testing via SSH tunnel enabled faster debugging than Docker rebuilds."

### **Risk Management Discussion**
"Double position bug demonstrates importance of order confirmation before state changes. IBKR's one-position-per-pair constraint requires careful order sequencing with settlement delays. Position reconciliation after reconnection prevents state drift but doesn't prevent concurrent order execution."

## ✅ Success Criteria for Session 7E

Session 7E is complete when:
1. ✅ No double position errors in 4+ hour test
2. ✅ EUR balance checked before trading
3. ✅ P&L updates correctly during positions
4. ✅ No Order TIF warnings
5. ✅ Bot uses 5-minute bars (not 60s prices)
6. ✅ Signals generate within 5 minutes of startup
7. ✅ 8-hour test completes without errors
8. ✅ Logs are clearly named and accessible

