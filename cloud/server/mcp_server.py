"""CNAA MCP Server Implementation.

Reference implementation of CNAA cloud server using MCP protocol.
This server:
- Registers all MCP tools defined in cnaa.tools
- Routes tool calls to storage backends
- Follows dumb service principle (JSON in, JSON out)

Algorithm responsibilities:
- IMPLEMENTED: Tool routing, request/response marshalling
- TODO (production): Authentication, rate limiting, request validation
- TODO (algorithm): Request batching, caching layer, query optimization
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from cnaa.models import (
    Environment,
    Memory,
    MemoryType,
    Preference,
    State,
    StateCategory,
)
from cnaa.tools import (
    DELETE_MEMORY,
    DELETE_PREFERENCE,
    DELETE_STATE,
    GET_ENVIRONMENT,
    GET_MEMORY,
    GET_PREFERENCE,
    GET_STATE,
    LIST_MEMORIES,
    STORE_MEMORY,
    TAG_SHORT_TERM,
    UPDATE_ENVIRONMENT,
    UPDATE_PREFERENCE,
    UPDATE_STATE,
    get_tool_definitions,
)
from cloud.storage.memory_store import InMemoryMemoryStore
from cloud.storage.state_store import InMemoryStateStore

logger = logging.getLogger(__name__)


class CNAA_MCPServer:
    """CNAA MCP Server reference implementation.
    
    This server handles MCP tool calls and routes them to storage backends.
    It follows the dumb service principle: JSON in, JSON out, no reasoning.
    
    Attributes:
        memory_store: Storage backend for memories
        state_store: Storage backend for states/preferences/environments
    """
    
    def __init__(
        self,
        memory_store: InMemoryMemoryStore | None = None,
        state_store: InMemoryStateStore | None = None,
    ) -> None:
        """Initialize the MCP server.
        
        Args:
            memory_store: Memory storage backend (defaults to InMemoryMemoryStore)
            state_store: State storage backend (defaults to InMemoryStateStore)
        """
        self.memory_store = memory_store or InMemoryMemoryStore()
        self.state_store = state_store or InMemoryStateStore()
        self._tool_handlers = self._register_tool_handlers()
    
    def _register_tool_handlers(self) -> dict[str, Any]:
        """Register tool call handlers.
        
        Returns:
            Dict mapping tool names to handler functions
        """
        return {
            STORE_MEMORY: self._handle_store_memory,
            GET_MEMORY: self._handle_get_memory,
            LIST_MEMORIES: self._handle_list_memories,
            TAG_SHORT_TERM: self._handle_tag_short_term,
            DELETE_MEMORY: self._handle_delete_memory,
            GET_STATE: self._handle_get_state,
            UPDATE_STATE: self._handle_update_state,
            DELETE_STATE: self._handle_delete_state,
            GET_PREFERENCE: self._handle_get_preference,
            UPDATE_PREFERENCE: self._handle_update_preference,
            DELETE_PREFERENCE: self._handle_delete_preference,
            GET_ENVIRONMENT: self._handle_get_environment,
            UPDATE_ENVIRONMENT: self._handle_update_environment,
        }
    
    def handle_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle an MCP tool call.
        
        IMPLEMENTED:
            Routes tool_name to registered handler via dict lookup.
            Wraps handler call with try/except for error handling.
            Returns JSON response dict.
            Time complexity: O(1) for routing, handler-dependent for execution.
        
        TODO (production):
            - Add request schema validation (validate arguments against tool inputSchema)
            - Add authentication/authorization checks
            - Add rate limiting per agent_id
            - Add request/response logging for debugging
        
        Args:
            tool_name: Name of the MCP tool to call
            arguments: Arguments for the tool call
            
        Returns:
            JSON response dict
        """
        handler = self._tool_handlers.get(tool_name)
        if handler is None:
            return {
                "status": "error",
                "message": f"Unknown tool: {tool_name}",
            }
        
        try:
            return handler(arguments)
        except Exception as e:
            logger.exception(f"Error handling tool {tool_name}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get all MCP tool definitions.
        
        Returns:
            List of tool definition dicts
        """
        return get_tool_definitions()
    
    # --- Memory Tool Handlers ---
    
    def _handle_store_memory(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle cnaa_store_memory tool call."""
        memory = Memory(
            memory_id=args["memory_id"],
            agent_id=args["agent_id"],
            type=MemoryType(args["type"]),
            content=args["content"],
            tags=args.get("tags", []),
            completion_score=args.get("completion_score", 0.0),
            metadata=args.get("metadata", {}),
        )
        return self.memory_store.store_memory(memory)
    
    def _handle_get_memory(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle cnaa_get_memory tool call."""
        memory = self.memory_store.get_memory(args["agent_id"], args["memory_id"])
        if memory is None:
            return {
                "status": "not_found",
                "message": f"Memory {args['memory_id']} not found",
            }
        
        return {
            "status": "ok",
            "memory": {
                "memory_id": memory.memory_id,
                "agent_id": memory.agent_id,
                "type": memory.type.value,
                "content": memory.content,
                "tags": memory.tags,
                "completion_score": memory.completion_score,
                "timestamp": memory.timestamp.isoformat() if memory.timestamp else None,
                "metadata": memory.metadata,
            },
        }
    
    def _handle_list_memories(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle cnaa_list_memories tool call."""
        memory_type = MemoryType(args["type"]) if "type" in args else None
        tags = args.get("tags")
        
        summaries = self.memory_store.list_memories(
            args["agent_id"],
            memory_type=memory_type,
            tags=tags,
        )
        
        return {
            "status": "ok",
            "memories": [
                {
                    "memory_id": s.memory_id,
                    "tags": s.tags,
                    "completion_score": s.completion_score,
                    "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                }
                for s in summaries
            ],
        }
    
    def _handle_tag_short_term(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle cnaa_tag_short_term tool call."""
        return self.memory_store.tag_short_term(args["agent_id"], args["tags"])
    
    def _handle_delete_memory(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle cnaa_delete_memory tool call."""
        return self.memory_store.delete_memory(args["agent_id"], args["memory_id"])
    
    # --- State Tool Handlers ---
    
    def _handle_get_state(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle cnaa_get_state tool call."""
        states = self.state_store.get_state(args["agent_id"])
        return {
            "status": "ok",
            "states": [
                {
                    "state_id": s.state_id,
                    "category": s.category.value,
                    "content": s.content,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
                for s in states
            ],
        }
    
    def _handle_update_state(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle cnaa_update_state tool call."""
        state = State(
            agent_id=args["agent_id"],
            state_id=args["state_id"],
            category=StateCategory(args["category"]),
            content=args["content"],
        )
        return self.state_store.update_state(args["agent_id"], state)
    
    def _handle_delete_state(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle cnaa_delete_state tool call."""
        return self.state_store.delete_state(args["agent_id"], args["state_id"])
    
    # --- Preference Tool Handlers ---
    
    def _handle_get_preference(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle cnaa_get_preference tool call."""
        prefs = self.state_store.get_preference(args["agent_id"])
        return {
            "status": "ok",
            "preferences": [
                {
                    "preference_id": p.preference_id,
                    "key": p.key,
                    "value": p.value,
                    "importance": p.importance,
                    "source_memory_ids": p.source_memory_ids,
                }
                for p in prefs
            ],
        }
    
    def _handle_update_preference(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle cnaa_update_preference tool call."""
        pref = Preference(
            agent_id=args["agent_id"],
            preference_id=args["preference_id"],
            key=args["key"],
            value=args["value"],
            importance=args.get("importance", 0.0),
            source_memory_ids=args.get("source_memory_ids", []),
        )
        return self.state_store.update_preference(args["agent_id"], pref)
    
    def _handle_delete_preference(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle cnaa_delete_preference tool call."""
        return self.state_store.delete_preference(
            args["agent_id"], args["preference_id"]
        )
    
    # --- Environment Tool Handlers ---
    
    def _handle_get_environment(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle cnaa_get_environment tool call."""
        env = self.state_store.get_environment(args["agent_id"])
        if env is None:
            return {
                "status": "not_found",
                "message": f"Environment for agent {args['agent_id']} not found",
            }
        
        return {
            "status": "ok",
            "environment": {
                "env_id": env.env_id,
                "context": env.context,
                "updated_at": env.updated_at.isoformat() if env.updated_at else None,
            },
        }
    
    def _handle_update_environment(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle cnaa_update_environment tool call."""
        env = Environment(
            agent_id=args["agent_id"],
            env_id=args["env_id"],
            context=args["context"],
        )
        return self.state_store.update_environment(args["agent_id"], env)
