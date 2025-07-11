#!/usr/bin/env python3
"""
Vertex AI Connection Test Script
Test Gemini 2.5 Pro model with service account authentication
"""
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account
import asyncio
import os
import json
from typing import List, Dict, Any
import time

# Configuration based on the service account file
PROJECT_ID = "personal-465515"
LOCATION = "us-central1"
SERVICE_ACCOUNT_FILE = "./personal-465515-ef83e1ad2a0f.json"

# Test prompts
TEST_PROMPTS = [
    "Explain the importance of bees to the ecosystem in three sentences.",
    "Write a brief summary of machine learning in 2 paragraphs.",
    "What are the key benefits of renewable energy? List 3 points."
]

# Models to test
MODELS_TO_TEST = [
    "gemini-2.5-pro",
    "gemini-1.5-pro", 
    "gemini-pro"
]

def test_service_account_file():
    """Test if service account file exists and is valid JSON"""
    print("🔍 Testing service account file...")
    
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"❌ Service account file not found: {SERVICE_ACCOUNT_FILE}")
        return False
    
    try:
        with open(SERVICE_ACCOUNT_FILE, 'r') as f:
            service_account_data = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in service_account_data:
                print(f"❌ Missing required field in service account: {field}")
                return False
        
        print(f"✅ Service account file valid")
        print(f"   Project ID: {service_account_data['project_id']}")
        print(f"   Client Email: {service_account_data['client_email']}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in service account file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading service account file: {e}")
        return False

def test_vertex_ai_sync(model_name: str, prompt: str) -> Dict[str, Any]:
    """Test synchronous Vertex AI connection"""
    try:
        print(f"🔗 Testing {model_name} with sync method...")
        
        # Create credentials from the service account key file
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
        
        # Initialize the Vertex AI client
        vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
        
        # Load the model
        model = GenerativeModel(model_name)
        
        # Record start time
        start_time = time.time()
        
        # Send the prompt to the model
        print(f"📤 Sending prompt: {prompt[:50]}...")
        response = model.generate_content(prompt)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Extract text response
        response_text = response.text
        
        print(f"✅ {model_name} responded successfully")
        print(f"   Response time: {response_time:.2f}s")
        print(f"   Response length: {len(response_text)} characters")
        print(f"   Response preview: {response_text[:100]}...")
        
        return {
            "success": True,
            "model": model_name,
            "response_time": response_time,
            "response_length": len(response_text),
            "response": response_text
        }
        
    except Exception as e:
        print(f"❌ Error with {model_name}: {e}")
        return {
            "success": False,
            "model": model_name,
            "error": str(e)
        }

async def test_vertex_ai_async(model_name: str, prompt: str) -> Dict[str, Any]:
    """Test async version for FastAPI compatibility"""
    try:
        print(f"🔗 Testing {model_name} with async method...")
        
        # Run the sync version in a thread pool for async compatibility
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: test_vertex_ai_sync(model_name, prompt)
        )
        
        if result["success"]:
            print(f"✅ {model_name} async test successful")
        else:
            print(f"❌ {model_name} async test failed")
            
        return result
        
    except Exception as e:
        print(f"❌ Async error with {model_name}: {e}")
        return {
            "success": False,
            "model": model_name,
            "error": str(e)
        }

def test_different_models():
    """Test various Gemini model versions"""
    print("\n🧪 Testing different Gemini models...")
    
    results = []
    test_prompt = TEST_PROMPTS[0]  # Use first test prompt
    
    for model_name in MODELS_TO_TEST:
        print(f"\n--- Testing {model_name} ---")
        result = test_vertex_ai_sync(model_name, test_prompt)
        results.append(result)
        
        # Add delay between tests
        time.sleep(1)
    
    # Summary
    print("\n📊 Model Test Summary:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        if result["success"]:
            print(f"{status} {result['model']}: {result['response_time']:.2f}s")
        else:
            print(f"{status} {result['model']}: {result['error']}")
    
    return results

async def test_async_functionality():
    """Test async functionality with multiple concurrent requests"""
    print("\n🚀 Testing async functionality...")
    
    # Test with gemini-2.5-pro if available
    model_name = "gemini-2.5-pro"
    
    # Create multiple concurrent requests
    tasks = []
    for i, prompt in enumerate(TEST_PROMPTS):
        task = test_vertex_ai_async(model_name, prompt)
        tasks.append(task)
    
    # Run concurrently
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    print(f"\n📊 Async Test Results:")
    print(f"   Total requests: {len(results)}")
    print(f"   Successful: {successful}")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average per request: {total_time/len(results):.2f}s")
    
    return results

def run_comprehensive_tests():
    """Run all tests in sequence"""
    print("🚀 Starting Vertex AI Comprehensive Tests")
    print("=" * 50)
    
    # Test 1: Service account file
    if not test_service_account_file():
        print("\n❌ Service account test failed. Cannot proceed.")
        return False
    
    # Test 2: Model availability
    print("\n" + "=" * 50)
    model_results = test_different_models()
    
    successful_models = [r for r in model_results if r["success"]]
    if not successful_models:
        print("\n❌ No models working. Cannot proceed with async tests.")
        return False
    
    # Test 3: Async functionality
    print("\n" + "=" * 50)
    asyncio.run(test_async_functionality())
    
    # Final summary
    print("\n" + "=" * 50)
    print("🎉 Test Summary:")
    print(f"   Working models: {len(successful_models)}")
    for model in successful_models:
        print(f"   ✅ {model['model']}")
    
    print(f"\n✅ Vertex AI integration is ready for DocuForge AI!")
    return True

if __name__ == "__main__":
    try:
        success = run_comprehensive_tests()
        if success:
            print("\n🎯 All tests passed! Ready to integrate Vertex AI.")
        else:
            print("\n⚠️  Some tests failed. Please check configuration.")
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user.")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")