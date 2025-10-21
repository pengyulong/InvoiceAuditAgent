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
        # 存储活跃的WebSocket连接 {audit_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # 存储连接的元数据 {audit_id: connection_info}
        self.connection_metadata: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, audit_id: str):
        """
        接受WebSocket连接
        """
        await websocket.accept()
        self.active_connections[audit_id] = websocket
        self.connection_metadata[audit_id] = {
            "connected_at": asyncio.get_event_loop().time(),
            "last_ping": asyncio.get_event_loop().time()
        }
        logger.info(f"WebSocket连接建立: {audit_id}")

        # 发送连接确认
        await self.send_message(audit_id, {
            "type": "connection_established",
            "data": {
                "audit_id": audit_id,
                "message": "WebSocket连接已建立"
            }
        })

    def disconnect(self, audit_id: str):
        """
        断开WebSocket连接
        """
        if audit_id in self.active_connections:
            del self.active_connections[audit_id]
        if audit_id in self.connection_metadata:
            del self.connection_metadata[audit_id]
        logger.info(f"WebSocket连接断开: {audit_id}")

    async def send_message(self, audit_id: str, message: dict):
        """
        向特定审计ID发送消息
        """
        if audit_id in self.active_connections:
            websocket = self.active_connections[audit_id]
            try:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
                logger.debug(f"发送消息到 {audit_id}: {message.get('type', 'unknown')}")
            except Exception as e:
                logger.error(f"发送消息失败 {audit_id}: {e}")
                # 连接可能已断开，清理连接
                self.disconnect(audit_id)
        else:
            logger.warning(f"未找到连接: {audit_id}")

    async def send_progress(self, audit_id: str, progress_data: dict):
        """
        发送进度更新
        """
        await self.send_message(audit_id, {
            "type": "progress",
            "data": {
                "audit_id": audit_id,
                **progress_data,
                "timestamp": asyncio.get_event_loop().time()
            }
        })

    async def send_error(self, audit_id: str, error_message: str, error_details: dict = None):
        """
        发送错误消息
        """
        await self.send_message(audit_id, {
            "type": "error",
            "data": {
                "audit_id": audit_id,
                "error_message": error_message,
                "error_details": error_details or {},
                "timestamp": asyncio.get_event_loop().time()
            }
        })

    async def send_agent_update(self, audit_id: str, agent_name: str, status: str, details: dict = None):
        """
        发送Agent状态更新
        """
        await self.send_message(audit_id, {
            "type": "agent_update",
            "data": {
                "audit_id": audit_id,
                "agent_name": agent_name,
                "status": status,
                "details": details or {},
                "timestamp": asyncio.get_event_loop().time()
            }
        })

    async def send_file_processed(self, audit_id: str, file_info: dict):
        """
        发送文件处理完成通知
        """
        await self.send_message(audit_id, {
            "type": "file_processed",
            "data": {
                "audit_id": audit_id,
                "file_info": file_info,
                "timestamp": asyncio.get_event_loop().time()
            }
        })

    async def send_audit_completed(self, audit_id: str, results: dict):
        """
        发送审计完成通知
        """
        await self.send_message(audit_id, {
            "type": "audit_completed",
            "data": {
                "audit_id": audit_id,
                "results": results,
                "timestamp": asyncio.get_event_loop().time()
            }
        })

    async def broadcast_message(self, message: dict):
        """
        向所有连接广播消息
        """
        disconnected_clients = []

        for audit_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"广播消息失败 {audit_id}: {e}")
                disconnected_clients.append(audit_id)

        # 清理断开的连接
        for audit_id in disconnected_clients:
            self.disconnect(audit_id)

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
        for audit_id in list(self.active_connections.keys()):
            try:
                websocket = self.active_connections[audit_id]
                await websocket.close()
            except Exception as e:
                logger.error(f"关闭连接失败 {audit_id}: {e}")

        self.active_connections.clear()
        self.connection_metadata.clear()
        logger.info("所有WebSocket连接已断开")

    def get_connection_count(self) -> int:
        """
        获取当前连接数量
        """
        return len(self.active_connections)

    def get_connection_info(self, audit_id: str) -> dict:
        """
        获取连接信息
        """
        return self.connection_metadata.get(audit_id, {})

    def is_connected(self, audit_id: str) -> bool:
        """
        检查是否有活跃连接
        """
        return audit_id in self.active_connections

# 创建全局WebSocket管理器实例
websocket_manager = WebSocketManager()