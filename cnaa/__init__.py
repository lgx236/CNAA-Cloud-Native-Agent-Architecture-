"""CNAA - Cloud Native Agentic Architecture.

Experience Runtime Framework for AI Agents.
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
"""

__version__ = "0.1.0"

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
    get_tool_definitions as get_schema_definitions,
)

# Interaction interfaces
from cnaa.interaction import MemoryInterface, StateInterface

# Lifecycle plugins (for external package integration)
from cnaa.lifecycle import (
    DefaultStateEvolutionPlugin,
    LifecycleConfig,
    LifecycleEvent,
    LifecyclePlugins,
    MemoryLifecycleManager,
    MemoryLifecyclePlugin,
    RetrievalPlugin,
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

__all__ = [
    # Version
    "__version__",
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
    "get_schema_definitions",
    # Interaction interfaces
    "MemoryInterface",
    "StateInterface",
    # Lifecycle plugins
    "DefaultStateEvolutionPlugin",
    "LifecycleConfig",
    "LifecycleEvent",
    "LifecyclePlugins",
    "MemoryLifecycleManager",
    "MemoryLifecyclePlugin",
    "RetrievalPlugin",
    "StateEvolutionPhase",
    "StateEvolutionPlugin",
    "StateEvolutionRule",
    "TimeBasedLifecyclePlugin",
    # MCP tools
    "get_tool_by_name",
    "get_tool_definitions",
    "get_tool_names",
]
