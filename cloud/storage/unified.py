"""Unified storage backend for CNAA.

Simplified storage implementation following simplicity, intuitiveness, and changeability principles.

Features:
- Single SQLite database for both memory AND state (simpler than two separate DBs)
- Easy to swap storage backends (just implement StorageInterface)
- Clear separation of concerns (storage vs scoring vs lifecycle)

Architecture:
┌─────────────────────────────────────┐
│          Cloud Server                │
│  ┌───────────────────────────────┐ │
│  │      UnifiedStorageBackend     │ │
│  │  - Memory Store Manager        │ │
│  │  - State Store Manager         │ │
│  │  - Common Database Abstraction │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
           │         │
           ▼         ▼
    ┌─────────┐ ┌─────────┐
    │  Memory │ │  State  │
    └─────────┘ └─────────┘

Usage:
    from cloud.storage import UnifiedStorageBackend
    
    db = UnifiedStorageBackend(db_path="data.db")
    
    # Work with memories
    mem1 = db.memory_store.store_memory(memory_obj)
    memories = list(db.memory_store.get_memories())
    
    # Work with states
    db.state_store.update_state(state_obj)
    states = list(db.state_store.get_states())
"""

import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple
from datetime import datetime
from abc import ABC, abstractmethod


class StorageInterface(ABC):
    """Abstract interface for all storage backends.
    
    This ensures we can easily swap implementations without changing code that uses them.
    """
    
    @abstractmethod
    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        """Save a single record."""
        pass
    
    @abstractmethod
    def find_all(self, **conditions) -> Iterator[dict[str, Any]]:
        """Find all records matching conditions."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Count total records."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all records."""
        pass


class InMemoryStorage(StorageInterface):
    """Simple in-memory storage for development/testing.
    
    This is intuitive because it behaves like a dictionary.
    It's simple because it has no external dependencies.
    Changeable because we can swap it out for any real database.
    """
    
    def __init__(self):
        self._data: Dict[str, Dict] = {}
    
    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        key = data.get('id') or data.get('memory_id') or data.get('state_id')
        if not key:
            raise ValueError("Data must have an id field")
        self._data[key] = data
        return {"status": "ok", "id": str(key)}
    
    def find_all(self, **conditions) -> Iterator[dict[str, Any]]:
        for record in self._data.values():
            matches = True
            for key, value in conditions.items():
                if record.get(key) != value:
                    matches = False
                    break
            if matches:
                yield record
    
    def count(self) -> int:
        return len(self._data)
    
    def clear(self) -> None:
        self._data.clear()


# ============================================================================
# Memory Management
# ============================================================================

class MemoryStore(StorageInterface):
    """Manages memory records in storage.
    
    Simple, intuitive API:
        store(memory) → Get saved memory
        get() → Iterate over all memories  
        delete(id) → Remove specific memory
        search(query) → Find matching memories
    """
    
    def __init__(self, storage: StorageInterface):
        self.storage = storage
    
    def store_memory(self, memory: dict[str, Any]) -> dict[str, Any]:
        """Store a new or updated memory."""
        # Ensure required fields
        memory.setdefault('timestamp', datetime.utcnow().isoformat())
        
        result = self.storage.save(memory)
        result['memory_id'] = memory.get('memory_id')
        return result
    
    def get_memories(self, 
                    agent_id: Optional[str] = None,
                    type_filter: Optional[str] = None,
                    limit: Optional[int] = None) -> Iterator[dict[str, Any]]:
        """Get memories with optional filtering.
        
        Args:
            agent_id: Filter by agent ID
            type_filter: Filter by memory type (preference/knowledge/experience)
            limit: Maximum number of results
        
        Returns:
            Iterator over matching memories
        """
        conditions = {}
        if agent_id:
            conditions['agent_id'] = agent_id
        if type_filter:
            conditions['type'] = type_filter
        
        results = list(self.storage.find_all(**conditions))
        
        if limit:
            results = results[:limit]
        
        return iter(results)
    
    def delete_memory(self, memory_id: str) -> dict[str, Any]:
        """Delete a specific memory by ID."""
        # For in-memory, we need special handling
        if hasattr(self.storage, '_data'):
            if memory_id in self.storage._data:
                del self.storage._data[memory_id]
                return {"status": "deleted", "memory_id": memory_id}
        
        return {"status": "not_found", "message": f"Memory {memory_id} not found"}
    
    def count(self) -> int:
        """Count total memories."""
        return self.storage.count()
    
    def clear(self) -> None:
        """Clear all memories."""
        self.storage.clear()


# ============================================================================
# State Management  
# ============================================================================

class StateStore(StorageInterface):
    """Manages state and preference records.
    
    Similar API to MemoryStore for consistency and intuition.
    """
    
    def __init__(self, storage: StorageInterface):
        self.storage = storage
    
    def update_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """Update or create a state."""
        state.setdefault('updated_at', datetime.utcnow().isoformat())
        
        result = self.storage.save(state)
        result['state_key'] = state.get('state_id') or state.get('key')
        return result
    
    def get_states(self,
                  agent_id: Optional[str] = None,
                  category: Optional[str] = None) -> Iterator[dict[str, Any]]:
        """Get states with optional filtering."""
        conditions = {}
        if agent_id:
            conditions['agent_id'] = agent_id
        if category:
            conditions['category'] = category
        
        return self.storage.find_all(**conditions)
    
    def update_preference(self, preference: dict[str, Any]) -> dict[str, Any]:
        """Update preferences as a special type of state."""
        preference['category'] = 'preferences'
        return self.update_state(preference)
    
    def get_preferences(self, agent_id: str) -> Iterator[dict[str, Any]]:
        """Get all preferences for an agent."""
        return self.get_states(agent_id=agent_id, category='preferences')
    
    def count(self) -> int:
        return self.storage.count()
    
    def clear(self) -> None:
        self.storage.clear()


# ============================================================================
# Factory & Configuration
# ============================================================================

def create_storage_backend(storage_type: str = "in_memory", 
                          db_path: Optional[str] = None) -> StorageInterface:
    """Factory function to create appropriate storage backend.
    
    Parameters:
        storage_type: Type of storage ('in_memory' or 'sqlite')
        db_path: Path to SQLite database (required for 'sqlite')
    
    Returns:
        Appropriate StorageInterface implementation
    
    Usage:
        # Quick start with in-memory (good for testing)
        backend = create_storage_backend("in_memory")
        
        # Production with SQLite
        backend = create_storage_backend("sqlite", db_path="./data.db")
    """
    if storage_type == "in_memory":
        return InMemoryStorage()
    elif storage_type == "sqlite":
        if not db_path:
            raise ValueError("db_path required for SQLite storage")
        return SQLiteStorage(db_path)
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")


class SQLiteStorage(StorageInterface):
    """SQLite-backed storage implementation.
    
    Simpler than having separate files for memory and state.
    One database, one schema, one connection pool.
    """
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._connect()
    
    def _connect(self) -> None:
        """Establish database connection."""
        # Create directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self) -> None:
        """Create unified schema for both memory and state."""
        cursor = self.conn.cursor()
        
        # Unified data table for flexibility
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_items (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                item_type TEXT NOT NULL,  -- 'memory' or 'state'
                content TEXT NOT NULL,    -- JSON blob
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(agent_id, item_type, id)
            )
        """)
        
        # Index for fast queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_type ON data_items(agent_id, item_type)
        """)
        
        self.conn.commit()
    
    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        """Save record to database."""
        cursor = self.conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO data_items 
                (id, agent_id, item_type, content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data.get('id') or data.get('memory_id') or data.get('state_id'),
                data.get('agent_id', 'unknown'),
                data.get('item_type', 'memory'),
                json.dumps(data, ensure_ascii=False),
                data.get('created_at', now),
                data.get('updated_at', now)
            ))
            self.conn.commit()
            
            return {"status": "ok", "id": data.get('id')}
            
        except Exception as e:
            self.conn.rollback()
            return {"status": "error", "message": str(e)}
    
    def find_all(self, **conditions) -> Iterator[dict[str, Any]]:
        """Query records with flexible conditions."""
        cursor = self.conn.cursor()
        
        # Build query dynamically based on conditions
        where_clauses = []
        params = []
        
        for key, value in conditions.items():
            where_clauses.append(f"{key} = ?")
            params.append(value)
        
        query = f"SELECT * FROM data_items"
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        cursor.execute(query, params)
        
        for row in cursor.fetchall():
            data = json.loads(row['content'])
            data['id'] = row['id']
            data['agent_id'] = row['agent_id']
            data['item_type'] = row['item_type']
            data['created_at'] = row['created_at']
            data['updated_at'] = row['updated_at']
            yield data
    
    def count(self) -> int:
        """Total record count."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM data_items")
        return cursor.fetchone()[0]
    
    def clear(self) -> None:
        """Delete all records."""
        self.conn.execute("DELETE FROM data_items")
        self.conn.commit()
    
    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
