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
    def __init__(self, config_file: str = "~/.local/share/screenshot-llm/config/config.json"):
        self.config_file = os.path.expanduser(config_file)
        self.config = self._load_config()
        self.client = None
        self._initialize_client()
    
    def _load_config(self) -> dict:
        """Load API configuration"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            # Check for API key in environment if not in config
            if not config.get('api_key'):
                if config.get('provider') == 'anthropic':
                    config['api_key'] = os.environ.get('ANTHROPIC_API_KEY', '')
                elif config.get('provider') == 'openai':
                    config['api_key'] = os.environ.get('OPENAI_API_KEY', '')
                    
            return config
        except Exception as e:
            logger.error(f"Could not load config: {e}")
            return {
                'provider': 'anthropic',
                'api_key': '',
                'model': 'claude-3-5-haiku-20241022',
                'max_tokens': 4096
            }
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        if not self.config.get('api_key'):
            logger.error("No API key configured")
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
        self.config['api_key'] = api_key
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self._initialize_client()
            logger.info("API key updated successfully")
        except Exception as e:
            logger.error(f"Failed to update API key: {e}")
            raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def test_client():
        client = LLMClient()
        # This would need a real screenshot file to test
        # response = await client.send_screenshot("/path/to/screenshot.png", "Help me with this terminal:")
        # print(response)
        print("LLM client initialized successfully")
    
    asyncio.run(test_client())