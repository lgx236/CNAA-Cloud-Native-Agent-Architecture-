"""SQLite state store for CNAA.

Stores states, preferences, and environments in SQLite database.
Simple implementation: one file per all state categories.
"""

import sqlite3
import json
from typing import Any
from cloud.storage.state_store import StateInterface
from cnaa.models import State, Preference, Environment, StateCategory
from datetime import datetime


class SqliteStateStore(StateInterface):
    """SQLite-based state storage - single file persistence."""
    
    def __init__(self, db_path: str = "cnaa_states.db"):
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
    
    def _create_tables(self) -> None:
        """Create tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # States table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS states (
                state_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(agent_id, state_id)
            )
        """)
        
        # Preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                preference_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                importance REAL DEFAULT 0.0,
                updated_at TEXT NOT NULL,
                UNIQUE(agent_id, preference_id)
            )
        """)
        
        # Environment table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS environment (
                env_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                context TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(agent_id, env_id)
            )
        """)
        
        self.conn.commit()
    
    def get_state(self, agent_id: str) -> list[State]:
        """Get all states for an agent."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM states WHERE agent_id = ?
        """, (agent_id,))
        
        return [self._row_to_state(dict(row)) for row in cursor.fetchall()]
    
    def update_state(self, agent_id: str, state: State) -> dict[str, Any]:
        """Upsert a state."""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO states 
                (state_id, agent_id, category, content, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                state.state_id,
                agent_id,
                state.category.value,
                json.dumps(state.content),
                state.updated_at.isoformat(),
            ))
            
            self.conn.commit()
            return {"status": "ok"}
            
        except Exception as e:
            self.conn.rollback()
            return {"status": "error", "message": str(e)}
    
    def delete_state(self, agent_id: str, state_id: str) -> dict[str, Any]:
        """Delete a state."""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM states WHERE agent_id = ? AND state_id = ?",
            (agent_id, state_id)
        )
        self.conn.commit()
        
        return {"status": "ok"}
    
    def get_preference(self, agent_id: str) -> list[Preference]:
        """Get all preferences for an agent."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM preferences WHERE agent_id = ?
        """, (agent_id,))
        
        return [self._row_to_preference(dict(row)) for row in cursor.fetchall()]
    
    def update_preference(self, agent_id: str, preference: Preference) -> dict[str, Any]:
        """Upsert a preference."""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO preferences 
                (preference_id, agent_id, key, value, importance, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                preference.preference_id,
                agent_id,
                preference.key,
                json.dumps(preference.value),
                preference.importance or 0.0,
                datetime.now().isoformat(),
            ))
            
            self.conn.commit()
            return {"status": "ok"}
            
        except Exception as e:
            self.conn.rollback()
            return {"status": "error", "message": str(e)}
    
    def delete_preference(self, agent_id: str, preference_id: str) -> dict[str, Any]:
        """Delete a preference."""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM preferences WHERE agent_id = ? AND preference_id = ?",
            (agent_id, preference_id)
        )
        self.conn.commit()
        
        return {"status": "ok"}
    
    def get_environment(self, agent_id: str) -> Environment | None:
        """Get environment for an agent."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM environment WHERE agent_id = ?
        """, (agent_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return self._row_to_environment(dict(row))
    
    def update_environment(self, agent_id: str, environment: Environment) -> dict[str, Any]:
        """Upsert environment."""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO environment 
                (env_id, agent_id, context, updated_at)
                VALUES (?, ?, ?, ?)
            """, (
                environment.env_id,
                agent_id,
                json.dumps(environment.context),
                environment.updated_at.isoformat(),
            ))
            
            self.conn.commit()
            return {"status": "ok"}
            
        except Exception as e:
            self.conn.rollback()
            return {"status": "error", "message": str(e)}
    
    def _row_to_state(self, row: dict) -> State:
        """Convert DB row to State object."""
        return State(
            agent_id=row["agent_id"],
            state_id=row["state_id"],
            category=StateCategory(row["category"]),
            content=json.loads(row["content"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
    
    def _row_to_preference(self, row: dict) -> Preference:
        """Convert DB row to Preference object."""
        return Preference(
            agent_id=row["agent_id"],
            preference_id=row["preference_id"],
            key=row["key"],
            value=json.loads(row["value"]),
            importance=row["importance"] or 0.0,
        )
    
    def _row_to_environment(self, row: dict) -> Environment:
        """Convert DB row to Environment object."""
        return Environment(
            agent_id=row["agent_id"],
            env_id=row["env_id"],
            context=json.loads(row["context"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


if __name__ == "__main__":
    # Quick test
    store = SqliteStateStore(":memory:")
    
    # Test state
    state = State(
        agent_id="test-agent",
        state_id="test-state-1",
        category=StateCategory.KNOWLEDGE,
        content={"key": "value"},
    )
    
    result = store.update_state("test-agent", state)
    print(f"Updated state: {result}")
    
    states = store.get_state("test-agent")
    print(f"Got {len(states)} states")
