"""LangChain integration for CNAA.

This module provides a mixin class that adds CNAA memory capabilities
to LangChain agents and tools.

Usage:
    from cnaa.adapters import BaseCNAAAdapter, MemoryType
    
    # Option 1: Use as mixin with LangChain agent
    class MyCNAALangChainAgent(BaseCNAAAdapter):
        agent_id = "my-langchain-agent"
        
        def _call(self, inputs):
            result = super()._call(inputs)
            self.on_task_complete(self.agent_id, result)
            return result
    
    # Option 2: Mix-in pattern
    from cnaa.adapters.langchain import LangChainCNAAMixin
    
    class MyLangChainAgent(LangChainCNAAMixin, SomeLangChainAgent):
        agent_id = "my-mixed-agent"
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LangChainCNAAMixin:
    """Mixin to add CNAA memory to LangChain agents/tools."""
    
    agent_id: str = "langchain-agent-001"
    
    def __init__(self, *args, **kwargs):
        """Initialize mixin with CNAA client."""
        super().__init__(*args, **kwargs)
        
        # Import base adapter if available
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
    
    def should_store_memory(self, result: Any) -> bool:
        """Determine if result should be stored in memory.
        
        Override this method for custom logic.
        
        Args:
            result: Agent execution result
            
        Returns:
            True if memory should be stored
        """
        # Default: store all successful results
        return result is not None and not isinstance(result, Exception)
    
    def on_task_complete(
        self,
        agent_id: str | None = None,
        task_result: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        completion_score: float = 1.0,
    ) -> None:
        """Called when agent task completes.
        
        Store the experience in CNAA cloud.
        
        Args:
            agent_id: Agent identifier (uses self.agent_id if not provided)
            task_result: Result of completed task
            tags: Tags for categorization
            completion_score: Completion score [0.0, 1.0]
        """
        if not hasattr(self, '_client') or not self._client:
            return
        
        agent_id = agent_id or self.agent_id
        
        if task_result is None:
            return
        
        content = {
            "task": getattr(self, 'last_query', 'Unknown task'),
            "result": str(task_result),
            "success": isinstance(task_result, dict) or 
                       (hasattr(task_result, '__str__') and not isinstance(task_result, Exception)),
        }
        
        try:
            from datetime import datetime
            from cnaa.adapters import MemoryType
            
            self.store_memory(
                agent_id=agent_id,
                memory_id=f"lc-task-{datetime.now().timestamp()}",
                memory_type=MemoryType.LONG_TERM,
                content=content,
                tags=tags or ["langchain"],
                completion_score=completion_score,
            )
            
            logger.debug(f"Stored LangChain task result for {agent_id}")
        except Exception as e:
            logger.error(f"Failed to store LangChain memory: {e}")
    
    def on_error(
        self,
        agent_id: str | None = None,
        error: Exception | None = None,
    ) -> None:
        """Called when agent encounters an error.
        
        Log error to CNAA for debugging.
        
        Args:
            agent_id: Agent identifier
            error: Exception that occurred
        """
        if error is None:
            return
        
        agent_id = agent_id or self.agent_id
        
        try:
            from datetime import datetime
            from cnaa.adapters import MemoryType
            
            self.store_memory(
                agent_id=agent_id,
                memory_id=f"lc-error-{datetime.now().timestamp()}",
                memory_type=MemoryType.SHORT_TERM,
                content={
                    "type": "error",
                    "error_message": str(error),
                    "error_type": type(error).__name__,
                    "traceback": getattr(error, '__traceback__', None),
                },
                tags=["langchain", "error"],
                completion_score=0.0,
            )
            
            logger.warning(f"Logged error to CNAA for {agent_id}: {error}")
        except Exception as e:
            logger.error(f"Failed to log error to CNAA: {e}")


# ============================================================================
# Integration Examples
# ============================================================================

def example_langchain_agent():
    """Example: LangChain agent with CNAA memory."""
    
    print("=" * 60)
    print("Example: LangChain + CNAA Integration")
    print("=" * 60)
    print()
    
    # This requires LangChain to be installed
    try:
        from langchain.agents import initialize_tools
        from langchain.agents import AgentExecutor, create_openai_functions_agent
        from langchain.chat_models import ChatOpenAI
        from langchain.prompts import PromptTemplate
        
        # Create base agent
        llm = ChatOpenAI(temperature=0)
        prompt_template = PromptTemplate(...)  # Your prompt
        
        # Add CNAA memory via mixin
        class CNAAEnabledAgent(LangChainCNAAMixin):
            agent_id = "cnaa-langchain-demo"
            
            def run(self, query: str) -> str:
                """Run agent and store result."""
                try:
                    result = self._run(query)
                    self.on_task_complete(
                        agent_id=self.agent_id,
                        task_result={"query": query, "result": result},
                        tags=["demo"]
                    )
                    return result
                except Exception as e:
                    self.on_error(agent_id=self.agent_id, error=e)
                    raise
        
        print("✅ LangChain agent with CNAA memory created successfully!")
        
    except ImportError:
        print("⚠️  LangChain not installed. Install with:")
        print("   pip install langchain openai")


if __name__ == "__main__":
    example_langchain_agent()
