"""CNAA MCP Tool Definitions.

Defines all MCP tools exposed by CNAA Server.
These tool definitions are a core deliverable of the framework:
they define WHAT capabilities CNAA provides to agents.

Tool categories:
- Memory tools: store/get/list/tag/delete memories
- State tools: get/update/delete state entries
- Preference tools: get/update/delete preferences
- Environment tools: get/update environment context
"""

from __future__ import annotations

from typing import Any

# Tool name constants
STORE_MEMORY = "cnaa_store_memory"
GET_MEMORY = "cnaa_get_memory"
LIST_MEMORIES = "cnaa_list_memories"
TAG_SHORT_TERM = "cnaa_tag_short_term"
DELETE_MEMORY = "cnaa_delete_memory"

GET_STATE = "cnaa_get_state"
UPDATE_STATE = "cnaa_update_state"
DELETE_STATE = "cnaa_delete_state"

GET_PREFERENCE = "cnaa_get_preference"
UPDATE_PREFERENCE = "cnaa_update_preference"
DELETE_PREFERENCE = "cnaa_delete_preference"

GET_ENVIRONMENT = "cnaa_get_environment"
UPDATE_ENVIRONMENT = "cnaa_update_environment"


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return all MCP tool definitions.

    Each tool definition includes:
    - name: Tool identifier
    - description: What the tool does
    - inputSchema: JSON Schema for input parameters

    Returns:
        List of tool definition dicts.
    """
    return [
        # --- Memory Tools ---
        {
            "name": STORE_MEMORY,
            "description": (
                "Store a memory (long-term or short-term). "
                "Long-term memories are persisted in cloud for cross-device access. "
                "Short-term memories are kept in local context."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier",
                    },
                    "memory_id": {
                        "type": "string",
                        "description": "Unique memory identifier",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["long_term", "short_term"],
                        "description": "Memory type",
                    },
                    "content": {
                        "type": "object",
                        "description": "Memory content (open JSON structure)",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Memory tags for retrieval",
                    },
                    "completion_score": {
                        "type": "number",
                        "description": "Task completion score [0.0, 1.0]",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Optional metadata",
                    },
                },
                "required": ["agent_id", "memory_id", "type", "content"],
            },
        },
        {
            "name": GET_MEMORY,
            "description": (
                "Retrieve a memory by ID. "
                "Used to pull full memory details from cloud when needed."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier",
                    },
                    "memory_id": {
                        "type": "string",
                        "description": "Memory identifier to retrieve",
                    },
                },
                "required": ["agent_id", "memory_id"],
            },
        },
        {
            "name": LIST_MEMORIES,
            "description": (
                "List memories for an agent. "
                "Supports filtering by type and tags."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["long_term", "short_term"],
                        "description": "Filter by memory type (optional)",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags (optional)",
                    },
                },
                "required": ["agent_id"],
            },
        },
        {
            "name": TAG_SHORT_TERM,
            "description": (
                "Tag short-term memories with labels. "
                "Used to mark recent memories for later retrieval "
                "or knowledge condensation."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags to apply",
                    },
                },
                "required": ["agent_id", "tags"],
            },
        },
        {
            "name": DELETE_MEMORY,
            "description": "Delete a memory from storage.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier",
                    },
                    "memory_id": {
                        "type": "string",
                        "description": "Memory identifier to delete",
                    },
                },
                "required": ["agent_id", "memory_id"],
            },
        },
        # --- State Tools ---
        {
            "name": GET_STATE,
            "description": (
                "Retrieve all state entries for an agent. "
                "State represents accumulated knowledge from experiences."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier",
                    },
                },
                "required": ["agent_id"],
            },
        },
        {
            "name": UPDATE_STATE,
            "description": (
                "Create or update a state entry. "
                "Used to persist accumulated knowledge."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier",
                    },
                    "state_id": {
                        "type": "string",
                        "description": "State identifier",
                    },
                    "category": {
                        "type": "string",
                        "enum": ["preference", "knowledge", "environment"],
                        "description": "State category",
                    },
                    "content": {
                        "type": "object",
                        "description": "State content (JSON)",
                    },
                },
                "required": ["agent_id", "state_id", "category", "content"],
            },
        },
        {
            "name": DELETE_STATE,
            "description": "Delete a state entry.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier",
                    },
                    "state_id": {
                        "type": "string",
                        "description": "State identifier to delete",
                    },
                },
                "required": ["agent_id", "state_id"],
            },
        },
        # --- Preference Tools ---
        {
            "name": GET_PREFERENCE,
            "description": (
                "Retrieve all preferences for an agent. "
                "Preferences represent important memory patterns "
                "that shape agent behavior."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier",
                    },
                },
                "required": ["agent_id"],
            },
        },
        {
            "name": UPDATE_PREFERENCE,
            "description": (
                "Create or update a preference entry. "
                "Used to persist important memory patterns."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier",
                    },
                    "preference_id": {
                        "type": "string",
                        "description": "Preference identifier",
                    },
                    "key": {
                        "type": "string",
                        "description": "Preference key/label",
                    },
                    "value": {
                        "type": "object",
                        "description": "Preference content (JSON)",
                    },
                    "importance": {
                        "type": "number",
                        "description": "Importance score [0.0, 1.0]",
                    },
                    "source_memory_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Source memory identifiers",
                    },
                },
                "required": [
                    "agent_id",
                    "preference_id",
                    "key",
                    "value",
                ],
            },
        },
        {
            "name": DELETE_PREFERENCE,
            "description": "Delete a preference entry.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier",
                    },
                    "preference_id": {
                        "type": "string",
                        "description": "Preference identifier to delete",
                    },
                },
                "required": ["agent_id", "preference_id"],
            },
        },
        # --- Environment Tools ---
        {
            "name": GET_ENVIRONMENT,
            "description": (
                "Retrieve the environment context for an agent. "
                "Environment provides context-aware information."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier",
                    },
                },
                "required": ["agent_id"],
            },
        },
        {
            "name": UPDATE_ENVIRONMENT,
            "description": (
                "Create or update the environment context. "
                "Used to persist current environment state."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier",
                    },
                    "env_id": {
                        "type": "string",
                        "description": "Environment identifier",
                    },
                    "context": {
                        "type": "object",
                        "description": "Environment context (JSON)",
                    },
                },
                "required": ["agent_id", "env_id", "context"],
            },
        },
    ]


def get_tool_names() -> list[str]:
    """Return list of all tool names.

    Returns:
        List of tool name strings.
    """
    return [
        STORE_MEMORY,
        GET_MEMORY,
        LIST_MEMORIES,
        TAG_SHORT_TERM,
        DELETE_MEMORY,
        GET_STATE,
        UPDATE_STATE,
        DELETE_STATE,
        GET_PREFERENCE,
        UPDATE_PREFERENCE,
        DELETE_PREFERENCE,
        GET_ENVIRONMENT,
        UPDATE_ENVIRONMENT,
    ]
