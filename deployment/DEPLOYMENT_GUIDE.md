# Trading Bot Deployment Guide

Complete guide for deploying the EUR/USD trading bot to DigitalOcean.

## Prerequisites

- DigitalOcean droplet running (157.230.113.17)
- IB Gateway running in Docker on droplet
- SSH access to droplet
- All files in `deployment/` directory

## Architecture Note

The Dockerfile uses the **project root** as build context (not the `deployment/`
directory) so it can copy both `deployment/` files and `modules/`. All `docker build`
commands must be run from the project root with `-f deployment/Dockerfile`.

## Deployment Steps

### Step 1: Prepare Local Files [LOCAL]

```bash
cd ~/Projects/Python-Quants-CPF-Program/_Final-Poject-Feb-2026/CPF-Final-Project

ls deployment/
# Should see: trading_bot.py, config_live.py, Dockerfile, requirements.txt,
#             .dockerignore, DEPLOYMENT_GUIDE.md
```

### Step 2: Transfer Files to Droplet [LOCAL]

```bash
# Create deployment directory on droplet
ssh root@157.230.113.17 "mkdir -p /root/trading_bot/deployment /root/trading_bot/modules"

# Transfer deployment files
scp deployment/trading_bot.py deployment/config_live.py \
    deployment/requirements.txt deployment/Dockerfile deployment/.dockerignore \
    root@157.230.113.17:/root/trading_bot/deployment/

# Transfer modules directory
scp -r modules/ root@157.230.113.17:/root/trading_bot/modules/
```

### Step 3: Build Docker Image [CLOUD]

```bash
ssh root@157.230.113.17
cd /root/trading_bot

# Build from project root with Dockerfile path
docker build -f deployment/Dockerfile -t trading-bot:latest .

# Verify image
docker images | grep trading-bot
```

### Step 4: Configure Trading Parameters [CLOUD]

```bash
nano /root/trading_bot/deployment/config_live.py

# Key settings to review:
# TIMEFRAME = '5min'     (or '4H')
# RUN_DURATION = "1h"    (start small)
# IB_PORT = 4002         (paper trading)
# POSITION_SIZE = 20000
```

### Step 5: Run Trading Bot [CLOUD]

**For 5-minute timeframe:**
```bash
docker run -d \
  --name trading-bot-5min \
  --network host \
  --restart unless-stopped \
  -v /root/trading_bot/logs:/app/logs \
  -v /root/trading_bot/deployment/config_live.py:/app/config_live.py \
  trading-bot:latest
```

**For 4-hour timeframe:**
```bash
# First update config_live.py: TIMEFRAME = '4H'
docker run -d \
  --name trading-bot-4h \
  --network host \
  --restart unless-stopped \
  -v /root/trading_bot/logs:/app/logs \
  -v /root/trading_bot/deployment/config_live.py:/app/config_live.py \
  trading-bot:latest
```

### Step 6: Verify Deployment [CLOUD]

```bash
docker ps | grep trading-bot

docker logs -f trading-bot-5min
# Expected:
# INFO - Trading Bot initialized for 5min timeframe
# INFO - Parameters: SMA 15/70, RSI 14 (35/75), Momentum 10 (threshold 0.0)
# INFO - Connected to IB Gateway at localhost:4002
# INFO - Trading bot started
```

## Monitoring Commands

### From Local Machine [LOCAL]

```bash
# Quick status
ssh root@157.230.113.17 "docker ps | grep trading-bot"

# Last 20 log lines
ssh root@157.230.113.17 "docker logs trading-bot-5min --tail 20"

# Live log stream
ssh root@157.230.113.17 "docker logs -f trading-bot-5min"

# Latest P&L
ssh root@157.230.113.17 "docker logs trading-bot-5min 2>&1 | grep 'P&L:' | tail -1"

# Count trades
ssh root@157.230.113.17 "docker logs trading-bot-5min 2>&1 | grep 'OPENED:' | wc -l"
```

## Downloading Results

```bash
mkdir -p ~/trading_results_$(date +%Y%m%d)

scp 'root@157.230.113.17:/root/trading_bot/logs/trades_*.csv' \
    ~/trading_results_$(date +%Y%m%d)/

scp 'root@157.230.113.17:/root/trading_bot/logs/trading_bot_*.log' \
    ~/trading_results_$(date +%Y%m%d)/

scp 'root@157.230.113.17:/root/trading_bot/logs/*_summary.txt' \
    ~/trading_results_$(date +%Y%m%d)/
```

## Container Management

```bash
# Stop
docker stop trading-bot-5min

# Start stopped container
docker start trading-bot-5min

# Remove
docker stop trading-bot-5min && docker rm trading-bot-5min

# Deploy fresh instance with new name
docker run -d \
  --name trading-bot-8h \
  --network host \
  --restart unless-stopped \
  -v /root/trading_bot/logs:/app/logs \
  -v /root/trading_bot/deployment/config_live.py:/app/config_live.py \
  trading-bot:latest
```

## Testing Protocol

### Phase 1: Initial Validation (Day 1)

**1.1 First 1-hour run** (`RUN_DURATION = "1h"`)
- Verify: connection, price fetching, logging
- Check logs for errors

**1.2 Second 1-hour run**
- Verify: indicator calculation (after ~70+ bars collected)
- Check signal generation if crossovers occur

**1.3 Third 1-hour run**
- Verify: trade execution (if signals occur)
- Confirm P&L tracking, CSV output

### Phase 2: Extended Test (Day 2)

**4-hour stability run** (`RUN_DURATION = "4h"`)
- Monitor first 30 minutes, then check hourly
- Verify stable memory usage and no crashes

### Phase 3: Week-Long Validation (Days 3-7)

**Option A: Daily 8-hour runs** (recommended)
- `RUN_DURATION = "8h"`, deploy each morning
- Clean start each day, clear daily results

**Option B: Continuous 5-day run**
- `RUN_DURATION = "5d"`, deploy Monday morning
- Bot handles weekends automatically

## Troubleshooting

### Bot Won't Connect to IB Gateway

```bash
# Check IB Gateway container
docker ps | grep ibgateway
docker logs ibgateway | tail -50

# Verify port
netstat -tuln | grep 4002
```

### No Trades Executing

- Market may be closed (weekend/holiday)
- Not enough price history yet (need SMA_SLOW + 10 bars minimum)
- No crossovers in current data (check logs for signal messages)

### Bot Crashes

```bash
docker logs trading-bot-5min
# Check for: import errors, config errors, connection refused
```

## Quick Reference

| Item | Location |
|------|----------|
| Bot files | `/root/trading_bot/deployment/` |
| Modules | `/root/trading_bot/modules/` |
| Logs | `/root/trading_bot/logs/` |
| Config | `/root/trading_bot/deployment/config_live.py` |
