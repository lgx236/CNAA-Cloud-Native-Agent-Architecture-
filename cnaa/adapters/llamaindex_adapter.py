"""LlamaIndex integration for CNAA."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LlamaIndexCNAAMixin:
    """Mixin to add CNAA memory to LlamaIndex agents."""
    
    agent_id: str = "llamaindex-agent-001"
    
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
    
    def on_query_complete(
        self,
        query: str,
        response: Any,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Called when query processing completes.
        
        Args:
            query: Original query
            response: Response from LlamaIndex
            tags: Tags for categorization
        """
        if not hasattr(self, '_client') or not self._client:
            return
        
        content = {
            "query": query,
            "response": str(response),
        }
        
        try:
            from datetime import datetime
            from cnaa.adapters import MemoryType
            
            self.store_memory(
                agent_id=self.agent_id,
                memory_id=f"llama-query-{datetime.now().timestamp()}",
                memory_type=MemoryType.LONG_TERM,
                content=content,
                tags=tags or ["llamaindex"],
                completion_score=1.0,
            )
            
        except Exception as e:
            logger.error(f"Failed to store LlamaIndex query: {e}")
    
    def on_error(
        self,
        error: Exception | None = None,
    ) -> None:
        """Called when LlamaIndex encounters an error."""
        if error is None:
            return
        
        try:
            from datetime import datetime
            from cnaa.adapters import MemoryType
            
            self.store_memory(
                agent_id=self.agent_id,
                memory_id=f"llama-error-{datetime.now().timestamp()}",
                memory_type=MemoryType.SHORT_TERM,
                content={
                    "type": "error",
                    "error_message": str(error),
                    "error_type": type(error).__name__,
                },
                tags=["llamaindex", "error"],
                completion_score=0.0,
            )
        except Exception as e:
            logger.error(f"Failed to log error to CNAA: {e}")


# Example usage in comments:
"""
Example: LlamaIndex Chat Engine with CNAA

from llama_index.core import StorageContext, load_index_from_storage
from llama_index.llms import OpenAI
from llama_index.engines import FactoidEngine
from llama_index.agent import OpenAIAgent
from cnaa.adapters.llamaindex import LlamaIndexCNAAMixin

class CNAALlamaAgent(LlamaIndexCNAAMixin, OpenAIAgent):
    agent_id = "my-llama-agent"
    
    def chat(self, message: str, chat_history: list = None):
        response = super().chat(message)
        self.on_query_complete(query=message, response=response.response)
        return response
"""
