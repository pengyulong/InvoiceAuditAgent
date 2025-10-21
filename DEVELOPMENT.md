# 智能合同发票审计系统 - 开发指南

## 快速开始

### 环境要求

- **Python**: 3.9+
- **Node.js**: 18+
- **Redis**: 6.0+ (可选，用于缓存)
- **Git**: 版本控制

### 一键启动

```bash
# 启动整个系统
./start.sh

# 停止系统
./stop.sh
```

### 手动启动

#### 1. 后端服务

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp ../.env.example .env
# 编辑 .env 文件，填入API密钥

# 初始化数据库
python -c "from app.core.database import init_db; init_db()"

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. 前端服务

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 访问地址

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 项目结构

```
InvoiceAuditAgent/
├── backend/                 # Python FastAPI 后端
│   ├── app/
│   │   ├── api/            # API路由
│   │   │   └── v1/         # API v1版本
│   │   ├── agents/         # AI Agent
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   ├── main.py             # FastAPI应用入口
│   └── requirements.txt    # Python依赖
├── frontend/               # Vue3 前端
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── views/          # 页面
│   │   ├── stores/         # Pinia状态管理
│   │   ├── services/       # API服务
│   │   ├── types/          # TypeScript类型
│   │   └── router/         # 路由配置
│   ├── package.json        # 前端依赖
│   └── vite.config.ts      # Vite配置
├── docs/                   # 文档
├── start.sh               # 启动脚本
├── stop.sh                # 停止脚本
└── README.md              # 项目说明
```

## 核心功能

### 1. 文件上传功能

- 支持ZIP文件上传（包含合同和发票）
- 文件类型自动识别
- 文件大小限制（50MB）
- 上传进度显示

### 2. AI Agent工作流

- **协调器Agent**: 整体流程协调
- **合同分析Agent**: 合同内容分析
- **发票分析Agent**: 发票内容分析
- **交叉验证Agent**: 合同发票匹配验证

### 3. 实时通信

- WebSocket实时进度推送
- Agent状态实时更新
- 错误信息实时通知

## API配置

### 环境变量配置

编辑 `.env` 文件：

```env
# AI模型API配置
QWEN_API_KEY=your_qwen_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 数据库配置
DATABASE_URL=sqlite:///./audit.db

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 其他配置...
```

### API密钥获取

1. **阿里云qwen3-vl**: 访问 [阿里云DashScope](https://dashscope.console.aliyun.com/)
2. **DeepSeek**: 访问 [DeepSeek API](https://platform.deepseek.com/)

## 开发规范

### 后端开发

- 使用 **FastAPI** 框架
- 遵循 **RESTful API** 设计
- 使用 **SQLAlchemy** ORM
- 实现 **异步编程** (async/await)
- 添加 **类型提示** 和 **文档字符串**

### 前端开发

- 使用 **Vue 3** + **TypeScript**
- 使用 **Composition API**
- 使用 **Pinia** 状态管理
- 使用 **Element Plus** UI组件库
- 遵循 **组件化开发**

### 代码规范

- Python: 使用 **Black** + **Flake8**
- TypeScript: 使用 **ESLint** + **Prettier**
- 提交前自动格式化代码

## 测试

### 运行测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test
```

### 测试数据

项目包含示例测试数据，可用于功能验证：

- 示例合同文件
- 示例发票文件
- 测试用ZIP包

## 部署

### Docker部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

### 生产环境

1. 配置生产环境变量
2. 使用 **PostgreSQL** 数据库
3. 配置 **Redis** 缓存
4. 使用 **Nginx** 反向代理
5. 配置 **SSL** 证书

## 常见问题

### Q: 启动失败怎么办？

A: 检查以下几点：
- Python和Node.js版本是否符合要求
- 端口3000和8000是否被占用
- API密钥是否正确配置
- 依赖是否完整安装

### Q: AI分析失败怎么办？

A: 检查以下几点：
- API密钥是否有效
- 网络连接是否正常
- API配额是否充足
- 文件格式是否支持

### Q: 如何添加新的AI模型？

A: 在 `app/services/ai_service.py` 中添加新的模型调用逻辑。

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 支持

如有问题，请提交 Issue 或联系开发团队。