"""Cloud Storage Layer.

Provides storage implementations for CNAA cloud server.
Current implementations:
- memory_store: In-memory storage for memories
- state_store: In-memory storage for states

These can be replaced with persistent storage (SQLite, PostgreSQL, etc.)
"""

from cloud.storage.memory_store import InMemoryMemoryStore
from cloud.storage.state_store import InMemoryStateStore

__all__ = [
    "InMemoryMemoryStore",
    "InMemoryStateStore",
]
