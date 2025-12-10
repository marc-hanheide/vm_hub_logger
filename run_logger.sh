#!/bin/bash
# Convenience script to run the VM Hub Logger

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
LOGGER_SCRIPT="$SCRIPT_DIR/vm_hub_logger.py"

# Check if virtual environment exists
if [ ! -f "$PYTHON_BIN" ]; then
    echo "Error: Virtual environment not found at $SCRIPT_DIR/.venv"
    echo "Please create it with: python3 -m venv .venv"
    exit 1
fi

# Run the logger with any passed arguments
"$PYTHON_BIN" "$LOGGER_SCRIPT" "$@"
