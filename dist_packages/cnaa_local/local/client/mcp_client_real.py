#!/usr/bin/env python3
"""Real HTTP-based MCP Client for CNAA v0.2."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CNAA_MCPClient:
    """Production-ready HTTP MCP client for CNAA Cloud."""

    def __init__(
        self,
        server_url: str = "http://localhost:8080",
        timeout: float = 30.0,
        api_key: Optional[str] = None,
    ):
        """Initialize MCP client."""
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.api_key = api_key
        
        # Initialize session if requests available
        self._session = None
        if REQUESTS_AVAILABLE:
            self._session = requests.Session()
            self._session.headers.update({
                "Content-Type": "application/json",
                "Accept": "application/json",
            })
            if api_key:
                self._session.headers["Authorization"] = f"Bearer {api_key}"
    
    def _make_request(self, method: str, endpoint: str, data: dict) -> dict:
        """Make HTTP request to cloud server."""
        url = f"{self.server_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            if REQUESTS_AVAILABLE and self._session:
                response = self._session.request(
                    method=method,
                    url=url,
                    json=data,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            
            else:
                import urllib.request
                import urllib.error
                
                req = urllib.request.Request(
                    url=url,
                    data=json.dumps(data).encode('utf-8'),
                    headers=headers,
                    method=method
                )
                
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode('utf-8'))
                    
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP request failed to {url}: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
            
        except urllib.error.URLError as e:
            error_msg = f"URLError while connecting to {url}: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
    
    # Memory Operations
    
    def store_memory(
        self,
        agent_id: str,
        memory_id: str,
        memory_type: str,
        content: dict[str, Any],
        tags: Optional[list[str]] = None,
        completion_score: float = 0.0,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Store a memory in Cloud."""
        return self._make_request("POST", "/mcp", {
            "tool": "cnaa_store_memory",
            "arguments": {
                "agent_id": agent_id,
                "memory_id": memory_id,
                "type": memory_type,
                "content": content,
                "tags": tags or [],
                "completion_score": completion_score,
                "metadata": metadata or {},
            }
        })
    
    def get_memory(
        self,
        agent_id: str,
        memory_id: str,
    ) -> dict[str, Any]:
        """Retrieve a single memory from Cloud."""
        return self._make_request("POST", "/mcp", {
            "tool": "cnaa_get_memory",
            "arguments": {
                "agent_id": agent_id,
                "memory_id": memory_id,
            }
        })
    
    def list_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        tags: Optional[list[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        reverse: bool = False,
    ) -> dict[str, Any]:
        """List memories from Cloud with filters."""
        args = {"agent_id": agent_id}
        if memory_type:
            args["type"] = memory_type
        if tags:
            args["tags"] = tags
        if start_time:
            args["start_time"] = start_time.isoformat()
        if end_time:
            args["end_time"] = end_time.isoformat()
        if limit:
            args["limit"] = limit
        args["reverse"] = reverse
        
        return self._make_request("POST", "/mcp", {
            "tool": "cnaa_list_memories",
            "arguments": args
        })
    
    def delete_memory(
        self,
        agent_id: str,
        memory_id: str,
    ) -> dict[str, Any]:
        """Delete a memory from Cloud."""
        return self._make_request("POST", "/mcp", {
            "tool": "cnaa_delete_memory",
            "arguments": {
                "agent_id": agent_id,
                "memory_id": memory_id,
            }
        })
    
    # State Operations
    
    def get_state(self, agent_id: str) -> dict[str, Any]:
        """Get all states for an agent from Cloud."""
        return self._make_request("POST", "/mcp", {
            "tool": "cnaa_get_state",
            "arguments": {"agent_id": agent_id}
        })
    
    def update_state(
        self,
        agent_id: str,
        state_id: str,
        category: str,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update a state in Cloud."""
        return self._make_request("POST", "/mcp", {
            "tool": "cnaa_update_state",
            "arguments": {
                "agent_id": agent_id,
                "state_id": state_id,
                "category": category,
                "content": content,
            }
        })
    
    def delete_state(
        self,
        agent_id: str,
        state_id: str,
    ) -> dict[str, Any]:
        """Delete a state from Cloud."""
        return self._make_request("POST", "/mcp", {
            "tool": "cnaa_delete_state",
            "arguments": {
                "agent_id": agent_id,
                "state_id": state_id,
            }
        })
    
    # Preference Operations
    
    def get_preference(self, agent_id: str) -> dict[str, Any]:
        """Get all preferences for an agent from Cloud."""
        return self._make_request("POST", "/mcp", {
            "tool": "cnaa_get_preference",
            "arguments": {"agent_id": agent_id}
        })
    
    def update_preference(
        self,
        agent_id: str,
        preference_id: str,
        key: str,
        value: dict[str, Any],
        importance: float = 0.0,
        source_memory_ids: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Create or update a preference in Cloud."""
        return self._make_request("POST", "/mcp", {
            "tool": "cnaa_update_preference",
            "arguments": {
                "agent_id": agent_id,
                "preference_id": preference_id,
                "key": key,
                "value": value,
                "importance": importance,
                "source_memory_ids": source_memory_ids or [],
            }
        })
    
    def delete_preference(
        self,
        agent_id: str,
        preference_id: str,
    ) -> dict[str, Any]:
        """Delete a preference from Cloud."""
        return self._make_request("POST", "/mcp", {
            "tool": "cnaa_delete_preference",
            "arguments": {
                "agent_id": agent_id,
                "preference_id": preference_id,
            }
        })
    
    # Environment Operations
    
    def get_environment(self, agent_id: str) -> dict[str, Any]:
        """Get environment context for an agent from Cloud."""
        return self._make_request("POST", "/mcp", {
            "tool": "cnaa_get_environment",
            "arguments": {"agent_id": agent_id}
        })
    
    def update_environment(
        self,
        agent_id: str,
        env_id: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Update environment context in Cloud."""
        return self._make_request("POST", "/mcp", {
            "tool": "cnaa_update_environment",
            "arguments": {
                "agent_id": agent_id,
                "env_id": env_id,
                "context": context,
            }
        })
    
    # Utility Methods
    
    def health_check(self) -> bool:
        """Check if cloud server is reachable."""
        try:
            if REQUESTS_AVAILABLE and self._session:
                response = self._session.get(
                    f"{self.server_url}/health",
                    timeout=5
                )
                return response.status_code == 200
            else:
                import urllib.request
                req = urllib.request.Request(
                    f"{self.server_url}/health",
                    method="GET"
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return resp.status == 200
        except Exception:
            return False
    
    def close(self):
        """Close session resources."""
        if self._session:
            self._session.close()


def main():
    """Demo usage of real MCP client."""
    print("=" * 60)
    print("CNAA v0.2 - Real HTTP MCP Client Demo")
    print("=" * 60)
    print()
    
    # Initialize client
    client = CNAA_MCPClient(
        server_url="http://localhost:8080",
        timeout=30.0,
        api_key=None
    )
    
    # Check connectivity
    print(f"Connecting to: {client.server_url}")
    if client.health_check():
        print("Cloud server is reachable!")
    else:
        print("Cannot connect to cloud server")
        print("Make sure server is running:")
        print("  ./scripts/start.sh")
        return
    
    # Demo store_memory
    print()
    print("Testing store_memory...")
    result = client.store_memory(
        agent_id="demo-agent",
        memory_id=f"mem-{int(datetime.now().timestamp())}",
        memory_type="long_term",
        content={"task": "Test memory via real HTTP client"},
        tags=["test", "demo"],
        completion_score=1.0
    )
    print(f"Result: {result}")
    
    # Demo list_memories
    print()
    print("Listing memories...")
    result = client.list_memories(agent_id="demo-agent", limit=5)
    if result.get("status") == "ok":
        memories = result.get("memories", [])
        print(f"Found {len(memories)} memories")
        for mem in memories[:3]:
            print(f"  {mem['memory_id']}")
    
    print()
    print("=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
