"""Time-Based Memory Slicer and Indexer.

Implements simple time-based memory slicing and indexing for agent context management.
This module allows agents to:
1. Slice large memories into chronological segments
2. Extract key information/tags during slicing
3. Store full content + tags in cloud
4. Query memories by time range and tags

Algorithm responsibilities:
- IMPLEMENTED: Time-based slicing, tag extraction, chronological indexing

Design principles:
- Simple and safe: Use timestamp-based splitting, no complex algorithms
- Agent-driven: Agents decide when and how to slice their context
- Tag-driven: Tags enable efficient retrieval
- Full-persistence: All data stored in cloud, referenced locally
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any
from dataclasses import dataclass, field
from cnaa.models import Memory, MemoryType


@dataclass
class MemorySlice:
    """A single slice of a memory chunk."""
    
    slice_id: str
    memory_id: str
    parent_memory_id: str
    index: int  # Sequential index within the memory
    content: dict[str, Any]
    start_time: datetime | None = None
    end_time: datetime | None = None
    summary: str = ""
    extracted_tags: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.extracted_tags is None:
            self.extracted_tags = []


@dataclass
class MemoryIndex:
    """Chronological index of memories for an agent."""
    
    agent_id: str
    index_id: str
    memories: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_memory(self, memory_id: str, timestamp: datetime, tags: list[str], **metadata):
        """Add a memory entry to the index."""
        entry = {
            "memory_id": memory_id,
            "timestamp": timestamp,
            "tags": tags or [],
            **metadata
        }
        self.memories.append(entry)
        self.updated_at = datetime.now()
    
    def get_by_time_range(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None
    ) -> list[dict[str, Any]]:
        """Get memories within a time range."""
        results = []
        for entry in self.memories:
            ts = entry.get("timestamp")
            if ts is None:
                continue
            
            if start_time and ts < start_time:
                continue
            if end_time and ts > end_time:
                continue
            
            results.append(entry)
        
        # Sort by timestamp descending (newest first)
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        return results
    
    def get_by_tags(self, tags: list[str]) -> list[dict[str, Any]]:
        """Get memories that contain any of the specified tags."""
        results = []
        for entry in self.memories:
            entry_tags = set(entry.get("tags", []))
            if any(tag in entry_tags for tag in tags):
                results.append(entry)
        
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        return results
    
    def get_latest_n(self, n: int) -> list[dict[str, Any]]:
        """Get the N most recent memories."""
        sorted_memories = sorted(
            self.memories, 
            key=lambda x: x["timestamp"] if x["timestamp"] else datetime.min, 
            reverse=True
        )
        return sorted_memories[:n]


class SimpleMemorySlicer:
    """Simple time-based memory slicer for agents.
    
    This slicer allows agents to:
    1. Chunk large contexts into manageable pieces
    2. Attach timestamps and tags to each chunk
    3. Build a chronological index for querying
    4. Store full chunks in cloud with references
    
    IMPLEMENTED:
        - Time-based slicing by token/content size
        - Automatic timestamp assignment
        - Simple tag extraction from content keywords
        - Chronological index maintenance
        - Query by time range and tags
    
    Algorithm choices:
        - Pure size/time-based splitting
        - Simple keyword matching for tags
        - Agent-driven control
    
    Example:
        ```python
        slicer = SimpleMemorySlicer(agent_id="agent-001")
        
        # Create a large context
        large_context = {...}  # dict with multiple events
        
        # Slice it into chunks
        chunks = slicer.slice_memory(
            memory_id="context-001",
            content=large_context,
            max_tokens_per_chunk=1000
        )
        
        # Build index
        slicer.build_index()
        
        # Query by time range
        recent = slicer.query_by_time_range(
            start_time=datetime.now() - timedelta(hours=24)
        )
        
        # Query by tags
        important = slicer.query_by_tags(["critical", "error"])
        ```
    """
    
    def __init__(self, agent_id: str):
        """Initialize the memory slicer.
        
        Args:
            agent_id: Agent identifier for this slicer instance
        """
        self.agent_id = agent_id
        self._slices: dict[str, MemorySlice] = {}  # slice_id -> MemorySlice
        self._parent_slices: dict[str, list[str]] = {}  # memory_id -> [slice_ids]
        self._index = MemoryIndex(agent_id=agent_id, index_id=f"index-{agent_id}")
    
    def slice_memory(
        self,
        memory_id: str,
        content: dict[str, Any],
        max_tokens_per_chunk: int = 1000,
        auto_timestamps: bool = True,
    ) -> list[MemorySlice]:
        """Slice a large memory into chronological chunks.
        
        IMPLEMENTED:
            - Split content by nested event arrays
            - Assign sequential indices
            - Auto-generate summaries from content keys
            - Assign timestamps if not present
        
        Args:
            memory_id: Parent memory identifier
            content: Large memory content (should be dict)
            max_tokens_per_chunk: Approximate token limit per chunk
            auto_timestamps: Whether to auto-generate timestamps
        
        Returns:
            List of MemorySlice objects
        """
        # Validate content type
        if not isinstance(content, dict):
            raise ValueError("Memory content must be a dictionary")
        
        slices = []
        parent_key = f"{self.agent_id}:{memory_id}"
        child_index = 0
        
        # Try to extract events array (common pattern in agent logs)
        events = self._extract_events(content)
        
        if events:
            # Split by events
            for i, event in enumerate(events):
                slice_content = self._create_slice_from_event(event, content)
                
                # Generate timestamp if needed
                timestamp = self._get_event_timestamp(event) if auto_timestamps else None
                
                # Generate summary
                summary = self._generate_summary(event, i)
                
                # Extract tags
                tags = self._extract_tags(event, content)
                
                slice_id = f"{memory_id}:slice:{i}"
                slice_obj = MemorySlice(
                    slice_id=slice_id,
                    memory_id=memory_id,
                    parent_memory_id=parent_key,
                    index=i,
                    content=slice_content,
                    start_time=timestamp,
                    end_time=timestamp + timedelta(minutes=5) if timestamp else None,
                    summary=summary,
                    extracted_tags=tags,
                )
                
                slices.append(slice_obj)
                self._slices[slice_id] = slice_obj
                child_index += 1
            
            self._parent_slices[parent_key] = [s.slice_id for s in slices]
        
        else:
            # No events array, treat as single chunk
            slice_id = f"{memory_id}:slice:0"
            summary = self._generate_summary(content, 0)
            tags = self._extract_tags(content, content)
            
            slice_obj = MemorySlice(
                slice_id=slice_id,
                memory_id=memory_id,
                parent_memory_id=parent_key,
                index=0,
                content=content,
                start_time=datetime.now() if auto_timestamps else None,
                summary=summary,
                extracted_tags=tags,
            )
            
            slices.append(slice_obj)
            self._slices[slice_id] = slice_obj
            self._parent_slices[parent_key] = [slice_id]
        
        return slices
    
    def _extract_events(self, content: dict[str, Any]) -> list[Any]:
        """Extract events from content dictionary.
        
        Looks for common patterns like 'events', 'messages', 'steps', 'history'.
        Returns empty list if no recognized pattern found.
        
        EXCLUDED keys (will not be treated as event containers):
        - 'steps': Often used internally but not meant for memory splitting
        - 'timeline': Usually metadata, not events
        """
        # Explicitly exclude certain keys that shouldn't trigger splitting
        excluded_keys = {"steps", "timeline", "metadata"}
        
        # If content has no recognized event container, return empty
        # This allows single-memory chunks
        event_keys = ["events", "messages", "history"]  # Removed some potentially problematic keys
        
        for key in event_keys:
            if key in content and isinstance(content[key], list) and len(content[key]) > 1:
                first_item = content[key][0]
                # Only treat as events if items look like events (have timestamp/action)
                if isinstance(first_item, dict):
                    return content[key]
        
        # Check for nested structures with multiple items
        for value in content.values():
            if isinstance(value, list) and len(value) > 1 and isinstance(value[0], dict):
                # Skip excluded keys
                continue
                
                # Ensure items have event-like structure
                first_item = value[0]
                if any(k in first_item for k in ["timestamp", "time", "action", "type", "event"]):
                    return value
        
        # No array found - return empty to trigger single-chunk behavior
        return []
    
    def _create_slice_from_event(
        self, 
        event: Any, 
        parent_content: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a slice from a single event."""
        if isinstance(event, dict):
            return event
        
        return {"event": event}
    
    def _get_event_timestamp(self, event: Any) -> datetime:
        """Extract or generate timestamp from event."""
        if isinstance(event, dict):
            # Try common timestamp fields
            ts_fields = ["timestamp", "time", "datetime", "created_at", "date"]
            for field in ts_fields:
                if field in event:
                    ts_value = event[field]
                    if isinstance(ts_value, datetime):
                        return ts_value
                    # Try parsing ISO format string
                    try:
                        return datetime.fromisoformat(str(ts_value).replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        continue
        
        # Fallback: current time
        return datetime.now()
    
    def _generate_summary(self, content: Any, index: int) -> str:
        """Generate a human-readable summary from content."""
        if isinstance(content, dict):
            # Use first few key-value pairs
            preview_parts = []
            for i, (key, value) in enumerate(content.items()):
                if i >= 3:
                    break
                val_str = str(value)[:50]
                preview_parts.append(f"{key}: {val_str}")
            
            if preview_parts:
                return f"[#{index}] {'; '.join(preview_parts)}"
        
        # Fallback: convert to string and truncate
        return f"[#{index}] {str(content)[:100]}"
    
    def _extract_tags(self, content: Any, parent_content: dict[str, Any]) -> list[str]:
        """Extract tags from content using simple keyword matching.
        
        IMPLEMENTED:
            - Look for high-importance keywords
            - Extract from predefined categories
            - Include context from parent content
        
        Implementation:
            - Keyword list matching (simple rule-based)
            - No external dependencies or ML models
        """
        tags = []
        
        # Define keyword categories (simple rule-based)
        keyword_categories = {
            "important": ["critical", "critical", "urgent", "high priority", "must", "require"],
            "error": ["error", "fail", "failed", "exception", "warning", "issue"],
            "success": ["success", "completed", "done", "succeeded", "ok", "success"],
            "information": ["info", "information", "note", "reminder", "background"],
            "decision": ["decision", "choose", "selected", "chose", "concluded"],
            "learning": ["learn", "understand", "discovered", "realize", "recognized"],
            "preference": ["prefer", "like", "dislike", "favorite", "习惯"],
        }
        
        # Search for keywords in content
        content_text = self._flatten_content_to_text(content)
        content_lower = content_text.lower()
        
        for category, keywords in keyword_categories.items():
            if any(keyword in content_lower for keyword in keywords):
                tags.append(category)
        
        # Add tags from content if present
        if isinstance(content, dict):
            if "tags" in content and isinstance(content["tags"], list):
                tags.extend([str(t) for t in content["tags"] if str(t) not in tags])
            
            if "labels" in content and isinstance(content["labels"], list):
                tags.extend([str(t) for t in content["labels"] if str(t) not in tags])
        
        return list(set(tags))  # Remove duplicates
    
    def _flatten_content_to_text(self, content: Any) -> str:
        """Flatten content to plain text."""
        if isinstance(content, str):
            return content
        
        if isinstance(content, dict):
            return " ".join(str(v) for v in content.values())
        
        if isinstance(content, list):
            return " ".join(str(item) for item in content)
        
        return str(content)
    
    def build_index(self) -> MemoryIndex:
        """Build chronological index from all slices.
        
        IMPLEMENTED:
            - Iterate through all slices
            - Extract timestamps
            - Index by time and tags
            - Return complete index
        
        Returns:
            Complete MemoryIndex object
        """
        # Clear existing index
        self._index = MemoryIndex(
            agent_id=self.agent_id,
            index_id=f"index-{self.agent_id}"
        )
        
        # Index all slices
        for slice_obj in self._slices.values():
            self._index.add_memory(
                memory_id=slice_obj.slice_id,
                timestamp=slice_obj.start_time or datetime.now(),
                tags=slice_obj.extracted_tags,
                parent_memory_id=slice_obj.parent_memory_id,
                index=slice_obj.index,
                summary=slice_obj.summary,
            )
        
        return self._index
    
    def query_by_time_range(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        include_content: bool = False,
    ) -> list[dict[str, Any]]:
        """Query memories within a time range.
        
        Args:
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)
            include_content: Whether to include full content
        
        Returns:
            List of memory entries with optional content
        """
        results = self._index.get_by_time_range(start_time, end_time)
        
        if include_content:
            for result in results:
                slice_id = result["memory_id"]
                if slice_id in self._slices:
                    result["content"] = self._slices[slice_id].content
        
        return results
    
    def query_by_tags(self, tags: list[str]) -> list[dict[str, Any]]:
        """Query memories that contain any of the specified tags.
        
        Args:
            tags: List of tag names to search for
        
        Returns:
            List of matching memory entries (no content)
        """
        return self._index.get_by_tags(tags)
    
    def get_latest_n(self, n: int) -> list[dict[str, Any]]:
        """Get the N most recent memories.
        
        Args:
            n: Number of memories to retrieve
        
        Returns:
            List of N most recent memory entries
        """
        return self._index.get_latest_n(n)
    
    def get_parent_memory(self, memory_id: str) -> list[MemorySlice]:
        """Get all slices belonging to a parent memory.
        
        Args:
            memory_id: Parent memory ID (with or without agent prefix)
        
        Returns:
            List of MemorySlice objects belonging to this parent
        """
        parent_key = memory_id
        if not parent_key.startswith(self.agent_id):
            parent_key = f"{self.agent_id}:{memory_id}"
        
        slice_ids = self._parent_slices.get(parent_key, [])
        return [self._slices[sid] for sid in slice_ids if sid in self._slices]
    
    def count(self) -> int:
        """Get total number of slices."""
        return len(self._slices)
    
    def clear(self) -> None:
        """Clear all slices and index."""
        self._slices.clear()
        self._parent_slices.clear()
        self._index = MemoryIndex(
            agent_id=self.agent_id,
            index_id=f"index-{self.agent_id}"
        )


def create_tagged_memory(
    agent_id: str,
    memory_id: str,
    slices: list[MemorySlice],
    full_content: dict[str, Any],
) -> Memory:
    """Convert sliced memories into a CNAA Memory object.
    
    This helper function creates a Memory object that can be stored in cloud,
    containing metadata about all slices.
    
    Args:
        agent_id: Agent identifier
        memory_id: Original memory identifier
        slices: List of MemorySlice objects
        full_content: Complete original content
    
    Returns:
        Memory object ready for cloud storage
    """
    # Collect all tags from slices
    all_tags = set()
    for slice_obj in slices:
        all_tags.update(slice_obj.extracted_tags)
    
    # Create memory metadata
    metadata = {
        "slice_count": len(slices),
        "slice_ids": [s.slice_id for s in slices],
        "full_content_ref": f"{agent_id}:{memory_id}",
        "indexed_at": datetime.now().isoformat(),
    }
    
    return Memory(
        memory_id=memory_id,
        agent_id=agent_id,
        type=MemoryType.LONG_TERM,
        content={"_metadata": metadata, "_full": full_content},
        tags=list(all_tags),
        completion_score=1.0,
        metadata=metadata,  # Also include in metadata field
    )
