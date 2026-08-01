"""State Cache.

Caches state, preference, and environment data from cloud for local access.
Reduces network calls and provides faster access to frequently used data.

Algorithm responsibilities:
- IMPLEMENTED: TTL-based cache invalidation, dict-based storage
- TODO (production): LRU cache, size limits, persistent cache
- TODO (algorithm): Smart prefetching, relevance-based caching
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from cnaa.models import Environment, Preference, State


class StateCache:
    """Cache for state data from cloud.
    
    Caches State, Preference, and Environment objects locally
    to reduce network calls and improve access speed.
    
    Example:
        ```python
        cache = StateCache(agent_id="agent-001", ttl_minutes=5)
        
        # Cache states from cloud response
        cache.update_states(states_list)
        
        # Get cached states
        states = cache.get_states()
        
        # Check if cache is expired
        if cache.is_expired():
            # Fetch from cloud and update cache
            pass
        ```
    """
    
    def __init__(
        self,
        agent_id: str,
        ttl_minutes: float = 5.0,
    ) -> None:
        """Initialize the state cache.
        
        IMPLEMENTED:
            Creates cache with separate loaded flags for each data type.
            Each type (states, preferences, environment) tracks its own
            freshness independently.
        
        TODO (algorithm extension point):
            - Support per-item TTL (states may expire differently than preferences)
            - Support stale-while-revalidate pattern
            - Support usage-based invalidation (keep hot items longer)
        
        Args:
            agent_id: Agent identifier
            ttl_minutes: Time-to-live for cache in minutes
        """
        self.agent_id = agent_id
        self.ttl = timedelta(minutes=ttl_minutes)
        
        self._states: list[State] = []
        self._preferences: list[Preference] = []
        self._environment: Environment | None = None
        
        # Track each data type's freshness separately
        self._states_loaded: bool = False
        self._preferences_loaded: bool = False
        self._environment_loaded: bool = False
        self._last_updated: datetime | None = None
    
    def update_states(self, states: list[State]) -> None:
        """Update cached states.
        
        IMPLEMENTED:
            Stores states and marks states as loaded.
            Updates global timestamp for backward compatibility.
        
        Args:
            states: List of State objects from cloud
        """
        self._states = states
        self._states_loaded = True
        self._last_updated = datetime.now()
    
    def update_preferences(self, preferences: list[Preference]) -> None:
        """Update cached preferences.
        
        IMPLEMENTED:
            Stores preferences and marks preferences as loaded.
            Updates global timestamp for backward compatibility.
        
        Args:
            preferences: List of Preference objects from cloud
        """
        self._preferences = preferences
        self._preferences_loaded = True
        self._last_updated = datetime.now()
    
    def update_environment(self, environment: Environment | None) -> None:
        """Update cached environment.
        
        IMPLEMENTED:
            Stores environment and marks environment as loaded.
            Updates global timestamp for backward compatibility.
        
        Args:
            environment: Environment object from cloud
        """
        self._environment = environment
        self._environment_loaded = True
        self._last_updated = datetime.now()
    
    def get_states(self) -> list[State]:
        """Get cached states.
        
        Returns:
            List of cached State objects
        """
        return self._states
    
    def get_preferences(self) -> list[Preference]:
        """Get cached preferences.
        
        Returns:
            List of cached Preference objects
        """
        return self._preferences
    
    def get_environment(self) -> Environment | None:
        """Get cached environment.
        
        Returns:
            Cached Environment object or None
        """
        return self._environment
    
    def is_expired(self) -> bool:
        """Check if cache has expired.
        
        IMPLEMENTED:
            Simple TTL check: if (now - last_updated) > ttl, expired.
            Returns True if never updated.
            Time complexity: O(1).
        
        TODO (algorithm extension point):
            - Support per-item TTL (states may expire differently than preferences)
            - Support stale-while-revalidate pattern
            - Support usage-based invalidation (keep hot items longer)
        
        Returns:
            True if cache is expired or never updated
        """
        if self._last_updated is None:
            return True
        
        return datetime.now() - self._last_updated > self.ttl
    
    def is_states_expired(self) -> bool:
        """Check if states cache has expired.
        
        IMPLEMENTED:
            Returns True if states have never been loaded or TTL expired.
        
        Returns:
            True if states cache is expired
        """
        if not self._states_loaded:
            return True
        return self.is_expired()
    
    def is_preferences_expired(self) -> bool:
        """Check if preferences cache has expired.
        
        IMPLEMENTED:
            Returns True if preferences have never been loaded or TTL expired.
        
        Returns:
            True if preferences cache is expired
        """
        if not self._preferences_loaded:
            return True
        return self.is_expired()
    
    def is_environment_expired(self) -> bool:
        """Check if environment cache has expired.
        
        IMPLEMENTED:
            Returns True if environment has never been loaded or TTL expired.
        
        Returns:
            True if environment cache is expired
        """
        if not self._environment_loaded:
            return True
        return self.is_expired()
    
    def clear(self) -> None:
        """Clear all cached data.
        
        IMPLEMENTED:
            Resets all data and loaded flags.
        """
        self._states = []
        self._preferences = []
        self._environment = None
        self._states_loaded = False
        self._preferences_loaded = False
        self._environment_loaded = False
        self._last_updated = None
    
    def get_state_by_id(self, state_id: str) -> State | None:
        """Get a specific state by ID.
        
        Args:
            state_id: State identifier
            
        Returns:
            State object if found, None otherwise
        """
        for state in self._states:
            if state.state_id == state_id:
                return state
        return None
    
    def get_preference_by_id(self, preference_id: str) -> Preference | None:
        """Get a specific preference by ID.
        
        Args:
            preference_id: Preference identifier
            
        Returns:
            Preference object if found, None otherwise
        """
        for pref in self._preferences:
            if pref.preference_id == preference_id:
                return pref
        return None
    
    def get_states_by_category(self, category: str) -> list[State]:
        """Get states filtered by category.
        
        Args:
            category: State category ("preference", "knowledge", or "environment")
            
        Returns:
            List of State objects matching the category
        """
        return [
            state for state in self._states
            if state.category.value == category
        ]
    
    def count(self) -> dict[str, int]:
        """Get count of cached items.
        
        Returns:
            Dict with counts of states, preferences, and environment
        """
        return {
            "states": len(self._states),
            "preferences": len(self._preferences),
            "environment": 1 if self._environment else 0,
        }
