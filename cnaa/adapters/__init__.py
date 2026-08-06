"""
CNAA Agent Framework Adapters Module.

This module provides a unified interface for integrating CNAA memory capabilities
with various agent frameworks through mixin patterns and base adapters.

Core Components:
    • BaseCNAAAdapter: Abstract base class defining the adapter contract
    • CNAAMemoryMixin: Utility mixin for common memory operations
    • Framework-specific Mixins: LangChain, LlamaIndex, AutoGen, CrewAI

Usage Example (LangChain):
    >>> from cnaa.adapters import LangChainCNAAMixin
    >>> 
    >>> class MyAgent(LangChainCNAAMixin, AgentExecutor):
    ...     agent_id = "my-agent"
    ...     def _call(self, inputs):
    ...         result = super()._call(inputs)
    ...         self.on_task_complete(self.agent_id, result)
    ...         return result

Usage Example (Custom Agent):
    >>> from cnaa.adapters import BaseCNAAAdapter
    >>> 
    >>> class CustomAgent(BaseCNAAAdapter):
    ...     def __init__(self):
    ...         super().__init__(server_url="http://localhost:8080")
    ...
    ...     def on_task_complete(self, agent_id, task_result):
    ...         self.store_memory(agent_id=agent_id, ...)
            
Architecture Overview:
    Layer 1: HTTP Client (local.client.mcp_client_real.CNAA_MCPClient)
    Layer 2: Adapter Base Class (BaseCNAAAdapter) - defines store_memory(), etc.
    Layer 3: Framework Mix-ins (LangChainCNAAMixin, etc.) - customize behavior
    
See docs/AGENT_ADAPTER_WORKING_PRINCIPLES.md for detailed architecture explanation.
"""

# ============================================================================
# Core Abstractions
# ============================================================================

from cnaa.adapters.adapter_base import (
    BaseCNAAAdapter,
    CNAAMemoryMixin,
    MemoryType,
    StateCategory,
    MemoryConfig,
    StateConfig,
    PreferenceConfig,
)

__all__ = [
    # Core abstractions
    "BaseCNAAAdapter",
    "CNAAMemoryMixin",
    "MemoryType",
    "StateCategory",
    "MemoryConfig",
    "StateConfig",
    "PreferenceConfig",
    # Framework-specific mixins (lazy-loaded)
    "LangChainCNAAMixin",
    "LlamaIndexCNAAMixin",
    "AutoGencNAAAMixin",
    "CrewAICNAAAMixin",
]

# ============================================================================
# Lazy Loading of Framework-Specific Adapters
# ============================================================================
# Framework adapters are imported on-demand to avoid hard dependencies.
# If a user doesn't have LangChain installed, they won't see import errors.
# 
# See pyproject.toml [options.extras_require] for framework requirements.
# ============================================================================

try:
    from cnaa.adapters.langchain_adapter import LangChainCNAAMixin
except ImportError:
    pass

try:
    from cnaa.adapters.llamaindex_adapter import LlamaIndexCNAAMixin
except ImportError:
    pass

try:
    from cnaa.adapters.autogen_adapter import AutoGencNAAAMixin
except ImportError:
    pass

try:
    from cnaa.adapters.crewai_adapter import CrewAICNAAAMixin
except ImportError:
    pass
