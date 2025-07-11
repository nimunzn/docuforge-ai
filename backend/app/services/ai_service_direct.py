from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.core.config import settings
import asyncio
import json
import aiohttp
import openai
import httpx


class AIProvider(ABC):
    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        pass

    @abstractmethod
    async def stream_generate(self, messages: List[Dict[str, str]], **kwargs):
        pass


class OpenAIProvider(AIProvider):
    def __init__(self, model: str = "gpt-4"):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 2000)
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    async def stream_generate(self, messages: List[Dict[str, str]], **kwargs):
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 2000),
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error streaming response: {str(e)}"


class ClaudeProvider(AIProvider):
    def __init__(self, model: str = "claude-3-sonnet-20240229"):
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")
        self.model = model
        self.api_key = settings.anthropic_api_key
        self.base_url = "https://api.anthropic.com"
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            # Convert messages to Claude format
            claude_messages = []
            system_message = None
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    claude_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "max_tokens": kwargs.get('max_tokens', 2000),
                "messages": claude_messages
            }
            
            if system_message:
                payload["system"] = system_message
            
            # Make direct HTTP request to Claude API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/messages",
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01"
                    },
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["content"][0]["text"]
                    else:
                        error_text = await response.text()
                        return f"Error: {response.status} - {error_text}"
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    async def stream_generate(self, messages: List[Dict[str, str]], **kwargs):
        try:
            # For now, generate and yield as chunks (works with both async and sync)
            response = await self.generate(messages, **kwargs)
            
            # Simulate streaming by yielding words
            words = response.split()
            for word in words:
                yield word + " "
                await asyncio.sleep(0.05)
                
        except Exception as e:
            yield f"Error streaming response: {str(e)}"


class MockProvider(AIProvider):
    """Mock provider for testing when no API keys are available"""
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        user_message = messages[-1]["content"].lower()
        
        if "document" in user_message and "proposal" in user_message:
            return json.dumps({
                "title": "Business Proposal",
                "sections": [
                    {"title": "Executive Summary", "content": "This proposal outlines a comprehensive solution to address the identified business opportunity."},
                    {"title": "Problem Statement", "content": "The current market situation presents significant challenges that require immediate attention."},
                    {"title": "Proposed Solution", "content": "We propose a innovative approach that leverages cutting-edge technology and proven methodologies."},
                    {"title": "Implementation Timeline", "content": "The project will be executed in three phases over 6 months."},
                    {"title": "Budget and Resources", "content": "Total investment required: $150,000 with expected ROI of 300% within 18 months."},
                    {"title": "Conclusion", "content": "This proposal represents a strategic opportunity for significant growth and market expansion."}
                ],
                "metadata": {
                    "document_type": "proposal",
                    "generated_by": "mock"
                }
            })
        
        elif "intent" in user_message:
            return json.dumps({
                "intent": "create_document",
                "document_type": "proposal",
                "confidence": 0.9,
                "parameters": {"title": "Business Proposal"},
                "clarification_needed": False
            })
        
        elif "expand" in user_message:
            return "This section provides detailed information about the topic, including relevant examples, supporting data, and comprehensive analysis to strengthen the main arguments presented."
        
        elif "style" in user_message:
            return json.dumps({
                "title": "Business Proposal",
                "sections": [
                    {"title": "Executive Summary", "content": "This professional proposal outlines a strategic business opportunity."},
                    {"title": "Problem Statement", "content": "The current business environment requires innovative solutions."}
                ],
                "metadata": {"style": "professional"}
            })
        
        elif "summary" in user_message:
            return "This document provides a comprehensive overview of the business proposal, including problem analysis, solution recommendations, and implementation roadmap."
        
        else:
            return f"I understand you're asking about: {user_message}. I can help you create professional documents, analyze content, and provide strategic recommendations."
    
    async def stream_generate(self, messages: List[Dict[str, str]], **kwargs):
        response = await self.generate(messages, **kwargs)
        
        # Simulate streaming
        words = response.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05)


class AIService:
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider,
            "claude": ClaudeProvider,  # Always include Claude
            "mock": MockProvider
        }
        self.default_provider = "openai"
    
    def get_provider(self, provider_name: str = None, model: str = None) -> AIProvider:
        provider_name = provider_name or self.default_provider
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not supported")
        
        provider_class = self.providers[provider_name]
        
        try:
            if model:
                return provider_class(model=model)
            else:
                return provider_class()
        except ValueError as e:
            # Fall back to mock provider if API key is missing
            if "not configured" in str(e):
                print(f"Provider {provider_name} API key not configured, using mock")
                return MockProvider()
            raise ValueError(f"Failed to initialize {provider_name}: {e}")
        except Exception as e:
            # For Claude, handle version compatibility issues
            if provider_name == "claude":
                print(f"Claude provider initialization failed ({e}), using mock")
                return MockProvider()
            raise ValueError(f"Failed to initialize {provider_name}: {e}")
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        provider: str = None, 
        model: str = None,
        **kwargs
    ) -> str:
        ai_provider = self.get_provider(provider, model)
        return await ai_provider.generate(messages, **kwargs)
    
    async def stream_response(
        self, 
        messages: List[Dict[str, str]], 
        provider: str = None, 
        model: str = None,
        **kwargs
    ):
        ai_provider = self.get_provider(provider, model)
        async for chunk in ai_provider.stream_generate(messages, **kwargs):
            yield chunk
    
    def get_available_providers(self) -> List[str]:
        available = []
        for name, provider_class in self.providers.items():
            if name == "mock":
                continue  # Skip mock in available list
            try:
                # Test provider initialization
                test_provider = provider_class()
                available.append(name)
                print(f"Provider {name} is available and ready")
            except ValueError as e:
                # API key not configured - this is expected
                if "not configured" in str(e):
                    print(f"Provider {name} not available: {e}")
                else:
                    print(f"Provider {name} configuration error: {e}")
                continue
            except Exception as e:
                # Other errors - log but don't prevent service from working
                print(f"Provider {name} initialization error: {e}")
                # For Claude, still include it in available list but with fallback
                if name == "claude":
                    available.append(name)
                    print(f"Provider {name} added with fallback handling")
                continue
        
        # Always include mock if no others available
        if not available:
            available.append("mock")
        
        return available
    
    def get_provider_models(self, provider: str) -> List[str]:
        model_map = {
            "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "claude": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            "mock": ["mock-model"]
        }
        return model_map.get(provider, [])