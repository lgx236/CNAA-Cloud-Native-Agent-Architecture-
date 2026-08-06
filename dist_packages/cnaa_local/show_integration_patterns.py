#!/usr/bin/env python3
"""
CNAA Agent Framework Integration - Simple Demo

This demonstrates how ANY agent framework can integrate with CNAA:
1. Python frameworks via adapters (LangChain, LlamaIndex, etc.)
2. Any language via HTTP client (TypeScript, Go, Java, custom)
3. Custom generic agent implementation

Run this while CNAA server is running!
"""

import sys
sys.path.insert(0, '/root/CNAA-Cloud-Native-Agent-Architecture-')

from datetime import datetime


def test_custom_adapter():
    """Test the BaseCNAAAdapter"""
    from cnaa.adapters import BaseCNAAAdapter, MemoryType
    
    class DemoAgent(BaseCNAAAdapter):
        def __init__(self):
            super().__init__(
                cnaa_server_url="http://localhost:8080",
                timeout=5.0,
            )
        
        def on_agent_start(self, agent_id: str):
            print(f"Agent starting...")
        
        def on_task_complete(self, agent_id: str, task_result: dict):
            print(f"✓ Stored task: {task_result.get('action', 'unknown')}")
        
        def on_error(self, agent_id: str, error: Exception):
            print(f"✗ Error: {error}")
    
    # Test without actual server
    agent = DemoAgent()
    
    if not agent.health_check():
        print("⚠️  No CNAA server at http://localhost:8080")
        print("   (Create memory configs to see adapter working)\n")
    
    return True


def test_langchain_pattern():
    """Show LangChain integration pattern"""
    print("\n📦 Pattern: LangChain + CNAA")
    print("-" * 50)
    
    code = '''
# Install: pip install langchain openai
from langchain.agents import AgentExecutor
from cnaa.adapters.langchain import LangChainCNAAMixin
from cnaa.adapters import MemoryType

class MyLangChainAgent(LangChainCNAAMixin, AgentExecutor):
    agent_id = "langchain-agent-001"
    
    def _call(self, inputs, *args, **kwargs):
        result = super()._call(inputs, *args, **kwargs)
        
        # Store experience automatically
        self.on_task_complete(
            agent_id=self.agent_id,
            task_result=result,
            tags=["langchain"],
            completion_score=0.95
        )
        
        return result

# Usage
agent = MyLangChainAgent.from_llm_and_tools(llm, tools)
response = agent.run("Process sales data")
'''
    
    print(code.strip())
    return True


def test_llamaindex_pattern():
    """Show LlamaIndex integration pattern"""
    print("\n📦 Pattern: LlamaIndex + CNAA")
    print("-" * 50)
    
    code = '''
# Install: pip install llama-index
from llama_index.agent import OpenAIAgent
from cnaa.adapters.llamaindex import LlamaIndexCNAAMixin

class CNAALlamaAgent(LlamaIndexCNAAMixin, OpenAIAgent):
    agent_id = "llama-agent-001"
    
    def chat(self, message: str):
        response = super().chat(message)
        
        # Store conversation
        self.on_query_complete(
            query=message,
            response=response.response,
            tags=["llamaindex"]
        )
        
        return response

# Usage
agent = CNAALlamaAgent.from_tools([], llm=OpenAI())
result = agent.chat("What did we learn yesterday?")
'''
    
    print(code.strip())
    return True


def test_autogen_pattern():
    """Show AutoGen integration pattern"""
    print("\n📦 Pattern: AutoGen + CNAA (Multi-Agent)")
    print("-" * 50)
    
    code = '''
# Install: pip install pyautogen
from autogen import ConversableAgent
from cnaa.adapters.autogen import AutoGencNAAAMixin

class CNAAConversableAgent(AutoGencNAAAMixin, ConversableAgent):
    agent_id = "autogen-agent-001"
    
    def generate_reply(self, messages, sender=None):
        reply = super().generate_reply(messages, sender)
        
        # Store each response
        self.on_response_generated(response=reply)
        
        return reply

# Usage: Multi-agent team with memory
assistant = CNAAConversableAgent("assistant", llm_config=...)
user = CNAAConversableAgent("user", human_input_mode="NEVER")

assistant.initiate_chat(
    user, 
    message="Analyze quarterly reports"
)
'''
    
    print(code.strip())
    return True


def test_crewai_pattern():
    """Show CrewAI integration pattern"""
    print("\n📦 Pattern: CrewAI + CNAA")
    print("-" * 50)
    
    code = '''
# Install: pip install crewai
from crewai import Agent, Crew, Task
from cnaa.adapters.crewai import CrewAICNAAAMixin

class CNAACrewAgent(CrewAICNAAAMixin, Agent):
    agent_id = "crewai-agent-001"
    
    def run(self, task_input: str):
        result = super().run(task_input)
        
        # Log task outcome
        self.on_task_complete(
            result=result,
            task_context={"input": task_input},
        )
        
        return result

# Usage
researcher = CNAACrewAgent(role="Researcher", ...)
writer = CNAACrewAgent(role="Writer", ...)

crew = Crew(agents=[researcher, writer])
result = crew.kickoff()
'''
    
    print(code.strip())
    return True


def test_http_client_pattern():
    """Show TypeScript/Node.js HTTP client usage"""
    print("\n🌐 Pattern: TypeScript/Node.js + CNAA (HTTP Client)")
    print("-" * 50)
    
    code = '''
// Install: npm install node-fetch
import { CNAAClient } from './cnaa_client';

const cnaa = new CNAAClient({
  serverUrl: 'http://localhost:8080',
});

// Store memory from any TypeScript agent
await cnaa.storeMemory({
  agentId: 'typescript-agent',
  memoryId: 'task-' + Date.now(),
  type: 'long_term',
  content: { 
    task: 'Data processing', 
    success: true,
    details: { rows: 100, errors: 0 }
  },
  completionScore: 0.95,
  tags: ['data-processing'],
});

// Or use fetch directly
const response = await fetch('http://localhost:8080/mcp', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    tool: 'cnaa_store_memory',
    arguments: {
      agent_id: 'my-agent',
      memory_id: 'mem-001',
      type: 'long_term',
      content: { description: 'Example memory' },
      completion_score: 1.0
    }
  }),
});
'''
    
    print(code.strip())
    return True


def show_integration_architecture():
    """Display integration architecture"""
    print("\n" + "=" * 70)
    print("🏗️  CNAA INTEGRATION ARCHITECTURE")
    print("=" * 70)
    print("""

┌─────────────────────────────────────────────────────────────┐
│                    AGENT FRAMEWORKS                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │LangChain │  │LlamaIndex│  │AutoGen   │  │CrewAI    │   │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘   │
│        │             │             │             │         │
└────────┼─────────────┼─────────────┼─────────────┼─────────┘
         │             │             │             │
         ▼             ▼             ▼             ▼
┌────────┴─────────────┴─────────────┴─────────────┴─────────┐
│              ADAPTER LAYER (Python mixins)                  │
│  • BaseCNAAAdapter (abstract base class)                   │
│  • LangChainCNAAMixin                                       │
│  • LlamaIndexCNAAMixin                                      │
│  • AutoGencNAAAMixin                                        │
│  • CrewAICNAAAMixin                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ HTTP POST /mcp (JSON over network)
┌─────────────────────────────────────────────────────────────┐
│           COMMUNICATION LAYER (Language Agnostic)          │
│  • TypeScript/Node.js → cnaa_client.ts                     │
│  • Go → gorilla/http client                                │
│  • Java → okHttp client                                    │
│  • Any language → curl/custom HTTP                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               CNAA CLOUD SERVER                              │
│  • MCP Router                                               │
│  • SQLite Database                                          │
│  • Algorithm Plugins                                        │
└─────────────────────────────────────────────────────────────┘

Key Features:
✅ All agents share memory through same cloud server
✅ Language agnostic - works with any programming language
✅ Mix-in pattern - easy integration without inheritance conflicts
✅ HTTP-based - supports distributed deployment
✅ No direct object references - pure network communication
""")


def main():
    """Show integration patterns"""
    print("\n" + "=" * 70)
    print("🤖 CNAA: Agent Framework Integration Guide")
    print("=" * 70)
    
    show_integration_architecture()
    
    # Test custom adapter
    test_custom_adapter()
    
    # Show patterns for other frameworks
    test_langchain_pattern()
    test_llamaindex_pattern()
    test_autogen_pattern()
    test_crewai_pattern()
    test_http_client_pattern()
    
    print("\n" + "=" * 70)
    print("📚 QUICK START")
    print("=" * 70)
    print("""
1️⃣ Start CNAA server:
   ./scripts/start.sh

2️⃣ Choose your integration:
   
   Option A: Python framework (e.g., LangChain)
     pip install langchain
     # Use pattern shown above
   
   Option B: TypeScript/Node.js
     npm install node-fetch
     # Copy cnaa_client.ts and customize
   
   Option C: Any language
     Use HTTP API directly via curl/fetch/custom client

3️⃣ Run your agent!
""")
    
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
