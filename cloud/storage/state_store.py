"""In-Memory State Store.

Reference implementation of state storage using in-memory dictionaries.
Stores State, Preference, and Environment objects.
"""

from typing import Any
from datetime import datetime
from cnaa.models import State, Preference, Environment
from cnaa.interaction import StateInterface


class InMemoryStateStore(StateInterface):
    """In-memory implementation of StateInterface.
    
    Stores states, preferences, and environments in dictionaries.
    """
    
    def __init__(self) -> None:
        """Initialize empty state store."""
        self._states: dict[tuple[str, str], State] = {}
        self._preferences: dict[tuple[str, str], Preference] = {}
        self._environments: dict[str, Environment] = {}
    
    # State operations
    
    def get_state(self, agent_id: str) -> list[State]:
        """Get all states for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of State objects
        """
        return [
            state for (aid, _), state in self._states.items()
            if aid == agent_id
        ]
    
    def update_state(self, agent_id: str, state: State) -> dict[str, Any]:
        """Create or update a state.
        
        Args:
            agent_id: Agent identifier
            state: State object to store
            
        Returns:
            Dict with status
        """
        key = (agent_id, state.state_id)
        self._states[key] = state
        return {"status": "ok"}
    
    def delete_state(self, agent_id: str, state_id: str) -> dict[str, Any]:
        """Delete a state.
        
        Args:
            agent_id: Agent identifier
            state_id: State identifier
            
        Returns:
            Dict with status
        """
        key = (agent_id, state_id)
        if key in self._states:
            del self._states[key]
        return {"status": "ok"}
    
    # Preference operations
    
    def get_preference(self, agent_id: str) -> list[Preference]:
        """Get all preferences for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of Preference objects
        """
        return [
            pref for (aid, _), pref in self._preferences.items()
            if aid == agent_id
        ]
    
    def update_preference(
        self, agent_id: str, preference: Preference
    ) -> dict[str, Any]:
        """Create or update a preference.
        
        Args:
            agent_id: Agent identifier
            preference: Preference object to store
            
        Returns:
            Dict with status
        """
        key = (agent_id, preference.preference_id)
        self._preferences[key] = preference
        return {"status": "ok"}
    
    def delete_preference(
        self, agent_id: str, preference_id: str
    ) -> dict[str, Any]:
        """Delete a preference.
        
        Args:
            agent_id: Agent identifier
            preference_id: Preference identifier
            
        Returns:
            Dict with status
        """
        key = (agent_id, preference_id)
        if key in self._preferences:
            del self._preferences[key]
        return {"status": "ok"}
    
    # Environment operations
    
    def get_environment(self, agent_id: str) -> Environment | None:
        """Get environment for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Environment object if found, None otherwise
        """
        return self._environments.get(agent_id)
    
    def update_environment(
        self, agent_id: str, environment: Environment
    ) -> dict[str, Any]:
        """Create or update environment.
        
        Args:
            agent_id: Agent identifier
            environment: Environment object to store
            
        Returns:
            Dict with status
        """
        self._environments[agent_id] = environment
        return {"status": "ok"}
    
    def clear(self) -> None:
        """Clear all states, preferences, and environments (for testing)."""
        self._states.clear()
        self._preferences.clear()
        self._environments.clear()
    
    def count_states(self) -> int:
        """Get total number of states (for testing).
        
        Returns:
            Number of states in store
        """
        return len(self._states)
    
    def count_preferences(self) -> int:
        """Get total number of preferences (for testing).
        
        Returns:
            Number of preferences in store
        """
        return len(self._preferences)
    
    def count_environments(self) -> int:
        """Get total number of environments (for testing).
        
        Returns:
            Number of environments in store
        """
        return len(self._environments)
