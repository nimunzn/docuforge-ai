#!/usr/bin/env python3
"""
Test script to debug the full document creation workflow
"""
import asyncio
import logging
from sqlalchemy.orm import Session
from app.core.database import get_db, engine
from app.services.document_service import DocumentService
from app.services.websocket_service import WebSocketManager
from app.agents.document_orchestrator import DocumentOrchestrator
from app.agents.agent_config import agent_config_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_full_workflow():
    """Test the full document creation workflow with database saving"""
    logger.info("=== Testing Full Document Creation Workflow ===")
    
    # Get database session
    with Session(engine) as db:
        document_service = DocumentService(db)
        websocket_manager = WebSocketManager()
        
        # Check initial document state
        document_id = 1
        initial_doc = document_service.get_document(document_id)
        logger.info(f"Initial document content: {initial_doc.content}")
        
        # Initialize orchestrator WITH document service
        config = agent_config_manager.get_config(document_id)
        orchestrator = DocumentOrchestrator(
            document_id=document_id,
            config=config,
            document_service=document_service,
            websocket_manager=websocket_manager
        )
        
        # Test document creation
        test_message = "create a simple business plan template"
        logger.info(f"Testing message: '{test_message}'")
        
        result = await orchestrator.process_user_request(
            user_message=test_message,
            conversation_id=1,
            conversation_history=[]
        )
        
        logger.info(f"Result success: {result.get('success')}")
        if result.get('success'):
            logger.info(f"Response length: {len(result.get('response', ''))}")
        else:
            logger.error(f"Error: {result.get('error')}")
        
        # Check if document was updated
        updated_doc = document_service.get_document(document_id)
        logger.info(f"Document updated: {updated_doc.content != initial_doc.content}")
        logger.info(f"Updated document content: {updated_doc.content}")
        
        return result.get('success', False)

if __name__ == "__main__":
    asyncio.run(test_full_workflow())