#!/bin/bash
# Cleanup script for Screenshot LLM Assistant
# Kills all running processes and cleans up temporary files

echo "🧹 Cleaning up Screenshot LLM Assistant processes..."

# Find all screenshot-llm processes
PROCESSES=$(ps aux | grep screenshot-llm | grep -v grep | grep -v kill-all.sh | awk '{print $2}')

if [ -z "$PROCESSES" ]; then
    echo "  ✅ No screenshot-llm processes found"
else
    echo "  🔍 Found processes: $PROCESSES"
    
    # Kill processes nicely first
    for pid in $PROCESSES; do
        echo "  🛑 Killing process $pid..."
        kill $pid 2>/dev/null
    done
    
    # Wait a moment
    sleep 2
    
    # Check if any are still running and force kill
    REMAINING=$(ps aux | grep screenshot-llm | grep -v grep | grep -v kill-all.sh | awk '{print $2}')
    if [ ! -z "$REMAINING" ]; then
        echo "  💀 Force killing remaining processes: $REMAINING"
        for pid in $REMAINING; do
            kill -9 $pid 2>/dev/null
        done
    fi
fi

# Kill any zenity dialogs that might be open
ZENITY_PROCESSES=$(ps aux | grep zenity | grep -v grep | awk '{print $2}')
if [ ! -z "$ZENITY_PROCESSES" ]; then
    echo "  🗃️  Closing zenity dialogs: $ZENITY_PROCESSES"
    for pid in $ZENITY_PROCESSES; do
        kill $pid 2>/dev/null
    done
fi

# Clean up socket file
if [ -f "screenshot-llm.sock" ]; then
    echo "  🧹 Removing socket file"
    rm -f screenshot-llm.sock
fi

# Clean up any temporary test files
if [ -f "gui.log" ]; then
    echo "  🧹 Removing test log file"
    rm -f gui.log
fi

# Final verification
REMAINING_ALL=$(ps aux | grep screenshot-llm | grep -v grep | grep -v kill-all.sh)
if [ -z "$REMAINING_ALL" ]; then
    echo "  ✅ All processes cleaned up successfully!"
    echo ""
    echo "🚀 Ready to start fresh:"
    echo "  ./run.sh"
    echo "  python start-screenshot-llm.py"
else
    echo "  ⚠️  Some processes may still be running:"
    echo "$REMAINING_ALL"
    echo ""
    echo "💡 If processes persist, try:"
    echo "  sudo killall python3"
    echo "  (Warning: This will kill ALL Python processes)"
fi