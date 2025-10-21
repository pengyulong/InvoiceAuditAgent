#!/bin/bash

# 智能合同发票审计系统启动脚本

echo "🚀 智能合同发票审计系统启动中..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python 3.9+"
    exit 1
fi

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到Node.js，请先安装Node.js 18+"
    exit 1
fi

# 检查Redis
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  警告: 未找到Redis，请确保Redis服务正在运行"
fi

# 创建环境变量文件
if [ ! -f ".env" ]; then
    echo "📝 创建环境变量文件..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请编辑并填入你的API密钥"
fi

# 启动后端服务
echo "🔧 启动后端服务..."
cd backend

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
echo "📦 安装后端依赖..."
source venv/bin/activate
pip install -r requirements.txt

# 初始化数据库
echo "🗄️ 初始化数据库..."
python -c "
from app.core.database import init_db
init_db()
print('✅ 数据库初始化完成')
"

# 启动后端服务（后台运行）
echo "🚀 启动FastAPI服务..."
# 复制.env文件到backend目录以确保配置正确加载
if [ -f "../.env" ]; then
    cp ../.env .env
    echo "✅ 已复制.env文件到backend目录"
fi
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"

cd ..

# 启动前端服务
echo "🎨 启动前端服务..."
cd frontend

# 安装前端依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 启动前端开发服务器（后台运行）
echo "🚀 启动Vue开发服务器..."
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"

cd ..

# 保存进程ID
echo "💾 保存进程信息..."
echo "BACKEND_PID=$BACKEND_PID" > .pids
echo "FRONTEND_PID=$FRONTEND_PID" >> .pids

# 创建日志目录
mkdir -p logs

echo ""
echo "🎉 系统启动完成！"
echo ""
echo "📱 前端地址: http://localhost:3000"
echo "🔗 后端API: http://localhost:8000"
echo "📖 API文档: http://localhost:8000/docs"
echo ""
echo "📝 日志文件:"
echo "   - 后端日志: logs/backend.log"
echo "   - 前端日志: logs/frontend.log"
echo ""
echo "🛑 停止服务: ./stop.sh"
echo ""
echo "⚠️  请确保："
echo "   1. 已编辑 .env 文件并填入API密钥"
echo "   2. Redis服务正在运行（如需缓存功能）"
echo "   3. 防火墙允许3000和8000端口访问"
echo ""

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo "🔍 检查服务状态..."

# 检查后端
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务运行正常"
else
    echo "❌ 后端服务启动失败，请检查 logs/backend.log"
fi

# 检查前端
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ 前端服务运行正常"
else
    echo "❌ 前端服务启动失败，请检查 logs/frontend.log"
fi

echo ""
echo "🎯 现在可以开始使用系统了！"