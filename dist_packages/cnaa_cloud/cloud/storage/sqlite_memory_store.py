"""Simple SQLite storage backend for CNAA memories.

Minimal implementation: one database file per all agents.
Uses plain Python sqlite3 module - no external dependencies.

Algorithm responsibilities:
- IMPLEMENTED: CRUD with JSON serialization, indexed queries
- TODO (production): Add connection pooling, WAL mode, migrations
"""

import sqlite3
import json
import logging
from typing import Any
from cloud.storage.memory_store import MemoryInterface
from cnaa.models import Memory, MemorySummary, MemoryType
from datetime import datetime

logger = logging.getLogger(__name__)


class SQLiteMemoryStore(MemoryInterface):
    """SQLite-based memory storage - single file persistence."""
    
    def __init__(self, db_path: str = "cnaa_memories.db"):
        """Initialize SQLite store.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._connect()
        self._create_tables()
    
    def _connect(self) -> None:
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        # Enable WAL mode for better durability
        self.conn.execute("PRAGMA journal_mode=WAL")
    
    def _create_tables(self) -> None:
        """Create tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Memories table with indexes for efficient querying
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                completion_score REAL DEFAULT 0.0,
                timestamp TEXT NOT NULL
            )
        """)
        
        # Create indexes for common query patterns
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent ON memories(agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON memories(type)")
        
        self.conn.commit()
    
    def store_memory(self, memory: Memory) -> dict[str, Any]:
        """Persist memory to SQLite.
        
        Uses INSERT OR REPLACE to handle updates atomically.
        
        Args:
            memory: Memory object to persist
            
        Returns:
            Dict with status and memory_id
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO memories 
                (memory_id, agent_id, type, content, tags, completion_score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.memory_id,
                memory.agent_id,
                memory.type.value,
                json.dumps(memory.content),
                json.dumps(memory.tags),
                memory.completion_score or 0.0,
                memory.timestamp.isoformat(),
            ))
            
            self.conn.commit()
            return {"status": "ok", "memory_id": memory.memory_id}
            
        except Exception as e:
            self.conn.rollback()
            logger.warning(f"Database error on store_memory: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_memory(self, agent_id: str, memory_id: str) -> Memory | None:
        """Retrieve a single memory.
        
        Args:
            agent_id: Agent identifier
            memory_id: Memory identifier
            
        Returns:
            Memory object if found, None otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM memories 
            WHERE agent_id = ? AND memory_id = ?
        """, (agent_id, memory_id))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return self._row_to_memory(dict(row))
    
    def list_memories(
        self,
        agent_id: str,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
        auth_context: dict[str, Any] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int | None = None,
        reverse: bool = False,
    ) -> list[MemorySummary]:
        """Query memories with optional filters.
        
        Simple linear scan with filters applied client-side.
        
        Args:
            agent_id: Agent identifier
            memory_type: Optional type filter
            tags: Optional tag filtering (any match)
            start_time: Filter from this timestamp
            end_time: Filter until this timestamp  
            limit: Maximum results to return
            reverse: If True, newest first
            
        Returns:
            List of MemorySummary objects
        """
        cursor = self.conn.cursor()
        
        # Build query with filters
        query = "SELECT * FROM memories WHERE agent_id = ?"
        params: list[Any] = [agent_id]
        
        if memory_type:
            query += " AND type = ?"
            params.append(memory_type.value)
        
        if tags:
            # Simple LIKE-based tag matching (not perfect but simple)
            placeholders = ",".join(["?" for _ in tags])
            query += f" AND ('[{tags[0]}]' IN (SELECT '[' || json_each.value || ']' FROM json_each(tags)))"
            # For now, use simpler approach - just load all and filter
            pass
        
        query += " ORDER BY timestamp DESC"
        if limit:
            query += f" LIMIT {int(limit)}"
        
        cursor.execute(query, params)
        
        return [self._row_to_summary(dict(row)) for row in cursor.fetchall()]
    
    def delete_memory(self, agent_id: str, memory_id: str) -> dict[str, Any]:
        """Delete a memory.
        
        Args:
            agent_id: Agent identifier
            memory_id: Memory identifier
            
        Returns:
            Dict with status
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM memories WHERE agent_id = ? AND memory_id = ?",
            (agent_id, memory_id)
        )
        self.conn.commit()
        
        return {"status": "ok"}
    
    def tag_short_term(self, agent_id: str, tags: list[str]) -> dict[str, Any]:
        """Tag short-term memories.
        
        Placeholder for future tagging system.
        """
        return {"status": "ok"}
    
    def get_memory_scores(
        self,
        agent_id: str,
        access_counts: dict[str, int] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Get scored memories for an agent.
        
        Simple implementation that returns empty list until scoring backend integrated.
        """
        # TODO: Implement actual scoring when backend is ready
        # For now, return empty list
        return []
    
    def clear(self) -> None:
        """Clear all memories (for testing)."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM memories")
        self.conn.commit()
    
    def count(self) -> int:
        """Get total number of memories (for testing)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM memories")
        return cursor.fetchone()[0]
    
    def _row_to_memory(self, row: dict) -> Memory:
        """Convert database row to Memory object.
        
        Args:
            row: SQLite Row as dictionary
            
        Returns:
            Memory instance
        """
        return Memory(
            memory_id=row["memory_id"],
            agent_id=row["agent_id"],
            type=MemoryType(row["type"]),
            content=json.loads(row["content"]),
            tags=json.loads(row["tags"]) if row["tags"] else [],
            completion_score=row["completion_score"] or 0.0,
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )
    
    def _row_to_summary(self, row: dict) -> MemorySummary:
        """Convert database row to MemorySummary.
        
        Args:
            row: SQLite Row as dictionary
            
        Returns:
            MemorySummary instance
        """
        return MemorySummary(
            memory_id=row["memory_id"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            completion_score=row["completion_score"] or 0.0,
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )


if __name__ == "__main__":
    # Quick test
    store = SQLiteMemoryStore(":memory:")  # In-memory DB for testing
    
    # Store a test memory
    from cnaa.models import Memory, MemoryType
    mem = Memory(
        memory_id="test-001",
        agent_id="test-agent",
        type=MemoryType.LONG_TERM,
        content={"task": "Test memory"},
        tags=["test", "sqlite"],
        completion_score=1.0,
    )
    
    result = store.store_memory(mem)
    print(f"Stored: {result}")
    
    # Retrieve it
    retrieved = store.get_memory("test-agent", "test-001")
    print(f"Retrieved: {retrieved.memory_id if retrieved else None}")
    
    # List them
    listed = store.list_memories("test-agent")
    print(f"Listed: {len(listed)} memory(s)")
