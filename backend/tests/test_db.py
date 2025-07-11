#!/usr/bin/env python3
"""Test database connection and basic operations"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine
from app.models.document import Document, DocumentVersion
from app.models.schemas import DocumentCreate
from app.services.document_service import DocumentService

def test_database():
    print("Testing database connection...")
    
    # Create a test session
    db = SessionLocal()
    
    try:
        # Test basic query
        print("Testing basic query...")
        documents = db.query(Document).all()
        print(f"Found {len(documents)} documents")
        
        # Test DocumentService
        print("Testing DocumentService...")
        service = DocumentService(db)
        
        # Create a test document
        doc_data = DocumentCreate(
            title="Test Document",
            type="test",
            content={"sections": [{"title": "Test Section", "content": "Test content"}]}
        )
        
        print("Creating test document...")
        test_doc = service.create_document(doc_data)
        print(f"Created document with ID: {test_doc.id}")
        
        # Test get documents
        print("Testing get_documents...")
        all_docs = service.get_documents()
        print(f"Total documents: {len(all_docs)}")
        
        # Test get single document
        print("Testing get_document...")
        retrieved_doc = service.get_document(test_doc.id)
        print(f"Retrieved document: {retrieved_doc.title}")
        
        print("Database test completed successfully!")
        
    except Exception as e:
        print(f"Database test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_database()