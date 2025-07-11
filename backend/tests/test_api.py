#!/usr/bin/env python3
"""Test API endpoints directly"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from app.core.database import SessionLocal
from app.api.routes.documents import get_documents
from app.services.document_service import DocumentService
from app.models.schemas import DocumentCreate

async def test_api():
    print("Testing API endpoints directly...")
    
    # Create a test session
    db = SessionLocal()
    
    try:
        print("Testing get_documents route...")
        result = await get_documents(db=db)
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result)}")
        
        for doc in result:
            print(f"Document: {doc.title} (ID: {doc.id})")
        
    except Exception as e:
        print(f"API test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_api())