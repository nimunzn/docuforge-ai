#!/usr/bin/env python3
"""
Test All Agents Using Gemini 2.5 Pro
Verify that all agent types now use Gemini 2.5 Pro exclusively
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_agent_configurations():
    """Test that all agents are configured to use Gemini 2.5 Pro"""
    print("🧪 Testing Agent Configurations...")
    
    try:
        from agents.agent_config import AgentConfig, AgentType, agent_config_manager
        
        # Get default config
        config = agent_config_manager.get_config()
        print(f"📋 Default config: {config.to_dict()}")
        
        # Test each agent type
        expected_provider = "google"
        expected_model = "gemini-2.5-pro"
        
        all_correct = True
        
        for agent_type in AgentType:
            provider, model = config.get_llm_for_agent(agent_type)
            status = "✅" if (provider == expected_provider and model == expected_model) else "❌"
            print(f"   {status} {agent_type.value}: {provider}/{model}")
            
            if provider != expected_provider or model != expected_model:
                all_correct = False
                print(f"      Expected: {expected_provider}/{expected_model}")
        
        if all_correct:
            print("✅ All agents correctly configured for Gemini 2.5 Pro!")
            return True
        else:
            print("❌ Some agents have incorrect configuration!")
            return False
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_each_agent_individually():
    """Test each agent type individually with Gemini 2.5 Pro"""
    print("\n🧪 Testing Each Agent Type with Gemini 2.5 Pro...")
    
    try:
        from agents.agent_config import AgentConfig, AgentType
        from agents.llm_router import LLMRouter
        
        # Use default config (should now be all Gemini)
        config = AgentConfig()
        router = LLMRouter(config)
        
        print(f"🛠️ Router initialized with adapters: {router.get_available_providers()}")
        
        # Test messages for each agent type
        test_cases = {
            AgentType.ORCHESTRATOR: {
                "messages": [
                    {"role": "system", "content": "You are an orchestrator. Analyze and coordinate."},
                    {"role": "user", "content": "Analyze this request: Create a business plan."}
                ],
                "expected_keywords": ["analyze", "plan", "business"]
            },
            AgentType.PLANNER: {
                "messages": [
                    {"role": "system", "content": "You are a document planner. Create structured plans."},
                    {"role": "user", "content": "Create a plan for a marketing strategy document."}
                ],
                "expected_keywords": ["plan", "structure", "marketing"]
            },
            AgentType.WRITER: {
                "messages": [
                    {"role": "system", "content": "You are a content writer. Generate high-quality content."},
                    {"role": "user", "content": "Write an introduction about renewable energy."}
                ],
                "expected_keywords": ["renewable", "energy", "introduction"]
            },
            AgentType.REVIEWER: {
                "messages": [
                    {"role": "system", "content": "You are a content reviewer. Provide feedback."},
                    {"role": "user", "content": "Review this text: 'Solar panels convert sunlight to electricity.'"}
                ],
                "expected_keywords": ["review", "solar", "feedback"]
            }
        }
        
        results = {}
        
        for agent_type, test_data in test_cases.items():
            print(f"\n🔄 Testing {agent_type.value}...")
            
            try:
                response = await router.route_request(
                    agent_type,
                    test_data["messages"]
                )
                
                print(f"✅ {agent_type.value} response ({len(response)} chars):")
                print(f"   {response[:100]}...")
                
                # Check if response seems relevant
                response_lower = response.lower()
                keyword_found = any(keyword in response_lower for keyword in test_data["expected_keywords"])
                
                results[agent_type.value] = {
                    "success": True,
                    "response_length": len(response),
                    "relevant": keyword_found,
                    "response": response[:200]
                }
                
            except Exception as e:
                print(f"❌ {agent_type.value} failed: {e}")
                results[agent_type.value] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Summary
        print(f"\n📊 Agent Test Results:")
        successful_agents = 0
        for agent_name, result in results.items():
            if result["success"]:
                status = "✅"
                successful_agents += 1
                relevance = "📝 Relevant" if result.get("relevant", False) else "❓ Generic"
                print(f"   {status} {agent_name}: {result['response_length']} chars, {relevance}")
            else:
                status = "❌"
                print(f"   {status} {agent_name}: {result['error']}")
        
        print(f"\n🎯 Success Rate: {successful_agents}/{len(test_cases)} agents working")
        return successful_agents == len(test_cases)
        
    except Exception as e:
        print(f"❌ Individual agent testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_streaming_functionality():
    """Test streaming with Gemini 2.5 Pro"""
    print("\n🧪 Testing Streaming Functionality...")
    
    try:
        from agents.agent_config import AgentConfig, AgentType
        from agents.llm_router import LLMRouter
        
        config = AgentConfig()
        router = LLMRouter(config)
        
        # Test streaming with writer agent
        messages = [
            {"role": "user", "content": "Write 3 benefits of cloud computing in bullet points."}
        ]
        
        print("🔄 Testing streaming response...")
        
        stream_response = ""
        chunk_count = 0
        
        async for chunk in router.stream_route_request(
            AgentType.WRITER,
            messages
        ):
            stream_response += chunk
            chunk_count += 1
            
            # Show progress every 10 chunks
            if chunk_count % 10 == 0:
                print(f"📦 Received {chunk_count} chunks ({len(stream_response)} chars so far)")
        
        print(f"✅ Streaming test completed!")
        print(f"   Total chunks: {chunk_count}")
        print(f"   Total characters: {len(stream_response)}")
        print(f"   Response preview: {stream_response[:150]}...")
        
        return len(stream_response) > 50  # Basic validation
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return False

async def run_comprehensive_test():
    """Run all tests to verify Gemini 2.5 Pro configuration"""
    print("🚀 Testing All Agents with Gemini 2.5 Pro")
    print("=" * 50)
    
    # Test 1: Configuration
    config_success = await test_agent_configurations()
    
    # Test 2: Individual agents
    if config_success:
        agents_success = await test_each_agent_individually()
    else:
        agents_success = False
    
    # Test 3: Streaming
    if agents_success:
        streaming_success = await test_streaming_functionality()
    else:
        streaming_success = False
    
    # Final summary
    print("\n" + "=" * 50)
    print("🎉 Comprehensive Test Summary:")
    print(f"   ✅ Configuration: {'PASS' if config_success else 'FAIL'}")
    print(f"   ✅ Agent Functionality: {'PASS' if agents_success else 'FAIL'}")
    print(f"   ✅ Streaming: {'PASS' if streaming_success else 'FAIL'}")
    
    all_tests_passed = all([config_success, agents_success, streaming_success])
    
    if all_tests_passed:
        print(f"\n🎯 ALL TESTS PASSED! All agents are now using Gemini 2.5 Pro exclusively!")
        print("🚀 DocuForge AI is ready with unified Gemini 2.5 Pro across all agents!")
        return True
    else:
        print(f"\n⚠️  Some tests failed. Please check the configuration.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(run_comprehensive_test())
        if success:
            print("\n🎉 Gemini 2.5 Pro configuration is complete and working!")
        else:
            print("\n⚠️  Configuration needs attention.")
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user.")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()