# Deployment Status - Current Configuration
**Date:** February 13, 2026  
**Status:** Deployed and functional, but needs Session 7E fixes  
**Environment:** DigitalOcean Droplet + Docker

---

## 🖥️ Server Configuration

### **DigitalOcean Droplet**
- **IP Address:** 157.230.113.17
- **OS:** Ubuntu 22.04.5 LTS
- **Kernel:** 5.15.0-168-generic x86_64
- **Memory:** 43% usage
- **Disk:** 24.9% of 48.27GB used
- **Access:** SSH with root user

```bash
# Connect
ssh root@157.230.113.17

# System info
uname -a
# Linux ib-gateway-server 5.15.0-168-generic #176-Ubuntu SMP...
```

---

## 📂 Directory Structure

```
/root/trading_bot/
├── deployment/
│   ├── trading_bot.py              # Main bot script (NEEDS FIXES)
│   ├── config_live.py              # Configuration parameters
│   ├── Dockerfile                  # Container definition
│   ├── requirements.txt            # Python dependencies
│   ├── .dockerignore              # Docker build exclusions
│   ├── DEPLOYMENT_GUIDE.md        # Deployment instructions
│   └── logs/                      # Log output directory
│       ├── trading_bot_YYYYMMDD_HHMMSS.log
│       ├── trades_YYYYMMDD_HHMMSS.csv
│       └── *_summary.txt
└── modules/
    ├── config/
    │   └── config.py
    ├── data/
    │   └── data_fetcher.py
    ├── indicators/
    │   └── indicators.py
    ├── strategy/
    │   └── strategy.py
    ├── backtest/
    │   └── backtest_engine.py
    └── optimization/
        └── optimizer.py
```

---

## 🐳 Docker Configuration

### **Current Container**
```bash
# List containers
docker ps -a

# Current container (if running)
CONTAINER ID   IMAGE                    STATUS
abc123def456   trading-bot:latest       Up X hours

# View logs
docker logs -f trading-bot-fixed
```

### **Dockerfile**
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Copy modules (relative to build context)
COPY modules/ /app/modules/

# Copy deployment files
COPY deployment/trading_bot.py /app/
COPY deployment/config_live.py /app/
COPY deployment/requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run bot
CMD ["python", "-u", "trading_bot.py"]
```

### **Build Context**
- **Build from:** `/root/trading_bot/` (parent directory)
- **Dockerfile location:** `/root/trading_bot/deployment/Dockerfile`
- **This allows:** `COPY ../modules /app/modules`

### **Build Command**
```bash
cd /root/trading_bot
docker build -f deployment/Dockerfile -t trading-bot:latest .
```

### **Run Command**
```bash
docker run -d \
  --name trading-bot-fixed \
  --network host \
  --restart unless-stopped \
  -v /root/trading_bot/deployment/logs:/app/logs \
  trading-bot:latest
```

**Flags:**
- `-d`: Detached (background)
- `--name`: Container name
- `--network host`: Use host network (accesses localhost:4002)
- `--restart unless-stopped`: Auto-restart on crash
- `-v`: Mount logs directory (persists across restarts)

---

## 🔌 IB Gateway Configuration

### **Connection Details**
- **Host:** localhost (from container's perspective)
- **Port:** 4002 (paper trading)
- **Client ID:** 3
- **Account Type:** Paper trading EUR account (~900K EUR)

### **Status Check**
```bash
# On droplet
netstat -tulpn | grep 4002
# Should show IB Gateway listening on port 4002

# Test connection
telnet localhost 4002
# Should connect if Gateway is running
```

### **IB Gateway Management**
```bash
# Check if running
ps aux | grep ibgateway

# Restart if needed (depends on how Gateway was installed)
# Usually runs as a service or standalone application
```

### **Expected Behavior**
- IB Gateway reboots daily at midnight EST
- Bot reconnection logic handles this automatically
- Confirmed working in 4-hour test (disconnect at 23:45, reconnected by 23:45:45)

---

## ⚙️ Configuration Parameters

### **config_live.py - Current Settings**
```python
# Connection
IB_HOST = 'localhost'
IB_PORT = 4002
IB_CLIENT_ID = 3

# Trading
SYMBOL = 'EUR'
CURRENCY = 'USD'
POSITION_SIZE = 20000  # EUR

# Timeframe
TIMEFRAME = '5min'
CHECK_FREQUENCY = 60  # seconds

# Strategy (from optimization)
SMA_SHORT = 15
SMA_LONG = 70
RSI_PERIOD = 14
RSI_LOWER = 35
RSI_UPPER = 75
MOMENTUM_PERIOD = 10
MOMENTUM_THRESHOLD = 0.0

# Runtime
RUN_DURATION = '4h'  # Or '1h' for testing
INITIAL_CAPITAL = 10000.0  # ⚠️ HARDCODED - Should come from account
```

### **Parameters Needing Change (Session 7E)**
- ❌ `INITIAL_CAPITAL` - Should query account balance
- ❌ `CHECK_FREQUENCY = 60` - Should be 300 for 5-minute bars
- ⚠️ No EUR balance check parameter

---

## 📊 Log Files

### **Location**
- **Container:** `/app/logs/`
- **Host:** `/root/trading_bot/deployment/logs/`
- **Access:** Download via `scp` or view directly

### **Current Naming Convention**
```
trading_bot_YYYYMMDD_HHMMSS.log
trades_YYYYMMDD_HHMMSS.csv
trades_YYYYMMDD_HHMMSS_summary.txt
```

### **Download Logs**
```bash
# From local machine
scp root@157.230.113.17:/root/trading_bot/deployment/logs/* ~/Downloads/

# Or with specific file
scp root@157.230.113.17:/root/trading_bot/deployment/logs/trading_bot_20260213_*.log ~/Downloads/
```

### **Session 7E Improvement**
```
# Suggested new format
trading_bot_5min_4hr_20260213_233522.log
trades_5min_4hr_20260213_233522.csv
```
- Includes timeframe
- Includes runtime duration
- Easier to identify when downloading multiple files

---

## 🔄 Deployment Workflow

### **Current Process (With Docker)**
1. Edit files locally
2. Transfer to droplet: `scp deployment/trading_bot.py root@157.230.113.17:/root/trading_bot/deployment/`
3. Build Docker image: `docker build --no-cache -f deployment/Dockerfile -t trading-bot:latest .`
4. Stop old container: `docker stop trading-bot-fixed && docker rm trading-bot-fixed`
5. Start new container: `docker run -d --name trading-bot-fixed --network host -v /root/trading_bot/deployment/logs:/app/logs trading-bot:latest`
6. Monitor: `docker logs -f trading-bot-fixed`

**Problem:** Slow iteration (rebuild takes ~30-60 seconds)

---

### **Recommended for Session 7E (Local Testing)**

#### **Option 1: SSH Tunnel (Recommended)**
```bash
# On local machine - create tunnel
ssh -L 4002:localhost:4002 root@157.230.113.17

# Keep this terminal open
# Now IB Gateway is accessible at localhost:4002 from your Mac
```

**Then run locally:**
```bash
# On local machine
cd ~/Projects/.../CPF-Final-Project
python deployment/trading_bot.py

# config_live.py stays the same (localhost:4002)
# But connects via tunnel to droplet
```

**Advantages:**
- Instant code changes
- See errors immediately
- No Docker rebuild delays
- Full Python debugging available

---

#### **Option 2: Direct Connection**
```python
# Edit config_live.py locally
IB_HOST = '157.230.113.17'  # Direct to droplet
IB_PORT = 4002
```

**Then run locally:**
```bash
cd ~/Projects/.../CPF-Final-Project
python deployment/trading_bot.py
```

**Advantages:**
- Same as Option 1
- No tunnel needed

**Disadvantage:**
- Exposes IB Gateway to internet (less secure)
- Requires firewall rule on droplet

---

#### **Testing Workflow**
1. **Develop locally** with tunnel or direct connection
2. **Test rapidly** - edit and re-run instantly
3. **Once stable** - deploy to Docker for production
4. **Run extended test** in Docker container

---

## 🐛 Known Issues (Pre Session 7E)

### **Bot Code Issues**
1. ❌ Double position bug (opens -40K instead of -20K)
2. ❌ Entry price not set (P&L shows $0.00)
3. ⚠️ Order TIF warnings (Error 10349)
4. ❌ No EUR balance check (Error 201)
5. ❌ Fetches 60s prices instead of 5-min bars
6. ❌ No historical warmup (70 min wait before signals)

### **Docker Issues**
- ✅ None - Docker working correctly
- Container runs stably
- Logs persist across restarts
- Network connectivity good

### **IB Gateway Issues**
- ⚠️ Midnight reboots (expected, handled by reconnection logic)
- ✅ Reconnection tested and working

---

## 📱 Monitoring & Access

### **Quick Status Check**
```bash
# SSH to droplet
ssh root@157.230.113.17

# Check container status
docker ps

# View recent logs
docker logs --tail 50 trading-bot-fixed

# Check if trading
docker logs trading-bot-fixed | grep "OPENED\|CLOSED"

# Check errors
docker logs trading-bot-fixed | grep "ERROR"
```

### **Download Latest Logs**
```bash
# From local machine
scp root@157.230.113.17:/root/trading_bot/deployment/logs/*$(date +%Y%m%d)* ~/Downloads/
```

### **Stop Bot**
```bash
# On droplet
docker stop trading-bot-fixed

# Or kill and remove
docker stop trading-bot-fixed && docker rm trading-bot-fixed
```

### **Restart Bot**
```bash
# On droplet
cd /root/trading_bot
docker run -d --name trading-bot-fixed --network host \
  -v /root/trading_bot/deployment/logs:/app/logs trading-bot:latest
```

---

## 🔐 Security Notes

### **Access Control**
- Root SSH access (consider adding non-root user)
- IB Gateway only accessible via localhost
- Docker network: host mode (container shares host network)

### **Firewall**
- Default Ubuntu firewall settings
- Only necessary ports open
- IB Gateway (4002) not exposed externally

### **API Keys**
- No API keys stored (uses IB Gateway connection)
- Paper trading account (no real money at risk)

---

## 🔧 Troubleshooting

### **Bot Won't Start**
```bash
# Check Docker logs
docker logs trading-bot-fixed

# Common issues:
# - IB Gateway not running
# - Port 4002 not accessible
# - Python syntax error
```

### **No Price Data**
```bash
# Check IB Gateway status
netstat -tulpn | grep 4002

# Check contract qualification in logs
docker logs trading-bot-fixed | grep "Contract qualified"
```

### **Position Issues**
```bash
# Check current positions
docker logs trading-bot-fixed | grep "Position confirmed"

# Manual check via TWS/IB Gateway interface
```

### **Log Files Missing**
```bash
# Check mount point
docker inspect trading-bot-fixed | grep -A 10 Mounts

# Verify logs directory
ls -lh /root/trading_bot/deployment/logs/
```

---

## 📈 Current Deployment Status

**Last Successful Run:** February 12-13, 2026, 23:35-03:35 UTC  
**Duration:** 4 hours, 12 seconds  
**Trades:** 4 executed  
**Issues:** Multiple bugs discovered (documented in critical-bugs-analysis.md)  
**Next Step:** Implement Session 7E fixes

---

## 🎯 Session 7E Deployment Plan

1. **Test locally first** (SSH tunnel or direct)
2. **Verify fixes** work without Docker
3. **Deploy to Docker** once stable
4. **Run 1-hour validation** test
5. **Run 8-hour production** test
6. **Download and analyze** all logs
7. **If successful:** Run multi-day test

---

**Contact Information:**
- **Droplet IP:** 157.230.113.17
- **SSH:** `ssh root@157.230.113.17`
- **IB Gateway:** localhost:4002 (from droplet)
- **Logs:** `/root/trading_bot/deployment/logs/`

**Last Updated:** February 13, 2026, 08:40 UTC
