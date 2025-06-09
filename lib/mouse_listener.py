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
        """Find a suitable mouse device with stricter filtering."""
        devices = [InputDevice(path) for path in evdev.list_devices()]
        mouse_candidates = []

        logger.debug("--- Scanning for Mouse Devices ---")
        for device in devices:
            capabilities = device.capabilities(verbose=False)
            device_name = device.name.lower()
            logger.debug(f"Checking device: {device.name} ({device.path})")

            # --- Strict Filtering Criteria ---
            # 1. Must have key/button events
            if ecodes.EV_KEY not in capabilities:
                logger.debug("  -> Skipping: No EV_KEY capability.")
                continue
            
            # 2. Must have relative movement events (critical for being a mouse)
            if ecodes.EV_REL not in capabilities:
                logger.debug("  -> Skipping: No EV_REL capability (not a mouse).")
                continue

            # 3. Must NOT be a keyboard
            if any(keyword in device_name for keyword in ['keyboard', 'kbd', 'keypad']):
                logger.debug("  -> Skipping: Name suggests it's a keyboard.")
                continue

            # 4. Must have the target button code
            keys = capabilities[ecodes.EV_KEY]
            if self.button_code not in keys:
                logger.debug(f"  -> Skipping: Does not have target button {self.button_code}.")
                continue
            
            logger.debug("  -> Candidate passed initial filters.")
            
            mouse_candidates.append(device)

        logger.debug("--- Finished Scanning ---")

        if not mouse_candidates:
            logger.error("No suitable mouse device found after strict filtering.")
            logger.error("Please run 'test-mouse-devices.py' to debug.")
            return None

        # --- Advanced Prioritization ---
        # Prioritize the best match from the candidates
        
        # 1. Perfect match: "Rival 3" but not "Wireless"
        for device in mouse_candidates:
            if "rival 3" in device.name.lower() and "wireless" not in device.name.lower():
                logger.info(f"Found ideal device: {device.name}")
                return device

        # 2. Fallback: Any "Rival" mouse
        for device in mouse_candidates:
            if "rival" in device.name.lower():
                logger.info(f"Found fallback 'Rival' device: {device.name}")
                return device
                
        # 3. Generic fallback: First device in the list
        selected_device = mouse_candidates[0]
        logger.info(f"Selected mouse device: {selected_device.name} at {selected_device.path}")
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