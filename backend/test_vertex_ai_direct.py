#!/usr/bin/env python3
"""
Direct Vertex AI Test Through Agents
Test Vertex AI by configuring agents to use Google provider
"""
import asyncio
import os
import sys

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_vertex_ai_direct():
    """Test Vertex AI by directly configuring an agent to use Google"""
    print("🧪 Testing Vertex AI directly through agents...")
    
    try:
        from app.agents.agent_config import AgentConfig, AgentType
        from app.agents.llm_router import LLMRouter
        
        # Create custom config with Google for orchestrator
        config = AgentConfig(
            orchestrator_llm="google",
            orchestrator_model="gemini-2.5-pro",
            writer_llm="google", 
            writer_model="gemini-2.5-pro",
            fallback_llm="mock",
            fallback_model="mock"
        )
        
        print(f"📋 Custom config: {config.to_dict()}")
        
        # Initialize router with custom config
        router = LLMRouter(config)
        print(f"🛠️ Router initialized with adapters: {router.get_available_providers()}")
        
        # Test message
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant that provides concise, accurate answers."},
            {"role": "user", "content": "Explain machine learning in exactly 2 sentences."}
        ]
        
        # Test orchestrator with Vertex AI
        print("\n🔄 Testing Vertex AI Orchestrator...")
        response = await router.route_request(
            AgentType.ORCHESTRATOR,
            test_messages
        )
        print(f"✅ Vertex AI Orchestrator response ({len(response)} chars):")
        print(f"   {response}")
        
        # Test writer with Vertex AI  
        print("\n🔄 Testing Vertex AI Writer...")
        writer_messages = [
            {"role": "system", "content": "You are a content writer. Create engaging, informative content."},
            {"role": "user", "content": "Write a brief introduction to renewable energy (3 sentences)."}
        ]
        
        writer_response = await router.route_request(
            AgentType.WRITER,
            writer_messages
        )
        print(f"✅ Vertex AI Writer response ({len(writer_response)} chars):")
        print(f"   {writer_response}")
        
        # Test streaming
        print("\n🔄 Testing Vertex AI streaming...")
        stream_messages = [
            {"role": "user", "content": "List 3 benefits of cloud computing."}
        ]
        
        stream_response = ""
        chunk_count = 0
        async for chunk in router.stream_route_request(
            AgentType.WRITER,
            stream_messages
        ):
            stream_response += chunk
            chunk_count += 1
            if chunk_count % 5 == 0:  # Print every 5 chunks
                print(f"📦 Streaming chunk {chunk_count}: '{chunk.strip()}'")
        
        print(f"✅ Streaming completed ({chunk_count} chunks, {len(stream_response)} chars total)")
        print(f"   Final response: {stream_response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct Vertex AI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_document_creation_with_vertex_ai():
    """Test document creation with Vertex AI"""
    print("\n🧪 Testing Document Creation with Vertex AI...")
    
    try:
        from app.agents.document_orchestrator import DocumentOrchestrator
        from app.agents.agent_config import AgentConfig
        
        # Configure orchestrator to use Vertex AI for writing
        config = AgentConfig(
            orchestrator_llm="google",
            orchestrator_model="gemini-2.5-pro",
            writer_llm="google",
            writer_model="gemini-2.5-pro",
            fallback_llm="mock",
            fallback_model="mock"
        )
        
        # Create orchestrator
        orchestrator = DocumentOrchestrator(
            document_id=1,
            config=config
        )
        
        # Test content creation request
        test_request = "Write a business plan template with introduction, market analysis, and financial projections sections"
        
        print(f"📤 Processing request: {test_request}")
        result = await orchestrator.process_user_request(test_request)
        
        if result.get("success", False):
            print("✅ Document creation with Vertex AI successful!")
            print(f"   Response length: {len(result['response'])} chars")
            print(f"   Response preview: {result['response'][:200]}...")
            print(f"   Plan updated: {result.get('plan_updated', False)}")
            print(f"   Preview ready: {result.get('preview_ready', False)}")
            print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
        else:
            print(f"❌ Document creation failed: {result.get('error', 'Unknown error')}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Document creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_direct_tests():
    """Run direct Vertex AI tests"""
    print("🚀 Starting Direct Vertex AI Tests")
    print("=" * 50)
    
    # Test 1: Direct Vertex AI through agents
    direct_success = await test_vertex_ai_direct()
    
    # Test 2: Document creation with Vertex AI
    if direct_success:
        doc_success = await test_document_creation_with_vertex_ai()
    else:
        doc_success = False
    
    # Final summary
    print("\n" + "=" * 50)
    print("🎉 Direct Vertex AI Test Summary:")
    print(f"   ✅ Direct Agent Tests: {'PASS' if direct_success else 'FAIL'}")
    print(f"   ✅ Document Creation: {'PASS' if doc_success else 'FAIL'}")
    
    if all([direct_success, doc_success]):
        print(f"\n🎯 All direct tests passed! Vertex AI Gemini 2.5 Pro is working perfectly!")
        return True
    else:
        print(f"\n⚠️  Some tests failed. Please check the logs.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(run_direct_tests())
        if success:
            print("\n🎉 Vertex AI with Gemini 2.5 Pro is fully operational!")
        else:
            print("\n⚠️  Some issues detected with Vertex AI integration.")
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user.")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()