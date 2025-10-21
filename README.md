# 智能合同发票审计系统

基于AI的智能合同发票审计系统，通过多模态大模型和LLM技术，自动化审计采购合同与发票的匹配性、合规性和准确性。

## 项目结构

```
InvoiceAuditAgent/
├── backend/                 # Python FastAPI 后端
│   ├── app/
│   │   ├── api/            # API路由层
│   │   │   └── v1/         # API v1版本
│   │   ├── agents/         # AI智能体
│   │   │   ├── contract_analyzer.py    # 合同分析Agent
│   │   │   ├── invoice_analyzer.py     # 发票分析Agent
│   │   │   ├── coordinator.py          # 协调Agent
│   │   │   └── cross_validator.py      # 交叉验证Agent
│   │   ├── core/           # 核心配置
│   │   │   ├── config.py    # 应用配置
│   │   │   ├── database.py  # 数据库配置
│   │   │   └── security.py  # 安全配置
│   │   ├── models/         # 数据模型
│   │   │   ├── audit.py     # 审计模型
│   │   │   ├── contract.py  # 合同模型
│   │   │   ├── invoice.py   # 发票模型
│   │   │   └── base.py      # 基础模型
│   │   ├── schemas/        # 数据验证模式
│   │   └── services/       # 业务逻辑层
│   │       ├── ai_service.py         # AI服务
│   │       ├── audit_service.py      # 审计服务
│   │       ├── file_service.py       # 文件服务
│   │       ├── websocket_service.py  # WebSocket服务
│   │       ├── tasks.py              # 任务处理
│   │       └── celery_app.py         # Celery配置
│   ├── main.py               # FastAPI应用入口
│   ├── requirements.txt      # Python依赖
│   ├── uploads/              # 文件上传目录
│   └── logs/                 # 日志目录
├── frontend/               # Vue 3 + TypeScript 前端
│   ├── src/
│   │   ├── assets/         # 静态资源
│   │   ├── router/         # 路由配置
│   │   ├── services/       # API服务层
│   │   ├── stores/         # Pinia状态管理
│   │   ├── types/          # TypeScript类型定义
│   │   └── views/          # 页面组件
│   │       └── Audit/      # 审计相关页面
│   ├── package.json        # Node.js依赖
│   └── vite.config.ts      # Vite配置
├── docs/                   # 项目文档
├── logs/                   # 系统日志
├── .spec-workflow/         # 规格工作流配置
├── prd.md                  # 产品需求文档
├── DESIGN.md               # 技术设计文档
└── README.md               # 项目说明
```

## 技术栈

- **前端**: Vue 3 + TypeScript + Element Plus
- **后端**: Python 3.9+ + FastAPI + LangGraph
- **AI模型**: 阿里云qwen3-vl-8b-thinking + DeepSeek-V3.2-exp
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **缓存**: Redis
- **任务队列**: Celery

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- Redis
- PostgreSQL (生产环境)

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd InvoiceAuditAgent
```

2. 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

3. 安装前端依赖
```bash
cd frontend
npm install
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入API密钥等配置
```

5. 启动服务
```bash
# 启动后端
cd backend
uvicorn main:app --reload

# 启动前端
cd frontend
npm run dev
```

## API文档

启动后端服务后，访问 http://localhost:8000/docs 查看API文档。

## 贡献指南

请查看 [开发设计文档](./rd.md) 了解详细的开发规范和流程。