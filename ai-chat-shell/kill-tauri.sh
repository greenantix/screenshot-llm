#!/bin/bash
echo "💀 Killing all Tauri-related processes..."
pkill -f tauri
pkill -f ai-chat-shell
echo "✅ Done."
