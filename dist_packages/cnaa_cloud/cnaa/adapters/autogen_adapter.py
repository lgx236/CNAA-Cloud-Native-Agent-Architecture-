"""AutoGen integration for CNAA."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AutoGencNAAAMixin:
    """Mixin to add CNAA memory to AutoGen agents/conversations."""
    
    agent_id: str = "autogen-agent-001"
    
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
    
    def on_message_received(
        self,
        sender: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Called when agent receives a message.
        
        Args:
            sender: Message sender identifier
            message: Message content
            metadata: Additional message metadata
        """
        # Optionally store conversation context
        pass
    
    def on_response_generated(
        self,
        response: str,
        task_context: str | None = None,
    ) -> None:
        """Called when agent generates a response.
        
        Args:
            response: Generated response
            task_context: Context of the task
        """
        if not hasattr(self, '_client') or not self._client:
            return
        
        try:
            from datetime import datetime
            from cnaa.adapters import MemoryType
            
            content = {
                "type": "conversation",
                "response": response,
                "context": task_context or "general_conversation",
            }
            
            self.store_memory(
                agent_id=self.agent_id,
                memory_id=f"autogen-msg-{datetime.now().timestamp()}",
                memory_type=MemoryType.LONG_TERM,
                content=content,
                tags=["autogen", "conversation"],
                completion_score=1.0,
            )
            
        except Exception as e:
            logger.error(f"Failed to store AutoGen message: {e}")
    
    def on_task_complete(
        self,
        result: Dict[str, Any],
        participants: List[str] | None = None,
    ) -> None:
        """Called when multi-agent task completes.
        
        Args:
            result: Final result
            participants: List of participant agent IDs
        """
        if not hasattr(self, '_client') or not self._client:
            return
        
        try:
            from datetime import datetime
            from cnaa.adapters import MemoryType
            
            content = {
                "type": "multi_agent_task",
                "result": result,
                "participants": participants or [],
            }
            
            self.store_memory(
                agent_id=self.agent_id,
                memory_id=f"autogen-task-{datetime.now().timestamp()}",
                memory_type=MemoryType.LONG_TERM,
                content=content,
                tags=["autogen", "task_completion"],
                completion_score=1.0,
            )
            
        except Exception as e:
            logger.error(f"Failed to store AutoGen task: {e}")


# Example usage in comments:
"""
Example: AutoGen ConversableAgent with CNAA

from autogen import ConversableAgent
from cnaa.adapters.autogen import AutoGencNAAAMixin

class CNAAAutoGenAgent(AutoGencNAAAMixin, ConversableAgent):
    agent_id = "my-autogen-agent"
    
    def generate_reply(self, messages, sender=None):
        reply = super().generate_reply(messages, sender)
        self.on_response_generated(response=reply)
        return reply
"""
