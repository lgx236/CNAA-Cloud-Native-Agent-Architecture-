"""CNAA - Cloud Native Agentic Architecture.

Experience Runtime Framework for AI Agents.
Provides agentic frameworks (e.g., openclow) with long-term memory
capabilities: persistent experience, knowledge accumulation, and
preference learning across sessions.

Core specification: data models, interaction interfaces,
MCP tool definitions, and lifecycle rules.

This package IS the architecture specification.
Cloud/ and local/ are reference implementations.

Key Components:
- models.py: Core data models (Memory, State, Preference, Environment)
- schemas.py: Centralized JSON schema definitions (single source of truth)
- interaction.py: Abstract interfaces for local-cloud interaction
- tools.py: MCP tool definitions
- lifecycle.py: Pluggable lifecycle interfaces for external packages

Integration:
Agentic frameworks integrate via LocalAgentInterface (local/agent.py)
to gain long-term memory capabilities for their agents.
"""

# Core version and API compatibility
__version__ = "1.0.0"
API_VERSION = "v1"
API_COMPATIBILITY_MATRIX = {
    "v1": {"status": "stable", "release_date": "2026-08"},
    "v0.2": {"status": "deprecated", "removal_date": "v1.2"}
}

# Core data models
from cnaa.models import (
    Environment,
    InstantMemory,
    Memory,
    MemoryStatus,
    MemoryType,
    Preference,
    SearchResult,
    State,
    StateCategory,
    TaskCheckpoint,
)

# Schema definitions (single source of truth for JSON formats)
from cnaa.schemas import (
    get_all_schemas,
    get_request_schemas,
    get_response_schemas,
    get_schema,
)

# Interaction interfaces
from cnaa.interaction import MemoryInterface, StateInterface

# Lifecycle plugins (for external package integration)
from cnaa.lifecycle import (
    DefaultStateEvolutionPlugin,
    LifecycleConfig,
    LifecycleEvent,
    LifecyclePlugins,
    MemoryLifecyclePlugin,
    RetrievalPlugin,
    SimpleTimeBasedCondensationPlugin,
    StateEvolutionPhase,
    StateEvolutionPlugin,
    StateEvolutionRule,
    TimeBasedLifecyclePlugin,
)

# MCP tool definitions
from cnaa.tools import (
    get_tool_by_name,
    get_tool_definitions,
    get_tool_names,
)

# Deprecation management
from cnaa.deprecation import (
    deprecated,
    get_deprecation_manager,
    is_deprecated,
    list_deprecated_items,
    mark_deprecated,
    warn_deprecated,
)

# Security
from cnaa.security import (
    AuthConfig,
    AuthContext,
    PermissionLevel,
    load_auth_config_from_env,
    validate_api_key,
)

__all__ = [
    # Version
    "__version__",
    "API_VERSION",
    "API_COMPATIBILITY_MATRIX",
    # Data models
    "Environment",
    "InstantMemory",
    "Memory",
    "MemoryStatus",
    "MemoryType",
    "Preference",
    "SearchResult",
    "State",
    "StateCategory",
    "TaskCheckpoint",
    # Schema definitions
    "get_all_schemas",
    "get_request_schemas",
    "get_response_schemas",
    "get_schema",
    # Interaction interfaces
    "MemoryInterface",
    "StateInterface",
    # Lifecycle plugins
    "DefaultStateEvolutionPlugin",
    "LifecycleConfig",
    "LifecycleEvent",
    "LifecyclePlugins",
    "MemoryLifecyclePlugin",
    "RetrievalPlugin",
    "SimpleTimeBasedCondensationPlugin",
    "StateEvolutionPhase",
    "StateEvolutionPlugin",
    "StateEvolutionRule",
    "TimeBasedLifecyclePlugin",
    # MCP tools
    "get_tool_by_name",
    "get_tool_definitions",
    "get_tool_names",
    # Deprecation management
    "deprecated",
    "get_deprecation_manager",
    "is_deprecated",
    "list_deprecated_items",
    "mark_deprecated",
    "warn_deprecated",
    # Security
    "AuthConfig",
    "AuthContext",
    "PermissionLevel",
    "load_auth_config_from_env",
    "validate_api_key",
]
