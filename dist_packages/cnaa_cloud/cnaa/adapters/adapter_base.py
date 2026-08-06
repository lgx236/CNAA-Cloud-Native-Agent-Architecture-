"""CNAA Base Agent Interface - Abstract base class for all agent framework adapters.

This module defines the standard interface that any agent framework adapter
must implement to integrate with CNAA cloud memory system.

Supported Agent Frameworks:
- LangChain (Python)
- LlamaIndex (Python)  
- AutoGen (Python)
- CrewAI (Python)
- Custom Agents (via GenericAgentAdapter)

Usage:
    from cnaa.adapters import BaseCNAAAdapter, MemoryType
    
    class MyCustomAdapter(BaseCNAAAdapter):
        def on_agent_start(self, agent_id: str):
            # Custom initialization
            
        def on_task_complete(self, agent_id: str, task_result: dict):
            # Custom memory storage logic
            
            super().on_task_complete(agent_id, task_result)
            # Custom cleanup logic
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Memory type classification."""
    LONG_TERM = "long_term"
    SHORT_TERM = "short_term"


class StateCategory(Enum):
    """State category classification."""
    KNOWLEDGE = "knowledge"
    PREFERENCE = "preference"
    ENVIRONMENT = "environment"


@dataclass
class MemoryConfig:
    """Configuration for storing memory."""
    
    agent_id: str
    memory_id: str
    memory_type: MemoryType
    content: Dict[str, Any]
    tags: Optional[List[str]] = None
    completion_score: float = 1.0
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API serialization."""
        return {
            "agent_id": self.agent_id,
            "memory_id": self.memory_id,
            "type": self.memory_type.value,
            "content": self.content,
            "tags": self.tags or [],
            "completion_score": self.completion_score,
            "metadata": self.metadata or {},
        }


@dataclass 
class StateConfig:
    """Configuration for storing state."""
    
    agent_id: str
    state_id: str
    category: StateCategory
    content: Dict[str, Any]


@dataclass
class PreferenceConfig:
    """Configuration for storing preference."""
    
    agent_id: str
    preference_id: str
    key: str
    value: Dict[str, Any]
    importance: float = 0.0
    source_memory_ids: Optional[List[str]] = None


class BaseCNAAAdapter(ABC):
    """Base abstract class for all CNAA agent framework adapters.
    
    All agent framework adapters must inherit from this class and implement
    the required methods to properly integrate with CNAA cloud memory.
    
    Attributes:
        cnaa_server_url: URL of CNAA Cloud Server
        api_key: Optional API key for authentication
        timeout: Request timeout in seconds
        
    Example (LangChain):
        ```python
        from langchain.agents import AgentExecutor
        from cnaa.adapters import BaseCNAAAdapter
        from cnaa.adapters.langchain import LangChainCNAAMixin
        
        class MyCNAALangChainAgent(LangChainCNAAMixin, AgentExecutor):
            '''Example: LangChain agent with CNAA memory'''
            
            agent_id = "my-langchain-agent"
            
            def _call(self, inputs, *args, **kwargs):
                # Run original agent logic
                result = super()._call(inputs, *args, **kwargs)
                
                # Store experience via CNAA
                if self.should_store_memory(result):
                    self.store_memory(
                        agent_id=self.agent_id,
                        memory_id=f"task-{datetime.now().timestamp()}",
                        memory_type=MemoryType.LONG_TERM,
                        content=result,
                        completion_score=0.95
                    )
                
                return result
        ```
    
    Example (Custom):
        ```python
        class MyCustomAgent(BaseCNAAAdapter):
            '''Generic adapter for custom agents'''
            
            def __init__(self):
                super().__init__("http://localhost:8080")
                self.cnaa_server_url = "http://cloud-server:8080"
            
            def process_result(self, agent_id: str, result: dict):
                '''Process agent result and store memories'''
                # Your custom processing logic
                self.store_memory(...)
        ```
    """
    
    def __init__(
        self,
        cnaa_server_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize CNAA adapter.
        
        Args:
            cnaa_server_url: CNAA Cloud Server URL
            api_key: Optional API key for authentication
            timeout: HTTP request timeout in seconds
        """
        self.cnaa_server_url = cnaa_server_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        
        # Import client dynamically to avoid hard dependency
        try:
            from local.client.mcp_client_real import CNAA_MCPClient
            self._client = CNAA_MCPClient(
                server_url=cnaa_server_url,
                api_key=api_key,
                timeout=timeout
            )
        except ImportError as e:
            logger.warning(f"Cannot import CNAA client: {e}")
            self._client = None
    
    # =========================================================================
    # Core Memory Operations
    # =========================================================================
    
    def store_memory(
        self,
        agent_id: str,
        memory_id: str,
        memory_type: MemoryType | str,
        content: Dict[str, Any],
        tags: Optional[List[str]] = None,
        completion_score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Store a memory in CNAA cloud.
        
        Args:
            agent_id: Agent identifier
            memory_id: Unique memory identifier
            memory_type: "long_term" or "short_term"
            content: Memory content
            tags: Optional tags for categorization
            completion_score: Completion score [0.0, 1.0]
            metadata: Additional metadata
            
        Returns:
            Response from CNAA cloud server
            
        Raises:
            RuntimeError: If CNAA client not available
        """
        if not self._client:
            raise RuntimeError("CNAA client not initialized")
        
        config = MemoryConfig(
            agent_id=agent_id,
            memory_id=memory_id,
            memory_type=MemoryType(memory_type) if isinstance(memory_type, str) else memory_type,
            content=content,
            tags=tags,
            completion_score=completion_score,
            metadata=metadata,
        )
        
        return self._client.store_memory(**config.to_dict())
    
    def get_memory(
        self,
        agent_id: str,
        memory_id: str,
    ) -> Dict[str, Any]:
        """Retrieve a specific memory from CNAA cloud.
        
        Args:
            agent_id: Agent identifier
            memory_id: Memory ID to retrieve
            
        Returns:
            Memory data if found
        """
        if not self._client:
            raise RuntimeError("CNAA client not initialized")
        
        return self._client.get_memory(agent_id=agent_id, memory_id=memory_id)
    
    def list_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """List memories for an agent from CNAA cloud.
        
        Args:
            agent_id: Agent identifier
            memory_type: Optional filter by type
            tags: Optional filter by tags
            limit: Maximum number of results
            
        Returns:
            List of memory summaries
        """
        if not self._client:
            raise RuntimeError("CNAA client not initialized")
        
        return self._client.list_memories(
            agent_id=agent_id,
            memory_type=memory_type,
            tags=tags,
            limit=limit,
        )
    
    def delete_memory(
        self,
        agent_id: str,
        memory_id: str,
    ) -> Dict[str, Any]:
        """Delete a memory from CNAA cloud.
        
        Args:
            agent_id: Agent identifier
            memory_id: Memory ID to delete
            
        Returns:
            Success status
        """
        if not self._client:
            raise RuntimeError("CNAA client not initialized")
        
        return self._client.delete_memory(agent_id=agent_id, memory_id=memory_id)
    
    # =========================================================================
    # State Operations
    # =========================================================================
    
    def update_state(
        self,
        agent_id: str,
        state_id: str,
        category: StateCategory | str,
        content: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update or create a knowledge state.
        
        Args:
            agent_id: Agent identifier
            state_id: State identifier
            category: State category
            content: State content
            
        Returns:
            Success status
        """
        if not self._client:
            raise RuntimeError("CNAA client not initialized")
        
        category_enum = (
            StateCategory(category) if isinstance(category, str) else category
        )
        
        return self._client.update_state(
            agent_id=agent_id,
            state_id=state_id,
            category=category_enum.value,
            content=content,
        )
    
    def get_state(self, agent_id: str) -> Dict[str, Any]:
        """Get all states for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of state entries
        """
        if not self._client:
            raise RuntimeError("CNAA client not initialized")
        
        return self._client.get_state(agent_id=agent_id)
    
    def delete_state(
        self,
        agent_id: str,
        state_id: str,
    ) -> Dict[str, Any]:
        """Delete a state.
        
        Args:
            agent_id: Agent identifier
            state_id: State ID to delete
            
        Returns:
            Success status
        """
        if not self._client:
            raise RuntimeError("CNAA client not initialized")
        
        return self._client.delete_state(agent_id=agent_id, state_id=state_id)
    
    # =========================================================================
    # Preference Operations
    # =========================================================================
    
    def update_preference(
        self,
        agent_id: str,
        preference_id: str,
        key: str,
        value: Dict[str, Any],
        importance: float = 0.0,
        source_memory_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update an agent preference.
        
        Args:
            agent_id: Agent identifier
            preference_id: Preference identifier
            key: Preference key
            value: Preference value
            importance: Importance score [0.0, 1.0]
            source_memory_ids: Source memory IDs
            
        Returns:
            Success status
        """
        if not self._client:
            raise RuntimeError("CNAA client not initialized")
        
        return self._client.update_preference(
            agent_id=agent_id,
            preference_id=preference_id,
            key=key,
            value=value,
            importance=importance,
            source_memory_ids=source_memory_ids,
        )
    
    def get_preference(self, agent_id: str) -> Dict[str, Any]:
        """Get all preferences for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of preferences
        """
        if not self._client:
            raise RuntimeError("CNAA client not initialized")
        
        return self._client.get_preference(agent_id=agent_id)
    
    def delete_preference(
        self,
        agent_id: str,
        preference_id: str,
    ) -> Dict[str, Any]:
        """Delete a preference.
        
        Args:
            agent_id: Agent identifier
            preference_id: Preference ID to delete
            
        Returns:
            Success status
        """
        if not self._client:
            raise RuntimeError("CNAA client not initialized")
        
        return self._client.delete_preference(
            agent_id=agent_id,
            preference_id=preference_id,
        )
    
    # =========================================================================
    # Environment Operations
    # =========================================================================
    
    def update_environment(
        self,
        agent_id: str,
        env_id: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update agent environment context.
        
        Args:
            agent_id: Agent identifier
            env_id: Environment identifier
            context: Environment context
            
        Returns:
            Success status
        """
        if not self._client:
            raise RuntimeError("CNAA client not initialized")
        
        return self._client.update_environment(
            agent_id=agent_id,
            env_id=env_id,
            context=context,
        )
    
    def get_environment(self, agent_id: str) -> Dict[str, Any]:
        """Get environment context for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Environment context
        """
        if not self._client:
            raise RuntimeError("CNAA client not initialized")
        
        return self._client.get_environment(agent_id=agent_id)
    
    # =========================================================================
    # Template Methods (to be overridden by subclasses)
    # =========================================================================
    
    @abstractmethod
    def on_agent_start(self, agent_id: str) -> None:
        """Hook called when agent starts.
        
        Override this method to add custom initialization logic.
        
        Args:
            agent_id: Agent identifier
        """
        pass
    
    @abstractmethod
    def on_task_complete(
        self,
        agent_id: str,
        task_result: Dict[str, Any],
    ) -> None:
        """Hook called when agent task completes.
        
        Override this method to customize memory storage behavior.
        
        Args:
            agent_id: Agent identifier
            task_result: Result of completed task
        """
        pass
    
    @abstractmethod
    def on_error(
        self,
        agent_id: str,
        error: Exception,
    ) -> None:
        """Hook called when agent encounters error.
        
        Override this method to log errors to CNAA.
        
        Args:
            agent_id: Agent identifier
            error: Exception that occurred
        """
        pass
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def health_check(self) -> bool:
        """Check if CNAA cloud server is reachable.
        
        Returns:
            True if server is healthy
        """
        if not self._client:
            return False
        
        return self._client.health_check()
    
    def close(self) -> None:
        """Close resources."""
        if self._client:
            self._client.close()


# ============================================================================
# Pre-built Mixin Classes for Common Frameworks
# ============================================================================

class CNAAMemoryMixin:
    """Mixin class that adds CNAA memory capabilities to any agent.
    
    Usage:
        class MyAgent(CNAAMemoryMixin, MyBaseAgent):
            agent_id = "my-agent-001"
            
            def run(self, query: str) -> str:
                result = super().run(query)
                self.on_task_complete(self.agent_id, {"query": query, "result": result})
                return result
    """
    
    def store_experience(
        self,
        agent_id: str,
        task: str,
        outcome: Dict[str, Any],
        tags: Optional[List[str]] = None,
        completion_score: float = 1.0,
    ) -> None:
        """Convenience method to store task experience.
        
        Args:
            agent_id: Agent identifier
            task: Task description
            outcome: Task result/outcome
            tags: Tags for categorization
            completion_score: Completion score
        """
        self.store_memory(
            agent_id=agent_id,
            memory_id=f"exp-{datetime.now().timestamp()}",
            memory_type=MemoryType.LONG_TERM,
            content={"task": task, "outcome": outcome},
            tags=tags,
            completion_score=completion_score,
        )
    
    def learn_from_experience(
        self,
        agent_id: str,
        lesson: str,
        context: Dict[str, Any],
    ) -> None:
        """Learn from an experience and store as knowledge state.
        
        Args:
            agent_id: Agent identifier
            lesson: Key lesson learned
            context: Context of learning
        """
        self.update_state(
            agent_id=agent_id,
            state_id=f"learned-{datetime.now().timestamp()}",
            category=StateCategory.KNOWLEDGE,
            content={
                "lesson": lesson,
                "context": context,
                "timestamp": datetime.now().isoformat(),
            },
        )
