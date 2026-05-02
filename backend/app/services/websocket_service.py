from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 活跃连接：{audit_id: {connection_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # 连接元数据：{connection_id: {audit_id, user_info, etc.}}
        self.connection_metadata: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, audit_id: str, connection_id: str = None):
        """接受WebSocket连接"""
        await websocket.accept()

        if connection_id is None:
            import uuid
            connection_id = str(uuid.uuid4())

        if audit_id not in self.active_connections:
            self.active_connections[audit_id] = {}

        self.active_connections[audit_id][connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "audit_id": audit_id,
            "connected_at": asyncio.get_event_loop().time()
        }

        logger.info(f"WebSocket连接已建立: audit_id={audit_id}, connection_id={connection_id}")

        # 发送连接确认消息
        await self.send_to_connection(connection_id, {
            "type": "connected",
            "connection_id": connection_id,
            "audit_id": audit_id,
            "message": "WebSocket连接已建立"
        })

        return connection_id

    def disconnect(self, audit_id: str, connection_id: str):
        """断开WebSocket连接"""
        if audit_id in self.active_connections:
            if connection_id in self.active_connections[audit_id]:
                del self.active_connections[audit_id][connection_id]

                # 如果该审计任务没有其他连接，删除整个条目
                if not self.active_connections[audit_id]:
                    del self.active_connections[audit_id]

        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]

        logger.info(f"WebSocket连接已断开: audit_id={audit_id}, connection_id={connection_id}")

    async def send_to_connection(self, connection_id: str, data: dict):
        """向特定连接发送消息"""
        if connection_id in self.connection_metadata:
            audit_id = self.connection_metadata[connection_id]["audit_id"]
            if audit_id in self.active_connections:
                if connection_id in self.active_connections[audit_id]:
                    websocket = self.active_connections[audit_id][connection_id]
                    try:
                        await websocket.send_text(json.dumps(data, ensure_ascii=False))
                    except Exception as e:
                        logger.error(f"发送WebSocket消息失败: connection_id={connection_id}, error={e}")
                        # 连接可能已断开，清理连接
                        self.disconnect(audit_id, connection_id)

    async def send_to_audit(self, audit_id: str, data: dict):
        """向特定审计任务的所有连接发送消息"""
        if audit_id in self.active_connections:
            disconnected_connections = []

            for connection_id, websocket in self.active_connections[audit_id].items():
                try:
                    await websocket.send_text(json.dumps(data, ensure_ascii=False))
                except Exception as e:
                    logger.error(f"发送WebSocket消息失败: audit_id={audit_id}, connection_id={connection_id}, error={e}")
                    disconnected_connections.append(connection_id)

            # 清理断开的连接
            for connection_id in disconnected_connections:
                self.disconnect(audit_id, connection_id)

    async def send_progress(self, audit_id: str, progress_data: dict):
        """发送进度更新消息"""
        message = {
            "type": "progress",
            "data": progress_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_to_audit(audit_id, message)

    async def send_agent_status(self, audit_id: str, agent_name: str, status: str, data: dict = None):
        """发送Agent状态更新消息"""
        message = {
            "type": "agent_status",
            "data": {
                "agent_name": agent_name,
                "status": status,
            },
            "timestamp": asyncio.get_event_loop().time()
        }
        if data:
            message["data"].update(data)
        await self.send_to_audit(audit_id, message)

    async def send_step_change(self, audit_id: str, data: dict):
        """发送步骤变化消息"""
        message = {
            "type": "step_change",
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_to_audit(audit_id, message)

    async def send_error(self, audit_id: str, error_data: dict):
        """发送错误消息"""
        message = {
            "type": "error",
            "data": error_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_to_audit(audit_id, message)

    async def send_completed(self, audit_id: str, result_data: dict):
        """发送完成消息"""
        message = {
            "type": "completed",
            "data": result_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_to_audit(audit_id, message)

    async def send_log(self, audit_id: str, log_message: str, level: str = "info", agent_name: str = ""):
        """发送日志消息"""
        message = {
            "type": "log",
            "data": {
                "message": log_message,
                "level": level,
                "agent_name": agent_name
            },
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_to_audit(audit_id, message)

    def get_connection_count(self, audit_id: str) -> int:
        """获取特定审计任务的连接数"""
        return len(self.active_connections.get(audit_id, {}))

    def get_total_connection_count(self) -> int:
        """获取总连接数"""
        return sum(len(connections) for connections in self.active_connections.values())

    def get_audit_connections(self, audit_id: str) -> Dict[str, dict]:
        """获取特定审计任务的连接信息"""
        connections = {}
        if audit_id in self.active_connections:
            for connection_id in self.active_connections[audit_id]:
                connections[connection_id] = self.connection_metadata.get(connection_id, {})
        return connections

    async def ping_all_connections(self):
        """向所有连接发送ping消息"""
        ping_message = {
            "type": "ping",
            "timestamp": asyncio.get_event_loop().time()
        }

        for audit_id in list(self.active_connections.keys()):
            await self.send_to_audit(audit_id, ping_message)


# 创建全局WebSocket管理器实例
websocket_manager = WebSocketManager()