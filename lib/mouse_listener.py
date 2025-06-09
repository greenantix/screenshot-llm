#!/usr/bin/env python3
import asyncio
import logging
from typing import Callable, Optional
from evdev import InputDevice, categorize, ecodes
import glob
import os

logger = logging.getLogger(__name__)

class MouseListener:
    def __init__(self, button_code: int = 9, callback: Optional[Callable] = None):
        self.button_code = button_code
        self.callback = callback
        self.devices = []
        self.running = False
        
    def find_mouse_devices(self):
        """Find all mouse input devices"""
        devices = []
        for device_path in glob.glob('/dev/input/event*'):
            try:
                device = InputDevice(device_path)
                # Check if device has mouse buttons
                if ecodes.BTN_MOUSE in device.capabilities().get(ecodes.EV_KEY, []):
                    devices.append(device)
                    logger.info(f"Found mouse device: {device.name} at {device_path}")
            except (OSError, PermissionError) as e:
                logger.debug(f"Cannot access {device_path}: {e}")
        return devices
    
    async def listen(self):
        """Listen for mouse button events"""
        self.devices = self.find_mouse_devices()
        if not self.devices:
            logger.error("No mouse devices found or insufficient permissions")
            logger.info("Try adding user to 'input' group: sudo usermod -a -G input $USER")
            return
        
        self.running = True
        logger.info(f"Listening for mouse button {self.button_code} on {len(self.devices)} devices")
        
        try:
            while self.running:
                # Use select to wait for events from any device
                import select
                device_fds = {dev.fd: dev for dev in self.devices}
                
                if not device_fds:
                    await asyncio.sleep(0.1)
                    continue
                
                # Wait for events with timeout
                ready_fds, _, _ = select.select(device_fds.keys(), [], [], 0.1)
                
                for fd in ready_fds:
                    device = device_fds[fd]
                    try:
                        for event in device.read():
                            if (event.type == ecodes.EV_KEY and 
                                event.code == ecodes.BTN_EXTRA and  # Button 9 is BTN_FORWARD
                                event.value == 1):  # Button press (not release)
                                logger.info(f"Mouse button {self.button_code} pressed")
                                if self.callback:
                                    await self.callback()
                    except OSError:
                        # Device disconnected
                        logger.warning(f"Device {device.path} disconnected")
                        self.devices.remove(device)
                
                await asyncio.sleep(0.001)  # Small delay to prevent high CPU usage
                
        except KeyboardInterrupt:
            logger.info("Mouse listener stopped by user")
        except Exception as e:
            logger.error(f"Error in mouse listener: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop listening"""
        self.running = False
        for device in self.devices:
            device.close()
        self.devices.clear()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def test_callback():
        print("Button 9 pressed!")
    
    listener = MouseListener(callback=test_callback)
    asyncio.run(listener.listen())