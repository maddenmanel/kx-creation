"""
Base Agent Class for KX System
Using AgentScope framework with Qwen model support
"""
from typing import Optional, Dict, Any
from agentscope.agent import AgentBase
from agentscope.message import Msg
from loguru import logger


class KXBaseAgent(AgentBase):
    """
    Base agent class for KX system
    Provides common functionality for all agents using AgentScope framework
    """
    
    def __init__(
        self,
        name: str,
        sys_prompt: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize base agent
        
        Args:
            name: Agent name
            sys_prompt: System prompt for the agent
            **kwargs: Additional arguments
        """
        super().__init__()
        self.name = name
        self.sys_prompt = sys_prompt
        self._kwargs = kwargs
        logger.info(f"Initialized {self.__class__.__name__}: {name}")
    
    def reply(self, x: Optional[Msg] = None) -> Msg:
        """
        Generate reply based on input message
        Must be implemented by subclasses
        
        Args:
            x: Input message
            
        Returns:
            Reply message
        """
        raise NotImplementedError("Subclasses must implement reply method")
    
    def _create_message(
        self,
        content: Any,
        role: str = "assistant",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Msg:
        """
        Create a formatted message
        
        Args:
            content: Message content
            role: Message role (user/assistant/system)
            metadata: Additional metadata
            
        Returns:
            Formatted message
        """
        return Msg(
            name=self.name,
            content=content,
            role=role,
            metadata=metadata or {}
        )
    
    def _log_error(self, error: Exception, context: str = "") -> None:
        """
        Log error with context
        
        Args:
            error: Exception that occurred
            context: Additional context information
        """
        error_msg = f"Error in {self.name}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        logger.error(error_msg)
    
    def _validate_input(self, x: Optional[Msg]) -> bool:
        """
        Validate input message
        
        Args:
            x: Input message to validate
            
        Returns:
            True if valid, False otherwise
        """
        if x is None:
            logger.warning(f"{self.name}: Received None message")
            return False
        
        if not hasattr(x, 'content'):
            logger.warning(f"{self.name}: Message missing content attribute")
            return False
        
        return True

