#!/bin/bash

# Function to check if required dependencies are installed
check_dependencies() {
    local missing=()
    
    # Check Python dependencies for GTK
    if ! python3 -c "import gi" 2>/dev/null; then
        missing+=("python3-gi")
    fi

    # Check system dependencies for pystray
    if ! dpkg -l | grep -q "gir1.2-ayatanaappindicator3"; then
        echo "Installing required system packages for tray icon support..."
        sudo apt-get install -y gir1.2-ayatanaappindicator3-0.1
    fi

    # Check additional Python packages
    if ! python3 -c "import pystray" 2>/dev/null; then
        echo "Installing required Python package: pystray"
        pip3 install pystray pillow
    fi
    
    # Check system dependencies
    dependencies=("grim" "wlr-randr" "maim" "scrot" "xdotool")
    for dep in "${dependencies[@]}"; do
        if ! command -v "$dep" &>/dev/null; then
            missing+=("$dep")
        fi
    done
    
    # If missing dependencies, prompt to install
    if [ ${#missing[@]} -gt 0 ]; then
        echo "Missing required dependencies: ${missing[*]}"
        echo "Please install them using:"
        echo "sudo apt install ${missing[*]}"
        exit 1
    fi
}

# Function to clean up any existing processes
cleanup() {
    echo "Cleaning up existing processes..."
    ./kill-all.sh >/dev/null 2>&1
}

# Function to start the application
start_app() {
    # Start GUI minimized if requested
    if [ "$1" == "--minimized" ]; then
        echo "Starting Screenshot LLM Assistant (minimized)..."
        python3 gtk-chat-gui.py --minimized &
    else
        echo "Starting Screenshot LLM Assistant..."
        python3 gtk-chat-gui.py &
    fi
    
    # Give GUI time to start
    sleep 2
    
    # Start daemon
    echo "Starting screenshot daemon..."
    python3 screenshot-llm.py &
    
    echo "Setup complete! Use mouse button 9 to take screenshots."
}

# Main script
check_dependencies
cleanup
start_app "$@"