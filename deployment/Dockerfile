FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY deployment/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy trading bot and configuration
COPY deployment/trading_bot.py .
COPY deployment/config_live.py .

# Copy modules from project root
COPY modules/ /app/modules/

# Create logs directory
RUN mkdir -p /app/logs

# Unbuffered output for real-time log viewing
CMD ["python", "-u", "trading_bot.py"]
