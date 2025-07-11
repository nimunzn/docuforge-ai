#!/usr/bin/env python3
"""
Test the complete system with all fixes applied
"""
import asyncio
import logging
from sqlalchemy.orm import Session
from app.core.database import get_db, engine
from app.services.document_service import DocumentService
from app.services.websocket_service import WebSocketManager
from app.services.conversation_service import ConversationService
from app.agents.document_orchestrator import DocumentOrchestrator
from app.agents.agent_config import agent_config_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_system():
    """Test the complete system with all fixes"""
    logger.info("=== Testing Complete System ===")
    
    # Get database session
    with Session(engine) as db:
        document_service = DocumentService(db)
        websocket_manager = WebSocketManager()
        conversation_service = ConversationService(db)
        
        # Test document operations
        document_id = 5  # Use document ID 5 as seen in logs
        
        # Check if document exists, create if needed
        document = document_service.get_document(document_id)
        if not document:
            logger.info(f"Creating test document with ID {document_id}")
            from app.models.schemas import DocumentCreate
            test_doc = DocumentCreate(
                title="Test Document",
                type="business_plan",
                content={}
            )
            document = document_service.create_document(test_doc)
            logger.info(f"Created document with ID: {document.id}")
        else:
            logger.info(f"Using existing document: {document.title}")
        
        # Test conversation service (with JSON serialization fix)
        try:
            conversation = conversation_service.get_or_create_conversation(document_id)
            logger.info(f"Conversation ID: {conversation.id}")
            
            # Test adding message with datetime serialization
            conversation_service.add_message(conversation.id, "user", "test message")
            logger.info("✅ Message added successfully (JSON serialization working)")
            
        except Exception as e:
            logger.error(f"❌ Conversation test failed: {e}")
        
        # Test document orchestrator
        try:
            config = agent_config_manager.get_config(document_id)
            orchestrator = DocumentOrchestrator(
                document_id=document_id,
                config=config,
                document_service=document_service,
                websocket_manager=websocket_manager
            )
            
            # Test document creation
            test_message = "create a simple business plan template"
            logger.info(f"Testing orchestrator with: '{test_message}'")
            
            result = await orchestrator.process_user_request(
                user_message=test_message,
                conversation_id=conversation.id,
                conversation_history=[]
            )
            
            if result.get('success'):
                logger.info("✅ Document generation successful")
                logger.info(f"Response length: {len(result.get('response', ''))}")
                
                # Check if document was updated
                updated_doc = document_service.get_document(document_id)
                if updated_doc.content and updated_doc.content != document.content:
                    logger.info("✅ Document content updated in database")
                else:
                    logger.warning("⚠️ Document content may not have been updated")
                    
            else:
                logger.error(f"❌ Document generation failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Orchestrator test failed: {e}")
            
        return True

if __name__ == "__main__":
    asyncio.run(test_complete_system())