"""
LLM Router - Direct API routing without external frameworks
Routes requests to appropriate LLM providers based on agent configuration
"""
from typing import Dict, List, Any, Optional, AsyncGenerator
from abc import ABC, abstractmethod
import asyncio
import json
import aiohttp
import openai
from app.core.config import settings
from app.agents.agent_config import AgentConfig, AgentType
from app.telemetry import trace_llm
import logging

logger = logging.getLogger(__name__)


class LLMAdapter(ABC):
    """Abstract base class for LLM adapters"""
    
    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    async def stream_generate(self, messages: List[Dict[str, str]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM"""
        pass


class OpenAIAdapter(LLMAdapter):
    """OpenAI API adapter"""
    
    def __init__(self, timeout_seconds: int = 30):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=timeout_seconds
        )
        self.timeout_seconds = timeout_seconds
    
    @trace_llm("openai", "gpt-4", "generate")
    async def generate(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        try:
            logger.debug(f"OpenAI request: model={model}, messages={len(messages)} messages")
            
            # Add timeout to the request
            timeout = kwargs.get('timeout', self.timeout_seconds)
            
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=kwargs.get('temperature', 0.7),
                    max_tokens=kwargs.get('max_tokens', 2000)
                ),
                timeout=timeout
            )
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response: {len(content)} characters")
            return content
        except asyncio.TimeoutError:
            logger.error(f"OpenAI API timeout after {kwargs.get('timeout', self.timeout_seconds)}s for model {model}")
            raise Exception(f"OpenAI API timeout after {kwargs.get('timeout', self.timeout_seconds)} seconds. This may be due to network issues or high API load. Please try again.")
        except Exception as e:
            logger.error(f"OpenAI API error for model {model}: {e}", exc_info=True)
            raise Exception(f"OpenAI API error: {str(e)}")
    
    @trace_llm("openai", "gpt-4", "stream_generate")
    async def stream_generate(self, messages: List[Dict[str, str]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        try:
            timeout = kwargs.get('timeout', self.timeout_seconds)
            
            stream = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=kwargs.get('temperature', 0.7),
                    max_tokens=kwargs.get('max_tokens', 2000),
                    stream=True
                ),
                timeout=timeout
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except asyncio.TimeoutError:
            logger.error(f"OpenAI streaming timeout after {kwargs.get('timeout', self.timeout_seconds)}s")
            yield f"Error: OpenAI streaming timeout after {kwargs.get('timeout', self.timeout_seconds)} seconds. This may be due to network issues or high API load."
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"Error streaming response: {str(e)}"


class ClaudeAdapter(LLMAdapter):
    """Claude API adapter using direct HTTP calls"""
    
    def __init__(self, timeout_seconds: int = 30):
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")
        self.api_key = settings.anthropic_api_key
        self.base_url = "https://api.anthropic.com"
        self.timeout_seconds = timeout_seconds
    
    @trace_llm("claude", "claude-3-sonnet-20240229", "generate")
    async def generate(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        try:
            logger.debug(f"Claude request: model={model}, messages={len(messages)} messages")
            
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
                "model": model,
                "max_tokens": kwargs.get('max_tokens', 2000),
                "messages": claude_messages
            }
            
            if system_message:
                payload["system"] = system_message
            
            # Add timeout to the request
            timeout = kwargs.get('timeout', self.timeout_seconds)
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            
            # Make direct HTTP request to Claude API
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
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
                        content = data["content"][0]["text"]
                        logger.debug(f"Claude response: {len(content)} characters")
                        return content
                    else:
                        error_text = await response.text()
                        logger.error(f"Claude API error {response.status}: {error_text}")
                        raise Exception(f"Claude API error {response.status}: {error_text}")
        
        except asyncio.TimeoutError:
            logger.error(f"Claude API timeout after {kwargs.get('timeout', self.timeout_seconds)}s for model {model}")
            raise Exception(f"Claude API timeout after {kwargs.get('timeout', self.timeout_seconds)} seconds. This may be due to network issues or high API load. Please try again.")
        except Exception as e:
            logger.error(f"Claude API error for model {model}: {e}", exc_info=True)
            raise Exception(f"Claude API error: {str(e)}")
    
    @trace_llm("claude", "claude-3-sonnet-20240229", "stream_generate")
    async def stream_generate(self, messages: List[Dict[str, str]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        # For now, implement pseudo-streaming by chunking the response
        try:
            response = await self.generate(messages, model, **kwargs)
            
            # Simulate streaming by yielding words
            words = response.split()
            for word in words:
                yield word + " "
                await asyncio.sleep(0.05)
        
        except asyncio.TimeoutError:
            logger.error(f"Claude streaming timeout after {kwargs.get('timeout', self.timeout_seconds)}s")
            yield f"Error: Claude streaming timeout after {kwargs.get('timeout', self.timeout_seconds)} seconds. This may be due to network issues or high API load."
        except Exception as e:
            logger.error(f"Claude streaming error: {e}")
            yield f"Error streaming response: {str(e)}"


class VertexAIAdapter(LLMAdapter):
    """Vertex AI adapter for Gemini models"""
    
    def __init__(self, timeout_seconds: int = 30):
        # Validate required configuration
        if not settings.google_cloud_project_id:
            raise ValueError("Google Cloud project ID not configured")
        if not settings.google_service_account_file:
            raise ValueError("Google service account file not configured")
        
        self.project_id = settings.google_cloud_project_id
        self.location = settings.google_cloud_location
        self.service_account_file = settings.google_service_account_file
        self.timeout_seconds = timeout_seconds
        
        # Validate service account file exists
        import os
        if not os.path.exists(self.service_account_file):
            raise ValueError(f"Service account file not found: {self.service_account_file}")
        
        # Initialize credentials and Vertex AI
        self._initialize_vertex_ai()
    
    def _initialize_vertex_ai(self):
        """Initialize Vertex AI with service account credentials"""
        try:
            import vertexai
            from google.oauth2 import service_account
            
            # Create credentials from service account file
            self.credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file
            )
            
            # Initialize Vertex AI
            vertexai.init(
                project=self.project_id, 
                location=self.location, 
                credentials=self.credentials
            )
            
            logger.info(f"✅ Vertex AI initialized: {self.project_id} @ {self.location}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise ValueError(f"Vertex AI initialization failed: {e}")
    
    @trace_llm("vertex-ai", "gemini-2.5-pro", "generate")
    async def generate(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        try:
            logger.debug(f"Vertex AI request: model={model}, messages={len(messages)} messages")
            
            # Import here to avoid import errors if not installed
            from vertexai.generative_models import GenerativeModel
            
            # Load the model
            vertex_model = GenerativeModel(model)
            
            # Convert messages to Vertex AI format
            vertex_prompt = self._convert_messages_to_vertex_format(messages)
            
            # Run in thread pool to make it async-compatible
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: vertex_model.generate_content(vertex_prompt)
                ),
                timeout=kwargs.get('timeout', self.timeout_seconds)
            )
            
            # Extract text response
            content = response.text
            logger.debug(f"Vertex AI response: {len(content)} characters")
            return content
            
        except asyncio.TimeoutError:
            logger.error(f"Vertex AI timeout after {kwargs.get('timeout', self.timeout_seconds)}s for model {model}")
            raise Exception(f"Vertex AI timeout after {kwargs.get('timeout', self.timeout_seconds)} seconds. This may be due to network issues or high API load. Please try again.")
        except Exception as e:
            logger.error(f"Vertex AI error for model {model}: {e}", exc_info=True)
            raise Exception(f"Vertex AI error: {str(e)}")
    
    @trace_llm("vertex-ai", "gemini-2.5-pro", "stream_generate")
    async def stream_generate(self, messages: List[Dict[str, str]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream response using word-by-word simulation"""
        try:
            # Get full response first
            response = await self.generate(messages, model, **kwargs)
            
            # Simulate streaming by yielding words with realistic timing
            words = response.split()
            for i, word in enumerate(words):
                chunk = word + " "
                yield chunk
                
                # Vary delay for more natural streaming
                if i % 10 == 0:  # Longer pause every 10 words
                    await asyncio.sleep(0.1)
                else:
                    await asyncio.sleep(0.03)
                    
        except asyncio.TimeoutError:
            logger.error(f"Vertex AI streaming timeout after {kwargs.get('timeout', self.timeout_seconds)}s")
            yield f"Error: Vertex AI streaming timeout after {kwargs.get('timeout', self.timeout_seconds)} seconds. This may be due to network issues or high API load."
        except Exception as e:
            logger.error(f"Vertex AI streaming error: {e}")
            yield f"Error streaming response: {str(e)}"
    
    def _convert_messages_to_vertex_format(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to Vertex AI prompt format"""
        
        # Combine all messages into a single prompt
        # System messages become context, user/assistant messages become conversation
        prompt_parts = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                # Add system message as context
                prompt_parts.append(f"Context: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        # Join into single prompt
        full_prompt = "\n\n".join(prompt_parts)
        
        # If no explicit user message, add a generic one
        if not any("User:" in part for part in prompt_parts):
            full_prompt = f"{full_prompt}\n\nUser: Please provide a helpful response."
        
        return full_prompt


class MockAdapter(LLMAdapter):
    """Mock adapter for testing"""
    
    @trace_llm("mock", "mock-model", "generate")
    async def generate(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        # Simple mock response
        last_message = messages[-1]["content"] if messages else "Hello"
        return f"Mock response to: {last_message[:50]}..."
    
    @trace_llm("mock", "mock-model", "stream_generate")
    async def stream_generate(self, messages: List[Dict[str, str]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        response = await self.generate(messages, model, **kwargs)
        words = response.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.1)


class LLMRouter:
    """Routes LLM requests to appropriate providers"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.adapters: Dict[str, LLMAdapter] = {}
        self._initialize_adapters()
    
    def _initialize_adapters(self):
        """Initialize available adapters"""
        logger.info("Initializing LLM adapters...")
        
        timeout_seconds = self.config.timeout_seconds
        
        try:
            self.adapters["openai"] = OpenAIAdapter(timeout_seconds=timeout_seconds)
            logger.info("✓ OpenAI adapter initialized")
        except ValueError as e:
            logger.warning(f"✗ OpenAI adapter not available: {e}")
        
        try:
            self.adapters["claude"] = ClaudeAdapter(timeout_seconds=timeout_seconds)
            logger.info("✓ Claude adapter initialized")
        except ValueError as e:
            logger.warning(f"✗ Claude adapter not available: {e}")
        
        try:
            self.adapters["google"] = VertexAIAdapter(timeout_seconds=timeout_seconds)
            logger.info("✓ Vertex AI adapter initialized")
        except ValueError as e:
            logger.warning(f"✗ Vertex AI adapter not available: {e}")
        
        # Mock adapter is always available
        self.adapters["mock"] = MockAdapter()
        logger.info("✓ Mock adapter initialized")
        
        logger.info(f"LLM Router ready with {len(self.adapters)} adapters: {list(self.adapters.keys())}")
        logger.info(f"Timeout configuration: {timeout_seconds}s")
    
    async def route_request(self, agent_type: AgentType, messages: List[Dict[str, str]], **kwargs) -> str:
        """Route request to appropriate LLM based on agent type"""
        provider, model = self.config.get_llm_for_agent(agent_type)
        
        logger.info(f"LLM Router: {agent_type} -> {provider}/{model}")
        logger.debug(f"Available adapters: {list(self.adapters.keys())}")
        
        # Set timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.config.timeout_seconds
        
        # Try the configured provider first
        if provider in self.adapters:
            try:
                logger.info(f"Calling {provider} with model {model} for {agent_type}")
                result = await self.adapters[provider].generate(messages, model, **kwargs)
                logger.info(f"Successfully got response from {provider} ({len(result)} chars)")
                return result
            except Exception as e:
                logger.error(f"Error with {provider} for {agent_type}: {e}", exc_info=True)
        else:
            logger.error(f"Provider {provider} not available. Available: {list(self.adapters.keys())}")
        
        # Fallback to mock if configured provider fails
        fallback_provider = self.config.fallback_llm
        if fallback_provider in self.adapters:
            logger.warning(f"Falling back to {fallback_provider} for {agent_type}")
            try:
                # For mock fallback, provide a helpful placeholder response
                if fallback_provider == "mock":
                    last_user_message = messages[-1]["content"] if messages else "unknown request"
                    result = f"I apologize, but I'm currently experiencing issues connecting to the AI service. " \
                           f"Your request '{last_user_message}' has been received, but I cannot generate the full content right now. " \
                           f"Please try again in a few moments. The system will continue to save any generated content."
                else:
                    result = await self.adapters[fallback_provider].generate(
                        messages, 
                        self.config.fallback_model, 
                        **kwargs
                    )
                logger.info(f"Fallback successful: {fallback_provider} returned {len(result)} chars")
                return result
            except Exception as e:
                logger.error(f"Fallback {fallback_provider} also failed for {agent_type}: {e}", exc_info=True)
        else:
            logger.error(f"Fallback provider {fallback_provider} not available")
        
        error_msg = f"I apologize, but I'm currently unable to process your request due to AI service issues. Please try again later."
        logger.critical(f"No available LLM providers for {agent_type}")
        return error_msg
    
    async def stream_route_request(self, agent_type: AgentType, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Route streaming request to appropriate LLM"""
        provider, model = self.config.get_llm_for_agent(agent_type)
        
        # Set timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.config.timeout_seconds
        
        # Try the configured provider first
        if provider in self.adapters:
            try:
                async for chunk in self.adapters[provider].stream_generate(messages, model, **kwargs):
                    yield chunk
                return
            except Exception as e:
                logger.error(f"Streaming error with {provider}: {e}")
        
        # Fallback to mock if configured provider fails
        fallback_provider = self.config.fallback_llm
        if fallback_provider in self.adapters:
            logger.warning(f"Falling back to {fallback_provider} for streaming {agent_type}")
            async for chunk in self.adapters[fallback_provider].stream_generate(
                messages, 
                self.config.fallback_model, 
                **kwargs
            ):
                yield chunk
        else:
            yield "Error: No available LLM providers"
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.adapters.keys())
    
    def is_provider_available(self, provider: str) -> bool:
        """Check if a provider is available"""
        return provider in self.adapters