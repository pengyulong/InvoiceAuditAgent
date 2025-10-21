# 智能合同发票审计系统 - 项目结构说明

## 项目概述

智能合同发票审计系统是一个基于AI的企业级审计工具，通过多模态大模型和LLM技术，自动化审计采购合同与发票的匹配性、合规性和准确性。

## 整体架构

```
InvoiceAuditAgent/
├── backend/                 # 后端服务 - FastAPI
├── frontend/               # 前端应用 - Vue 3
├── docs/                   # 项目文档
├── logs/                   # 系统日志
├── .spec-workflow/         # 规格工作流配置
├── prd.md                  # 产品需求文档
├── DESIGN.md               # 技术设计文档
└── README.md               # 项目说明
```

## 后端架构详解 (backend/)

### 目录结构
```
backend/
├── app/                    # 应用核心代码
│   ├── api/               # API路由层
│   ├── agents/            # AI智能体
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   ├── schemas/           # 数据验证模式
│   └── services/          # 业务逻辑层
├── main.py                # FastAPI应用入口
├── requirements.txt       # Python依赖
├── uploads/               # 文件上传目录
└── logs/                  # 日志目录
```

### API层 (app/api/)
负责处理HTTP请求和响应，提供RESTful API接口。

- **v1/audit.py**: 审计相关API
  - `POST /api/v1/audit/start` - 启动审计任务
  - `GET /api/v1/audit/tasks` - 获取审计任务列表
  - `GET /api/v1/audit/status/{task_id}` - 获取任务状态

- **v1/upload.py**: 文件上传API
  - `POST /api/v1/upload/zip` - 上传ZIP文件
  - `POST /api/v1/upload/single` - 上传单个文件

- **v1/results.py**: 结果查询API
  - `GET /api/v1/results/{task_id}` - 获取审计结果
  - `GET /api/v1/results/statistics` - 获取统计数据

### AI智能体层 (app/agents/)
基于LangGraph的多Agent协作系统，负责AI驱动的审计分析。

- **contract_analyzer.py**: 合同分析Agent
  - 合同文本提取和理解
  - 关键条款识别
  - 风险点检测

- **invoice_analyzer.py**: 发票分析Agent
  - 发票图像识别 (OCR)
  - 发票信息提取
  - 发票真伪验证

- **coordinator.py**: 协调Agent
  - 任务分发和协调
  - Agent间通信
  - 工作流管理

- **cross_validator.py**: 交叉验证Agent
  - 合同发票匹配验证
  - 数据一致性检查
  - 异常检测

### 核心配置层 (app/core/)
系统配置和基础设施组件。

- **config.py**: 应用配置
  - 数据库连接配置
  - AI服务API配置
  - 安全和认证配置

- **database.py**: 数据库配置
  - SQLAlchemy数据库连接
  - 会话管理
  - 连接池配置

- **security.py**: 安全配置
  - JWT认证
  - 密码加密
  - API安全策略

### 数据模型层 (app/models/)
SQLAlchemy ORM模型定义。

- **audit.py**: 审计任务模型
  - AuditTask: 审计任务主表
  - AuditResult: 审计结果表

- **contract.py**: 合同模型
  - Contract: 合同信息表
  - ContractClause: 合同条款表

- **invoice.py**: 发票模型
  - Invoice: 发票信息表
  - InvoiceItem: 发票明细表

- **base.py**: 基础模型
  - 基础字段定义
  - 通用方法

### 数据验证层 (app/schemas/)
Pydantic数据验证和序列化。

- **results.py**: 结果数据模式
  - 响应数据格式定义
  - 数据验证规则
  - API文档生成

### 业务逻辑层 (app/services/)
核心业务逻辑实现。

- **ai_service.py**: AI服务
  - DashScope API集成
  - 图像分析服务
  - 文本分析服务

- **audit_service.py**: 审计服务
  - 审计流程管理
  - 结果生成
  - 报告导出

- **file_service.py**: 文件服务
  - 文件上传处理
  - ZIP文件解压
  - 文件类型识别

- **websocket_service.py**: WebSocket服务
  - 实时通信
  - 进度推送
  - 状态更新

- **tasks.py**: 任务处理
  - 异步任务定义
  - Celery任务配置
  - 任务状态管理

- **celery_app.py**: Celery配置
  - 消息队列配置
  - 任务调度
  - Worker管理

## 前端架构详解 (frontend/)

### 目录结构
```
frontend/
├── src/
│   ├── assets/            # 静态资源
│   ├── router/            # 路由配置
│   ├── services/          # API服务层
│   ├── stores/            # 状态管理
│   ├── types/             # TypeScript类型定义
│   └── views/             # 页面组件
├── package.json           # Node.js依赖
├── vite.config.ts         # Vite配置
└── public/                # 公共资源
```

### 资源层 (src/assets/)
- 静态图片资源
- 样式文件
- 图标字体

### 路由层 (src/router/)
Vue Router配置和路由定义。

- **index.ts**: 路由配置
  - 路由映射定义
  - 路由守卫
  - 懒加载配置

### API服务层 (src/services/)
HTTP客户端和API调用封装。

- **api.ts**: API基础配置
  - Axios实例配置
  - 请求/响应拦截器
  - 错误处理

- **audit.ts**: 审计服务
  - 审计任务API调用
  - 状态查询
  - 结果获取

- **upload.ts**: 上传服务
  - 文件上传API
  - 进度监控
  - 文件验证

### 状态管理层 (src/stores/)
Pinia状态管理。

- **audit.ts**: 审计状态
  - 当前任务状态
  - 审计进度
  - WebSocket连接

### 类型定义层 (src/types/)
TypeScript类型声明。

- **index.ts**: 类型定义
  - API响应类型
  - 数据模型类型
  - 组件Props类型

### 视图组件层 (src/views/)
页面级组件。

- **Audit/**: 审计相关页面
  - **index.vue**: 审计主页面
    - 任务列表展示
    - 文件上传入口
    - 统计数据展示

  - **Upload.vue**: 文件上传页面
    - 拖拽上传界面
    - 文件预览
    - 上传进度

  - **Processing.vue**: 处理进度页面
    - 实时进度展示
    - 处理日志
    - 状态监控

## 数据流架构

### 前端数据流
```
用户操作 → View组件 → Pinia Store → API服务 → HTTP请求
响应返回 → Store更新 → View重渲染 → 用户看到结果
```

### 后端数据流
```
API请求 → 路由处理 → 业务逻辑 → AI分析 → 数据库存储
WebSocket推送 → 前端接收 → 状态更新 → 界面刷新
```

## 部署架构

### 开发环境
- **前端**: Vite开发服务器 (http://localhost:5173)
- **后端**: Uvicorn ASGI服务器 (http://localhost:8000)
- **数据库**: SQLite本地文件
- **消息队列**: Redis本地实例

### 生产环境
- **前端**: Nginx静态文件服务
- **后端**: Gunicorn + Uvicorn进程
- **数据库**: PostgreSQL集群
- **消息队列**: Redis集群
- **文件存储**: 对象存储服务

## 技术栈总结

### 前端技术栈
- **框架**: Vue 3.4+ (Composition API)
- **语言**: TypeScript 5.0+
- **UI库**: Element Plus 2.4+
- **状态管理**: Pinia 2.1+
- **路由**: Vue Router 4.2+
- **HTTP客户端**: Axios 1.6+
- **构建工具**: Vite 5.0+
- **样式**: CSS3 + Scoped CSS

### 后端技术栈
- **框架**: FastAPI 0.104+
- **语言**: Python 3.9+
- **AI框架**: LangGraph 0.0+
- **异步处理**: asyncio + aiofiles
- **任务队列**: Celery 5.3+
- **数据库ORM**: SQLAlchemy 2.0+
- **API文档**: OpenAPI/Swagger
- **WebSocket**: FastAPI WebSocket

### AI服务技术栈
- **多模态模型**: 阿里云 DashScope (qwen-vl)
- **语言模型**: DeepSeek-V3.2-exp
- **图像处理**: OCR + 计算机视觉
- **自然语言处理**: 文本理解和生成

### 数据和存储
- **关系数据库**: SQLite (开发) / PostgreSQL (生产)
- **缓存**: Redis
- **文件存储**: 本地文件系统 / 对象存储
- **消息队列**: Redis + Celery

## 开发规范

### 代码规范
- **Python**: 遵循PEP 8规范
- **TypeScript**: 使用ESLint + Prettier
- **Vue 3**: 遵循官方风格指南
- **Git**: 使用Conventional Commits

### 测试策略
- **单元测试**: pytest (后端) + Vitest (前端)
- **集成测试**: FastAPI TestClient
- **端到端测试**: Playwright
- **性能测试**: Locust

### 文档规范
- **API文档**: 自动生成OpenAPI/Swagger
- **代码注释**: 中文注释为主
- **README**: 详细的使用说明
- **设计文档**: 完整的技术设计

## 扩展性设计

### 水平扩展
- **前端**: CDN分发 + 负载均衡
- **后端**: 多实例部署 + API网关
- **数据库**: 读写分离 + 分库分表
- **AI服务**: 模型服务化 + 负载均衡

### 功能扩展
- **插件系统**: 支持自定义审计规则
- **多租户**: 支持企业级多租户
- **国际化**: 多语言支持
- **移动端**: 响应式设计 + PWA

这个项目结构说明文档为开发团队提供了完整的技术架构参考，有助于新成员快速理解项目结构和各组件的职责。