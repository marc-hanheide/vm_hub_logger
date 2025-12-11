# Virgin Media Hub 5 Event Logger

A Python script to automatically retrieve and log event data from Virgin Media Hub 5 routers.

## Features

- **Automatic polling**: Retrieves logs at configurable intervals (default: 10 seconds)
- **Deduplication**: Prevents duplicate entries in the log file
- **Critical event highlighting**: Displays new critical events in red with formatting
- **Persistent storage**: Saves all events to a local JSON log file
- **Command-line interface**: Configurable options for hub IP, log file location, and polling interval

## Requirements

- Python 3.6+
- `requests` library (for HTTP requests)
- Access to Virgin Media Hub 5 on the network

## Installation

### Option 1: Docker (Recommended)

The easiest way to run the logger is using Docker:

```bash
# Build and run with docker compose
docker compose up -d

# View logs
docker compose logs -f

# Stop the logger
docker compose down
```

### Option 2: Python Virtual Environment

1. Navigate to the project directory:
```bash
cd /Users/mhanheide/workspace/vm_hub_logger
```

2. Activate the virtual environment:
```bash
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Option 3: Convenience Script

Use the provided shell script:

```bash
./run_logger.sh
```

## Usage

### Docker Usage

The Docker container is configured via environment variables in `compose.yaml`:

```yaml
environment:
  - HUB_IP=192.168.0.1           # Your hub's IP address
  - LOG_FILE=/app/logs/vm_hub_events.log
  - INTERVAL=10                   # Polling interval in seconds
```

To override settings:

```bash
# Edit compose.yaml, then restart
docker compose up -d

# Or use environment variables
HUB_IP=192.168.1.1 INTERVAL=30 docker compose up -d
```

Logs are persisted in the `./logs` directory on your host machine.

**Docker Commands:**

```bash
# Build the image
docker compose build

# Run in foreground (see output)
docker compose up

# Run in background
docker compose up -d

# View logs
docker compose logs -f

# Stop container
docker compose down

# Rebuild and restart
docker compose up -d --build
```

### Python Direct Usage

```bash
python vm_hub_logger.py
```

This will:
- Connect to the hub at `192.168.0.1` (default)
- Poll every 10 seconds (default)
- Save logs to `vm_hub_events.log` (default)

### Command-Line Options (Python Direct Usage)

```bash
python vm_hub_logger.py --help
```

Available options:

- `--hub-ip IP`: Specify the IP address of your Virgin Media Hub (default: 192.168.0.1)
- `--log-file PATH`: Path to the log file (default: vm_hub_events.log)
- `--interval SECONDS`: Polling interval in seconds (default: 10)
- `--version`: Show version information

### Examples (Python Direct Usage)

```bash
# Poll every 30 seconds
python vm_hub_logger.py --interval 30

# Use a different hub IP address
python vm_hub_logger.py --hub-ip 192.168.1.1

# Save logs to a specific location
python vm_hub_logger.py --log-file /var/log/vm_hub.log

# Combine multiple options
python vm_hub_logger.py --hub-ip 192.168.0.1 --interval 5 --log-file logs/hub_events.log

# Use the convenience script
./run_logger.sh
```

## Output

### Log File Format

Events are stored as JSON objects, one per line:

```json
{"priority": "critical", "time": "2025-12-10T20:11:21.000Z", "message": "16 consecutive T3 timeouts..."}
{"priority": "warning", "time": "2025-12-10T20:10:58.000Z", "message": "DBC-REQ Mismatch..."}
```

### Critical Event Display

When a new critical event is detected, it's displayed on screen in red:

```
🚨 CRITICAL EVENT
Time: 2025-12-10 20:11:21 UTC
Message: 16 consecutive T3 timeouts while trying to range on upstream channel 2
--------------------------------------------------------------------------------
```

## Stopping the Logger

**Docker:**
```bash
docker compose down
```

**Python Direct:**
Press `Ctrl+C` to gracefully stop the logger. It will display a summary before exiting.

**Convenience Script:**
Press `Ctrl+C` to stop the logger running via `run_logger.sh`.

## How It Works

1. **Initial Load**: Reads existing log file to avoid duplicating already-recorded events
2. **Polling Loop**: Continuously fetches logs from the hub using curl
3. **Deduplication**: Uses a hash of (time + priority + message) to identify unique events
4. **Logging**: Appends new events to the log file as JSON objects
5. **Alert Display**: Shows critical events in red on the terminal

## Troubleshooting

- **Connection errors**: Ensure your hub IP is correct and accessible
- **SSL warnings**: The script automatically suppresses SSL warnings for local router connections
- **Permission errors**: Ensure you have write permission for the log file location
- **Import errors**: Make sure you've installed dependencies with `pip install -r requirements.txt`
- **Docker issues**: 
  - Ensure Docker and Docker Compose are installed
  - Check container logs: `docker compose logs`
  - Verify network connectivity from container to hub
  - For custom networks, adjust `network_mode` in `compose.yaml`

## Tools and Scripts

### Main Logger: `vm_hub_logger.py`
The primary logging application that polls the Virgin Media Hub 5 for events.

### Log Analysis: `analyze_logs.py`
Comprehensive analysis tool for logged events with statistics and summaries.

### Convenience Script: `run_logger.sh`
Shell script to quickly start the logger with default settings using Python.

### Docker Files
- **`Dockerfile`**: Container image definition for the logger application
- **`compose.yaml`**: Docker Compose configuration for easy deployment

### Container Image
- **Image**: `lcas.lincoln.ac.uk/marc-hanheide/vm_hub_logger:latest`
- **Base**: Python 3.11 slim
- **Configuration**: Via environment variables (HUB_IP, LOG_FILE, INTERVAL)

## Log Analysis

The `analyze_logs.py` script provides comprehensive analysis of logged events with statistics and summaries.

### Usage

```bash
# Basic analysis with console output
python analyze_logs.py vm_hub_events.log

# Generate JSON report file
python analyze_logs.py vm_hub_events.log --json
```

### Features

- **Priority Breakdown**: Count and percentage of events by severity (critical, error, warning, notice)
- **Critical Issue Analysis**: Detailed breakdown of T3 timeouts, retries exhausted, and affected channels
- **Channel Failure Tracking**: Per-channel failure statistics
- **Outage Detection**: Automatically identifies potential outage periods (clusters of critical events)
- **Warning Analysis**: MDD timeout counts, DBC mismatch counts
- **Status Message Counts**: CM-STATUS messages, profile changes, login events
- **Smart Recommendations**: Context-aware recommendations based on issue severity

### Sample Output

```
======================================================================
VIRGIN MEDIA HUB LOG ANALYSIS SUMMARY
======================================================================

📊 OVERVIEW
  Total Events: 301
  Date Range: 2025-12-01 20:22:29 to 2025-12-11 07:56:30

📈 EVENT PRIORITY BREAKDOWN
  🔴 Critical       95 ( 31.6%)
  🟠 Error           4 (  1.3%)
  🟡 Warning        62 ( 20.6%)
  🔵 Notice        140 ( 46.5%)

🚨 CRITICAL ISSUES (T3 TIMEOUTS)
  Total Critical Events: 95
  Affected Upstream Channels: 0, 1, 2, 3, 4, 8

⏱️  IDENTIFIED OUTAGE PERIODS (5 total)
  1. 2025-12-10 20:21:55 to 2025-12-10 20:23:47
     Duration: 1.9 min | Events: 21
```

### JSON Export

The `--json` flag exports detailed statistics to a JSON file (`<logfile>_analysis.json`) for further processing or integration with other tools.

## License

MIT License

