import requests
import json
from typing import List, Optional, AsyncGenerator
import asyncio
import aiohttp
from models import ChatMessage, MessageRole

class OllamaService:
    def __init__(self, host: str = "http://localhost:11434", model: str = "tinyllama"):
        self.host = host
        self.model = model
        self.api_generate = f"{host}/api/generate"
        self.api_chat = f"{host}/api/chat"
        self.api_tags = f"{host}/api/tags"

    async def check_connection(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_tags) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [m['name'] for m in data.get('models', [])]
                        return any(self.model in model for model in models)
        except:
            return False
        return False

    async def pull_model(self) -> bool:
        """Pull the model if not available"""
        try:
            async with aiohttp.ClientSession() as session:
                data = {"name": self.model}
                async with session.post(f"{self.host}/api/pull", json=data) as response:
                    if response.status == 200:
                        # Stream the pull progress
                        async for line in response.content:
                            if line:
                                progress = json.loads(line)
                                if progress.get('status') == 'success':
                                    return True
        except Exception as e:
            print(f"Error pulling model: {e}")
        return False

    async def generate_response(
        self,
        prompt: str,
        context: Optional[List[ChatMessage]] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Generate response from Ollama"""
        # Build conversation context
        messages = []

        # Add system message for Bao's personality
        messages.append({
            "role": "system",
            "content": "You are Bao, a friendly and helpful AI assistant shaped like a cute bao bun. You're warm, approachable, and always eager to help. You love making people smile and occasionally make gentle bao-related puns."
        })

        # Add conversation history
        if context:
            for msg in context[-10:]:  # Keep last 10 messages for context
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })

        # Add current prompt
        messages.append({
            "role": "user",
            "content": prompt
        })

        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "model": self.model,
                    "messages": messages,
                    "stream": stream
                }

                async with session.post(self.api_chat, json=data) as response:
                    if response.status == 200:
                        if stream:
                            async for line in response.content:
                                if line:
                                    try:
                                        chunk = json.loads(line)
                                        if chunk.get('message', {}).get('content'):
                                            yield chunk['message']['content']
                                    except json.JSONDecodeError:
                                        continue
                        else:
                            result = await response.json()
                            yield result.get('message', {}).get('content', '')
                    else:
                        yield f"Error: Unable to generate response (Status: {response.status})"
        except aiohttp.ClientError as e:
            yield f"Error connecting to Ollama: {str(e)}. Please ensure Ollama is running."
        except Exception as e:
            yield f"Unexpected error: {str(e)}"

    async def generate_simple(self, prompt: str) -> str:
        """Generate a simple non-streaming response"""
        full_response = ""
        async for chunk in self.generate_response(prompt, stream=False):
            full_response += chunk
        return full_response

    def should_search(self, message: str) -> bool:
        """Determine if a message requires web search"""
        search_indicators = [
            'search', 'look up', 'find out', 'what is the latest',
            'current', 'today', 'recent', 'news', 'weather',
            'price', 'stock', 'when', 'where is', 'who is',
            'latest', 'newest', 'updated', '2024', '2025'
        ]
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in search_indicators)