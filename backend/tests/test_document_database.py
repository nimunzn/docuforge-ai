#!/usr/bin/env python3
"""
Test script to debug document database issues
"""
import asyncio
import logging
from sqlalchemy.orm import Session
from app.core.database import get_db, engine
from app.services.document_service import DocumentService
from app.models.schemas import DocumentCreate, DocumentUpdate
from app.models.document import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_document_database():
    """Test document database operations"""
    logger.info("=== Testing Document Database ===")
    
    # Get database session
    with Session(engine) as db:
        document_service = DocumentService(db)
        
        # Check if document ID 1 exists
        existing_doc = document_service.get_document(1)
        logger.info(f"Document ID 1 exists: {existing_doc is not None}")
        
        if existing_doc:
            logger.info(f"Document title: {existing_doc.title}")
            logger.info(f"Document content type: {type(existing_doc.content)}")
            logger.info(f"Document content: {existing_doc.content}")
        else:
            # Create a test document
            logger.info("Creating test document...")
            test_doc = DocumentCreate(
                title="Test Business Plan",
                type="business_plan",
                content={}
            )
            created_doc = document_service.create_document(test_doc)
            logger.info(f"Created document with ID: {created_doc.id}")
            
            # Test updating it
            update_data = DocumentUpdate(
                content={
                    "type": "business_plan",
                    "title": "Test Business Plan Template",
                    "sections": [
                        {
                            "id": "section_0",
                            "title": "Executive Summary",
                            "content": "This is a test executive summary",
                            "order": 0
                        }
                    ]
                }
            )
            
            updated_doc = document_service.update_document(created_doc.id, update_data)
            if updated_doc:
                logger.info("✓ Document update successful")
                logger.info(f"Updated content: {updated_doc.content}")
            else:
                logger.error("✗ Document update failed")

if __name__ == "__main__":
    test_document_database()