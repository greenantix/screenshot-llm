#!/usr/bin/env python3
import subprocess
import os
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ContextDetector:
    def __init__(self, contexts_file: str = "~/.local/share/screenshot-llm/config/contexts.json"):
        self.contexts_file = os.path.expanduser(contexts_file)
        self.contexts = self._load_contexts()
        self.is_wayland = os.environ.get('WAYLAND_DISPLAY') is not None
    
    def _load_contexts(self) -> dict:
        """Load context configurations"""
        try:
            with open(self.contexts_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Could not load contexts: {e}")
            return {"default": {
                "apps": ["*"],
                "get_context": "active window title",
                "prompt_template": "Help me with:"
            }}
    
    def get_active_window_info(self) -> Dict[str, str]:
        """Get active window information"""
        window_info = {
            'app_name': '',
            'window_title': '',
            'pid': '',
            'working_dir': ''
        }
        
        try:
            if self.is_wayland:
                window_info.update(self._get_wayland_window_info())
            else:
                window_info.update(self._get_x11_window_info())
        except Exception as e:
            logger.warning(f"Could not get window info: {e}")
        
        return window_info
    
    def _get_wayland_window_info(self) -> Dict[str, str]:
        """Get window info on Wayland (GNOME Shell)"""
        info = {}
        
        try:
            # Get active window via GNOME Shell
            result = subprocess.run([
                'gdbus', 'call', '--session',
                '--dest', 'org.gnome.Shell',
                '--object-path', '/org/gnome/Shell',
                '--method', 'org.gnome.Shell.Eval',
                'global.display.get_focus_window().get_wm_class()'
            ], capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                # Parse the result to get app name
                output = result.stdout.strip()
                if '"' in output:
                    app_name = output.split('"')[1]
                    info['app_name'] = app_name.lower()
            
            # Get window title
            result = subprocess.run([
                'gdbus', 'call', '--session',
                '--dest', 'org.gnome.Shell',
                '--object-path', '/org/gnome/Shell',
                '--method', 'org.gnome.Shell.Eval',
                'global.display.get_focus_window().get_title()'
            ], capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if '"' in output:
                    title = output.split('"')[1]
                    info['window_title'] = title
                    
        except Exception as e:
            logger.debug(f"GNOME Shell method failed: {e}")
            
        # Fallback: try to get info from ps
        if not info.get('app_name'):
            try:
                # Get focused window PID (this is tricky on Wayland)
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                # This is a simplified approach - might need refinement
                for line in result.stdout.split('\n'):
                    if any(term in line.lower() for term in ['gnome-terminal', 'code', 'firefox']):
                        parts = line.split()
                        if len(parts) > 10:
                            info['app_name'] = parts[10].split('/')[-1]
                            info['pid'] = parts[1]
                            break
            except Exception as e:
                logger.debug(f"ps fallback failed: {e}")
        
        return info
    
    def _get_x11_window_info(self) -> Dict[str, str]:
        """Get window info on X11"""
        info = {}
        
        try:
            # Get active window ID
            result = subprocess.run(['xdotool', 'getactivewindow'], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode != 0:
                return info
                
            window_id = result.stdout.strip()
            
            # Get window class (app name)
            result = subprocess.run(['xdotool', 'getwindowname', window_id],
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                info['window_title'] = result.stdout.strip()
            
            # Get window class
            result = subprocess.run(['xprop', '-id', window_id, 'WM_CLASS'],
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                output = result.stdout
                if '"' in output:
                    # WM_CLASS returns something like: WM_CLASS(STRING) = "gnome-terminal-server", "Gnome-terminal"
                    class_name = output.split('"')[1]
                    info['app_name'] = class_name.lower()
            
            # Get PID
            result = subprocess.run(['xdotool', 'getwindowpid', window_id],
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                info['pid'] = result.stdout.strip()
                
        except Exception as e:
            logger.debug(f"X11 window detection failed: {e}")
        
        return info
    
    def get_working_directory(self, pid: str) -> str:
        """Get working directory from PID"""
        if not pid:
            return os.getcwd()
            
        try:
            cwd_path = f"/proc/{pid}/cwd"
            if os.path.exists(cwd_path):
                return os.readlink(cwd_path)
        except Exception as e:
            logger.debug(f"Could not get working directory for PID {pid}: {e}")
        
        return os.getcwd()
    
    def get_git_status(self, working_dir: str) -> str:
        """Get git status if in a git repository"""
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  cwd=working_dir, capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                if result.stdout.strip():
                    return "modified files"
                else:
                    return "clean"
            else:
                return "not a git repo"
        except Exception:
            return "not a git repo"
    
    def detect_context_type(self, window_info: Dict[str, str]) -> str:
        """Detect which context profile to use"""
        app_name = window_info.get('app_name', '').lower()
        
        for context_name, context_config in self.contexts.items():
            if context_name == 'default':
                continue
            for app in context_config['apps']:
                if app.lower() in app_name or app_name.startswith(app.lower()):
                    return context_name
        
        return 'default'
    
    def build_context_prompt(self) -> str:
        """Build context-aware prompt for LLM"""
        window_info = self.get_active_window_info()
        context_type = self.detect_context_type(window_info)
        context_config = self.contexts.get(context_type, self.contexts['default'])
        
        logger.info(f"Detected context: {context_type} for app: {window_info.get('app_name', 'unknown')}")
        
        # Build context variables
        context_vars = {
            'app': window_info.get('app_name', 'unknown'),
            'window_title': window_info.get('window_title', ''),
        }
        
        # Add context-specific variables
        if context_type == 'terminal':
            working_dir = self.get_working_directory(window_info.get('pid', ''))
            context_vars.update({
                'pwd': working_dir,
                'git_status': self.get_git_status(working_dir)
            })
        elif context_type == 'vscode':
            working_dir = self.get_working_directory(window_info.get('pid', ''))
            context_vars.update({
                'project': os.path.basename(working_dir) if working_dir else 'unknown',
                'file': 'current file',  # Would need VS Code API for this
                'language': 'unknown'  # Would need to detect from file extension
            })
        elif context_type == 'browser':
            # For browser, we'd need to extract URL from window title or use browser API
            context_vars.update({
                'url': 'current page',
                'title': window_info.get('window_title', '')
            })
        
        # Format the prompt template
        try:
            prompt = context_config['prompt_template'].format(**context_vars)
        except KeyError as e:
            logger.warning(f"Missing context variable {e}, using default prompt")
            prompt = f"I'm using {context_vars.get('app', 'an application')}. Help me with:"
        
        return prompt

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    detector = ContextDetector()
    window_info = detector.get_active_window_info()
    print(f"Window info: {window_info}")
    prompt = detector.build_context_prompt()
    print(f"Context prompt: {prompt}")