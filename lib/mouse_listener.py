#!/usr/bin/env python3
"""
Mouse listener for Screenshot LLM Assistant
"""

import asyncio
import logging
from typing import Callable
import evdev
from evdev import InputDevice, categorize, ecodes

logger = logging.getLogger(__name__)

class MouseListener:
    """Listens for mouse button presses"""
    
    def __init__(self, button_code: int = 276, callback: Callable = None, device_path: str = None):
        # Default to button 276 (BTN_EXTRA/BTN_FORWARD), which is commonly mouse button 9
        self.button_code = button_code
        self.callback = callback
        self.device_path = device_path
        self.running = False
        self.device = None
        
    async def listen(self):
        """Start listening for mouse events"""
        self.running = True
        
        # Find mouse device
        if self.device_path:
            try:
                logger.info(f"Using specified mouse device: {self.device_path}")
                self.device = InputDevice(self.device_path)
            except Exception as e:
                logger.error(f"Failed to open specified device '{self.device_path}': {e}")
                logger.error("Falling back to auto-detection.")
                self.device = self._find_mouse_device()
        else:
            self.device = self._find_mouse_device()

        if not self.device:
            logger.error("No suitable mouse device found. Please specify it in config.json.")
            return
        
        logger.info(f"Listening for mouse button {self.button_code} on {self.device.path}")
        
        try:
            async for event in self.device.async_read_loop():
                if not self.running:
                    break
                    
                if event.type == ecodes.EV_KEY and event.code == self.button_code and event.value == 1:
                    logger.info(f"Mouse button {self.button_code} pressed")
                    if self.callback:
                        await self.callback()
                        
        except Exception as e:
            logger.error(f"Error in mouse listener: {e}")
        finally:
            self.stop()
    
    def _find_mouse_device(self):
        """Find a suitable mouse device with robust scoring algorithm."""
        devices = [InputDevice(path) for path in evdev.list_devices()]
        scored_candidates = []

        logger.debug("--- Scanning for Mouse Devices ---")
        for device in devices:
            capabilities = device.capabilities(verbose=False)
            device_name = device.name.lower()
            logger.debug(f"Checking device: {device.name} ({device.path})")

            # --- Basic Requirements ---
            # 1. Must have key/button events
            if ecodes.EV_KEY not in capabilities:
                logger.debug("  -> Skipping: No EV_KEY capability.")
                continue
            
            # 2. Must have relative movement events (critical for being a mouse)
            if ecodes.EV_REL not in capabilities:
                logger.debug("  -> Skipping: No EV_REL capability (not a mouse).")
                continue

            # 3. Must have the target button code
            keys = capabilities[ecodes.EV_KEY]
            if self.button_code not in keys:
                logger.debug(f"  -> Skipping: Does not have target button {self.button_code}.")
                continue

            # --- Scoring Algorithm ---
            score = 0
            reasons = []

            # Positive indicators - prioritize actual mice over composite devices
            if "rival 3" in device_name and "keyboard" not in device_name:
                score += 150
                reasons.append("Rival 3 mouse (+150)")
            elif "rival" in device_name and "keyboard" not in device_name:
                score += 120
                reasons.append("Rival series mouse (+120)")
            elif "mouse" in device_name:
                score += 100
                reasons.append("has 'mouse' in name (+100)")
            
            # Check for standard mouse buttons (strong positive indicator)
            if ecodes.BTN_LEFT in keys and ecodes.BTN_RIGHT in keys:
                score += 80
                reasons.append("has left/right buttons (+80)")
            elif ecodes.BTN_LEFT in keys or ecodes.BTN_RIGHT in keys:
                score += 40
                reasons.append("has basic mouse button (+40)")

            # Middle button is also a good indicator
            if ecodes.BTN_MIDDLE in keys:
                score += 20
                reasons.append("has middle button (+20)")

            # Bonus for SteelSeries devices (user's hardware)
            if "steelseries" in device_name:
                score += 30
                reasons.append("SteelSeries device (+30)")
            
            # Penalty for composite device names (like "Apex 7 TKL Mouse" which is part of keyboard)
            if any(kb_name in device_name for kb_name in ["apex", "tkl"]):
                score -= 50
                reasons.append("composite keyboard device (-50)")

            # Negative indicators (heavy penalties)
            if any(keyword in device_name for keyword in ['keyboard', 'kbd', 'keypad']):
                score -= 200
                reasons.append("keyboard-related name (-200)")
            
            if "consumer control" in device_name:
                score -= 150
                reasons.append("consumer control device (-150)")

            # Bonus for devices with more mouse-like button ranges
            mouse_button_count = sum(1 for key in keys if 272 <= key <= 279)  # BTN_LEFT to BTN_TASK
            if mouse_button_count >= 5:
                score += 50
                reasons.append(f"many mouse buttons ({mouse_button_count}) (+50)")
            elif mouse_button_count >= 3:
                score += 25
                reasons.append(f"several mouse buttons ({mouse_button_count}) (+25)")

            logger.debug(f"  -> Score: {score}, Reasons: {', '.join(reasons)}")
            
            if score > 0:  # Only consider devices with positive scores
                scored_candidates.append((score, device, reasons))
                logger.debug("  -> Added as candidate")
            else:
                logger.debug("  -> Rejected (negative score)")

        logger.debug("--- Finished Scanning ---")

        if not scored_candidates:
            logger.error("No suitable mouse device found after scoring.")
            logger.error("Please run 'test-mouse-devices.py' to debug.")
            return None

        # Sort by score (highest first) and select the best
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, selected_device, best_reasons = scored_candidates[0]
        
        logger.info(f"Selected mouse device: {selected_device.name} at {selected_device.path}")
        logger.info(f"Selection score: {best_score}, Reasons: {', '.join(best_reasons)}")
        
        # Log other candidates for debugging
        if len(scored_candidates) > 1:
            logger.debug("Other candidates:")
            for score, device, reasons in scored_candidates[1:4]:  # Show top 3 alternatives
                logger.debug(f"  {device.name} (score: {score})")
        
        return selected_device
    
    def stop(self):
        """Stop listening for mouse events"""
        self.running = False
        if self.device:
            self.device.close()
            self.device = None
        logger.info("Mouse listener stopped")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def test_callback():
        print("Mouse button pressed!")
    
    async def main():
        listener = MouseListener(button_code=276, callback=test_callback)
        
        try:
            await listener.listen()
        except KeyboardInterrupt:
            listener.stop()
    
    asyncio.run(main())