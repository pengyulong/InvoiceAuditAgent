#!/usr/bin/env python3
"""
测试运行器
统一管理和运行所有测试用例
"""

import sys
import os
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime


class TestRunner:
    """测试运行器"""

    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "test_suites": []
        }

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 80)
        print("智能合同发票审计系统 - 测试套件")
        print("=" * 80)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 1. 运行AI集成测试
        self.run_ai_integration_tests()

        # 2. 运行前端组件测试
        self.run_frontend_tests()

        # 3. 运行API端点测试
        self.run_api_tests()

        # 4. 运行集成测试
        self.run_integration_tests()

        # 5. 生成测试报告
        self.generate_test_report()

    def run_ai_integration_tests(self):
        """运行AI集成测试"""
        print("🧠 运行AI集成测试...")
        print("-" * 50)

        try:
            # 切换到项目根目录
            project_root = Path(__file__).parent.parent
            os.chdir(project_root)

            # 运行AI集成测试脚本
            result = subprocess.run([
                sys.executable, "test_ai_integration.py"
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                print("✅ AI集成测试通过")
                self.test_results["passed_tests"] += 1
            else:
                print("❌ AI集成测试失败")
                print(f"错误输出: {result.stderr}")
                self.test_results["failed_tests"] += 1

            self.test_results["total_tests"] += 1
            self.test_results["test_suites"].append({
                "name": "AI集成测试",
                "status": "passed" if result.returncode == 0 else "failed",
                "duration": 0,
                "output": result.stdout + result.stderr
            })

        except subprocess.TimeoutExpired:
            print("❌ AI集成测试超时")
            self.test_results["failed_tests"] += 1
        except Exception as e:
            print(f"❌ AI集成测试异常: {e}")
            self.test_results["failed_tests"] += 1

        print()

    def run_frontend_tests(self):
        """运行前端组件测试"""
        print("🎨 运行前端组件测试...")
        print("-" * 50)

        try:
            # 导入前端测试模块
            sys.path.append(str(Path(__file__).parent))
            from test_frontend_components import run_frontend_tests

            start_time = time.time()
            passed, total = run_frontend_tests()
            duration = time.time() - start_time

            print(f"前端测试结果: {passed}/{total} 通过")
            if passed == total:
                print("✅ 前端组件测试通过")
                self.test_results["passed_tests"] += 1
            else:
                print("❌ 前端组件测试部分失败")
                self.test_results["failed_tests"] += 1

            self.test_results["total_tests"] += 1
            self.test_results["test_suites"].append({
                "name": "前端组件测试",
                "status": "passed" if passed == total else "failed",
                "duration": duration,
                "details": {"passed": passed, "total": total}
            })

        except Exception as e:
            print(f"❌ 前端组件测试异常: {e}")
            self.test_results["failed_tests"] += 1

        print()

    def run_api_tests(self):
        """运行API端点测试"""
        print("🔌 运行API端点测试...")
        print("-" * 50)

        try:
            # 检查是否安装了pytest
            try:
                import pytest
            except ImportError:
                print("⚠️ pytest未安装，跳过API端点测试")
                self.test_results["skipped_tests"] += 1
                return

            # 切换到测试目录
            test_dir = Path(__file__).parent
            os.chdir(test_dir)

            # 运行pytest
            start_time = time.time()
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "test_api_endpoints.py",
                "-v", "--tb=short", "--no-header"
            ], capture_output=True, text=True, timeout=120)

            duration = time.time() - start_time

            # 解析pytest输出
            output_lines = result.stdout.split('\n')
            passed = 0
            failed = 0
            total = 0

            for line in output_lines:
                if " passed" in line and " failed" in line:
                    # 解析类似 "3 passed, 1 failed" 的行
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed" and i > 0:
                            passed += int(parts[i-1])
                        elif part == "failed" and i > 0:
                            failed += int(parts[i-1])
                    total = passed + failed
                    break

            if result.returncode == 0 and failed == 0:
                print("✅ API端点测试通过")
                self.test_results["passed_tests"] += 1
            else:
                print(f"❌ API端点测试失败 ({passed} passed, {failed} failed)")
                if result.stderr:
                    print(f"错误输出: {result.stderr}")
                self.test_results["failed_tests"] += 1

            self.test_results["total_tests"] += 1
            self.test_results["test_suites"].append({
                "name": "API端点测试",
                "status": "passed" if result.returncode == 0 else "failed",
                "duration": duration,
                "details": {"passed": passed, "failed": failed, "total": total},
                "output": result.stdout
            })

        except subprocess.TimeoutExpired:
            print("❌ API端点测试超时")
            self.test_results["failed_tests"] += 1
        except Exception as e:
            print(f"❌ API端点测试异常: {e}")
            self.test_results["failed_tests"] += 1

        print()

    def run_integration_tests(self):
        """运行集成测试"""
        print("🔗 运行集成测试...")
        print("-" * 50)

        try:
            # 导入集成测试模块
            sys.path.append(str(Path(__file__).parent))
            from test_integration import run_integration_tests

            start_time = time.time()
            run_integration_tests()
            duration = time.time() - start_time

            print("✅ 集成测试完成")
            self.test_results["passed_tests"] += 1

            self.test_results["total_tests"] += 1
            self.test_results["test_suites"].append({
                "name": "集成测试",
                "status": "passed",
                "duration": duration
            })

        except Exception as e:
            print(f"❌ 集成测试异常: {e}")
            self.test_results["failed_tests"] += 1

        print()

    def generate_test_report(self):
        """生成测试报告"""
        print("=" * 80)
        print("测试报告")
        print("=" * 80)

        print(f"总测试套件: {self.test_results['total_tests']}")
        print(f"通过: {self.test_results['passed_tests']}")
        print(f"失败: {self.test_results['failed_tests']}")
        print(f"跳过: {self.test_results['skipped_tests']}")
        print()

        # 计算成功率
        if self.test_results['total_tests'] > 0:
            success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests']) * 100
            print(f"成功率: {success_rate:.1f}%")
        else:
            print("成功率: N/A")

        print()
        print("详细结果:")
        for suite in self.test_results['test_suites']:
            status_icon = "✅" if suite['status'] == 'passed' else "❌" if suite['status'] == 'failed' else "⏭️"
            duration_text = f" ({suite['duration']:.2f}s)" if 'duration' in suite else ""
            print(f"  {status_icon} {suite['name']}{duration_text}")

            if 'details' in suite:
                details = suite['details']
                if 'passed' in details and 'total' in details:
                    print(f"      {details['passed']}/{details['total']} 测试通过")

        print()
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 保存测试报告到文件
        self.save_test_report()

        # 返回测试是否全部通过
        return self.test_results['failed_tests'] == 0

    def save_test_report(self):
        """保存测试报告到文件"""
        try:
            report_dir = Path(__file__).parent.parent / "test_reports"
            report_dir.mkdir(exist_ok=True)

            report_file = report_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)

            print(f"📄 测试报告已保存到: {report_file}")

        except Exception as e:
            print(f"⚠️ 保存测试报告失败: {e}")


def run_specific_test(test_name):
    """运行特定的测试套件"""
    runner = TestRunner()

    test_mapping = {
        "ai": runner.run_ai_integration_tests,
        "frontend": runner.run_frontend_tests,
        "api": runner.run_api_tests,
        "integration": runner.run_integration_tests
    }

    if test_name.lower() in test_mapping:
        print(f"运行特定测试: {test_name}")
        test_mapping[test_name.lower()]()
        runner.generate_test_report()
    else:
        print(f"未知的测试名称: {test_name}")
        print(f"可用的测试: {', '.join(test_mapping.keys())}")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 运行特定测试
        test_name = sys.argv[1]
        run_specific_test(test_name)
    else:
        # 运行所有测试
        runner = TestRunner()
        success = runner.run_all_tests()

        # 根据测试结果设置退出码
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()