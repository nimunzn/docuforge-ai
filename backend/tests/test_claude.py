#!/usr/bin/env python3
"""Test Claude provider initialization"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_service_direct import ClaudeProvider
from app.core.config import settings

def test_claude():
    print("Testing Claude provider initialization...")
    print(f"API key configured: {bool(settings.anthropic_api_key)}")
    
    try:
        provider = ClaudeProvider()
        print("Claude provider initialized successfully!")
        return True
    except Exception as e:
        print(f"Claude provider initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_claude()