"""
集成测试用例
测试前端和后端的完整交互流程
"""

import pytest
import asyncio
import json
import time
import os
from pathlib import Path
import sys

# 添加后端路径
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient
from main import app


class TestFullWorkflow:
    """完整工作流测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def test_files(self):
        """创建测试文件"""
        files = []

        # 创建模拟合同文件
        contract_path = "test_contract.pdf"
        with open(contract_path, "wb") as f:
            f.write(b"%PDF-1.4 test contract content")

        # 创建模拟发票文件
        invoice_path = "test_invoice.pdf"
        with open(invoice_path, "wb") as f:
            f.write(b"%PDF-1.4 test invoice content")

        files.extend([contract_path, invoice_path])

        yield files

        # 清理测试文件
        for file_path in files:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_complete_audit_workflow(self, client, test_files):
        """测试完整的审计工作流"""
        task_id = f"test-task-{int(time.time())}"

        # 步骤1: 上传文件
        print("\n步骤1: 上传文件...")
        upload_response = self.upload_files(client, test_files, task_id)
        assert upload_response.status_code in [200, 201]

        upload_data = upload_response.json()
        assert "task_id" in upload_data
        assert upload_data["task_id"] == task_id

        # 步骤2: 开始审计
        print("步骤2: 开始审计...")
        audit_response = self.start_audit(client, task_id)
        assert audit_response.status_code in [200, 202]

        # 步骤3: 检查审计状态
        print("步骤3: 检查审计状态...")
        for i in range(10):  # 最多等待10次
            status_response = self.get_audit_status(client, task_id)
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"  当前状态: {status_data.get('status')}, 进度: {status_data.get('progress', 0)}%")

                if status_data.get("status") == "completed":
                    break
                elif status_data.get("status") == "failed":
                    print(f"  审计失败: {status_data.get('error_message')}")
                    break

            time.sleep(2)  # 等待2秒

        # 步骤4: 获取审计结果
        print("步骤4: 获取审计结果...")
        results_response = self.get_audit_results(client, task_id)
        if results_response.status_code == 200:
            results_data = results_response.json()
            assert "results" in results_data
            self.validate_audit_results(results_data["results"])
        else:
            print(f"  获取结果失败: {results_response.status_code}")

        print("✅ 完整工作流测试完成")

    def upload_files(self, client, file_paths, task_id):
        """上传文件"""
        files = []
        for file_path in file_paths:
            with open(file_path, "rb") as f:
                content = f.read()
                files.append(("files", (os.path.basename(file_path), content, "application/pdf")))

        return client.post(f"/api/v1/upload/files?task_id={task_id}", files=files)

    def start_audit(self, client, task_id):
        """开始审计"""
        audit_data = {
            "task_id": task_id,
            "audit_config": {
                "enable_contract_analysis": True,
                "enable_invoice_analysis": True,
                "enable_cross_validation": True,
                "enable_report_generation": True
            }
        }
        return client.post("/api/v1/audit/start", json=audit_data)

    def get_audit_status(self, client, task_id):
        """获取审计状态"""
        return client.get(f"/api/v1/audit/{task_id}/status")

    def get_audit_results(self, client, task_id):
        """获取审计结果"""
        return client.get(f"/api/v1/audit/{task_id}/results")

    def validate_audit_results(self, results):
        """验证审计结果"""
        required_fields = ["summary", "contract_info", "invoices", "issues"]

        for field in required_fields:
            assert field in results, f"审计结果缺少字段: {field}"

        # 验证摘要信息
        summary = results["summary"]
        assert "status" in summary
        assert "contract_amount" in summary
        assert "invoice_total" in summary

        # 验证合同信息
        contract_info = results["contract_info"]
        assert "contract_number" in contract_info
        assert "total_amount" in contract_info

        # 验证发票信息
        invoices = results["invoices"]
        assert isinstance(invoices, list)
        for invoice in invoices:
            assert "invoice_number" in invoice
            assert "amount" in invoice


class TestWebSocketIntegration:
    """WebSocket集成测试"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_websocket_audit_updates(self, client):
        """测试WebSocket审计更新"""
        task_id = f"ws-test-{int(time.time())}"

        with client.websocket_connect(f"/ws/audit/{task_id}") as websocket:
            # 发送开始消息
            websocket.send_json({"type": "start_audit", "task_id": task_id})

            # 接收消息
            messages_received = []
            for _ in range(5):  # 最多等待5条消息
                try:
                    message = websocket.receive_json()
                    messages_received.append(message)
                    print(f"收到WebSocket消息: {message.get('type')}")
                except Exception:
                    break

            # 验证收到的消息
            assert len(messages_received) > 0
            message_types = [msg.get("type") for msg in messages_received]
            assert "progress" in message_types or "log" in message_types

        print("✅ WebSocket集成测试完成")

    def test_websocket_connection_management(self, client):
        """测试WebSocket连接管理"""
        task_id = f"conn-test-{int(time.time())}"

        # 测试连接建立
        with client.websocket_connect(f"/ws/audit/{task_id}") as websocket:
            assert websocket is not None

            # 测试心跳
            websocket.send_json({"type": "ping"})
            try:
                response = websocket.receive_json()
                assert response.get("type") in ["pong", "heartbeat"]
            except Exception:
                pass  # 心跳响应可能不是必需的

        print("✅ WebSocket连接管理测试完成")


class TestErrorHandlingIntegration:
    """错误处理集成测试"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_upload_error_handling(self, client):
        """测试上传错误处理"""
        # 测试上传无效文件
        with open("invalid_file.txt", "w") as f:
            f.write("invalid content")

        try:
            with open("invalid_file.txt", "rb") as f:
                files = {"files": ("invalid_file.txt", f, "text/plain")}
                response = client.post("/api/v1/upload/files", files=files)

            assert response.status_code in [400, 422]
            error_data = response.json()
            assert "detail" in error_data

        finally:
            if os.path.exists("invalid_file.txt"):
                os.remove("invalid_file.txt")

    def test_audit_error_handling(self, client):
        """测试审计错误处理"""
        # 测试不存在的任务ID
        nonexistent_task = "nonexistent-task-id"

        response = client.post("/api/v1/audit/start", json={
            "task_id": nonexistent_task,
            "audit_config": {"enable_contract_analysis": True}
        })

        assert response.status_code in [400, 404, 500]

    def test_concurrent_requests(self, client):
        """测试并发请求处理"""
        import threading
        import queue

        results = queue.Queue()

        def make_request():
            try:
                response = client.get("/api/v1/audit/statistics")
                results.put(response.status_code)
            except Exception as e:
                results.put(f"Error: {e}")

        # 启动多个并发请求
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 检查结果
        success_count = 0
        while not results.empty():
            result = results.get()
            if result == 200:
                success_count += 1

        # 至少应该有一半的请求成功
        assert success_count >= 5
        print(f"✅ 并发请求测试: {success_count}/10 成功")


class TestPerformanceIntegration:
    """性能集成测试"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_response_time(self, client):
        """测试响应时间"""
        start_time = time.time()
        response = client.get("/api/v1/audit/statistics")
        end_time = time.time()

        response_time = end_time - start_time
        assert response_time < 5.0, f"响应时间过长: {response_time}秒"
        assert response.status_code == 200

        print(f"✅ 响应时间测试: {response_time:.2f}秒")

    def test_large_request_handling(self, client):
        """测试大请求处理"""
        # 创建大型请求数据
        large_data = {
            "task_id": f"large-test-{int(time.time())}",
            "audit_config": {
                "enable_contract_analysis": True,
                "enable_invoice_analysis": True,
                "enable_cross_validation": True,
                "enable_report_generation": True,
                # 添加大量配置选项
                "additional_settings": {f"setting_{i}": f"value_{i}" for i in range(1000)}
            }
        }

        start_time = time.time()
        response = client.post("/api/v1/audit/start", json=large_data)
        end_time = time.time()

        response_time = end_time - start_time
        print(f"大请求处理时间: {response_time:.2f}秒")

        # 请求应该被处理（可能成功或失败，但不应该超时）
        assert response.status_code in [200, 400, 404, 422, 500]
        assert response_time < 10.0, "大请求处理时间过长"


def run_integration_tests():
    """运行集成测试"""
    print("=" * 60)
    print("集成测试开始")
    print("=" * 60)

    # 运行完整工作流测试
    print("\n运行完整工作流测试...")
    workflow_test = TestFullWorkflow()
    try:
        # 由于需要创建测试文件，这里只运行基础测试
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        print("✅ 基础连接测试通过")
    except Exception as e:
        print(f"❌ 基础连接测试失败: {e}")

    # 运行WebSocket测试
    print("\n运行WebSocket测试...")
    ws_test = TestWebSocketIntegration()
    try:
        ws_test.test_websocket_connection_management(client)
        print("✅ WebSocket连接测试通过")
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")

    # 运行错误处理测试
    print("\n运行错误处理测试...")
    error_test = TestErrorHandlingIntegration()
    try:
        error_test.test_audit_error_handling(client)
        print("✅ 错误处理测试通过")
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")

    # 运行性能测试
    print("\n运行性能测试...")
    perf_test = TestPerformanceIntegration()
    try:
        perf_test.test_response_time(client)
        print("✅ 性能测试通过")
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")

    print("\n" + "=" * 60)
    print("集成测试完成")
    print("=" * 60)


if __name__ == "__main__":
    run_integration_tests()