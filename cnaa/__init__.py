"""cnaa - Cloud Native Agent Architecture Core Package.

This is the main entry point for CNAA, providing a clean, simple API for:
- Memory management
- State persistence  
- Preference storage
- MCP tool integration
- Authentication & authorization

The package follows the principle of simplicity: intuitive names, 
minimal code, maximum clarity.
"""

# ============================================================================
# VERSION
# ============================================================================

__version__ = "1.0.0"
API_VERSION = "v1"
API_COMPATIBILITY_MATRIX = {
    "v1": {"status": "stable", "release_date": "2026-08"},
    "v0.2": {"status": "deprecated", "removal_date": "v1.2"}
}

# ============================================================================
# CORE DATA MODELS (Public API)
# ============================================================================

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

# ============================================================================
# SCHEMA DEFINITIONS (JSON Schema as Single Source of Truth)
# ============================================================================

from cnaa.schemas import (
    get_all_schemas,
    get_request_schemas,
    get_response_schemas,
    get_schema,
)

# ============================================================================
# INTERACTION INTERFACES (Abstract Base Classes)
# ============================================================================

from cnaa.interaction import MemoryInterface, StateInterface

# ============================================================================
# LIFECYCLE PLUGINS (Extensibility Points)
# ============================================================================

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

# ============================================================================
# MCP TOOL DEFINITIONS
# ============================================================================

from cnaa.tools import (
    get_tool_by_name,
    get_tool_definitions,
    get_tool_names,
)

# ============================================================================
# DEPRECATION MANAGEMENT
# ============================================================================

from cnaa.deprecation import (
    deprecated,
    get_deprecation_manager,
    is_deprecated,
    list_deprecated_items,
    mark_deprecated,
    warn_deprecated,
)

# ============================================================================
# AUTHENTICATION & SECURITY
# ============================================================================

from cnaa.security import (
    AuthConfig,
    AuthContext,
    PermissionLevel,
    load_auth_config_from_env,
    validate_api_key,
)

# ============================================================================
# PUBLIC API EXPORTS (What users actually need to know about)
# ============================================================================

__all__ = [
    # Version
    "__version__",
    "API_VERSION",
    "API_COMPATIBILITY_MATRIX",
    
    # Data Models
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
    
    # Schemas
    "get_all_schemas",
    "get_request_schemas",
    "get_response_schemas",
    "get_schema",
    
    # Interfaces
    "MemoryInterface",
    "StateInterface",
    
    # Lifecycle
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
    
    # Tools
    "get_tool_by_name",
    "get_tool_definitions",
    "get_tool_names",
    
    # Deprecation
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
