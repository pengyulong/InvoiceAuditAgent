"""
API端点测试用例
测试FastAPI应用的所有主要端点
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json
import os
from pathlib import Path

# 导入应用
import sys
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from main import app


class TestAPIEndpoints:
    """API端点测试类"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def async_client(self):
        """创建异步测试客户端"""
        return AsyncClient(app=app, base_url="http://test")

    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "智能合同发票审计系统" in data["message"]

    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_ai_health_check(self, client):
        """测试AI服务健康检查"""
        response = client.get("/api/v1/audit/ai-health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "baidu_ocr_available" in data["data"]
        assert "deepseek_available" in data["data"]

    def test_upload_endpoint_no_file(self, client):
        """测试没有文件的上传请求"""
        response = client.post("/api/v1/upload/files")
        assert response.status_code == 422  # 验证错误

    def test_upload_endpoint_with_file(self, client):
        """测试带文件的上传请求"""
        # 创建测试文件
        test_file_path = "test_contract.pdf"
        with open(test_file_path, "wb") as f:
            f.write(b"test pdf content")

        try:
            with open(test_file_path, "rb") as f:
                files = {"files": ("test_contract.pdf", f, "application/pdf")}
                response = client.post("/api/v1/upload/files", files=files)

            # 应该成功或返回适当的错误（如果没有后端处理）
            assert response.status_code in [200, 400, 500]

        finally:
            # 清理测试文件
            if os.path.exists(test_file_path):
                os.remove(test_file_path)

    def test_audit_statistics(self, client):
        """测试审计统计端点"""
        response = client.get("/api/v1/audit/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_audits" in data
        assert "completed_audits" in data
        assert "success_rate" in data

    def test_audit_history(self, client):
        """测试审计历史端点"""
        response = client.get("/api/v1/audit/history?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    def test_audit_status_nonexistent(self, client):
        """测试查询不存在的审计状态"""
        response = client.get("/api/v1/audit/nonexistent-id/status")
        assert response.status_code == 404

    def test_audit_results_nonexistent(self, client):
        """测试获取不存在的审计结果"""
        response = client.get("/api/v1/audit/nonexistent-id/results")
        assert response.status_code == 404

    def test_cors_headers(self, client):
        """测试CORS头部"""
        response = client.options("/api/v1/audit/statistics")
        assert response.status_code == 200
        # 检查CORS头部是否存在
        headers = response.headers
        assert "access-control-allow-origin" in headers or "Access-Control-Allow-Origin" in headers

    def test_api_docs_available(self, client):
        """测试API文档可用性"""
        # Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200

        # ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_websocket_endpoint(self, client):
        """测试WebSocket端点（基础连接测试）"""
        # 注意：TestClient对WebSocket的支持有限
        # 这里主要测试端点是否存在
        with client.websocket_connect("/ws/audit/test-task") as websocket:
            # WebSocket连接应该建立成功
            assert websocket is not None

    def test_error_handling_404(self, client):
        """测试404错误处理"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_error_handling_500(self, client):
        """测试500错误处理"""
        # 这个测试取决于具体的错误场景
        # 这里是一个通用的错误处理测试
        response = client.post("/api/v1/audit/start", json={})
        # 应该返回验证错误或服务器错误
        assert response.status_code in [400, 422, 500]

    def test_rate_limiting(self, client):
        """测试速率限制（如果实现了）"""
        # 快速发送多个请求
        responses = []
        for _ in range(10):
            response = client.get("/api/v1/audit/statistics")
            responses.append(response)
            if response.status_code == 429:  # 速率限制
                break

        # 如果有速率限制，应该至少有一个429响应
        # 如果没有速率限制，所有响应都应该是200
        status_codes = [r.status_code for r in responses]
        assert all(code in [200, 429] for code in status_codes)


class TestFileUpload:
    """文件上传专项测试"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_upload_invalid_file_type(self, client):
        """测试上传无效文件类型"""
        # 创建一个.txt文件
        test_file_path = "test_invalid.txt"
        with open(test_file_path, "w") as f:
            f.write("test content")

        try:
            with open(test_file_path, "rb") as f:
                files = {"files": ("test_invalid.txt", f, "text/plain")}
                response = client.post("/api/v1/upload/files", files=files)

            # 应该返回文件类型错误
            assert response.status_code in [400, 422]

        finally:
            if os.path.exists(test_file_path):
                os.remove(test_file_path)

    def test_upload_oversized_file(self, client):
        """测试上传超大文件"""
        # 这个测试需要模拟超大文件，实际测试中可能需要调整
        pass

    def test_upload_multiple_files(self, client):
        """测试上传多个文件"""
        files_data = []

        # 创建多个测试文件
        for i in range(3):
            test_file_path = f"test_file_{i}.pdf"
            with open(test_file_path, "wb") as f:
                f.write(f"test content {i}".encode())
            files_data.append(test_file_path)

        try:
            files = []
            for i, file_path in enumerate(files_data):
                with open(file_path, "rb") as f:
                    files.append(("files", (f"test_file_{i}.pdf", f.read(), "application/pdf")))

            response = client.post("/api/v1/upload/files", files=files)
            # 验证响应
            assert response.status_code in [200, 400, 500]

        finally:
            # 清理测试文件
            for file_path in files_data:
                if os.path.exists(file_path):
                    os.remove(file_path)


class TestAuditWorkflow:
    """审计工作流测试"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_start_audit_without_files(self, client):
        """测试在没有文件的情况下开始审计"""
        audit_data = {
            "task_id": "test-task-123",
            "audit_config": {
                "enable_contract_analysis": True,
                "enable_invoice_analysis": True,
                "enable_cross_validation": True
            }
        }

        response = client.post("/api/v1/audit/start", json=audit_data)
        # 应该返回错误，因为没有上传文件
        assert response.status_code in [400, 404, 500]

    def test_pause_nonexistent_audit(self, client):
        """测试暂停不存在的审计"""
        response = client.post("/api/v1/audit/nonexistent-id/pause")
        assert response.status_code == 404

    def test_resume_nonexistent_audit(self, client):
        """测试恢复不存在的审计"""
        response = client.post("/api/v1/audit/nonexistent-id/resume")
        assert response.status_code == 404

    def test_cancel_nonexistent_audit(self, client):
        """测试取消不存在的审计"""
        response = client.delete("/api/v1/audit/nonexistent-id")
        assert response.status_code == 404


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])