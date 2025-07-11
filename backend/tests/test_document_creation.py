#!/usr/bin/env python3
"""
Test script to validate document creation workflow
"""
import asyncio
import logging
from app.agents.document_orchestrator import DocumentOrchestrator
from app.agents.agent_config import agent_config_manager
from app.agents.agent_states import AgentContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_document_creation():
    """Test document creation workflow end-to-end"""
    logger.info("=== Testing Document Creation ===")
    
    try:
        # Initialize orchestrator (without document service for now)
        document_id = 1
        config = agent_config_manager.get_config(document_id)
        orchestrator = DocumentOrchestrator(document_id, config)
        
        # Test the exact message that failed
        test_message = "create a business plan template"
        
        logger.info(f"Testing message: '{test_message}'")
        
        # Test the orchestrator process
        result = await orchestrator.process_user_request(
            user_message=test_message,
            conversation_id=1,
            conversation_history=[]
        )
        
        logger.info(f"Result success: {result.get('success')}")
        logger.info(f"Response: {result.get('response', 'No response')[:200]}...")
        if not result.get('success'):
            logger.error(f"Error: {result.get('error')}")
        
        return result.get('success', False)
        
    except Exception as e:
        logger.error(f"Failed to test document creation: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    asyncio.run(test_document_creation())