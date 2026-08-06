#!/usr/bin/env python3
"""
CNAA Agent Framework Integration Demo

This script demonstrates CNAA integration with multiple agent frameworks:
- LangChain
- LlamaIndex  
- AutoGen (mock)
- CrewAI (mock)
- Custom Generic Agent

All agents share memory through the same CNAA cloud server!

Usage:
    python examples/multi_agent_framework_demo.py
"""

import logging
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def test_langchain_integration():
    """Test LangChain agent with CNAA memory"""
    print("\n" + "=" * 70)
    print("🤖 Testing LangChain Integration")
    print("=" * 70)
    
    try:
        # Try to import LangChain
        from langchain.agents import AgentExecutor
        
        # Import CNAA adapter
        from cnaa.adapters.langchain import LangChainCNAAMixin
        from cnaa.adapters import MemoryType
        
        class DemoLangChainAgent(LangChainCNAAMixin):
            """Simple demo agent for testing"""
            
            agent_id = "langchain-demo-001"
            
            def __init__(self):
                super().__init__()
                self.cnaa_server_url = "http://localhost:8080"
            
            def execute_task(self, query: str) -> dict:
                """Simulate task execution"""
                result = {
                    "query": query,
                    "response": f"Processed: {query}",
                    "timestamp": datetime.now().isoformat(),
                }
                
                # Store in CNAA memory
                self.on_task_complete(
                    agent_id=self.agent_id,
                    task_result=result,
                    tags=["langchain", "demo"],
                    completion_score=0.95,
                )
                
                return result
        
        # Create agent and run
        agent = DemoLangChainAgent()
        
        if agent.health_check():
            print(f"✅ Connected to CNAA at {agent.cnaa_server_url}")
        else:
            print("⚠️  Could not connect to CNAA (running offline demo)")
            return False
        
        # Simulate multiple tasks
        queries = ["Calculate sales data", "Analyze customer feedback"]
        for query in queries:
            result = agent.execute_task(query)
            print(f"✅ Stored LangChain task: {query[:40]}...")
        
        return True
        
    except ImportError as e:
        print(f"⚠️  LangChain not installed: {e}")
        print("   Install with: pip install langchain openai")
        return None  # Unknown status (not installed)
    except Exception as e:
        print(f"❌ LangChain integration error: {e}")
        logger.exception("LangChain error:")
        return False


def test_llamaindex_integration():
    """Test LlamaIndex agent with CNAA memory"""
    print("\n" + "=" * 70)
    print("📚 Testing LlamaIndex Integration")
    print("=" * 70)
    
    try:
        from llama_index.core import ServiceContext
        from cnaa.adapters.llamaindex import LlamaIndexCNAAMixin
        
        class DemoLlamaIndexAgent(LlamaIndexCNAAMixin):
            agent_id = "llamaindex-demo-001"
            
            def chat(self, query: str):
                """Mock chat method"""
                response = f"Answered: {query}"
                
                self.on_query_complete(
                    query=query,
                    response=response,
                    tags=["llamaindex", "demo"]
                )
                
                return response
        
        agent = DemoLlamaIndexAgent()
        
        if agent.health_check():
            print(f"✅ Connected to CNAA at {agent.cnaa_server_url}")
        else:
            print("⚠️  Could not connect to CNAA (running offline demo)")
            return False
        
        # Test queries
        queries = ["What is AI?", "Explain neural networks"]
        for query in queries:
            agent.chat(query)
            print(f"✅ Stored LlamaIndex query: {query}")
        
        return True
        
    except ImportError as e:
        print(f"⚠️  LlamaIndex not installed: {e}")
        print("   Install with: pip install llama-index")
        return None
    except Exception as e:
        print(f"❌ LlamaIndex integration error: {e}")
        logger.exception("LlamaIndex error:")
        return False


def test_autogen_integration():
    """Test AutoGen multi-agent integration"""
    print("\n" + "=" * 70)
    print("🤝 Testing AutoGen Integration")
    print("=" * 70)
    
    try:
        from autogen import ConversableAgent
        from cnaa.adapters.autogen import AutoGencNAAAMixin
        
        class DemoAutoGenAgent(AutoGencNAAAMixin, ConversableAgent):
            agent_id = "autogen-demo-001"
            
            def __init__(self, name: str, **kwargs):
                # Skip ConversableAgent init to avoid dependencies
                super().__init__()
                self.name = name
            
            def generate_reply(self, messages, sender=None):
                """Override reply generation"""
                last_message = messages[-1].get('content', '')
                
                # Generate mock response
                reply = f"Response to: {last_message}"
                
                # Store message in CNAA
                self.on_response_generated(response=reply)
                
                return reply
        
        # Create demo agents
        agent1 = DemoAutoGenAgent("assistant")
        agent2 = DemoAutoGenAgent("user")
        
        if agent1.health_check():
            print(f"✅ Connected to CNAA at {agent1.cnaa_server_url}")
        else:
            print("⚠️  Could not connect to CNAA (running offline demo)")
            return False
        
        # Simulate conversation
        messages = [
            {"content": "Hello"},
            {"content": "How can I help?"},
            {"content": "Tell me about CNAA"},
        ]
        
        for msg in messages:
            agent1.generate_reply(messages=[msg])
            print(f"✅ Stored AutoGen message")
        
        return True
        
    except ImportError as e:
        print(f"⚠️  AutoGen not installed: {e}")
        print("   Install with: pip install pyautogen")
        return None
    except Exception as e:
        print(f"❌ AutoGen integration error: {e}")
        logger.exception("AutoGen error:")
        return False


def test_crewai_integration():
    """Test CrewAI agent integration"""
    print("\n" + "=" * 70)
    print("👥 Testing CrewAI Integration")
    print("=" * 70)
    
    try:
        from crewai import Agent
        from cnaa.adapters.crewai import CrewAICNAAAMixin
        
        class DemoCrewAIAgent(CrewAICNAAAMixin):
            agent_id = "crewai-demo-001"
            
            def __init__(self, role: str):
                super().__init__()
                self.role = role
            
            def run_task(self, task_description: str):
                """Execute a task"""
                result = f"Completed: {task_description}"
                
                self.on_task_complete(
                    result=result,
                    task_context={"task": task_description},
                )
                
                return result
        
        agent = DemoCrewAIAgent("Senior Researcher")
        
        if agent.health_check():
            print(f"✅ Connected to CNAA at {agent.cnaa_server_url}")
        else:
            print("⚠️  Could not connect to CNAA (running offline demo)")
            return False
        
        # Run sample tasks
        tasks = [
            "Research market trends",
            "Analyze competitor data",
        ]
        
        for task in tasks:
            agent.run_task(task)
            print(f"✅ Stored CrewAI task: {task}")
        
        return True
        
    except ImportError as e:
        print(f"⚠️  CrewAI not installed: {e}")
        print("   Install with: pip install crewai")
        return None
    except Exception as e:
        print(f"❌ CrewAI integration error: {e}")
        logger.exception("CrewAI error:")
        return False


def test_custom_generic_agent():
    """Test custom generic agent integration"""
    print("\n" + "=" * 70)
    print("🛠️ Testing Custom Generic Agent Integration")
    print("=" * 70)
    
    try:
        from cnaa.adapters import BaseCNAAAdapter, MemoryType
        
        class MyCustomAgent(BaseCNAAAdapter):
            """Fully custom agent implementation"""
            
            agent_id = "custom-generic-001"
            
            def process_request(self, request: dict) -> dict:
                """Process incoming request"""
                try:
                    result = self._execute_request(request)
                    
                    # On success, store experience
                    self.on_task_complete(
                        agent_id=self.agent_id,
                        task_result={
                            "request": request,
                            "success": True,
                            "result": result,
                        },
                        tags=["custom"],
                        completion_score=1.0,
                    )
                    
                    return result
                    
                except Exception as e:
                    # On error, log it
                    self.on_error(agent_id=self.agent_id, error=e)
                    raise
            
            def _execute_request(self, request: dict) -> dict:
                """Mock request execution"""
                return {
                    "processed": True,
                    "input": request,
                    "output": f"Result for {request.get('action')}",
                }
            
            def on_agent_start(self, agent_id: str):
                print(f"   🚀 Custom agent '{agent_id}' started")
                self.update_state(
                    agent_id=agent_id,
                    state_id="startup",
                    category="knowledge",
                    content={"status": "ready"},
                )
            
            def on_task_complete(self, agent_id: str, task_result: dict):
                print(f"   ✅ Stored task result for {agent_id}")
            
            def on_error(self, agent_id: str, error: Exception):
                print(f"   ❌ Logged error for {agent_id}: {error}")
        
        # Create and test custom agent
        agent = MyCustomAgent()
        
        if agent.health_check():
            print(f"✅ Connected to CNAA at {agent.cnaa_server_url}")
        else:
            print("⚠️  Could not connect to CNAA (running offline demo)")
            return False
        
        # Execute some requests
        requests = [
            {"action": "calculate_sales", "data": [100, 200, 300]},
            {"action": "analyze_feedback", "sentiment": "positive"},
        ]
        
        for req in requests:
            result = agent.process_request(req)
            print(f"✅ Processed request: {req['action']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Custom agent integration error: {e}")
        logger.exception("Custom agent error:")
        return False


def main():
    """Run all framework integration tests"""
    print("\n" + "=" * 70)
    print("🧪 CNAA Multi-Framework Integration Demo")
    print("=" * 70)
    print("\nPurpose: Demonstrate CNAA integration with multiple agent")
    print("frameworks through unified HTTP API interface.")
    print("\nNote: All frameworks share memory via same CNAA server!")
    print("=" * 70 + "\n")
    
    results = {}
    
    # Test each framework
    results["LangChain"] = test_langchain_integration()
    results["LlamaIndex"] = test_llamaindex_integration()
    results["AutoGen"] = test_autogen_integration()
    results["CrewAI"] = test_crewai_integration()
    results["Custom Generic"] = test_custom_generic_agent()
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 INTEGRATION TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    total_tests = len(results)
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"✅ Passed:    {passed}/{total_tests}")
    print(f"❌ Failed:    {failed}/{total_tests}")
    print(f"⏭️ Skipped:   {skipped}/{total_tests} (not installed)\n")
    
    for framework, result in results.items():
        if result is True:
            icon = "✅"
        elif result is False:
            icon = "❌"
        else:
            icon = "⏭️"
        
        status = "Passed" if result is True else ("Failed" if result is False else "Skipped")
        print(f"{icon} {framework:<15} : {status}")
    
    print("\n" + "=" * 70)
    
    if passed > 0:
        print(f"\n🎉 SUCCESS! {passed} framework(s) integrated successfully")
        print("\nTo enable more integrations, install missing dependencies:")
        print("  pip install langchain openai")
        print("  pip install llama-index")
        print("  pip install pyautogen")
        print("  pip install crewai")
    
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
