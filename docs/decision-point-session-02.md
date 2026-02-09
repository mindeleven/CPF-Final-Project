# Decision Point: Data Fetching Approach

**Date:** February 9, 2026  
**Context:** Session 2 data layer code complete, but IB Gateway connection via SSH tunnel fails

---

## 🎯 The Decision

**You need to choose one path before Session 3:**

---

## PATH A: Debug SSH Tunnel (Continued Troubleshooting)

### **What We'd Try:**

**1. Switch to ib-insync Library** (15-20 min)
```bash
pip uninstall ib_async
pip install ib-insync==0.9.86
# Update imports in fetch script
# Test connection
```
- **Why:** Different async implementation might handle tunnels better
- **Risk:** May require code changes if API differs

**2. SSH Tunnel Optimizations** (10-15 min)
```bash
# Try compression
ssh -C -L 4002:localhost:4002 root@157.230.113.17

# Try different cipher
ssh -c aes128-ctr -L 4002:localhost:4002 root@157.230.113.17

# Try keepalive
ssh -o ServerAliveInterval=30 -L 4002:localhost:4002 root@157.230.113.17
```
- **Why:** Reduce latency, prevent timeouts
- **Risk:** May not affect API handshake layer

**3. Increase System Buffers** (5 min)
```bash
sudo sysctl -w net.inet.tcp.sendspace=131072
sudo sysctl -w net.inet.tcp.recvspace=131072
```
- **Why:** More buffer for async data
- **Risk:** Requires sudo, temporary

**4. Event Loop Debugging** (20-30 min)
- Add verbose logging to see exact failure point
- Test with minimal ib_async script
- Monitor IB Gateway logs during handshake
- **Why:** Understand where handshake breaks
- **Risk:** Deep technical debugging

**5. Compare with Practice Project** (15 min)
- Review how practice project connected
- Check if it used tunnel or ran on server
- Compare exact connection code
- **Why:** Find what changed
- **Risk:** Practice setup might have been different

### **Total Estimated Time:** 1-3 hours

### **Success Probability:** 60-70%
- **If it works:** Local development workflow established
- **If it fails:** Lost 1-3 hours, still need to use workaround

### **When to Choose Path A:**
- ✅ You have 2-4 hours available tomorrow
- ✅ Learning SSH tunneling/debugging is valuable to you
- ✅ Local development workflow is important
- ✅ You want to understand root cause
- ✅ You're comfortable with possibility of no solution

---

## PATH B: Pragmatic Cloud Fetch (Proven Solution)

### **What We'd Do:**

**Step 1: Run fetch on cloud server** (2 min)
```bash
ssh root@157.230.113.17
cd /root
git clone https://github.com/mindeleven/CPF-Final-Project.git
cd CPF-Final-Project
pip3 install pandas numpy ib_async
python3 -m scripts.fetch_historical_data
```

**Step 2: Wait for completion** (2-5 min)
- Script will fetch all 3 timeframes
- ~15,000 total bars
- Saves to `data/historical/`

**Step 3: Copy to Mac** (1 min)
```bash
# On Mac
cd ~/CPF-Final-Project
scp -r root@157.230.113.17:/root/CPF-Final-Project/data/historical/* data/historical/
```

**Step 4: Verify and commit** (2 min)
```bash
# Test loader
python -c "from modules.data import load_all_timeframes; data = load_all_timeframes(); print({k: len(v) for k, v in data.items()})"

# Commit CSVs
git add data/historical/
git commit -m "Add historical EUR/USD data (5min, 4H, 1D)"
git push
```

### **Total Time:** 5-10 minutes

### **Success Probability:** 100%
- Already confirmed working on server
- No unknowns
- Guaranteed to have data for Session 3

### **When to Choose Path B:**
- ✅ You want to move forward quickly
- ✅ Session 3 (Indicators) is higher priority
- ✅ Local connection isn't critical (data already fetched)
- ✅ You have limited time tomorrow
- ✅ You value certainty over debugging

---

## 🤔 Considerations

### **Project Requirements (CPF)**
- ✓ "Data should come from static data files" ← Both paths satisfy this
- ✓ "Notebook should not call APIs" ← Both paths satisfy this
- ✓ "Reproducible" ← Both paths satisfy this

**The CPF requirement is met either way** - once CSVs are committed to GitHub, the notebook loads static files.

### **Grading Impact**
- **Path A:** No advantage (graders don't see how you fetched data)
- **Path B:** No disadvantage (CSVs are identical)

**Conclusion:** This decision affects your workflow, not your grade.

### **Future Data Updates**
- **Path A:** Can fetch updates locally anytime
- **Path B:** Need to SSH to server or solve tunnel later

**Impact:** Minimal - historical data rarely changes once fetched

### **Learning Value**
- **Path A:** Learn SSH tunneling, ib_async debugging, network troubleshooting
- **Path B:** Learn pragmatism, time management, workaround strategies

**Both are valuable skills!**

---

## 📊 Recommendation Matrix

| Factor | Path A (Debug) | Path B (Cloud) |
|--------|----------------|----------------|
| **Time Required** | 1-3 hours | 10 minutes |
| **Success Certainty** | 60-70% | 100% |
| **Learning Value** | High (technical) | Moderate (pragmatic) |
| **Project Progress** | Blocked if fails | Immediate |
| **Stress Level** | Medium-High | Low |
| **Future Benefit** | Local workflow | One-time solution |

---

## 🎯 My Recommendation

**If you have 2+ hours tomorrow and enjoy debugging:** → **Path A**

**If you want to keep project momentum:** → **Path B**

**Hybrid approach:**
1. Try Path A for 1 hour maximum
2. If not working, switch to Path B
3. Total time: 70 minutes worst case

---

## 📝 Decision Template

**Fill this out tomorrow before starting:**
```
Decision: [ ] Path A (Debug) [ ] Path B (Cloud) [ ] Hybrid

Reasoning:
_________________________________________________

Time available: __________ hours

Priority today: [ ] Debugging [ ] Progress

Next session time: __________
```

---

## 🔄 What Happens Next

### **If Path A:**
- Continue this chat or start fresh
- I provide detailed debugging steps
- We systematically try each solution
- Set 2-hour time limit, then switch to Path B

### **If Path B:**
- I provide exact commands for cloud fetch
- You execute and verify
- I create Specification 3 (Indicators)
- Session 3 begins

### **Either way:**
- Session 3 starts with working data
- Project continues smoothly
- No impact on final deliverable

---

**The right choice is the one that fits your time and priorities tomorrow. Both paths lead to the same destination.**

**Sleep on it, decide fresh tomorrow.** 🌙

---

**End of Decision Point Document**