#!/usr/bin/env python3
"""
IPC Handler for Screenshot LLM Assistant

Handles inter-process communication between the daemon and GUI window.
Uses Unix domain sockets for reliable, fast local communication.
"""

import asyncio
import json
import logging
import os
import socket
import threading
from typing import Dict, Any, Callable, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class IPCMessage:
    """Represents an IPC message"""
    def __init__(self, command: str, data: Dict[str, Any] = None):
        self.command = command
        self.data = data or {}
        self.timestamp = None
    
    def to_json(self) -> str:
        """Serialize message to JSON"""
        return json.dumps({
            "command": self.command,
            "data": self.data
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'IPCMessage':
        """Deserialize message from JSON"""
        data = json.loads(json_str)
        return cls(data["command"], data.get("data", {}))

class IPCServer:
    """IPC Server for receiving messages (used by GUI)"""
    
    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self.server_socket = None
        self.running = False
        self.message_handlers: Dict[str, Callable] = {}
        self.clients = []
        
    def register_handler(self, command: str, handler: Callable):
        """Register a handler for a specific command"""
        self.message_handlers[command] = handler
        logger.debug(f"Registered handler for command: {command}")
    
    async def start(self):
        """Start the IPC server"""
        # Remove existing socket file if it exists
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.socket_path), exist_ok=True)
        
        # Create Unix domain socket
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.socket_path)
        self.server_socket.listen(5)
        
        # Set permissions (user only)
        os.chmod(self.socket_path, 0o600)
        
        self.running = True
        logger.info(f"IPC server started on: {self.socket_path}")
        
        try:
            while self.running:
                # Accept connections
                try:
                    client_socket, addr = await asyncio.get_event_loop().run_in_executor(
                        None, self.server_socket.accept
                    )
                    
                    # Handle client in background
                    asyncio.create_task(self._handle_client(client_socket))
                    
                except Exception as e:
                    if self.running:
                        logger.error(f"Error accepting connection: {e}")
                    
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.stop()
    
    async def _handle_client(self, client_socket):
        """Handle messages from a client"""
        try:
            self.clients.append(client_socket)
            
            while self.running:
                try:
                    # Read message length first (4 bytes)
                    length_data = await asyncio.get_event_loop().run_in_executor(
                        None, client_socket.recv, 4
                    )
                    
                    if not length_data:
                        break
                    
                    message_length = int.from_bytes(length_data, byteorder='big')
                    
                    # Read the actual message
                    message_data = b''
                    while len(message_data) < message_length:
                        chunk = await asyncio.get_event_loop().run_in_executor(
                            None, client_socket.recv, message_length - len(message_data)
                        )
                        if not chunk:
                            break
                        message_data += chunk
                    
                    if len(message_data) == message_length:
                        # Process message
                        message_str = message_data.decode('utf-8')
                        await self._process_message(message_str)
                    
                except Exception as e:
                    logger.debug(f"Client communication error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            try:
                client_socket.close()
                if client_socket in self.clients:
                    self.clients.remove(client_socket)
            except:
                pass
    
    async def _process_message(self, message_str: str):
        """Process incoming message"""
        try:
            message = IPCMessage.from_json(message_str)
            logger.debug(f"Received IPC message: {message.command}")
            
            # Call appropriate handler
            if message.command in self.message_handlers:
                handler = self.message_handlers[message.command]
                if asyncio.iscoroutinefunction(handler):
                    await handler(message.data)
                else:
                    handler(message.data)
            else:
                logger.warning(f"No handler for command: {message.command}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def stop(self):
        """Stop the IPC server"""
        self.running = False
        
        # Close all client connections
        for client in self.clients[:]:
            try:
                client.close()
            except:
                pass
        self.clients.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Remove socket file
        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except:
                pass
        
        logger.info("IPC server stopped")

class IPCClient:
    """IPC Client for sending messages (used by daemon)"""
    
    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self.socket = None
        self.connected = False
    
    async def connect(self, timeout: float = 5.0, retries: int = 3) -> bool:
        """Connect to IPC server with retry logic"""
        for attempt in range(retries):
            try:
                # Clean up any existing socket
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                    self.socket = None
                
                # Check if socket file exists
                if not os.path.exists(self.socket_path):
                    logger.debug(f"Socket file {self.socket_path} does not exist (attempt {attempt + 1})")
                    if attempt < retries - 1:
                        await asyncio.sleep(0.5)  # Wait before retry
                        continue
                    return False
                
                self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.socket.settimeout(timeout)
                
                await asyncio.get_event_loop().run_in_executor(
                    None, self.socket.connect, self.socket_path
                )
                
                self.connected = True
                logger.debug(f"Connected to IPC server on attempt {attempt + 1}")
                return True
                
            except (FileNotFoundError, ConnectionRefusedError, OSError) as e:
                logger.debug(f"Connection attempt {attempt + 1} failed: {e}")
                self.connected = False
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                    self.socket = None
                
                if attempt < retries - 1:
                    await asyncio.sleep(0.5)  # Wait before retry
                else:
                    logger.debug(f"All {retries} connection attempts failed")
                    
        return False
    
    async def send_message(self, message: IPCMessage) -> bool:
        """Send message to server with robust error handling"""
        # Try to connect if not connected
        if not self.connected:
            if not await self.connect():
                logger.debug("Could not establish IPC connection")
                return False
        
        try:
            message_str = message.to_json()
            message_bytes = message_str.encode('utf-8')
            
            # Send message length first
            length_bytes = len(message_bytes).to_bytes(4, byteorder='big')
            
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.send, length_bytes + message_bytes
            )
            
            logger.debug(f"Sent IPC message: {message.command}")
            return True
            
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            logger.debug(f"IPC connection lost: {e}")
            self.disconnect()
            
            # Try to reconnect and send once more
            if await self.connect():
                try:
                    message_str = message.to_json()
                    message_bytes = message_str.encode('utf-8')
                    length_bytes = len(message_bytes).to_bytes(4, byteorder='big')
                    
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.socket.send, length_bytes + message_bytes
                    )
                    
                    logger.debug(f"Sent IPC message after reconnect: {message.command}")
                    return True
                except Exception as retry_error:
                    logger.debug(f"Retry send failed: {retry_error}")
                    self.disconnect()
                    return False
            else:
                return False
                
        except Exception as e:
            logger.debug(f"Unexpected error sending IPC message: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    async def send_screenshot(self, image_path: str, context: Dict[str, Any]) -> bool:
        """Send screenshot notification to GUI"""
        message = IPCMessage("screenshot", {
            "image_path": image_path,
            "context": context
        })
        return await self.send_message(message)
    
    async def send_llm_response(self, response_text: str) -> bool:
        """Send LLM response to GUI"""
        message = IPCMessage("llm_response", {
            "response": response_text
        })
        return await self.send_message(message)
    
    async def show_window(self) -> bool:
        """Request GUI to show/focus window"""
        message = IPCMessage("show_window", {})
        return await self.send_message(message)
    
    async def hide_window(self) -> bool:
        """Request GUI to hide window"""
        message = IPCMessage("hide_window", {})
        return await self.send_message(message)

class IPCManager:
    """Manages IPC for both client and server roles"""
    
    def __init__(self, config_dir: str = "~/.local/share/screenshot-llm"):
        self.config_dir = os.path.expanduser(config_dir)
        self.socket_path = os.path.join(self.config_dir, "screenshot-llm.sock")
        
    def create_server(self) -> IPCServer:
        """Create IPC server instance"""
        try:
            logger.debug(f"Creating IPC server with socket path: {self.socket_path}")
            server = IPCServer(self.socket_path)
            logger.debug(f"IPC server created successfully: {server}")
            return server
        except Exception as e:
            logger.error(f"Failed to create IPC server: {e}")
            return None
    
    def create_client(self) -> IPCClient:
        """Create IPC client instance"""
        return IPCClient(self.socket_path)
    
    def is_server_running(self) -> bool:
        """Check if IPC server is running"""
        return os.path.exists(self.socket_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    async def test_ipc():
        """Test IPC functionality"""
        manager = IPCManager()
        
        # Test server
        server = manager.create_server()
        
        def handle_test(data):
            print(f"Server received: {data}")
        
        server.register_handler("test", handle_test)
        
        # Start server in background
        server_task = asyncio.create_task(server.start())
        
        # Give server time to start
        await asyncio.sleep(0.5)
        
        # Test client
        client = manager.create_client()
        
        success = await client.send_message(IPCMessage("test", {"message": "Hello IPC!"}))
        print(f"Client send result: {success}")
        
        # Cleanup
        await asyncio.sleep(0.5)
        server.stop()
        client.disconnect()
        
        try:
            await server_task
        except:
            pass
    
    asyncio.run(test_ipc())