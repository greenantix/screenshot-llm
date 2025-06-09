import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

class ConversationManager:
    def __init__(self):
        self.messages: List[Dict] = []
        self.max_api_messages = 10  # Maximum number of messages to send to API
        self.conversation_dir = Path("conversations")
        
        # Create conversations directory if it doesn't exist
        self.conversation_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique conversation ID
        self.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to the conversation history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        
        if metadata:
            message["metadata"] = metadata
            
        self.messages.append(message)

    def get_messages_for_api(self) -> List[Dict]:
        """Format recent messages for the LLM API"""
        formatted_messages = []
        recent_messages = self.messages[-self.max_api_messages:]
        
        # Add system message with context if first message
        if len(formatted_messages) == 0:
            context = self._format_context_for_llm()
            formatted_messages.append({
                "role": "system",
                "content": context
            })
        
        # Format conversation messages
        for msg in recent_messages:
            formatted_msg = {
                "role": msg["role"],
                "content": msg["content"]
            }
            
            # Handle screenshots in content
            if "metadata" in msg and "screenshot" in msg["metadata"]:
                formatted_msg["content"] = self._format_screenshot_content(
                    msg["content"], 
                    msg["metadata"]["screenshot"]
                )
            
            formatted_messages.append(formatted_msg)
            
        return formatted_messages

    def _format_context_for_llm(self) -> str:
        """Format system context for the LLM"""
        context = [
            "You are an AI assistant helping with desktop and development tasks.",
            "You can see screenshots shared by the user and provide assistance based on them.",
            "You understand technical terminology and can provide code examples when relevant.",
            "",
            "When responding:"
            "- Be concise and direct",
            "- Use markdown formatting for code and technical terms",
            "- If you see a screenshot, describe what you observe before providing help",
        ]
        return "\n".join(context)

    def _format_screenshot_content(self, text: str, screenshot_data: Dict) -> str:
        """Format message content that includes a screenshot"""
        return f"{text}\n[Screenshot showing {screenshot_data.get('description', 'image')}]"

    def save_conversation(self):
        """Save the current conversation to a file"""
        if not self.messages:
            return
            
        filename = f"conversation_{self.conversation_id}.json"
        filepath = self.conversation_dir / filename
        
        conversation_data = {
            "id": self.conversation_id,
            "timestamp": datetime.now().isoformat(),
            "messages": self.messages
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(conversation_data, f, indent=2)

    def load_conversation(self, conversation_id: str) -> bool:
        """Load a conversation from file"""
        filepath = self.conversation_dir / f"conversation_{conversation_id}.json"
        
        if not filepath.exists():
            return False
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                conversation_data = json.load(f)
                
            self.conversation_id = conversation_data["id"]
            self.messages = conversation_data["messages"]
            return True
            
        except Exception as e:
            print(f"Error loading conversation: {e}")
            return False

    def list_conversations(self) -> List[Dict]:
        """List all saved conversations"""
        conversations = []
        
        for filepath in self.conversation_dir.glob("conversation_*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                conversations.append({
                    "id": data["id"],
                    "timestamp": data["timestamp"],
                    "message_count": len(data["messages"]),
                    "first_message": data["messages"][0]["content"][:100] if data["messages"] else ""
                })
            except Exception as e:
                print(f"Error reading conversation file {filepath}: {e}")
                
        return sorted(conversations, key=lambda x: x["timestamp"], reverse=True)

    def new_conversation(self):
        """Start a new conversation"""
        self.messages = []
        self.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def get_conversation_summary(self) -> Dict:
        """Get summary of current conversation"""
        return {
            "id": self.conversation_id,
            "message_count": len(self.messages),
            "start_time": self.messages[0]["timestamp"] if self.messages else None,
            "last_update": self.messages[-1]["timestamp"] if self.messages else None
        }