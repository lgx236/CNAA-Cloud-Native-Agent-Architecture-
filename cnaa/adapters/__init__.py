"""CNAA Agent Framework Adapters."""

from cnaa.adapters.adapter_base import (
    BaseCNAAAdapter,
    CNAAMemoryMixin,
    MemoryType,
    StateCategory,
    MemoryConfig,
    StateConfig,
    PreferenceConfig,
)

# Import specific framework adapters (lazy loading)
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

__all__ = [
    "BaseCNAAAdapter",
    "CNAAMemoryMixin",
    "MemoryType",
    "StateCategory",
    "MemoryConfig",
    "StateConfig",
    "PreferenceConfig",
    # Framework-specific mixins
    "LangChainCNAAMixin",
    "LlamaIndexCNAAMixin",
    "AutoGencNAAAMixin",
    "CrewAICNAAAMixin",
]
