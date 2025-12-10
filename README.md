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

## Usage

### Basic Usage

```bash
python vm_hub_logger.py
```

This will:
- Connect to the hub at `192.168.0.1` (default)
- Poll every 10 seconds (default)
- Save logs to `vm_hub_events.log` (default)

### Command-Line Options

```bash
python vm_hub_logger.py --help
```

Available options:

- `--hub-ip IP`: Specify the IP address of your Virgin Media Hub (default: 192.168.0.1)
- `--log-file PATH`: Path to the log file (default: vm_hub_events.log)
- `--interval SECONDS`: Polling interval in seconds (default: 10)
- `--version`: Show version information

### Examples

```bash
# Poll every 30 seconds
python vm_hub_logger.py --interval 30

# Use a different hub IP address
python vm_hub_logger.py --hub-ip 192.168.1.1

# Save logs to a specific location
python vm_hub_logger.py --log-file /var/log/vm_hub.log

# Combine multiple options
python vm_hub_logger.py --hub-ip 192.168.0.1 --interval 5 --log-file logs/hub_events.log
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

Press `Ctrl+C` to gracefully stop the logger. It will display a summary before exiting.

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

## License

MIT License
