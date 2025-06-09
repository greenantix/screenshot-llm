#!/usr/bin/env python3
"""
Context detection for Screenshot LLM Assistant
"""

import os
import subprocess
import logging
import json
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ContextDetector:
    """Detects application context and working directory information"""
    
    def __init__(self):
        self.contexts_config = self._load_contexts_config()
        
    def _load_contexts_config(self) -> Dict:
        """Load context detection rules from config"""
        try:
            config_path = "config/contexts.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load contexts config: {e}")
        
        # Return default contexts
        return {
            "applications": {
                "code": ["code", "codium", "atom", "sublime_text", "vim", "nvim", "emacs"],
                "terminal": ["gnome-terminal", "konsole", "xterm", "alacritty", "kitty", "terminator"],
                "browser": ["firefox", "chrome", "chromium", "brave", "opera", "safari"],
                "ide": ["intellij", "pycharm", "webstorm", "eclipse", "netbeans"]
            },
            "file_extensions": {
                "python": [".py", ".pyw", ".ipynb"],
                "javascript": [".js", ".jsx", ".ts", ".tsx"],
                "web": [".html", ".htm", ".css", ".scss", ".sass"],
                "config": [".json", ".yaml", ".yml", ".toml", ".ini", ".conf"],
                "shell": [".sh", ".bash", ".zsh", ".fish"]
            }
        }
    
    def get_active_window_info(self) -> Dict[str, str]:
        """Get information about the active window"""
        window_info = {
            "app_name": "unknown",
            "window_title": "",
            "working_directory": "",
            "process_id": "",
            "window_class": ""
        }
        
        try:
            if self._is_wayland():
                window_info.update(self._get_wayland_window_info())
            else:
                window_info.update(self._get_x11_window_info())
        except Exception as e:
            logger.error(f"Failed to get window info: {e}")
        
        # Get working directory if we have a process ID
        if window_info.get("process_id"):
            try:
                cwd = self._get_process_working_directory(window_info["process_id"])
                if cwd:
                    window_info["working_directory"] = cwd
            except Exception as e:
                logger.debug(f"Failed to get working directory: {e}")
        
        return window_info
    
    def _is_wayland(self) -> bool:
        """Check if running under Wayland"""
        return 'WAYLAND_DISPLAY' in os.environ
    
    def _get_x11_window_info(self) -> Dict[str, str]:
        """Get window information on X11"""
        info = {}
        
        try:
            # Get active window ID
            result = subprocess.run(['xdotool', 'getactivewindow'], 
                                  capture_output=True, text=True, check=True)
            window_id = result.stdout.strip()
            
            # Get window title
            result = subprocess.run(['xdotool', 'getwindowname', window_id],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                info["window_title"] = result.stdout.strip()
            
            # Get window class
            result = subprocess.run(['xprop', '-id', window_id, 'WM_CLASS'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # Parse WM_CLASS output: WM_CLASS(STRING) = "instance", "class"
                wm_class = result.stdout.strip()
                if '=' in wm_class:
                    class_part = wm_class.split('=')[1].strip()
                    # Extract class name (second quoted string)
                    parts = class_part.split(',')
                    if len(parts) >= 2:
                        app_class = parts[1].strip().strip('"')
                        info["window_class"] = app_class
                        info["app_name"] = app_class.lower()
            
            # Get process ID
            result = subprocess.run(['xdotool', 'getwindowpid', window_id],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                info["process_id"] = result.stdout.strip()
                
        except subprocess.CalledProcessError as e:
            logger.debug(f"xdotool command failed: {e}")
        except Exception as e:
            logger.error(f"Failed to get X11 window info: {e}")
        
        return info
    
    def _get_wayland_window_info(self) -> Dict[str, str]:
        """Get window information on Wayland (limited)"""
        info = {}
        
        # Wayland doesn't provide easy access to active window info
        # We can try some heuristics or use compositor-specific tools
        
        try:
            # Try to get info from process list
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if result.returncode == 0:
                # Look for common GUI applications
                lines = result.stdout.split('\n')
                for line in lines:
                    for app_category, apps in self.contexts_config.get("applications", {}).items():
                        for app in apps:
                            if app in line and 'grep' not in line:
                                # Found a running GUI app
                                parts = line.split()
                                if len(parts) > 1:
                                    info["process_id"] = parts[1]
                                    info["app_name"] = app
                                    break
                        if info.get("app_name"):
                            break
                    if info.get("app_name"):
                        break
        except Exception as e:
            logger.debug(f"Failed to get Wayland window info: {e}")
        
        return info
    
    def _get_process_working_directory(self, pid: str) -> Optional[str]:
        """Get the working directory of a process"""
        try:
            cwd_path = f"/proc/{pid}/cwd"
            if os.path.exists(cwd_path):
                return os.readlink(cwd_path)
        except Exception as e:
            logger.debug(f"Failed to get working directory for PID {pid}: {e}")
        
        return None
    
    def build_context_prompt(self) -> str:
        """Build a context-aware prompt for the LLM"""
        window_info = self.get_active_window_info()
        
        prompt_parts = ["Context information for the screenshot:"]
        
        # Add application context
        app_name = window_info.get("app_name", "unknown")
        if app_name != "unknown":
            app_type = self._categorize_application(app_name)
            prompt_parts.append(f"- Active application: {app_name} ({app_type})")
        
        # Add window title if available
        window_title = window_info.get("window_title", "")
        if window_title:
            prompt_parts.append(f"- Window title: {window_title}")
        
        # Add working directory context
        working_dir = window_info.get("working_directory", "")
        if working_dir:
            project_context = self._analyze_directory_context(working_dir)
            prompt_parts.append(f"- Working directory: {working_dir}")
            if project_context:
                prompt_parts.append(f"- Project type: {project_context}")
        
        # Add environment information
        desktop_env = os.environ.get('DESKTOP_SESSION', 'unknown')
        if desktop_env != 'unknown':
            prompt_parts.append(f"- Desktop environment: {desktop_env}")
        
        return "\n".join(prompt_parts)
    
    def _categorize_application(self, app_name: str) -> str:
        """Categorize an application by type"""
        app_name_lower = app_name.lower()
        
        for category, apps in self.contexts_config.get("applications", {}).items():
            if any(app in app_name_lower for app in apps):
                return category
        
        return "application"
    
    def _analyze_directory_context(self, directory: str) -> Optional[str]:
        """Analyze directory to determine project type"""
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return None
            
            # Check for common project files
            project_indicators = {
                "package.json": "Node.js/JavaScript",
                "requirements.txt": "Python",
                "Pipfile": "Python (Pipenv)",
                "pyproject.toml": "Python (Poetry)",
                "Cargo.toml": "Rust",
                "go.mod": "Go",
                "pom.xml": "Java (Maven)",
                "build.gradle": "Java (Gradle)",
                "composer.json": "PHP",
                "Gemfile": "Ruby",
                "mix.exs": "Elixir",
                "pubspec.yaml": "Dart/Flutter",
                "CMakeLists.txt": "C/C++ (CMake)",
                "Makefile": "C/C++/Make",
                ".gitignore": "Git repository",
                "docker-compose.yml": "Docker project",
                "Dockerfile": "Docker project"
            }
            
            for file, project_type in project_indicators.items():
                if (dir_path / file).exists():
                    return project_type
            
            # Check file extensions in directory
            file_extensions = []
            for file in dir_path.iterdir():
                if file.is_file():
                    file_extensions.append(file.suffix.lower())
            
            # Analyze predominant file types
            for file_type, extensions in self.contexts_config.get("file_extensions", {}).items():
                if any(ext in file_extensions for ext in extensions):
                    return f"{file_type} project"
            
        except Exception as e:
            logger.debug(f"Failed to analyze directory context: {e}")
        
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    detector = ContextDetector()
    
    # Test window info detection
    window_info = detector.get_active_window_info()
    print("Window Info:")
    for key, value in window_info.items():
        print(f"  {key}: {value}")
    
    # Test context prompt building
    print("\nContext Prompt:")
    print(detector.build_context_prompt())