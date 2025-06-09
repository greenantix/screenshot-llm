#!/usr/bin/env python3
import subprocess
import sys

def show_response_zenity(response):
    # Show in zenity dialog
    try:
        subprocess.run([
            'zenity', 
            '--text-info',
            '--title=Screenshot LLM Analysis',
            '--width=900',
            '--height=700',
            '--font=monospace'
        ], input=response.encode(), check=True)
    except subprocess.CalledProcessError:
        # Fallback to notification if zenity fails
        subprocess.run(['notify-send', 'Screenshot Analysis Failed', 'Could not display response'])
    
    # Also save to file for reference
    with open('/tmp/last-screenshot-analysis.txt', 'w') as f:
        f.write(response)

if __name__ == "__main__":
    show_response_zenity(sys.argv[1] if len(sys.argv) > 1 else "Test response")
