"""Cloud Agent Interface.

Provides a Python interface for agentic frameworks to interact with
CNAA cloud server. This is a convenience wrapper around the MCP server
for direct Python usage.

For MCP protocol usage, agentic frameworks should use the MCP tools directly.

IMPLEMENTED:
    - CloudAgentInterface class wrapping CNAA_MCPServer
    - 10 convenience methods: store/get/list memories, get/update states,
      get/update preferences, get/update environment
    - Each method marshals arguments and delegates to handle_tool_call()
    - Time complexity: O(1) per call (routing only)

TODO (algorithm extension point):
    - Add batch operations (store/list multiple memories at once)
    - Add caching layer for frequently accessed memories
    - Add bulk search/filter capabilities
    - Add async method variants for concurrent access
    - Add connection health check and auto-reconnect
"""

from __future__ import annotations

from typing import Any

from cloud.server.mcp_server import CNAA_MCPServer


class CloudAgentInterface:
    """Agentic framework interface for CNAA cloud server.
    
    This class provides a Python API for agentic frameworks (e.g., openclow)
    to interact with CNAA cloud. It wraps the MCP server and provides
    method-based access for convenient integration.
    
    CNAA cloud provides agentic systems with:
    - Long-term memory storage: persistent experience across sessions
    - State management: knowledge accumulation and preference learning
    - Environment context: current working context
    
    IMPLEMENTED:
        All methods delegate to CNAA_MCPServer.handle_tool_call().
        Each method marshals arguments and returns JSON response dict.
        Time complexity: O(1) per call (routing only).
    
    TODO (algorithm extension point):
        - Add batch operations (store multiple memories at once)
        - Add caching layer for frequently accessed memories
        - Add bulk search/filter capabilities
    
    For MCP protocol usage, agentic frameworks should call the MCP tools directly.
    This interface is for convenience when using Python.
    
    Example (openclow integration):
        ```python
        from cloud import CloudAgentInterface
        
        # openclow creates one interface per agent instance
        cloud = CloudAgentInterface()
        
        # Store long-term memory
        cloud.store_memory(
            agent_id="openclow-agent-001",
            memory_id="mem-001",
            memory_type="long_term",
            content={"task": "example", "result": "success"},
        )
        
        # Retrieve long-term memory
        memory = cloud.get_memory("openclow-agent-001", "mem-001")
        
        # Get accumulated state (knowledge, preferences)
        states = cloud.get_state("openclow-agent-001")
        ```
    """
    
    def __init__(self, server: CNAA_MCPServer | None = None) -> None:
        """Initialize the agent interface.
        
        Args:
            server: CNAA MCP server instance (creates new one if None)
        """
        self.server = server or CNAA_MCPServer()
    
    def store_memory(
        self,
        agent_id: str,
        memory_id: str,
        memory_type: str,
        content: dict[str, Any],
        tags: list[str] | None = None,
        completion_score: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Store a memory in CNAA cloud.
        
        Args:
            agent_id: Agent identifier
            memory_id: Unique memory identifier
            memory_type: "long_term" or "short_term"
            content: Memory content (JSON-serializable dict)
            tags: Optional list of tags for retrieval
            completion_score: Task completion score [0.0, 1.0]
            metadata: Optional metadata
            
        Returns:
            Response dict with status and memory_id
        """
        return self.server.handle_tool_call(
            "cnaa_store_memory",
            {
                "agent_id": agent_id,
                "memory_id": memory_id,
                "type": memory_type,
                "content": content,
                "tags": tags or [],
                "completion_score": completion_score,
                "metadata": metadata or {},
            },
        )
    
    def get_memory(self, agent_id: str, memory_id: str) -> dict[str, Any]:
        """Retrieve a memory from CNAA cloud.
        
        Args:
            agent_id: Agent identifier
            memory_id: Memory identifier
            
        Returns:
            Response dict with memory data
        """
        return self.server.handle_tool_call(
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
        
        Args:
            agent_id: Agent identifier
            memory_type: Optional filter by type ("long_term" or "short_term")
            tags: Optional filter by tags
            
        Returns:
            Response dict with list of memory summaries
        """
        args: dict[str, Any] = {"agent_id": agent_id}
        if memory_type:
            args["type"] = memory_type
        if tags:
            args["tags"] = tags
        
        return self.server.handle_tool_call("cnaa_list_memories", args)
    
    def get_state(self, agent_id: str) -> dict[str, Any]:
        """Get all states for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Response dict with list of states
        """
        return self.server.handle_tool_call(
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
        """Create or update a state.
        
        Args:
            agent_id: Agent identifier
            state_id: State identifier
            category: State category ("preference", "knowledge", or "environment")
            content: State content
            
        Returns:
            Response dict with status
        """
        return self.server.handle_tool_call(
            "cnaa_update_state",
            {
                "agent_id": agent_id,
                "state_id": state_id,
                "category": category,
                "content": content,
            },
        )
    
    def get_preference(self, agent_id: str) -> dict[str, Any]:
        """Get all preferences for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Response dict with list of preferences
        """
        return self.server.handle_tool_call(
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
        source_memory_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create or update a preference.
        
        Args:
            agent_id: Agent identifier
            preference_id: Preference identifier
            key: Preference key/label
            value: Preference content
            importance: Importance score [0.0, 1.0]
            source_memory_ids: Optional list of source memory IDs
            
        Returns:
            Response dict with status
        """
        return self.server.handle_tool_call(
            "cnaa_update_preference",
            {
                "agent_id": agent_id,
                "preference_id": preference_id,
                "key": key,
                "value": value,
                "importance": importance,
                "source_memory_ids": source_memory_ids or [],
            },
        )
    
    def get_environment(self, agent_id: str) -> dict[str, Any]:
        """Get environment for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Response dict with environment data
        """
        return self.server.handle_tool_call(
            "cnaa_get_environment",
            {"agent_id": agent_id},
        )
    
    def update_environment(
        self,
        agent_id: str,
        env_id: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update environment.
        
        Args:
            agent_id: Agent identifier
            env_id: Environment identifier
            context: Environment context
            
        Returns:
            Response dict with status
        """
        return self.server.handle_tool_call(
            "cnaa_update_environment",
            {
                "agent_id": agent_id,
                "env_id": env_id,
                "context": context,
            },
        )
