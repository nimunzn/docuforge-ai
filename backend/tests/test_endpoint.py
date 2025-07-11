#!/usr/bin/env python3
"""Test the providers endpoint directly"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from app.api.routes.ai import get_available_providers

async def test_endpoint():
    print("Testing providers endpoint...")
    
    try:
        result = await get_available_providers()
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"Endpoint test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_endpoint())