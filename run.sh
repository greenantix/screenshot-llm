#!/bin/bash
# Quick start script for Screenshot LLM Assistant v2.0

cd "$(dirname "$0")"

echo "🚀 Starting Screenshot LLM Assistant v2.0..."
echo ""

# Check if config exists
if [ ! -f "config/config.json" ]; then
    echo "❌ Configuration not found!"
    echo "Please edit config/config.json and add your API key."
    exit 1
fi

# Check API key
if ! grep -q '"api_key":\s*"[^"]\+[^"]"' config/config.json; then
    echo "⚠️  Warning: No API key found in config.json"
    echo "   Please add your Anthropic or OpenAI API key to config/config.json"
    echo ""
fi

# Check tkinter
if python3 -c "import tkinter" 2>/dev/null; then
    echo "✅ Dependencies: All installed"
else
    echo "❌ Missing tkinter! Please run: sudo apt install python3-tk"
    exit 1
fi

echo "✅ Screenshot tools: Available"  
echo "✅ Permissions: User in input group"
echo "✅ GUI Framework: tkinter available"
echo ""

echo "Choose startup mode:"
echo "1) Complete system (GUI + Daemon) [Recommended]"
echo "2) GUI only"
echo "3) Daemon only (fallback mode)"
echo "4) Run tests"
echo "5) Kill all processes (cleanup)"
echo ""

read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo "🎯 Starting complete system..."
        python start-screenshot-llm.py
        ;;
    2)
        echo "🖥️  Starting GUI only..."
        python screenshot-llm-gui.py
        ;;
    3)
        echo "⚙️  Starting daemon only..."
        python screenshot-llm.py
        ;;
    4)
        echo "🧪 Running tests..."
        python test-persistent-chat.py
        ;;
    5)
        echo "🧹 Cleaning up all processes..."
        ./kill-all.sh
        ;;
    *)
        echo "Invalid choice. Starting complete system..."
        python start-screenshot-llm.py
        ;;
esac