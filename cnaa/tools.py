"""CNAA MCP Tool Definitions.

Defines all MCP tools exposed by CNAA Server.
These tool definitions are a core deliverable of the framework:
they define WHAT capabilities CNAA provides to agents.

Tool schemas are imported from cnaa.schemas for centralized management.
Modify cnaa/schemas.py to change interface formats.

Tool categories:
- Memory tools: store/get/list/tag/delete memories
- State tools: get/update/delete state entries
- Preference tools: get/update/delete preferences
- Environment tools: get/update environment context
"""

from __future__ import annotations

from typing import Any

# Import schemas from centralized schema definitions
from cnaa.schemas import (
    DELETE_MEMORY_REQUEST,
    DELETE_PREFERENCE_REQUEST,
    DELETE_STATE_REQUEST,
    GET_ENVIRONMENT_REQUEST,
    GET_MEMORY_REQUEST,
    GET_PREFERENCE_REQUEST,
    GET_STATE_REQUEST,
    LIST_MEMORIES_REQUEST,
    STORE_MEMORY_REQUEST,
    TAG_SHORT_TERM_REQUEST,
    UPDATE_ENVIRONMENT_REQUEST,
    UPDATE_PREFERENCE_REQUEST,
    UPDATE_STATE_REQUEST,
)

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
            "inputSchema": STORE_MEMORY_REQUEST,
        },
        {
            "name": GET_MEMORY,
            "description": (
                "Retrieve a memory by ID. "
                "Used to pull full memory details from cloud when needed."
            ),
            "inputSchema": GET_MEMORY_REQUEST,
        },
        {
            "name": LIST_MEMORIES,
            "description": (
                "List memories for an agent. "
                "Supports filtering by type and tags."
            ),
            "inputSchema": LIST_MEMORIES_REQUEST,
        },
        {
            "name": TAG_SHORT_TERM,
            "description": (
                "Tag short-term memories with labels. "
                "Used to mark recent memories for later retrieval "
                "or knowledge condensation."
            ),
            "inputSchema": TAG_SHORT_TERM_REQUEST,
        },
        {
            "name": DELETE_MEMORY,
            "description": "Delete a memory from storage.",
            "inputSchema": DELETE_MEMORY_REQUEST,
        },
        # --- State Tools ---
        {
            "name": GET_STATE,
            "description": (
                "Retrieve all state entries for an agent. "
                "State represents accumulated knowledge from experiences."
            ),
            "inputSchema": GET_STATE_REQUEST,
        },
        {
            "name": UPDATE_STATE,
            "description": (
                "Create or update a state entry. "
                "Used to persist accumulated knowledge."
            ),
            "inputSchema": UPDATE_STATE_REQUEST,
        },
        {
            "name": DELETE_STATE,
            "description": "Delete a state entry.",
            "inputSchema": DELETE_STATE_REQUEST,
        },
        # --- Preference Tools ---
        {
            "name": GET_PREFERENCE,
            "description": (
                "Retrieve all preferences for an agent. "
                "Preferences represent important memory patterns "
                "that shape agent behavior."
            ),
            "inputSchema": GET_PREFERENCE_REQUEST,
        },
        {
            "name": UPDATE_PREFERENCE,
            "description": (
                "Create or update a preference entry. "
                "Used to persist important memory patterns."
            ),
            "inputSchema": UPDATE_PREFERENCE_REQUEST,
        },
        {
            "name": DELETE_PREFERENCE,
            "description": "Delete a preference entry.",
            "inputSchema": DELETE_PREFERENCE_REQUEST,
        },
        # --- Environment Tools ---
        {
            "name": GET_ENVIRONMENT,
            "description": (
                "Retrieve the environment context for an agent. "
                "Environment provides context-aware information."
            ),
            "inputSchema": GET_ENVIRONMENT_REQUEST,
        },
        {
            "name": UPDATE_ENVIRONMENT,
            "description": (
                "Create or update the environment context. "
                "Used to persist current environment state."
            ),
            "inputSchema": UPDATE_ENVIRONMENT_REQUEST,
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


def get_tool_by_name(name: str) -> dict[str, Any] | None:
    """Get a tool definition by name.

    Args:
        name: The tool name.

    Returns:
        Tool definition dict if found, None otherwise.
    """
    for tool in get_tool_definitions():
        if tool["name"] == name:
            return tool
    return None
