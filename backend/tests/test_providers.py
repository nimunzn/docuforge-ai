#!/usr/bin/env python3
"""Test AI providers"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_service_direct import AIService

def test_providers():
    print("Testing AI providers...")
    
    try:
        ai_service = AIService()
        
        print("\nTesting get_available_providers...")
        providers = ai_service.get_available_providers()
        print(f"Available providers: {providers}")
        
        print("\nTesting get_provider_models...")
        for provider in providers:
            models = ai_service.get_provider_models(provider)
            print(f"{provider}: {models}")
        
        print("\nTesting default_provider...")
        print(f"Default provider: {ai_service.default_provider}")
        
    except Exception as e:
        print(f"Provider test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_providers()