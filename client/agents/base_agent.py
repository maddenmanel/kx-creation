"""
基础Agent类
"""
import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from loguru import logger

from models.schemas import AgentResponse


class BaseAgent(ABC):
    """基础Agent抽象类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.start_time = None
    
    def _start_timer(self):
        """开始计时"""
        self.start_time = time.time()
    
    def _get_processing_time(self) -> float:
        """获取处理时间"""
        if self.start_time:
            return time.time() - self.start_time
        return 0.0
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        处理输入数据
        
        Args:
            input_data: 输入数据
            
        Returns:
            AgentResponse: 处理结果
        """
        pass
    
    def create_response(
        self,
        success: bool,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        创建响应对象
        
        Args:
            success: 是否成功
            message: 消息
            data: 数据
            
        Returns:
            AgentResponse: 响应对象
        """
        return AgentResponse(
            agent_name=self.name,
            success=success,
            message=message,
            data=data,
            processing_time=self._get_processing_time()
        )
    
    def log_info(self, message: str):
        """记录信息日志"""
        logger.info(f"[{self.name}] {message}")
    
    def log_error(self, message: str):
        """记录错误日志"""
        logger.error(f"[{self.name}] {message}")
    
    def log_warning(self, message: str):
        """记录警告日志"""
        logger.warning(f"[{self.name}] {message}")
