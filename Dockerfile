FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY vm_hub_logger.py .

# Create directory for logs
RUN mkdir -p /app/logs

# Set environment variables with defaults
ENV HUB_IP=192.168.0.1
ENV LOG_FILE=/app/logs/vm_hub_events.log
ENV INTERVAL=600

# Run the logger with environment variables
CMD ["sh", "-c", "python vm_hub_logger.py --hub-ip ${HUB_IP} --log-file ${LOG_FILE} --interval ${INTERVAL}"]
