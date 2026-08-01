"""Local Agent Interface.

Provides a unified interface for agents to interact with CNAA.
This is the main entry point for agent integration.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from cnaa.models import Environment, Preference, State, StateCategory
from local.client.mcp_client import CNAA_MCPClient
from local.memory.instant_memory import InstantMemoryManager
from local.state.state_cache import StateCache


class LocalAgentInterface:
    """Agent-facing interface for CNAA local client.
    
    This is the main entry point for agents to interact with CNAA.
    It combines:
    - Instant memory management (local)
    - State cache (local)
    - MCP client (cloud communication)
    
    The interface is designed for agent frameworks like openclow to integrate
    basic memory capabilities through CNAA.
    
    Example:
        ```python
        from local import LocalAgentInterface
        
        # Create agent interface
        agent = LocalAgentInterface(
            agent_id="agent-001",
            server_url="http://localhost:8080",
        )
        
        # Store a memory (goes to cloud)
        agent.store_memory(
            memory_id="mem-001",
            memory_type="long_term",
            content={"task": "example"},
        )
        
        # Create instant memory (local)
        agent.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Completed task",
            memory_id="mem-001",
        )
        
        # Get cached states
        states = agent.get_states()
        ```
    """
    
    def __init__(
        self,
        agent_id: str,
        server_url: str | None = None,
        cloud_server: Any = None,
        cache_ttl_minutes: float = 5.0,
    ) -> None:
        """Initialize the local agent interface.
        
        Args:
            agent_id: Agent identifier
            server_url: URL of CNAA cloud server (for HTTP transport)
            cloud_server: Cloud server instance (for direct testing)
            cache_ttl_minutes: State cache TTL in minutes
        """
        self.agent_id = agent_id
        
        # Initialize components
        self.memory_manager = InstantMemoryManager(agent_id)
        self.state_cache = StateCache(agent_id, ttl_minutes=cache_ttl_minutes)
        self.mcp_client = CNAA_MCPClient(server_url=server_url)
        
        # For testing: connect client to cloud server directly
        if cloud_server:
            self.mcp_client.set_mock_handler(cloud_server)
    
    # --- Memory Operations (Cloud) ---
    
    def store_memory(
        self,
        memory_id: str,
        memory_type: str,
        content: dict[str, Any],
        tags: list[str] | None = None,
        completion_score: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Store a memory in CNAA cloud.
        
        Args:
            memory_id: Memory identifier
            memory_type: "long_term" or "short_term"
            content: Memory content
            tags: Optional tags
            completion_score: Completion score [0.0, 1.0]
            metadata: Optional metadata
            
        Returns:
            Response dict
        """
        return self.mcp_client.store_memory(
            agent_id=self.agent_id,
            memory_id=memory_id,
            memory_type=memory_type,
            content=content,
            tags=tags,
            completion_score=completion_score,
            metadata=metadata,
        )
    
    def get_memory(self, memory_id: str) -> dict[str, Any]:
        """Get a memory from CNAA cloud.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Response dict with memory data
        """
        return self.mcp_client.get_memory(self.agent_id, memory_id)
    
    def list_memories(
        self,
        memory_type: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """List memories from CNAA cloud.
        
        Args:
            memory_type: Optional type filter
            tags: Optional tag filter
            
        Returns:
            Response dict with memory list
        """
        return self.mcp_client.list_memories(
            self.agent_id, memory_type=memory_type, tags=tags
        )
    
    def delete_memory(self, memory_id: str) -> dict[str, Any]:
        """Delete a memory from CNAA cloud.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Response dict
        """
        return self.mcp_client.delete_memory(self.agent_id, memory_id)
    
    # --- Instant Memory Operations (Local) ---
    
    def create_instant_memory(
        self,
        task_id: str,
        checkpoint_id: str,
        summary: str,
        memory_id: str,
    ) -> dict[str, Any]:
        """Create an instant memory locally.
        
        Instant memories are lightweight summaries kept in local context.
        They reference full data stored in cloud.
        
        Args:
            task_id: Task identifier
            checkpoint_id: Checkpoint identifier
            summary: Lightweight summary
            memory_id: Memory identifier (should match cloud memory_id)
            
        Returns:
            Response dict with instant memory data
        """
        instant = self.memory_manager.create_instant_memory(
            task_id=task_id,
            checkpoint_id=checkpoint_id,
            summary=summary,
            memory_id=memory_id,
        )
        
        return {
            "status": "ok",
            "memory_id": instant.memory_id,
            "cnaa_ref": instant.cnaa_ref,
        }
    
    def get_active_instant_memories(self) -> list[dict[str, Any]]:
        """Get all active instant memories.
        
        Returns:
            List of instant memory dicts
        """
        memories = self.memory_manager.get_active_memories()
        return [
            {
                "memory_id": m.memory_id,
                "task_id": m.task_id,
                "checkpoint_id": m.checkpoint_id,
                "summary": m.summary,
                "cnaa_ref": m.cnaa_ref,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            }
            for m in memories
        ]
    
    def condense_old_instant_memories(self, threshold_hours: float = 1.0) -> int:
        """Condense old instant memories.
        
        Args:
            threshold_hours: Age threshold in hours
            
        Returns:
            Number of memories condensed
        """
        return self.memory_manager.condense_old_memories(threshold_hours)
    
    # --- State Operations (Cloud with Local Cache) ---
    
    def get_states(self, use_cache: bool = True) -> list[dict[str, Any]]:
        """Get states, using cache if available.
        
        Args:
            use_cache: Whether to use local cache
            
        Returns:
            List of state dicts
        """
        if use_cache and not self.state_cache.is_expired():
            states = self.state_cache.get_states()
        else:
            # Fetch from cloud
            response = self.mcp_client.get_state(self.agent_id)
            if response["status"] == "ok":
                # Update cache
                self._update_state_cache(response.get("states", []))
                states = self.state_cache.get_states()
            else:
                return []
        
        return [
            {
                "state_id": s.state_id,
                "category": s.category.value,
                "content": s.content,
            }
            for s in states
        ]
    
    def update_state(
        self,
        state_id: str,
        category: str,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        """Update a state in CNAA cloud.
        
        Args:
            state_id: State identifier
            category: State category
            content: State content
            
        Returns:
            Response dict
        """
        result = self.mcp_client.update_state(
            self.agent_id, state_id, category, content
        )
        
        # Invalidate cache
        self.state_cache.clear()
        
        return result
    
    def get_preferences(self, use_cache: bool = True) -> list[dict[str, Any]]:
        """Get preferences, using cache if available.
        
        Args:
            use_cache: Whether to use local cache
            
        Returns:
            List of preference dicts
        """
        if use_cache and not self.state_cache.is_expired():
            prefs = self.state_cache.get_preferences()
        else:
            # Fetch from cloud
            response = self.mcp_client.get_preference(self.agent_id)
            if response["status"] == "ok":
                self._update_preference_cache(response.get("preferences", []))
                prefs = self.state_cache.get_preferences()
            else:
                return []
        
        return [
            {
                "preference_id": p.preference_id,
                "key": p.key,
                "value": p.value,
                "importance": p.importance,
            }
            for p in prefs
        ]
    
    def update_preference(
        self,
        preference_id: str,
        key: str,
        value: dict[str, Any],
        importance: float = 0.0,
        source_memory_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update a preference in CNAA cloud.
        
        Args:
            preference_id: Preference identifier
            key: Preference key
            value: Preference value
            importance: Importance score
            source_memory_ids: Source memory IDs
            
        Returns:
            Response dict
        """
        result = self.mcp_client.update_preference(
            self.agent_id,
            preference_id,
            key,
            value,
            importance,
            source_memory_ids,
        )
        
        # Invalidate cache
        self.state_cache.clear()
        
        return result
    
    def get_environment(self, use_cache: bool = True) -> dict[str, Any] | None:
        """Get environment, using cache if available.
        
        Args:
            use_cache: Whether to use local cache
            
        Returns:
            Environment dict or None
        """
        if use_cache and not self.state_cache.is_expired():
            env = self.state_cache.get_environment()
            if env:
                return {
                    "env_id": env.env_id,
                    "context": env.context,
                }
            return None
        
        # Fetch from cloud
        response = self.mcp_client.get_environment(self.agent_id)
        if response["status"] == "ok":
            env_data = response.get("environment")
            if env_data:
                self.state_cache.update_environment(
                    Environment(
                        agent_id=self.agent_id,
                        env_id=env_data["env_id"],
                        context=env_data["context"],
                    )
                )
                return {
                    "env_id": env_data["env_id"],
                    "context": env_data["context"],
                }
        
        return None
    
    def update_environment(
        self,
        env_id: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Update environment in CNAA cloud.
        
        Args:
            env_id: Environment identifier
            context: Environment context
            
        Returns:
            Response dict
        """
        result = self.mcp_client.update_environment(
            self.agent_id, env_id, context
        )
        
        # Invalidate cache
        self.state_cache.clear()
        
        return result
    
    # --- Helper Methods ---
    
    def _update_state_cache(self, states_data: list[dict[str, Any]]) -> None:
        """Update state cache from cloud response data.
        
        Args:
            states_data: List of state dicts from cloud
        """
        states = [
            State(
                agent_id=self.agent_id,
                state_id=s["state_id"],
                category=StateCategory(s["category"]),
                content=s["content"],
            )
            for s in states_data
        ]
        self.state_cache.update_states(states)
    
    def _update_preference_cache(
        self, prefs_data: list[dict[str, Any]]
    ) -> None:
        """Update preference cache from cloud response data.
        
        Args:
            prefs_data: List of preference dicts from cloud
        """
        prefs = [
            Preference(
                agent_id=self.agent_id,
                preference_id=p["preference_id"],
                key=p["key"],
                value=p["value"],
                importance=p.get("importance", 0.0),
                source_memory_ids=p.get("source_memory_ids", []),
            )
            for p in prefs_data
        ]
        self.state_cache.update_preferences(prefs)
