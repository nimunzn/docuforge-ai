#!/usr/bin/env python3
"""
Test script to validate LLM setup and configuration
"""
import asyncio
import logging
from app.agents.llm_router import LLMRouter
from app.agents.agent_config import AgentConfig, AgentType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_llm_setup():
    """Test LLM adapter initialization and basic functionality"""
    logger.info("=== Testing LLM Setup ===")
    
    try:
        # Initialize config and router
        config = AgentConfig()
        router = LLMRouter(config)
        
        logger.info(f"Available adapters: {list(router.adapters.keys())}")
        
        # Test each agent type
        test_message = [{"role": "user", "content": "Hello, can you respond with 'Test successful'?"}]
        
        for agent_type in AgentType:
            logger.info(f"\nTesting {agent_type}...")
            try:
                response = await router.route_request(agent_type, test_message)
                logger.info(f"✓ {agent_type} responded: {response[:100]}...")
            except Exception as e:
                logger.error(f"✗ {agent_type} failed: {e}")
        
    except Exception as e:
        logger.error(f"Failed to initialize LLM router: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_llm_setup())