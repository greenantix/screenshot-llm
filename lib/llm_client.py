#!/usr/bin/env python3
import os
import json
import base64
import logging
import asyncio
from typing import Optional, Dict
import anthropic
import openai
from PIL import Image

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, llm_config: Dict):
        self.config = self._validate_config(llm_config)
        self.client = None
        self._initialize_client()

    def _validate_config(self, llm_config: Dict) -> dict:
        """Validate and set defaults for the LLM configuration."""
        # Check for API key in environment if not in config
        if not llm_config.get('api_key'):
            provider = llm_config.get('provider', 'openai')
            if provider == 'anthropic':
                llm_config['api_key'] = os.environ.get('ANTHROPIC_API_KEY', '')
            else: # default to openai
                llm_config['api_key'] = os.environ.get('OPENAI_API_KEY', '')
        
        # Set defaults
        defaults = {
            'provider': 'openai',
            'model': 'gpt-4o',
            'max_tokens': 4096,
            'temperature': 0.7
        }
        
        if llm_config.get('provider') == 'anthropic':
            defaults['model'] = 'claude-3-5-sonnet-20241022'
        
        # Merge defaults with provided config
        config = defaults.copy()
        config.update(llm_config)
        return config
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        if not self.config.get('api_key') or self.config.get('api_key') == '':
            provider = self.config.get('provider', 'openai')
            env_var = 'OPENAI_API_KEY' if provider == 'openai' else 'ANTHROPIC_API_KEY'
            logger.error(f"No API key configured for {provider}. Please set {env_var} environment variable or update config/config.json")
            return
            
        try:
            if self.config['provider'] == 'anthropic':
                self.client = anthropic.AsyncAnthropic(api_key=self.config['api_key'])
            elif self.config['provider'] == 'openai':
                self.client = openai.AsyncOpenAI(api_key=self.config['api_key'])
            else:
                logger.error(f"Unsupported provider: {self.config['provider']}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        try:
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encode image: {e}")
            raise
    
    def _get_image_mime_type(self, image_path: str) -> str:
        """Get image MIME type"""
        ext = os.path.splitext(image_path)[1].lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp'
        }
        return mime_types.get(ext, 'image/png')
    
    async def send_screenshot(self, image_path: str, context_prompt: str) -> str:
        """Send screenshot to LLM and get response"""
        if not self.client:
            raise Exception("LLM client not initialized")
        
        try:
            # Encode image
            image_data = self._encode_image(image_path)
            mime_type = self._get_image_mime_type(image_path)
            
            if self.config['provider'] == 'anthropic':
                return await self._send_anthropic(image_data, mime_type, context_prompt)
            elif self.config['provider'] == 'openai':
                return await self._send_openai(image_data, mime_type, context_prompt)
            else:
                raise Exception(f"Unsupported provider: {self.config['provider']}")
                
        except Exception as e:
            logger.error(f"Failed to send screenshot to LLM: {e}")
            raise
    
    async def send_conversation(self, messages: list, context_prompt: str = "") -> str:
        """Send conversation with context to LLM"""
        if not self.client:
            raise Exception("LLM client not initialized")
        
        try:
            if self.config['provider'] == 'anthropic':
                return await self._send_anthropic_conversation(messages, context_prompt)
            elif self.config['provider'] == 'openai':
                return await self._send_openai_conversation(messages, context_prompt)
            else:
                raise Exception(f"Unsupported provider: {self.config['provider']}")
                
        except Exception as e:
            logger.error(f"Failed to send conversation to LLM: {e}")
            raise
    
    async def _send_anthropic(self, image_data: str, mime_type: str, context_prompt: str) -> str:
        """Send to Anthropic Claude"""
        message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"{context_prompt}\n\nPlease analyze this screenshot and provide helpful commands or suggestions. Format any commands in code blocks for easy copying."
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_data
                    }
                }
            ]
        }
        
        response = await self.client.messages.create(
            model=self.config['model'],
            max_tokens=self.config['max_tokens'],
            messages=[message]
        )
        
        return response.content[0].text
    
    async def _send_openai(self, image_data: str, mime_type: str, context_prompt: str) -> str:
        """Send to OpenAI"""
        message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"{context_prompt}\n\nPlease analyze this screenshot and provide helpful commands or suggestions. Format any commands in code blocks for easy copying."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_data}"
                    }
                }
            ]
        }
        
        response = await self.client.chat.completions.create(
            model=self.config['model'],
            max_tokens=self.config['max_tokens'],
            messages=[message]
        )
        
        return response.choices[0].message.content
    
    def update_api_key(self, api_key: str):
        """Update API key in config"""
        try:
            # Load full config
            with open(self.config_file, 'r') as f:
                full_config = json.load(f)
            
            # Update API key
            if 'llm' not in full_config:
                full_config['llm'] = {}
            full_config['llm']['api_key'] = api_key
            
            # Save updated config
            with open(self.config_file, 'w') as f:
                json.dump(full_config, f, indent=2)
            
            # Update current config and reinitialize client
            self.config['api_key'] = api_key
            self._initialize_client()
            
            logger.info("API key updated successfully")
            
        except Exception as e:
            logger.error(f"Failed to update API key: {e}")
            raise
    
    async def _send_anthropic_conversation(self, messages: list, context_prompt: str = "") -> str:
        """Send conversation to Anthropic Claude"""
        # Format messages for Anthropic
        formatted_messages = []
        
        for msg in messages:
            if msg.get("role") == "system":
                continue  # System messages handled separately
            
            content = msg.get("content", "")
            if isinstance(content, list):
                # Handle multipart content (text + images)
                formatted_messages.append({
                    "role": msg["role"],
                    "content": content
                })
            else:
                # Simple text content
                formatted_messages.append({
                    "role": msg["role"],
                    "content": content
                })
        
        # Add system prompt if provided
        system_prompt = context_prompt if context_prompt else "You are a helpful AI assistant."
        
        response = await self.client.messages.create(
            model=self.config['model'],
            max_tokens=self.config['max_tokens'],
            system=system_prompt,
            messages=formatted_messages
        )
        
        return response.content[0].text
    
    async def _send_openai_conversation(self, messages: list, context_prompt: str = "") -> str:
        """Send conversation to OpenAI"""
        # Format messages for OpenAI
        formatted_messages = []
        
        # Add system message if provided
        if context_prompt:
            formatted_messages.append({
                "role": "system",
                "content": context_prompt
            })
        
        for msg in messages:
            content = msg.get("content", "")
            
            if isinstance(content, list):
                # Handle multipart content (text + images)
                formatted_content = []
                
                for part in content:
                    if part.get("type") == "text":
                        formatted_content.append({
                            "type": "text",
                            "text": part["text"]
                        })
                    elif part.get("type") == "image_path":
                        # Convert image_path to base64 for OpenAI
                        try:
                            image_data = self._encode_image(part["image_path"])
                            mime_type = self._get_image_mime_type(part["image_path"])
                            formatted_content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            })
                        except Exception as e:
                            logger.error(f"Failed to process image: {e}")
                            # Skip the image part if processing fails
                            continue
                
                formatted_messages.append({
                    "role": msg["role"],
                    "content": formatted_content
                })
            else:
                # Simple text content
                formatted_messages.append({
                    "role": msg["role"],
                    "content": content
                })
        
        response = await self.client.chat.completions.create(
            model=self.config['model'],
            max_tokens=self.config['max_tokens'],
            messages=formatted_messages
        )
        
        return response.choices[0].message.content

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def test_client():
        client = LLMClient()
        # This would need a real screenshot file to test
        # response = await client.send_screenshot("/path/to/screenshot.png", "Help me with this terminal:")
        # print(response)
        print("LLM client initialized successfully")
    
    asyncio.run(test_client())