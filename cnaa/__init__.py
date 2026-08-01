"""CNAA - Cloud Native Agentic Architecture.

Experience Runtime Framework for AI Agents.
Core specification: data models, interaction interfaces,
MCP tool definitions, and lifecycle rules.

This package IS the architecture specification.
Cloud/ and local/ are reference implementations.
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
    State,
    StateCategory,
    TaskCheckpoint,
)

# Interaction interfaces
from cnaa.interaction import MemoryInterface, StateInterface

# Lifecycle management
from cnaa.lifecycle import (
    LifecycleConfig,
    LifecycleEvent,
    MemoryLifecycleManager,
    StateEvolutionPhase,
    StateEvolutionRule,
)

# MCP tool definitions
from cnaa.tools import get_tool_definitions, get_tool_names

__all__ = [
    # Data models
    "Environment",
    "InstantMemory",
    "Memory",
    "MemoryStatus",
    "MemoryType",
    "Preference",
    "State",
    "StateCategory",
    "TaskCheckpoint",
    # Interaction interfaces
    "MemoryInterface",
    "StateInterface",
    # Lifecycle
    "LifecycleConfig",
    "LifecycleEvent",
    "MemoryLifecycleManager",
    "StateEvolutionPhase",
    "StateEvolutionRule",
    # Tools
    "get_tool_definitions",
    "get_tool_names",
]
