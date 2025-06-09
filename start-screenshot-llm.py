#!/usr/bin/env python3
"""
Screenshot LLM Assistant - Startup Script

Manages launching both the daemon and GUI processes with proper coordination.
"""

import asyncio
import logging
import os
import sys
import subprocess
import signal
import time
import argparse
from pathlib import Path

# Add lib directory to path  
lib_path = Path(__file__).parent / 'lib'
sys.path.insert(0, str(lib_path))

from ipc_handler import IPCManager

logger = logging.getLogger(__name__)

class ScreenshotLLMStarter:
    def __init__(self, config_dir: str = "~/.local/share/screenshot-llm"):
        self.config_dir = os.path.expanduser(config_dir)
        self.daemon_process = None
        self.gui_process = None
        self.running = False
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = os.path.join(self.config_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'screenshot-llm-starter.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger.info("Screenshot LLM Assistant starter initializing...")
    
    def start_gui(self, minimized: bool = False):
        """Start the GUI process"""
        gui_script = os.path.join(os.path.dirname(__file__), "screenshot-llm-gui.py")
        
        cmd = [sys.executable, gui_script, "--config-dir", self.config_dir]
        if minimized:
            cmd.append("--minimized")
        
        try:
            self.gui_process = subprocess.Popen(cmd)
            logger.info(f"Started GUI process with PID: {self.gui_process.pid}")
            
            # Give GUI time to start IPC server
            time.sleep(2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to start GUI process: {e}")
            return False
    
    def start_daemon(self):
        """Start the daemon process"""
        daemon_script = os.path.join(os.path.dirname(__file__), "screenshot-llm.py")
        
        cmd = [sys.executable, daemon_script, "--config-dir", self.config_dir]
        
        try:
            self.daemon_process = subprocess.Popen(cmd)
            logger.info(f"Started daemon process with PID: {self.daemon_process.pid}")
            return True
        except Exception as e:
            logger.error(f"Failed to start daemon process: {e}")
            return False
    
    def check_gui_running(self) -> bool:
        """Check if GUI process is running"""
        ipc_manager = IPCManager(self.config_dir)
        return ipc_manager.is_server_running()
    
    def start_all(self, gui_first: bool = True, minimized: bool = False):
        """Start both GUI and daemon with proper coordination"""
        logger.info("Starting Screenshot LLM Assistant...")
        
        if gui_first:
            # Start GUI first to establish IPC server
            if not self.start_gui(minimized):
                logger.error("Failed to start GUI, aborting")
                return False
            
            # Wait for GUI to be ready
            for i in range(10):  # Wait up to 10 seconds
                if self.check_gui_running():
                    logger.info("GUI IPC server is ready")
                    break
                time.sleep(1)
            else:
                logger.warning("GUI IPC server not detected, continuing anyway")
            
            # Start daemon
            if not self.start_daemon():
                logger.error("Failed to start daemon")
                self.stop_all()
                return False
        else:
            # Start daemon first (will fall back to zenity if no GUI)
            if not self.start_daemon():
                logger.error("Failed to start daemon, aborting")
                return False
            
            # Start GUI
            if not self.start_gui(minimized):
                logger.error("Failed to start GUI")
                # Don't stop daemon - it can work without GUI
        
        self.running = True
        logger.info("Screenshot LLM Assistant started successfully")
        return True
    
    def stop_all(self):
        """Stop all processes"""
        logger.info("Stopping Screenshot LLM Assistant...")
        
        self.running = False
        
        # Stop daemon first
        if self.daemon_process:
            try:
                self.daemon_process.terminate()
                self.daemon_process.wait(timeout=5)
                logger.info("Daemon process stopped")
            except subprocess.TimeoutExpired:
                logger.warning("Daemon process did not stop gracefully, killing")
                self.daemon_process.kill()
            except Exception as e:
                logger.error(f"Error stopping daemon: {e}")
        
        # Stop GUI
        if self.gui_process:
            try:
                self.gui_process.terminate()
                self.gui_process.wait(timeout=5)
                logger.info("GUI process stopped")
            except subprocess.TimeoutExpired:
                logger.warning("GUI process did not stop gracefully, killing")
                self.gui_process.kill()
            except Exception as e:
                logger.error(f"Error stopping GUI: {e}")
    
    def monitor_processes(self):
        """Monitor processes and restart if needed"""
        while self.running:
            try:
                # Check daemon
                if self.daemon_process and self.daemon_process.poll() is not None:
                    logger.warning("Daemon process died, restarting...")
                    self.start_daemon()
                
                # Check GUI
                if self.gui_process and self.gui_process.poll() is not None:
                    logger.warning("GUI process died, restarting...")
                    self.start_gui()
                
                time.sleep(5)  # Check every 5 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in process monitor: {e}")
                time.sleep(5)
    
    def run(self, gui_first: bool = True, minimized: bool = False, monitor: bool = True):
        """Run the complete system"""
        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.stop_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Start all processes
            if not self.start_all(gui_first, minimized):
                logger.error("Failed to start system")
                return False
            
            # Monitor processes if requested
            if monitor:
                self.monitor_processes()
            else:
                # Just wait for processes to finish
                try:
                    if self.daemon_process:
                        self.daemon_process.wait()
                    if self.gui_process:
                        self.gui_process.wait()
                except KeyboardInterrupt:
                    pass
            
        except Exception as e:
            logger.error(f"System error: {e}")
        finally:
            self.stop_all()
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Screenshot LLM Assistant Starter")
    parser.add_argument('--config-dir', default="~/.local/share/screenshot-llm",
                       help='Configuration directory')
    parser.add_argument('--daemon-first', action='store_true',
                       help='Start daemon before GUI (default: GUI first)')
    parser.add_argument('--minimized', action='store_true',
                       help='Start GUI minimized')
    parser.add_argument('--no-monitor', action='store_true',
                       help='Do not monitor and restart processes')
    parser.add_argument('--gui-only', action='store_true',
                       help='Start only the GUI')
    parser.add_argument('--daemon-only', action='store_true',
                       help='Start only the daemon')
    
    args = parser.parse_args()
    
    starter = ScreenshotLLMStarter(args.config_dir)
    
    try:
        if args.gui_only:
            success = starter.start_gui(args.minimized)
            if success and not args.no_monitor:
                starter.gui_process.wait()
        elif args.daemon_only:
            success = starter.start_daemon()
            if success and not args.no_monitor:
                starter.daemon_process.wait()
        else:
            # Start both
            gui_first = not args.daemon_first
            success = starter.run(gui_first, args.minimized, not args.no_monitor)
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Startup interrupted by user")
        starter.stop_all()
    except Exception as e:
        logger.error(f"Startup error: {e}")
        starter.stop_all()
        sys.exit(1)

if __name__ == "__main__":
    main()