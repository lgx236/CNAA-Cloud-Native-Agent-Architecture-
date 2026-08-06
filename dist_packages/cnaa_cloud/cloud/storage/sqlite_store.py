"""SQLite Memory Store Implementation.

Production-ready storage backend for CNAA v0.2.

Features:
- ACID transaction support
- Connection pooling for performance
- Index optimization for fast queries
- Cross-platform (no external dependencies)

Algorithm responsibilities:
- IMPLEMENTED: SQLite CRUD, multi-filter query, pagination
- Time complexity: O(log n) with proper indexing
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from typing import Any, Optional

from cnaa.interaction import MemoryInterface
from cnaa.models import Memory, MemoryType, MemorySummary


class SQLiteMemoryStore(MemoryInterface):
    """Production-ready SQLite memory storage.
    
    Implements full MemoryInterface with persistent storage.
    Features:
    - Automatic schema creation
    - Thread-safe operations
    - Optimized indexes
    
    Usage:
        store = SQLiteMemoryStore(db_path="./data/cnaa.db")
        result = store.store_memory(memory)
    """
    
    def __init__(self, db_path: str = "./data/cnaa.db"):
        """Initialize SQLite store.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._local = threading.local()
        self._ensure_data_dir()
        self._init_schema()
    
    def _ensure_data_dir(self):
        """Create data directory if not exists."""
        import os
        import pathlib
        data_dir = pathlib.Path(self.db_path).parent
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection.
        
        Returns:
            SQLite connection object
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
        
        return self._local.connection
    
    def _init_schema(self):
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                memory_id TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                completion_score REAL DEFAULT 0.0,
                timestamp TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                UNIQUE(agent_id, memory_id)
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_type ON memories(agent_id, type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags ON memories(tags)")
        
        # Create index for scores
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_completion ON memories(completion_score DESC)")
        
        conn.commit()
    
    def store_memory(
        self, 
        memory: Memory, 
        auth_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Store a memory in SQLite database.
        
        Args:
            memory: Memory object to store
            auth_context: Optional authentication context
            
        Returns:
            Dict with status and memory_id
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO memories 
                (agent_id, memory_id, type, content, tags, completion_score, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.agent_id,
                memory.memory_id,
                memory.type.value,
                json.dumps(memory.content),
                json.dumps(memory.tags),
                memory.completion_score,
                memory.timestamp.isoformat(),
                json.dumps(memory.metadata) if memory.metadata else '{}'
            ))
            
            conn.commit()
            return {
                "status": "ok",
                "memory_id": memory.memory_id,
                "backend": "sqlite"
            }
        except sqlite3.IntegrityError as e:
            return {"status": "error", "message": f"Integrity error: {str(e)}"}
    
    def get_memory(
        self,
        agent_id: str,
        memory_id: str,
        auth_context: dict[str, Any] | None = None
    ) -> Optional[Memory]:
        """Retrieve a single memory by ID.
        
        Args:
            agent_id: Agent identifier
            memory_id: Memory identifier
            auth_context: Optional authentication context
            
        Returns:
            Memory object if found, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM memories 
            WHERE agent_id = ? AND memory_id = ?
        """, (agent_id, memory_id))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return self._row_to_memory(row)
    
    def list_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[list[str]] = None,
        auth_context: Optional[dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        reverse: bool = False,
    ) -> list[MemorySummary]:
        """List memories with optional filters.
        
        Args:
            agent_id: Agent identifier
            memory_type: Optional filter by type
            tags: Optional filter by tags
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum results to return
            reverse: Sort order (ascending/descending)
            
        Returns:
            List of MemorySummary objects
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM memories WHERE agent_id = ?"
        params = [agent_id]
        
        if memory_type:
            query += " AND type = ?"
            params.append(memory_type.value)
        
        if tags:
            tag_conditions = " OR ".join([f"tags LIKE ?" for _ in tags])
            query += f" AND ({tag_conditions})"
            params.extend([f"%{tag}%" for tag in tags])
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        order = "ASC" if reverse else "DESC"
        query += f" ORDER BY timestamp {order}"
        
        if limit:
            query += f" LIMIT {int(limit)}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [self._row_to_summary(row) for row in rows]
    
    def delete_memory(
        self,
        agent_id: str,
        memory_id: str,
        auth_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Delete a memory from the store.
        
        Args:
            agent_id: Agent identifier
            memory_id: Memory identifier
            auth_context: Optional authentication context
            
        Returns:
            Dict with status
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM memories WHERE agent_id = ? AND memory_id = ?",
            (agent_id, memory_id)
        )
        
        conn.commit()
        
        if cursor.rowcount > 0:
            return {"status": "deleted", "backend": "sqlite"}
        else:
            return {"status": "not_found", "backend": "sqlite"}
    
    def tag_short_term(
        self, 
        agent_id: str, 
        tags: list[str]
    ) -> dict[str, Any]:
        """Add tags to short-term memories.
        
        Args:
            agent_id: Agent identifier
            tags: Tags to add
            
        Returns:
            Dict with status and count
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        for tag in tags:
            cursor.execute("""
                UPDATE memories 
                SET tags = json_insert(
                    COALESCE(tags, '[]'),
                    '$.-' || ?
                )
                WHERE agent_id = ? AND type = 'short_term'
            """, (tag, agent_id))
        
        conn.commit()
        
        return {"status": "tagged", "count": len(tags)}
    
    def get_memory_scores(
        self,
        agent_id: str,
        access_counts: dict[str, int] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Get scored memories for an agent.
        
        Simple scoring implementation using recency only.
        Can be extended with more complex algorithms.
        
        Args:
            agent_id: Agent identifier
            access_counts: Access frequency counts
            context: Context for relevance scoring
            
        Returns:
            List of scored memory summaries
        """
        memories = self.list_memories(agent_id=agent_id)
        
        scored_results = []
        for summary in memories:
            score_data = self._calculate_simple_score(summary)
            scored_results.append(score_data)
        
        # Sort by composite score descending
        scored_results.sort(key=lambda x: x["composite_score"], reverse=True)
        
        return scored_results
    
    def _calculate_simple_score(self, summary: MemorySummary) -> dict[str, Any]:
        """Calculate simple recency-based score.
        
        Algorithm: Linear decay over 30 days
        Score = max(0, 1 - age_days / 30)
        
        Args:
            summary: Memory summary
            
        Returns:
            Dict with scores and original data
        """
        if summary.timestamp is None:
            age_days = 0
            recency_score = 1.0
        else:
            now = datetime.now()
            age_seconds = (now - summary.timestamp).total_seconds()
            age_days = age_seconds / 86400
            
            # Linear decay: 1.0 at day 0 → 0 at day 30
            recency_score = max(0.0, 1.0 - age_days / 30.0)
        
        # Composite score (only recency for simple algorithm)
        composite_score = recency_score
        
        return {
            "memory_id": summary.memory_id,
            "scores": {
                "recency": round(recency_score, 4),
                "completion": summary.completion_score,
                "importance": 0.0,
                "frequency": 0.0,
                "relevance": 0.0,
            },
            "composite_score": round(composite_score, 4),
            **summary.__dict__
        }
    
    def _row_to_memory(self, row: sqlite3.Row) -> Memory:
        """Convert SQLite row to Memory object."""
        return Memory(
            memory_id=row["memory_id"],
            agent_id=row["agent_id"],
            type=MemoryType(row["type"]),
            content=json.loads(row["content"]),
            tags=json.loads(row["tags"]) if row["tags"] else [],
            completion_score=row["completion_score"] or 0.0,
            timestamp=datetime.fromisoformat(row["timestamp"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
        )
    
    def _row_to_summary(self, row: sqlite3.Row) -> MemorySummary:
        """Convert SQLite row to MemorySummary object."""
        return MemorySummary(
            memory_id=row["memory_id"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            completion_score=row["completion_score"] or 0.0,
            timestamp=datetime.fromisoformat(row["timestamp"]) if row["timestamp"] else None
        )
    
    def close(self):
        """Close database connection."""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            self._local.connection = None
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()
