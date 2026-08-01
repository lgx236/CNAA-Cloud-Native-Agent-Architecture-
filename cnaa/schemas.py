"""CNAA Interface Schema Definitions.

This is the SINGLE SOURCE OF TRUTH for all interface JSON schemas.
Modify this file to change interface formats.

Local clients fetch these schemas from cloud server to understand
the available interfaces and their formats.

Schema categories:
- Request schemas: What local sends to cloud
- Response schemas: What cloud returns to local
- Data schemas: Common data structure definitions
"""

from __future__ import annotations

from typing import Any

# ============================================================================
# Common Data Schemas
# ============================================================================

MEMORY_SCHEMA = {
    "type": "object",
    "properties": {
        "memory_id": {"type": "string", "description": "Unique memory identifier"},
        "agent_id": {"type": "string", "description": "Agent identifier"},
        "type": {
            "type": "string",
            "enum": ["long_term", "short_term"],
            "description": "Memory type",
        },
        "content": {"type": "object", "description": "Memory content (open JSON)"},
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Memory tags",
        },
        "completion_score": {
            "type": "number",
            "description": "Task completion score [0.0, 1.0]",
        },
        "timestamp": {"type": "string", "format": "date-time"},
        "metadata": {"type": "object", "description": "Optional metadata"},
    },
    "required": ["memory_id", "agent_id", "type", "content"],
}

STATE_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
        "state_id": {"type": "string", "description": "State unique identifier"},
        "category": {
            "type": "string",
            "enum": ["preference", "knowledge", "environment"],
            "description": "State category",
        },
        "content": {"type": "object", "description": "State content (JSON)"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
    "required": ["agent_id", "state_id", "category", "content"],
}

PREFERENCE_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
        "preference_id": {"type": "string", "description": "Preference identifier"},
        "key": {"type": "string", "description": "Preference key/label"},
        "value": {"type": "object", "description": "Preference content (JSON)"},
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
    "required": ["agent_id", "preference_id", "key", "value"],
}

ENVIRONMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
        "env_id": {"type": "string", "description": "Environment identifier"},
        "context": {"type": "object", "description": "Environment context (JSON)"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
    "required": ["agent_id", "env_id", "context"],
}

INSTANT_MEMORY_SCHEMA = {
    "type": "object",
    "properties": {
        "memory_id": {"type": "string", "description": "Memory identifier"},
        "task_id": {"type": "string", "description": "Task identifier"},
        "checkpoint_id": {"type": "string", "description": "Checkpoint identifier"},
        "summary": {"type": "string", "description": "Lightweight summary"},
        "status": {
            "type": "string",
            "enum": ["active", "condensed", "evicted"],
            "description": "Memory status",
        },
        "cnaa_ref": {
            "type": "string",
            "description": "Reference to cloud long-term memory",
        },
        "timestamp": {"type": "string", "format": "date-time"},
    },
    "required": ["memory_id", "task_id", "checkpoint_id", "summary"],
}

# ============================================================================
# Request Schemas (Local → Cloud)
# ============================================================================

# Memory Requests
STORE_MEMORY_REQUEST = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
        "memory_id": {"type": "string", "description": "Memory identifier"},
        "type": {
            "type": "string",
            "enum": ["long_term", "short_term"],
            "description": "Memory type",
        },
        "content": {"type": "object", "description": "Memory content"},
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Memory tags",
        },
        "completion_score": {
            "type": "number",
            "description": "Completion score [0.0, 1.0]",
        },
        "metadata": {"type": "object", "description": "Optional metadata"},
    },
    "required": ["agent_id", "memory_id", "type", "content"],
}

GET_MEMORY_REQUEST = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
        "memory_id": {"type": "string", "description": "Memory identifier"},
    },
    "required": ["agent_id", "memory_id"],
}

LIST_MEMORIES_REQUEST = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
        "type": {
            "type": "string",
            "enum": ["long_term", "short_term"],
            "description": "Filter by type (optional)",
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Filter by tags (optional)",
        },
    },
    "required": ["agent_id"],
}

TAG_SHORT_TERM_REQUEST = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tags to apply",
        },
    },
    "required": ["agent_id", "tags"],
}

DELETE_MEMORY_REQUEST = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
        "memory_id": {"type": "string", "description": "Memory identifier"},
    },
    "required": ["agent_id", "memory_id"],
}

# State Requests
GET_STATE_REQUEST = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
    },
    "required": ["agent_id"],
}

UPDATE_STATE_REQUEST = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
        "state_id": {"type": "string", "description": "State identifier"},
        "category": {
            "type": "string",
            "enum": ["preference", "knowledge", "environment"],
            "description": "State category",
        },
        "content": {"type": "object", "description": "State content"},
    },
    "required": ["agent_id", "state_id", "category", "content"],
}

DELETE_STATE_REQUEST = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
        "state_id": {"type": "string", "description": "State identifier"},
    },
    "required": ["agent_id", "state_id"],
}

# Preference Requests
GET_PREFERENCE_REQUEST = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
    },
    "required": ["agent_id"],
}

UPDATE_PREFERENCE_REQUEST = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
        "preference_id": {"type": "string", "description": "Preference identifier"},
        "key": {"type": "string", "description": "Preference key"},
        "value": {"type": "object", "description": "Preference content"},
        "importance": {
            "type": "number",
            "description": "Importance score [0.0, 1.0]",
        },
        "source_memory_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Source memory IDs",
        },
    },
    "required": ["agent_id", "preference_id", "key", "value"],
}

DELETE_PREFERENCE_REQUEST = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
        "preference_id": {"type": "string", "description": "Preference identifier"},
    },
    "required": ["agent_id", "preference_id"],
}

# Environment Requests
GET_ENVIRONMENT_REQUEST = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
    },
    "required": ["agent_id"],
}

UPDATE_ENVIRONMENT_REQUEST = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string", "description": "Agent identifier"},
        "env_id": {"type": "string", "description": "Environment identifier"},
        "context": {"type": "object", "description": "Environment context"},
    },
    "required": ["agent_id", "env_id", "context"],
}

# ============================================================================
# Response Schemas (Cloud → Local)
# ============================================================================

STATUS_RESPONSE = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok", "error"]},
        "message": {"type": "string", "description": "Error message (if error)"},
    },
    "required": ["status"],
}

STORE_MEMORY_RESPONSE = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok", "error"]},
        "memory_id": {"type": "string"},
        "message": {"type": "string"},
    },
    "required": ["status", "memory_id"],
}

GET_MEMORY_RESPONSE = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok", "error", "not_found"]},
        "memory": MEMORY_SCHEMA,
        "message": {"type": "string"},
    },
    "required": ["status"],
}

LIST_MEMORIES_RESPONSE = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok", "error"]},
        "memories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "completion_score": {"type": "number"},
                    "timestamp": {"type": "string"},
                },
            },
        },
        "message": {"type": "string"},
    },
    "required": ["status", "memories"],
}

GET_STATE_RESPONSE = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok", "error"]},
        "states": {"type": "array", "items": STATE_SCHEMA},
        "message": {"type": "string"},
    },
    "required": ["status", "states"],
}

GET_PREFERENCE_RESPONSE = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok", "error"]},
        "preferences": {"type": "array", "items": PREFERENCE_SCHEMA},
        "message": {"type": "string"},
    },
    "required": ["status", "preferences"],
}

GET_ENVIRONMENT_RESPONSE = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok", "error", "not_found"]},
        "environment": ENVIRONMENT_SCHEMA,
        "message": {"type": "string"},
    },
    "required": ["status"],
}

# ============================================================================
# Schema Registry
# ============================================================================

def get_all_schemas() -> dict[str, Any]:
    """Return all schema definitions.
    
    Returns:
        Dict mapping schema names to their definitions.
    """
    return {
        # Data schemas
        "memory": MEMORY_SCHEMA,
        "state": STATE_SCHEMA,
        "preference": PREFERENCE_SCHEMA,
        "environment": ENVIRONMENT_SCHEMA,
        "instant_memory": INSTANT_MEMORY_SCHEMA,
        
        # Request schemas
        "store_memory_request": STORE_MEMORY_REQUEST,
        "get_memory_request": GET_MEMORY_REQUEST,
        "list_memories_request": LIST_MEMORIES_REQUEST,
        "tag_short_term_request": TAG_SHORT_TERM_REQUEST,
        "delete_memory_request": DELETE_MEMORY_REQUEST,
        "get_state_request": GET_STATE_REQUEST,
        "update_state_request": UPDATE_STATE_REQUEST,
        "delete_state_request": DELETE_STATE_REQUEST,
        "get_preference_request": GET_PREFERENCE_REQUEST,
        "update_preference_request": UPDATE_PREFERENCE_REQUEST,
        "delete_preference_request": DELETE_PREFERENCE_REQUEST,
        "get_environment_request": GET_ENVIRONMENT_REQUEST,
        "update_environment_request": UPDATE_ENVIRONMENT_REQUEST,
        
        # Response schemas
        "status_response": STATUS_RESPONSE,
        "store_memory_response": STORE_MEMORY_RESPONSE,
        "get_memory_response": GET_MEMORY_RESPONSE,
        "list_memories_response": LIST_MEMORIES_RESPONSE,
        "get_state_response": GET_STATE_RESPONSE,
        "get_preference_response": GET_PREFERENCE_RESPONSE,
        "get_environment_response": GET_ENVIRONMENT_RESPONSE,
    }


def get_schema(name: str) -> dict[str, Any] | None:
    """Get a specific schema by name.
    
    Args:
        name: Schema name (e.g., "memory", "store_memory_request")
    
    Returns:
        Schema dict if found, None otherwise.
    """
    schemas = get_all_schemas()
    return schemas.get(name)


def get_request_schemas() -> dict[str, Any]:
    """Return all request schemas.
    
    Returns:
        Dict of request schema definitions.
    """
    return {
        "store_memory": STORE_MEMORY_REQUEST,
        "get_memory": GET_MEMORY_REQUEST,
        "list_memories": LIST_MEMORIES_REQUEST,
        "tag_short_term": TAG_SHORT_TERM_REQUEST,
        "delete_memory": DELETE_MEMORY_REQUEST,
        "get_state": GET_STATE_REQUEST,
        "update_state": UPDATE_STATE_REQUEST,
        "delete_state": DELETE_STATE_REQUEST,
        "get_preference": GET_PREFERENCE_REQUEST,
        "update_preference": UPDATE_PREFERENCE_REQUEST,
        "delete_preference": DELETE_PREFERENCE_REQUEST,
        "get_environment": GET_ENVIRONMENT_REQUEST,
        "update_environment": UPDATE_ENVIRONMENT_REQUEST,
    }


def get_response_schemas() -> dict[str, Any]:
    """Return all response schemas.
    
    Returns:
        Dict of response schema definitions.
    """
    return {
        "status": STATUS_RESPONSE,
        "store_memory": STORE_MEMORY_RESPONSE,
        "get_memory": GET_MEMORY_RESPONSE,
        "list_memories": LIST_MEMORIES_RESPONSE,
        "get_state": GET_STATE_RESPONSE,
        "get_preference": GET_PREFERENCE_RESPONSE,
        "get_environment": GET_ENVIRONMENT_RESPONSE,
    }
