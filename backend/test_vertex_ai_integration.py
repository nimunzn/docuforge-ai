#!/usr/bin/env python3
"""
Vertex AI Integration Test
Test Vertex AI through the DocuForge AI agent system
"""
import asyncio
import os
import sys

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_llm_router():
    """Test Vertex AI through LLMRouter"""
    print("🧪 Testing Vertex AI through LLMRouter...")
    
    try:
        from app.agents.agent_config import AgentConfig, AgentType
        from app.agents.llm_router import LLMRouter
        
        # Create agent config
        config = AgentConfig()
        print(f"📋 Config: {config.to_dict()}")
        
        # Initialize router
        router = LLMRouter(config)
        print(f"🛠️ Router initialized with adapters: {router.get_available_providers()}")
        
        # Test message
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a brief 2-sentence explanation of artificial intelligence."}
        ]
        
        # Test orchestrator with Google/Vertex AI
        if "google" in router.get_available_providers():
            print("\n🔄 Testing Vertex AI through Orchestrator agent...")
            response = await router.route_request(
                AgentType.ORCHESTRATOR,
                test_messages
            )
            print(f"✅ Orchestrator response ({len(response)} chars):")
            print(f"   {response[:100]}...")
            
            # Test streaming
            print("\n🔄 Testing Vertex AI streaming...")
            stream_response = ""
            async for chunk in router.stream_route_request(
                AgentType.ORCHESTRATOR,
                test_messages
            ):
                stream_response += chunk
                if len(stream_response) % 50 < len(chunk):  # Print every ~50 chars
                    print(f"📦 Streaming: {len(stream_response)} chars so far...")
            
            print(f"✅ Streaming completed ({len(stream_response)} chars total)")
            
        else:
            print("❌ Google/Vertex AI adapter not available")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ LLMRouter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_document_orchestrator():
    """Test Vertex AI through Document Orchestrator"""
    print("\n🧪 Testing Vertex AI through Document Orchestrator...")
    
    try:
        from app.agents.document_orchestrator import DocumentOrchestrator
        from app.agents.agent_config import AgentConfig
        
        # Create orchestrator
        config = AgentConfig()
        orchestrator = DocumentOrchestrator(
            document_id=1,  # Test document ID
            config=config
        )
        
        # Test user request
        test_request = "Create a simple business plan template with 3 sections"
        
        print(f"📤 Processing request: {test_request}")
        result = await orchestrator.process_user_request(test_request)
        
        if result.get("success", False):
            print("✅ Document Orchestrator test successful!")
            print(f"   Response: {result['response'][:100]}...")
            print(f"   Plan updated: {result.get('plan_updated', False)}")
            print(f"   Preview ready: {result.get('preview_ready', False)}")
            print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
        else:
            print(f"❌ Document Orchestrator failed: {result.get('error', 'Unknown error')}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Document Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_agent_configuration():
    """Test agent configuration with Google/Vertex AI"""
    print("\n🧪 Testing Agent Configuration...")
    
    try:
        from app.agents.agent_config import AgentConfig, AgentType, agent_config_manager
        
        # Test default config
        config = agent_config_manager.get_config()
        print(f"📋 Default config: {config.to_dict()}")
        
        # Test getting LLM for each agent type
        for agent_type in AgentType:
            provider, model = config.get_llm_for_agent(agent_type)
            print(f"   {agent_type.value}: {provider}/{model}")
        
        # Test Google-specific configuration
        orchestrator_provider, orchestrator_model = config.get_llm_for_agent(AgentType.ORCHESTRATOR)
        planner_provider, planner_model = config.get_llm_for_agent(AgentType.PLANNER)
        
        print(f"\n🎯 Key configurations:")
        print(f"   Orchestrator: {orchestrator_provider}/{orchestrator_model}")
        print(f"   Planner: {planner_provider}/{planner_model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent configuration test failed: {e}")
        return False

async def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Starting Vertex AI Integration Tests")
    print("=" * 50)
    
    # Test 1: Agent Configuration
    config_success = await test_agent_configuration()
    
    # Test 2: LLM Router
    if config_success:
        router_success = await test_llm_router()
    else:
        router_success = False
    
    # Test 3: Document Orchestrator
    if router_success:
        orchestrator_success = await test_document_orchestrator()
    else:
        orchestrator_success = False
    
    # Final summary
    print("\n" + "=" * 50)
    print("🎉 Integration Test Summary:")
    print(f"   ✅ Configuration: {'PASS' if config_success else 'FAIL'}")
    print(f"   ✅ LLM Router: {'PASS' if router_success else 'FAIL'}")
    print(f"   ✅ Document Orchestrator: {'PASS' if orchestrator_success else 'FAIL'}")
    
    if all([config_success, router_success, orchestrator_success]):
        print(f"\n🎯 All tests passed! Vertex AI is fully integrated with DocuForge AI.")
        return True
    else:
        print(f"\n⚠️  Some tests failed. Please check the configuration.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(run_integration_tests())
        if success:
            print("\n🎉 Vertex AI integration is ready for production!")
        else:
            print("\n⚠️  Integration needs attention before production use.")
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user.")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()