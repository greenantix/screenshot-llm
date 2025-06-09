#!/bin/bash

# Function to kill processes by name
kill_process() {
    local process_name=$1
    local pids
    
    # Find PIDs for the process
    pids=$(pgrep -f "$process_name" 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo "Stopping $process_name processes..."
        for pid in $pids; do
            # Don't kill the kill-all.sh script itself
            if [ "$pid" != $$ ]; then
                kill -15 "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
            fi
        done
    fi
}

# Kill all related processes
kill_process "screenshot-llm.py"
kill_process "screenshot-llm-gui.py"

# Clean up IPC socket if it exists
socket_path="/tmp/screenshot-llm.sock"
if [ -S "$socket_path" ]; then
    echo "Removing IPC socket..."
    rm "$socket_path"
fi

# Give processes time to clean up
sleep 1

# Check if any processes are still running
remaining=$(pgrep -f "screenshot-llm" 2>/dev/null)
if [ -n "$remaining" ]; then
    echo "Warning: Some processes are still running. PIDs: $remaining"
    echo "You may need to kill them manually or wait a moment and try again."
else
    echo "All processes stopped successfully."
fi