from fastapi import WebSocket
from typing import Dict, Set
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    WebSocket连接管理器
    """
    def __init__(self):
        # 存储活跃的WebSocket连接 {task_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # 存储连接的元数据 {task_id: connection_info}
        self.connection_metadata: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        """
        接受WebSocket连接
        """
        await websocket.accept()
        self.active_connections[task_id] = websocket
        self.connection_metadata[task_id] = {
            "connected_at": asyncio.get_event_loop().time(),
            "last_ping": asyncio.get_event_loop().time()
        }
        logger.info(f"WebSocket连接建立: {task_id}")

        # 发送连接确认
        await self.send_message(task_id, {
            "type": "connection_established",
            "data": {
                "task_id": task_id,
                "message": "WebSocket连接已建立"
            }
        })

    def disconnect(self, task_id: str):
        """
        断开WebSocket连接
        """
        if task_id in self.active_connections:
            del self.active_connections[task_id]
        if task_id in self.connection_metadata:
            del self.connection_metadata[task_id]
        logger.info(f"WebSocket连接断开: {task_id}")

    async def send_message(self, task_id: str, message: dict):
        """
        向特定任务ID发送消息
        """
        if task_id in self.active_connections:
            websocket = self.active_connections[task_id]
            try:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
                logger.debug(f"发送消息到 {task_id}: {message.get('type', 'unknown')}")
            except Exception as e:
                logger.error(f"发送消息失败 {task_id}: {e}")
                # 连接可能已断开，清理连接
                self.disconnect(task_id)
        else:
            logger.warning(f"未找到连接: {task_id}")

    async def send_progress(self, task_id: str, progress_data: dict):
        """
        发送进度更新
        """
        await self.send_message(task_id, {
            "type": "progress",
            "data": {
                "task_id": task_id,
                **progress_data,
                "timestamp": asyncio.get_event_loop().time()
            }
        })

    async def send_error(self, task_id: str, error_message: str, error_details: dict = None):
        """
        发送错误消息
        """
        await self.send_message(task_id, {
            "type": "error",
            "data": {
                "task_id": task_id,
                "error_message": error_message,
                "error_details": error_details or {},
                "timestamp": asyncio.get_event_loop().time()
            }
        })

    async def send_agent_update(self, task_id: str, agent_name: str, status: str, details: dict = None):
        """
        发送Agent状态更新
        """
        await self.send_message(task_id, {
            "type": "agent_update",
            "data": {
                "task_id": task_id,
                "agent_name": agent_name,
                "status": status,
                "details": details or {},
                "timestamp": asyncio.get_event_loop().time()
            }
        })

    async def send_file_processed(self, task_id: str, file_info: dict):
        """
        发送文件处理完成通知
        """
        await self.send_message(task_id, {
            "type": "file_processed",
            "data": {
                "task_id": task_id,
                "file_info": file_info,
                "timestamp": asyncio.get_event_loop().time()
            }
        })

    async def send_audit_completed(self, task_id: str, results: dict):
        """
        发送审计完成通知
        """
        await self.send_message(task_id, {
            "type": "audit_completed",
            "data": {
                "task_id": task_id,
                "results": results,
                "timestamp": asyncio.get_event_loop().time()
            }
        })

    async def broadcast_message(self, message: dict):
        """
        向所有连接广播消息
        """
        disconnected_clients = []

        for task_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"广播消息失败 {task_id}: {e}")
                disconnected_clients.append(task_id)

        # 清理断开的连接
        for task_id in disconnected_clients:
            self.disconnect(task_id)

    async def ping_all_connections(self):
        """
        向所有连接发送ping消息
        """
        await self.broadcast_message({
            "type": "ping",
            "data": {
                "timestamp": asyncio.get_event_loop().time()
            }
        })

    async def disconnect_all(self):
        """
        断开所有连接
        """
        for task_id in list(self.active_connections.keys()):
            try:
                websocket = self.active_connections[task_id]
                await websocket.close()
            except Exception as e:
                logger.error(f"关闭连接失败 {task_id}: {e}")

        self.active_connections.clear()
        self.connection_metadata.clear()
        logger.info("所有WebSocket连接已断开")

    def get_connection_count(self) -> int:
        """
        获取当前连接数量
        """
        return len(self.active_connections)

    def get_connection_info(self, task_id: str) -> dict:
        """
        获取连接信息
        """
        return self.connection_metadata.get(task_id, {})

    def is_connected(self, task_id: str) -> bool:
        """
        检查是否有活跃连接
        """
        return task_id in self.active_connections

# 创建全局WebSocket管理器实例
websocket_manager = WebSocketManager()