"""CrewAI integration for CNAA."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CrewAICNAAAMixin:
    """Mixin to add CNAA memory to CrewAI agents/tasks."""
    
    agent_id: str = "crewai-agent-001"
    
    def __init__(self, *args, **kwargs):
        """Initialize mixin with CNAA client."""
        super().__init__(*args, **kwargs)
        
        try:
            from cnaa.adapters.adapter_base import BaseCNAAAdapter
            BaseCNAAAdapter.__init__(
                self,
                cnaa_server_url="http://localhost:8080",
                api_key=None,
                timeout=30.0,
            )
        except ImportError:
            logger.warning("Cannot initialize CNAA client")
            pass
    
    def on_task_start(self, task_name: str) -> None:
        """Called when a crew task starts.
        
        Args:
            task_name: Name of the task
        """
        if not hasattr(self, '_client') or not self._client:
            return
        
        try:
            from datetime import datetime
            from cnaa.adapters import MemoryType
            
            content = {
                "type": "task_start",
                "task_name": task_name,
                "status": "started",
            }
            
            self.store_memory(
                agent_id=self.agent_id,
                memory_id=f"crewai-task-{datetime.now().timestamp()}",
                memory_type=MemoryType.SHORT_TERM,
                content=content,
                tags=["crewai", "task"],
                completion_score=0.0,
            )
            
        except Exception as e:
            logger.error(f"Failed to log CrewAI task start: {e}")
    
    def on_task_complete(
        self,
        result: str | Dict[str, Any],
        task_context: Dict[str, Any],
    ) -> None:
        """Called when crew task completes successfully.
        
        Args:
            result: Task result/output
            task_context: Context about the task
        """
        if not hasattr(self, '_client') or not self._client:
            return
        
        try:
            from datetime import datetime
            from cnaa.adapters import MemoryType
            
            content = {
                "type": "task_completion",
                "result": str(result),
                "context": task_context,
                "success": True,
            }
            
            self.store_memory(
                agent_id=self.agent_id,
                memory_id=f"crewai-done-{datetime.now().timestamp()}",
                memory_type=MemoryType.LONG_TERM,
                content=content,
                tags=["crewai", "completed"],
                completion_score=1.0,
            )
            
        except Exception as e:
            logger.error(f"Failed to store CrewAI task: {e}")
    
    def on_error(
        self,
        error: Exception,
        context: Dict[str, Any] | None = None,
    ) -> None:
        """Called when crew encounters an error.
        
        Args:
            error: Exception that occurred
            context: Error context information
        """
        if not hasattr(self, '_client') or not self._client:
            return
        
        try:
            from datetime import datetime
            from cnaa.adapters import MemoryType
            
            content = {
                "type": "error",
                "error_message": str(error),
                "error_type": type(error).__name__,
                "context": context or {},
            }
            
            self.store_memory(
                agent_id=self.agent_id,
                memory_id=f"crewai-error-{datetime.now().timestamp()}",
                memory_type=MemoryType.SHORT_TERM,
                content=content,
                tags=["crewai", "error"],
                completion_score=0.0,
            )
            
        except Exception as e:
            logger.error(f"Failed to log error to CNAA: {e}")


# Example usage in comments:
"""
Example: CrewAI Agent with CNAA

from crewai import Agent
from cnaa.adapters.crewai import CrewAICNAAAMixin

class CNAACrewAgent(CrewAICNAAAMixin, Agent):
    agent_id = "my-crewai-agent"
    
    def run(self, task_input: str):
        result = super().run(task_input)
        self.on_task_complete(result=result, task_context={"input": task_input})
        return result
"""
