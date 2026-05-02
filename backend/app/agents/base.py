"""Agent基类"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, Awaitable

logger = logging.getLogger(__name__)


class AgentError(Exception):
    """Agent执行异常"""
    pass


class BaseAgent:
    """AI Agent基类，提供状态管理、进度回调和错误处理"""

    def __init__(self, name: str, agent_type: str):
        self.name = name
        self.agent_type = agent_type
        self.status = "idle"
        self.progress = 0.0
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.error_message: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self._progress_callback: Optional[Callable[[str, float, str], Awaitable[None]]] = None

    def set_progress_callback(self, callback: Callable[[str, float, str], Awaitable[None]]):
        """设置进度回调函数"""
        self._progress_callback = callback

    async def _report_progress(self, progress: float, message: str = ""):
        """上报进度"""
        self.progress = progress
        if self._progress_callback:
            await self._progress_callback(self.name, progress, message)

    async def run(self, **kwargs) -> Dict[str, Any]:
        """执行Agent任务，子类需实现 _execute 方法"""
        self.status = "running"
        self.start_time = time.time()
        self.error_message = None

        try:
            await self._report_progress(0.0, f"{self.name} 开始执行")
            self.result = await self._execute(**kwargs)
            self.status = "completed"
            self.end_time = time.time()
            elapsed = self.end_time - self.start_time
            await self._report_progress(100.0, f"{self.name} 执行完成 ({elapsed:.1f}s)")
            logger.info(f"Agent[{self.name}] 执行完成, 耗时 {elapsed:.1f}s")
            return self.result

        except AgentError as e:
            self._handle_error(str(e))
            raise
        except Exception as e:
            self._handle_error(f"{self.name} 执行异常: {str(e)}")
            raise AgentError(str(e)) from e

    async def _execute(self, **kwargs) -> Dict[str, Any]:
        """子类实现具体逻辑"""
        raise NotImplementedError

    def _handle_error(self, message: str):
        self.status = "error"
        self.end_time = time.time()
        self.error_message = message
        logger.error(f"Agent[{self.name}] 错误: {message}")

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "agent_type": self.agent_type,
            "status": self.status,
            "progress": self.progress,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "error_message": self.error_message,
        }
