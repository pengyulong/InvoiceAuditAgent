#!/bin/bash

# 智能合同发票审计系统停止脚本

echo "🛑 停止智能合同发票审计系统..."

# 读取进程ID
if [ -f ".pids" ]; then
    source .pids

    # 停止后端服务
    if [ ! -z "$BACKEND_PID" ]; then
        echo "🔧 停止后端服务 (PID: $BACKEND_PID)..."
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            echo "✅ 后端服务已停止"
        else
            echo "⚠️  后端服务进程不存在"
        fi
    fi

    # 停止前端服务
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "🎨 停止前端服务 (PID: $FRONTEND_PID)..."
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            echo "✅ 前端服务已停止"
        else
            echo "⚠️  前端服务进程不存在"
        fi
    fi

    # 删除进程ID文件
    rm .pids
else
    echo "⚠️  未找到进程信息文件"
fi

# 强制停止相关进程
echo "🔍 检查并停止残留进程..."

# 停止uvicorn进程
pkill -f "uvicorn main:app" 2>/dev/null && echo "✅ 已停止 uvicorn 进程"

# 停止npm run dev进程
pkill -f "npm run dev" 2>/dev/null && echo "✅ 已停止 npm 进程"

# 停止可能的Vue开发服务器进程
pkill -f "vite" 2>/dev/null && echo "✅ 已停止 Vite 进程"

echo ""
echo "✅ 系统已停止"
echo ""
echo "📝 日志文件保留在 logs/ 目录中"
echo "🚀 重新启动: ./start.sh"