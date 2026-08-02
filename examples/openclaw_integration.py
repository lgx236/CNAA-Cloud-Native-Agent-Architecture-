"""Example: OpenClaw Integration with CNAA.

This example demonstrates how an agentic framework like OpenClaw
can integrate with CNAA to provide long-term memory capabilities.

OpenClaw (TypeScript) connects to CNAA (Python) via HTTP API.
"""

from __future__ import annotations

import json
import requests
from typing import Any


class OpenClawCNAAIntegration:
    """Example integration of OpenClaw with CNAA.
    
    This shows how an agentic framework would use CNAA to give
    its agents persistent memory across sessions.
    
    IMPLEMENTED:
        HTTP client for CNAA cloud server.
        Methods for all CNAA operations (store/get/list/delete memories,
        get/update states, preferences, environments).
    
    TODO (when integrating with real OpenClaw):
        - Add connection pooling and retry logic
        - Add request/response logging
        - Integrate with OpenClaw's agent lifecycle hooks
        - Add automatic memory condensation on task completion
    """
    
    def __init__(self, cnaa_server_url: str = "http://localhost:8080", api_key: str | None = None):
        """Initialize the integration.
        
        Args:
            cnaa_server_url: URL of the CNAA cloud server
            api_key: Optional API key for CNAA authentication.
                     When provided, requests include an Authorization header.
                     See docs/zh/api-reference-v0.1.md for details.
        """
        self.cnaa_url = cnaa_server_url
        self.api_key = api_key
    
    def _call_mcp_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call an MCP tool on CNAA server via HTTP.
        
        Args:
            tool_name: Name of the MCP tool
            arguments: Tool arguments
            
        Returns:
            Tool response dict
        """
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        response = requests.post(
            f"{self.cnaa_url}/mcp",
            json={"tool": tool_name, "arguments": arguments},
            headers=headers,
            timeout=30,
        )
        return response.json()
    
    # --- Memory Operations ---
    
    def store_memory(
        self,
        agent_id: str,
        memory_id: str,
        memory_type: str,
        content: dict[str, Any],
        tags: list[str] | None = None,
        completion_score: float = 0.0,
    ) -> dict[str, Any]:
        """Store a memory in CNAA.
        
        Example: After OpenClaw agent completes a task, store the experience.
        
        Args:
            agent_id: OpenClaw agent identifier
            memory_id: Unique memory identifier
            memory_type: "long_term" or "short_term"
            content: Memory content (task details, results, etc.)
            tags: Optional tags for retrieval
            completion_score: Task completion score [0.0, 1.0]
            
        Returns:
            Response dict
        """
        return self._call_mcp_tool(
            "cnaa_store_memory",
            {
                "agent_id": agent_id,
                "memory_id": memory_id,
                "type": memory_type,
                "content": content,
                "tags": tags or [],
                "completion_score": completion_score,
            },
        )
    
    def get_memory(self, agent_id: str, memory_id: str) -> dict[str, Any]:
        """Retrieve a memory from CNAA.
        
        Example: OpenClaw agent recalls a specific past experience.
        
        Args:
            agent_id: OpenClaw agent identifier
            memory_id: Memory identifier
            
        Returns:
            Response dict with memory data
        """
        return self._call_mcp_tool(
            "cnaa_get_memory",
            {"agent_id": agent_id, "memory_id": memory_id},
        )
    
    def list_memories(
        self,
        agent_id: str,
        memory_type: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """List memories for an agent.
        
        Example: OpenClaw shows agent's memory history.
        
        Args:
            agent_id: OpenClaw agent identifier
            memory_type: Optional type filter
            tags: Optional tag filter
            
        Returns:
            Response dict with memory list
        """
        args: dict[str, Any] = {"agent_id": agent_id}
        if memory_type:
            args["type"] = memory_type
        if tags:
            args["tags"] = tags
        
        return self._call_mcp_tool("cnaa_list_memories", args)
    
    # --- State Operations ---
    
    def get_states(self, agent_id: str) -> dict[str, Any]:
        """Get accumulated knowledge states.
        
        Example: OpenClaw agent retrieves learned knowledge.
        
        Args:
            agent_id: OpenClaw agent identifier
            
        Returns:
            Response dict with states
        """
        return self._call_mcp_tool(
            "cnaa_get_state",
            {"agent_id": agent_id},
        )
    
    def update_state(
        self,
        agent_id: str,
        state_id: str,
        category: str,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        """Update a knowledge state.
        
        Example: OpenClaw agent learns a new pattern from experience.
        
        Args:
            agent_id: OpenClaw agent identifier
            state_id: State identifier
            category: "preference", "knowledge", or "environment"
            content: State content
            
        Returns:
            Response dict
        """
        return self._call_mcp_tool(
            "cnaa_update_state",
            {
                "agent_id": agent_id,
                "state_id": state_id,
                "category": category,
                "content": content,
            },
        )
    
    # --- Preference Operations ---
    
    def get_preferences(self, agent_id: str) -> dict[str, Any]:
        """Get agent preferences.
        
        Example: OpenClaw agent retrieves learned preferences.
        
        Args:
            agent_id: OpenClaw agent identifier
            
        Returns:
            Response dict with preferences
        """
        return self._call_mcp_tool(
            "cnaa_get_preference",
            {"agent_id": agent_id},
        )
    
    def update_preference(
        self,
        agent_id: str,
        preference_id: str,
        key: str,
        value: dict[str, Any],
        importance: float = 0.0,
    ) -> dict[str, Any]:
        """Update an agent preference.
        
        Example: OpenClaw agent learns a user preference.
        
        Args:
            agent_id: OpenClaw agent identifier
            preference_id: Preference identifier
            key: Preference key
            value: Preference value
            importance: Importance score [0.0, 1.0]
            
        Returns:
            Response dict
        """
        return self._call_mcp_tool(
            "cnaa_update_preference",
            {
                "agent_id": agent_id,
                "preference_id": preference_id,
                "key": key,
                "value": value,
                "importance": importance,
            },
        )
    
    # --- Environment Operations ---
    
    def get_environment(self, agent_id: str) -> dict[str, Any]:
        """Get agent environment context.
        
        Example: OpenClaw agent retrieves current working context.
        
        Args:
            agent_id: OpenClaw agent identifier
            
        Returns:
            Response dict with environment
        """
        return self._call_mcp_tool(
            "cnaa_get_environment",
            {"agent_id": agent_id},
        )
    
    def update_environment(
        self,
        agent_id: str,
        env_id: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Update agent environment context.
        
        Example: OpenClaw agent updates working context.
        
        Args:
            agent_id: OpenClaw agent identifier
            env_id: Environment identifier
            context: Environment context
            
        Returns:
            Response dict
        """
        return self._call_mcp_tool(
            "cnaa_update_environment",
            {
                "agent_id": agent_id,
                "env_id": env_id,
                "context": context,
            },
        )


# --- Usage Example ---

if __name__ == "__main__":
    """Example: OpenClaw agent using CNAA for long-term memory."""
    
    # Initialize CNAA integration (without authentication)
    cnaa = OpenClawCNAAIntegration("http://localhost:8080")
    
    # Or initialize with API key authentication:
    # cnaa = OpenClawCNAAIntegration(
    #     "http://localhost:8080",
    #     api_key="sk-cnaa-001",
    # )
    
    # Example 1: Store a completed task experience
    print("Storing task experience...")
    result = cnaa.store_memory(
        agent_id="openclaw-agent-001",
        memory_id="mem-001",
        memory_type="long_term",
        content={
            "task": "database migration",
            "result": "success",
            "duration_minutes": 45,
            "notes": "Migrated user table to new schema",
        },
        tags=["database", "migration"],
        completion_score=0.95,
    )
    print(f"Result: {result}")
    
    # Example 2: Retrieve the memory
    print("\nRetrieving memory...")
    memory = cnaa.get_memory("openclaw-agent-001", "mem-001")
    print(f"Memory: {json.dumps(memory, indent=2)}")
    
    # Example 3: Update agent's knowledge state
    print("\nUpdating knowledge state...")
    result = cnaa.update_state(
        agent_id="openclaw-agent-001",
        state_id="state-001",
        category="knowledge",
        content={
            "topic": "database migration",
            "learned": "Always backup before schema changes",
        },
    )
    print(f"Result: {result}")
    
    # Example 4: Update agent preference
    print("\nUpdating preference...")
    result = cnaa.update_preference(
        agent_id="openclaw-agent-001",
        preference_id="pref-001",
        key="coding_style",
        value={"preferred": "functional", "avoid": "global_state"},
        importance=0.8,
    )
    print(f"Result: {result}")
    
    print("\n✓ OpenClaw agent now has long-term memory via CNAA!")
