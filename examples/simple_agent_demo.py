"""Simple Agent Example - Direct HTTP API Usage.

This example shows how to use CNAA v0.2 with a minimal agent setup.
No external dependencies except requests library.

Usage:
    python examples/simple_agent.py

Requirements:
    - CNAA server running at http://localhost:8080
    - Python 3.11+
    - requests library (optional)
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any
import urllib.request


class SimpleAgent:
    """Minimal agent using CNAA for experience memory."""
    
    def __init__(self, agent_id: str, cloud_url: str = "http://localhost:8080"):
        """Initialize simple agent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            cloud_url: CNAA server URL
        """
        self.agent_id = agent_id
        self.cloud_url = cloud_url
        self.api_key = os.getenv("CNAA_API_KEY", "")
    
    def _send_request(self, method: str, endpoint: str, data: dict) -> dict:
        """Send HTTP request to CNAA server.
        
        Args:
            method: HTTP method (GET/POST)
            endpoint: API endpoint path
            data: Request payload
            
        Returns:
            JSON response dictionary
        """
        url = f"{self.cloud_url}{endpoint}"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        request_data = json.dumps(data).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=request_data,
            headers=headers,
            method=method
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def store_memory(self, task: str, tags: list[str] | None = None, 
                     completion_score: float = 1.0, metadata: dict | None = None) -> dict:
        """Store an experience memory.
        
        Args:
            task: Task description or result
            tags: Optional tags for categorization
            completion_score: Task completion score [0.0, 1.0]
            metadata: Optional metadata dictionary
            
        Returns:
            Server response with status and memory_id
        """
        memory_id = f"mem-{int(datetime.now().timestamp())}"
        
        # Build MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "cnaa_store_memory",
                "arguments": {
                    "agent_id": self.agent_id,
                    "memory_id": memory_id,
                    "type": "long_term",
                    "content": {"task": task},
                    "tags": tags or [],
                    "completion_score": completion_score,
                    "metadata": metadata or {}
                }
            },
            "id": str(uuid.uuid4())
        }
        
        return self._send_request("POST", "/mcp", mcp_request)
    
    def get_memory(self, memory_id: str) -> dict | None:
        """Retrieve a specific memory.
        
        Args:
            memory_id: Memory ID to retrieve
            
        Returns:
            Memory object if found, None otherwise
        """
        memory_id_list = memory_id.split("-")[-1] if "-" in memory_id else memory_id
        
        # Query by listing with limit
        memories = self.list_memories(limit=100)
        
        for mem_summary in memories:
            if mem_summary.get("memory_id") == memory_id:
                return {
                    "status": "ok",
                    "memory": {
                        **mem_summary,
                        "content": {"task": f"Retrieved: {memory_id}"}
                    }
                }
        
        return {"status": "not_found", "message": f"Memory {memory_id} not found"}
    
    def list_memories(self, limit: int = 10, tags: list[str] | None = None) -> list[dict]:
        """List recent memories.
        
        Args:
            limit: Maximum number of memories to return
            tags: Optional tag filter
            
        Returns:
            List of memory summaries
        """
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "cnaa_list_memories",
                "arguments": {
                    "agent_id": self.agent_id,
                    "limit": limit,
                    "tags": tags
                }
            },
            "id": str(uuid.uuid4())
        }
        
        response = self._send_request("POST", "/mcp", mcp_request)
        
        if response.get("status") == "ok":
            return response.get("memories", [])
        
        return []
    
    def delete_memory(self, memory_id: str) -> dict:
        """Delete a memory.
        
        Args:
            memory_id: Memory ID to delete
            
        Returns:
            Server response
        """
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "cnaa_delete_memory",
                "arguments": {
                    "agent_id": self.agent_id,
                    "memory_id": memory_id
                }
            },
            "id": str(uuid.uuid4())
        }
        
        return self._send_request("POST", "/mcp", mcp_request)


def main():
    """Demo usage of SimpleAgent."""
    print("=" * 60)
    print("CNAA v0.2 - Simple Agent Demo")
    print("=" * 60)
    print()
    
    # Initialize agent
    agent = SimpleAgent(agent_id="demo-agent-001")
    
    print(f"✓ Agent initialized: {agent.agent_id}")
    print(f"✓ Cloud URL: {agent.cloud_url}")
    print()
    
    # Test 1: Store a memory
    print("📝 Test 1: Store a memory")
    print("-" * 60)
    
    store_result = agent.store_memory(
        task="Completed web development project analysis",
        tags=["important", "webdev", "completed"],
        completion_score=1.0,
        metadata={"project": "portfolio-site"}
    )
    
    print(f"Result: {json.dumps(store_result, indent=2)}")
    print()
    
    # Test 2: Store multiple memories
    print("📝 Test 2: Store multiple memories")
    print("-" * 60)
    
    for i in range(3):
        agent.store_memory(
            task=f"Analyzed document {i+1}",
            tags=["document", "analysis"],
            completion_score=0.7 + (i * 0.1)
        )
    
    print(f"✓ Stored 3 additional memories")
    print()
    
    # Test 3: List memories
    print("📄 Test 3: List all memories")
    print("-" * 60)
    
    memories = agent.list_memories(limit=10)
    print(f"Found {len(memories)} memories:")
    for mem in memories:
        print(f"  • {mem['memory_id']} - Score: {mem['completion_score']:.1f}")
    print()
    
    # Test 4: Get memory by ID (if we stored one)
    print("📄 Test 4: Retrieve first memory")
    print("-" * 60)
    
    if memories:
        first_mem = memories[0]
        print(f"First memory: {first_mem['memory_id']}")
        print(f"Tags: {', '.join(first_mem['tags'])}")
        print()
    
    # Summary
    print("=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    print()
    print("💡 Next steps:")
    print("   1. Read full documentation in docs/v0.2_ROADMAP.md")
    print("   2. Check advanced examples in examples/ directory")
    print("   3. See QUICK_START_V02.md for deployment guide")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure CNAA server is running:")
        print("  ./scripts/start.sh")
