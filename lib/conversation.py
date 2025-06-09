#!/usr/bin/env python3
"""
Conversation Manager for Screenshot LLM Assistant

Handles conversation history, message formatting, and persistence.
"""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self, config_dir: str = "~/.local/share/screenshot-llm", config: Dict = None):
        self.config_dir = os.path.expanduser(config_dir)
        self.conversations_dir = os.path.join(self.config_dir, "conversations")
        os.makedirs(self.conversations_dir, exist_ok=True)
        
        self.messages: List[Dict[str, Any]] = []
        self.current_context = {}
        self.conversation_id = None
        
        # Get max_api_messages from config or use default
        conv_config = config.get("conversation", {}) if config else {}
        self.max_api_messages = conv_config.get("max_api_messages", 10)
        
    def create_new_conversation(self) -> str:
        """Create a new conversation with unique ID"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.conversation_id = f"conversation_{timestamp}"
        self.messages.clear()
        self.current_context.clear()
        
        logger.info(f"Created new conversation: {self.conversation_id}")
        return self.conversation_id
    
    def add_screenshot_message(self, image_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add screenshot message to conversation"""
        message = {
            "timestamp": datetime.now().isoformat(),
            "type": "screenshot",
            "content": f"Screenshot: {os.path.basename(image_path)}",
            "image_path": image_path,
            "context": context
        }
        
        self.messages.append(message)
        self.current_context.update(context)
        
        # Auto-save conversation
        self._auto_save()
        
        logger.info(f"Added screenshot message: {message['content']}")
        return message
    
    def add_user_message(self, text: str) -> Dict[str, Any]:
        """Add user text message to conversation"""
        message = {
            "timestamp": datetime.now().isoformat(),
            "type": "user",
            "content": text,
            "context": self.current_context.copy()
        }
        
        self.messages.append(message)
        
        # Auto-save conversation
        self._auto_save()
        
        logger.info("Added user message")
        return message
    
    def add_assistant_message(self, text: str) -> Dict[str, Any]:
        """Add assistant response to conversation"""
        message = {
            "timestamp": datetime.now().isoformat(),
            "type": "assistant",
            "content": text,
            "context": self.current_context.copy()
        }
        
        self.messages.append(message)
        
        # Auto-save conversation
        self._auto_save()
        
        logger.info("Added assistant message")
        return message
    
    def get_messages_for_api(self) -> List[Dict[str, Any]]:
        """Format recent messages for LLM API"""
        # Get the most recent messages up to the limit
        recent_messages = self.messages[-self.max_api_messages:]
        
        api_messages = []
        
        for msg in recent_messages:
            if msg["type"] == "screenshot":
                # Format screenshot message for API
                context_text = self._format_context(msg.get("context", {}))
                api_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{context_text}\n\nPlease analyze this screenshot and provide helpful commands or suggestions. Format any commands in code blocks for easy copying."
                        },
                        {
                            "type": "image_path",  # Will be processed by LLM client
                            "image_path": msg["image_path"]
                        }
                    ]
                })
            elif msg["type"] == "user":
                api_messages.append({
                    "role": "user",
                    "content": msg["content"]
                })
            elif msg["type"] == "assistant":
                api_messages.append({
                    "role": "assistant",
                    "content": msg["content"]
                })
        
        return api_messages
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for display"""
        if not context:
            return "Screenshot captured"
        
        parts = []
        
        if context.get("app"):
            parts.append(f"Active application: {context['app']}")
        
        if context.get("window_title"):
            parts.append(f"Window title: {context['window_title']}")
        
        if context.get("working_directory"):
            parts.append(f"Working directory: {context['working_directory']}")
        
        if context.get("screen_info"):
            parts.append(f"Screen: {context['screen_info']}")
        
        return "Context:\n" + "\n".join(f"- {part}" for part in parts) if parts else "Screenshot captured"
    
    def save_conversation(self, conversation_id: Optional[str] = None) -> str:
        """Save conversation to disk"""
        if not conversation_id:
            conversation_id = self.conversation_id or self.create_new_conversation()
        
        conversation_data = {
            "id": conversation_id,
            "created": datetime.now().isoformat(),
            "messages": self.messages,
            "context": self.current_context
        }
        
        filepath = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        
        try:
            with open(filepath, 'w') as f:
                json.dump(conversation_data, f, indent=2)
            
            logger.info(f"Saved conversation to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            raise
    
    def load_conversation(self, conversation_id: str) -> bool:
        """Load conversation from disk"""
        filepath = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        
        if not os.path.exists(filepath):
            logger.warning(f"Conversation file not found: {filepath}")
            return False
        
        try:
            with open(filepath, 'r') as f:
                conversation_data = json.load(f)
            
            self.conversation_id = conversation_data["id"]
            self.messages = conversation_data.get("messages", [])
            self.current_context = conversation_data.get("context", {})
            
            logger.info(f"Loaded conversation: {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to load conversation: {e}")
            return False
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all saved conversations"""
        conversations = []
        
        try:
            for filename in os.listdir(self.conversations_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.conversations_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                        
                        # Get conversation summary
                        message_count = len(data.get("messages", []))
                        last_message_time = None
                        
                        if data.get("messages"):
                            last_message_time = data["messages"][-1].get("timestamp")
                        
                        conversations.append({
                            "id": data["id"],
                            "created": data.get("created"),
                            "last_activity": last_message_time,
                            "message_count": message_count,
                            "filepath": filepath
                        })
                    except Exception as e:
                        logger.warning(f"Could not read conversation file {filename}: {e}")
            
            # Sort by last activity (most recent first)
            conversations.sort(key=lambda x: x.get("last_activity", ""), reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
        
        return conversations
    
    def _auto_save(self):
        """Auto-save conversation after each message"""
        if self.conversation_id and self.messages:
            try:
                self.save_conversation()
            except Exception as e:
                logger.warning(f"Auto-save failed: {e}")
    
    def get_conversation_summary(self) -> str:
        """Get a brief summary of the current conversation"""
        if not self.messages:
            return "Empty conversation"
        
        message_count = len(self.messages)
        screenshot_count = len([m for m in self.messages if m["type"] == "screenshot"])
        
        if self.messages:
            start_time = datetime.fromisoformat(self.messages[0]["timestamp"])
            duration = datetime.now() - start_time
            
            return f"{message_count} messages, {screenshot_count} screenshots, {duration.total_seconds()//60:.0f}m ago"
        
        return f"{message_count} messages, {screenshot_count} screenshots"
    
    def clear_conversation(self):
        """Clear current conversation"""
        self.messages.clear()
        self.current_context.clear()
        self.conversation_id = None
        logger.info("Conversation cleared")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test the conversation manager
    conv = ConversationManager()
    conv.create_new_conversation()
    
    # Add some test messages
    conv.add_screenshot_message(
        "/tmp/test.png", 
        {"app": "terminal", "window_title": "zsh"}
    )
    conv.add_assistant_message("I can see you're working in the terminal. How can I help?")
    conv.add_user_message("How do I list files?")
    conv.add_assistant_message("You can use the `ls` command to list files in the current directory.")
    
    # Test API message formatting
    api_messages = conv.get_messages_for_api()
    print(f"API messages: {len(api_messages)}")
    
    # Test save/load
    conv.save_conversation()
    
    print(f"Conversation summary: {conv.get_conversation_summary()}")