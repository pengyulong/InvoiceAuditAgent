# 智能合同发票审计系统 - 开发设计文档 (RD)

## 1. 项目概述

### 1.1 项目目标
开发一个基于AI的智能合同发票审计系统，通过多模态大模型和LLM技术，自动化审计采购合同与发票的匹配性、合规性和准确性。

### 1.2 技术栈选择
- **前端**: Vue 3 + TypeScript + Element Plus
- **后端**: Python 3.9+ + FastAPI + LangGraph
- **AI模型**: 阿里云qwen3-vl-8b-thinking + DeepSeek-V3.2-exp
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **缓存**: Redis
- **任务队列**: Celery
- **文件存储**: 本地存储 + MinIO

## 2. 系统架构设计

### 2.1 整体架构
```
前端 (Vue 3)
    ↓ HTTP/WebSocket
API网关 (FastAPI)
    ↓
业务逻辑层 (Service Layer)
    ↓
Agent编排层 (LangGraph)
    ↓
模型服务层 (AI API)
    ↓
数据存储层 (SQLite/PostgreSQL + Redis)
```

### 2.2 核心模块设计

#### 2.2.1 前端模块结构
```
frontend/
├── src/
│   ├── components/          # 通用组件
│   │   ├── Upload/         # 文件上传组件
│   │   ├── Progress/       # 进度显示组件
│   │   ├── ResultTable/    # 结果表格组件
│   │   └── Charts/         # 图表组件
│   ├── views/              # 页面视图
│   │   ├── Home/           # 首页
│   │   ├── Audit/          # 审计页面
│   │   └── Results/        # 结果页面
│   ├── stores/             # Pinia状态管理
│   ├── services/           # API服务
│   ├── utils/              # 工具函数
│   └── types/              # TypeScript类型定义
```

#### 2.2.2 后端模块结构
```
backend/
├── app/
│   ├── api/                # API路由
│   │   ├── v1/
│   │   │   ├── audit.py    # 审计相关API
│   │   │   ├── upload.py   # 文件上传API
│   │   │   └── results.py  # 结果查询API
│   ├── core/               # 核心配置
│   │   ├── config.py       # 配置管理
│   │   ├── security.py     # 安全相关
│   │   └── database.py     # 数据库配置
│   ├── services/           # 业务逻辑
│   │   ├── audit_service.py
│   │   ├── file_service.py
│   │   └── report_service.py
│   ├── agents/             # AI Agent
│   │   ├── coordinator.py  # 协调器Agent
│   │   ├── contract_analyzer.py
│   │   ├── invoice_analyzer.py
│   │   └── cross_validator.py
│   ├── models/             # 数据模型
│   │   ├── audit.py
│   │   ├── contract.py
│   │   └── invoice.py
│   └── utils/              # 工具函数
```

## 3. AI Agent工作流设计

### 3.1 LangGraph工作流架构
```python
# 1. 协调器Agent (Coordinator)
- 接收用户上传文件
- 初步文件验证和分类
- 任务分发和状态管理
- 结果汇总和报告生成

# 2. 合同分析Agent (Contract Analyzer)
- 使用多模态模型解析合同图像
- 提取关键信息：合同编号、金额、商品清单
- 合同合理性评估
- 输出结构化数据

# 3. 发票分析Agent (Invoice Analyzer)
- 批量处理发票图像
- 提取发票信息
- 重复发票检测
- 发票错误识别

# 4. 交叉验证Agent (Cross-Validator)
- 合同-发票信息匹配
- 金额一致性验证
- 覆盖率计算
- 差异项识别
```

### 3.2 工作流程图
```
开始 → 文件上传 → 协调器 → 并行处理 → 交叉验证 → 结果汇总 → 报告生成 → 结束
                    ↓
                 文件验证
                    ↓
               [合同分析] + [发票分析]
                    ↓
                 结果同步
                    ↓
                 交叉验证
                    ↓
                 报告生成
```

## 4. 数据库设计

### 4.1 核心表结构

#### 4.1.1 审计任务表 (audit_tasks)
```sql
CREATE TABLE audit_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    total_files INTEGER DEFAULT 0,
    processed_files INTEGER DEFAULT 0,
    error_message TEXT NULL
);
```

#### 4.1.2 合同信息表 (contracts)
```sql
CREATE TABLE contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES audit_tasks(id),
    contract_number VARCHAR(255) UNIQUE,
    buyer_name VARCHAR(255),
    seller_name VARCHAR(255),
    total_amount DECIMAL(15,2),
    tax_rate DECIMAL(5,4),
    contract_date DATE,
    file_path TEXT,
    extracted_data JSONB,
    confidence_score DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.1.3 发票信息表 (invoices)
```sql
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES audit_tasks(id),
    invoice_code VARCHAR(255),
    invoice_number VARCHAR(255),
    buyer_name VARCHAR(255),
    seller_name VARCHAR(255),
    total_amount DECIMAL(15,2),
    tax_amount DECIMAL(15,2),
    invoice_date DATE,
    file_path TEXT,
    extracted_data JSONB,
    confidence_score DECIMAL(5,4),
    is_duplicate BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.1.4 审计结果表 (audit_results)
```sql
CREATE TABLE audit_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES audit_tasks(id),
    result_type VARCHAR(50) NOT NULL, -- 'error', 'warning', 'info'
    severity VARCHAR(20) NOT NULL, -- 'high', 'medium', 'low'
    title VARCHAR(255) NOT NULL,
    description TEXT,
    affected_entities JSONB, -- 涉及的合同/发票ID
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 索引设计
```sql
-- 性能优化索引
CREATE INDEX idx_audit_tasks_status ON audit_tasks(status);
CREATE INDEX idx_contracts_task_id ON contracts(task_id);
CREATE INDEX idx_invoices_task_id ON invoices(task_id);
CREATE INDEX idx_invoices_number ON invoices(invoice_number);
CREATE INDEX idx_audit_results_task_id ON audit_results(task_id);
CREATE INDEX idx_audit_results_severity ON audit_results(severity);
```

## 5. API接口设计

### 5.1 RESTful API规范

#### 5.1.1 文件上传接口
```
POST /api/v1/upload/zip
- 功能: 上传ZIP文件(合同+发票)
- 请求: multipart/form-data
- 响应: task_id, file_list

POST /api/v1/upload/contract
- 功能: 上传单个合同文件
- 请求: multipart/form-data
- 响应: contract_id

POST /api/v1/upload/invoices
- 功能: 批量上传发票文件
- 请求: multipart/form-data
- 响应: invoice_ids[]
```

#### 5.1.2 审计接口
```
POST /api/v1/audit/start
- 功能: 开始审计任务
- 请求: {"task_id": "uuid", "audit_config": {...}}
- 响应: {"audit_id": "uuid", "status": "started"}

GET /api/v1/audit/{audit_id}/status
- 功能: 查询审计状态
- 响应: {"status": "processing", "progress": 45, "current_step": "合同分析"}

GET /api/v1/audit/{audit_id}/results
- 功能: 获取审计结果
- 响应: 完整的审计报告数据
```

#### 5.1.3 WebSocket接口
```
WS /ws/audit/{audit_id}
- 功能: 实时推送审计进度
- 消息格式: {"type": "progress", "data": {...}}
```

### 5.2 响应格式标准
```json
{
  "code": 200,
  "message": "success",
  "data": {...},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 6. 前端详细设计

### 6.1 状态管理 (Pinia)

#### 6.1.1 审计状态管理
```typescript
// stores/audit.ts
export const useAuditStore = defineStore('audit', {
  state: () => ({
    currentTask: null as AuditTask | null,
    auditProgress: 0,
    currentStep: '',
    results: null as AuditResult | null,
    wsConnection: null as WebSocket | null
  }),

  actions: {
    async startAudit(taskId: string) { },
    async getAuditResults(auditId: string) { },
    connectWebSocket(auditId: string) { }
  }
})
```

### 6.2 核心组件设计

#### 6.2.1 文件上传组件
```vue
<!-- components/Upload/ZipUpload.vue -->
<template>
  <el-upload
    class="zip-uploader"
    drag
    :before-upload="beforeUpload"
    :on-success="handleSuccess"
    :on-error="handleError"
    action="/api/v1/upload/zip"
    accept=".zip"
    :limit="1"
  >
    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
    <div class="el-upload__text">
      拖拽ZIP文件到此处或 <em>点击上传</em>
    </div>
    <template #tip>
      <div class="el-upload__tip">
        支持格式：ZIP（包含1份合同和多份发票），大小不超过50MB
      </div>
    </template>
  </el-upload>
</template>
```

#### 6.2.2 进度显示组件
```vue
<!-- components/Progress/AuditProgress.vue -->
<template>
  <div class="audit-progress">
    <el-steps :active="currentStepIndex" finish-status="success">
      <el-step title="文件上传" description="上传合同和发票文件" />
      <el-step title="合同分析" description="AI分析合同内容" />
      <el-step title="发票分析" description="批量处理发票信息" />
      <el-step title="交叉验证" description="合同发票匹配验证" />
      <el-step title="报告生成" description="生成审计报告" />
    </el-steps>

    <el-progress
      :percentage="auditProgress"
      :status="progressStatus"
      :stroke-width="8"
    />
  </div>
</template>
```

### 6.3 路由设计
```typescript
// router/index.ts
const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home/index.vue')
  },
  {
    path: '/audit',
    name: 'Audit',
    component: () => import('@/views/Audit/index.vue'),
    children: [
      {
        path: 'upload',
        name: 'FileUpload',
        component: () => import('@/views/Audit/Upload.vue')
      },
      {
        path: 'processing/:taskId',
        name: 'AuditProcessing',
        component: () => import('@/views/Audit/Processing.vue')
      }
    ]
  },
  {
    path: '/results/:auditId',
    name: 'Results',
    component: () => import('@/views/Results/index.vue')
  }
]
```

## 7. 后端详细设计

### 7.1 FastAPI应用结构

#### 7.1.1 主应用文件
```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import audit, upload, results
from app.core.config import settings

app = FastAPI(title="智能合同发票审计系统", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(audit.router, prefix="/api/v1/audit", tags=["审计"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["上传"])
app.include_router(results.router, prefix="/api/v1/results", tags=["结果"])
```

#### 7.1.2 数据库配置
```python
# core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 7.2 Agent实现设计

#### 7.2.1 协调器Agent
```python
# agents/coordinator.py
from langgraph import Graph, State
from typing import Dict, Any, List
from app.services.ai_service import AIService

class CoordinatorAgent:
    def __init__(self):
        self.ai_service = AIService()
        self.contract_analyzer = ContractAnalyzer()
        self.invoice_analyzer = InvoiceAnalyzer()
        self.cross_validator = CrossValidator()

    async def coordinate_audit(self, task_id: str, files: Dict[str, Any]) -> Dict[str, Any]:
        # 1. 文件验证和分类
        classified_files = await self.classify_files(files)

        # 2. 并行处理合同和发票
        contract_results = await self.contract_analyzer.analyze_contracts(
            classified_files['contracts']
        )
        invoice_results = await self.invoice_analyzer.analyze_invoices(
            classified_files['invoices']
        )

        # 3. 交叉验证
        validation_results = await self.cross_validator.validate(
            contract_results, invoice_results
        )

        # 4. 生成报告
        report = await self.generate_report(
            contract_results, invoice_results, validation_results
        )

        return {
            'task_id': task_id,
            'status': 'completed',
            'report': report
        }
```

#### 7.2.2 合同分析Agent
```python
# agents/contract_analyzer.py
from app.models.contract import Contract
from app.services.ai_service import AIService

class ContractAnalyzer:
    def __init__(self):
        self.ai_service = AIService()

    async def analyze_contracts(self, contract_files: List[str]) -> List[Dict]:
        results = []
        for file_path in contract_files:
            # 使用多模态模型分析合同
            analysis = await self.ai_service.analyze_contract_image(file_path)

            # 提取关键信息
            contract_info = self.extract_contract_info(analysis)

            # 验证和合理性检查
            validation = await self.validate_contract(contract_info)

            results.append({
                'file_path': file_path,
                'extracted_info': contract_info,
                'validation': validation,
                'confidence_score': analysis.get('confidence', 0)
            })

        return results

    def extract_contract_info(self, analysis: Dict) -> Dict:
        # 从AI分析结果中提取结构化信息
        return {
            'contract_number': analysis.get('contract_number'),
            'buyer_name': analysis.get('buyer_name'),
            'seller_name': analysis.get('seller_name'),
            'total_amount': analysis.get('total_amount'),
            'tax_rate': analysis.get('tax_rate'),
            'items': analysis.get('items', []),
            'contract_date': analysis.get('contract_date')
        }
```

### 7.3 任务队列设计

#### 7.3.1 Celery配置
```python
# services/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "audit_system",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
```

#### 7.3.2 异步任务定义
```python
# services/audit_tasks.py
from celery import current_task
from app.services.celery_app import celery_app
from app.agents.coordinator import CoordinatorAgent

@celery_app.task(bind=True)
def audit_task(self, task_id: str, files: Dict[str, Any]):
    try:
        # 更新任务状态
        self.update_state(state='PROGRESS', meta={'progress': 0})

        # 执行审计
        coordinator = CoordinatorAgent()
        result = coordinator.coordinate_audit(task_id, files)

        return result
    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc)}
        )
        raise
```

## 8. 开发计划与TODO

### 8.1 开发阶段划分

#### 阶段1: 基础框架搭建 (第1-2周)
- [x] 项目结构初始化
- [ ] 后端FastAPI基础框架
- [ ] 前端Vue3项目初始化
- [ ] 数据库设计和迁移
- [ ] 基础配置和环境搭建

#### 阶段2: 核心功能开发 (第3-5周)
- [ ] 文件上传功能
- [ ] AI Agent基础框架
- [ ] 合同分析Agent实现
- [ ] 发票分析Agent实现
- [ ] 交叉验证逻辑

#### 阶段3: 前端界面开发 (第6-7周)
- [ ] 文件上传界面
- [ ] 实时进度显示
- [ ] 结果展示页面
- [ ] 数据可视化组件

#### 阶段4: 集成测试与优化 (第8周)
- [ ] 前后端集成测试
- [ ] 性能优化
- [ ] 错误处理完善
- [ ] 文档编写

### 8.2 详细TODO列表

#### 8.2.1 基础设施
- [ ] 创建Python虚拟环境
- [ ] 安装FastAPI、SQLAlchemy、Celery等依赖
- [ ] 创建Vue3项目，安装Element Plus
- [ ] 配置开发环境和热重载
- [ ] 设置ESLint、Prettier代码规范
- [ ] 配置Git hooks和CI/CD

#### 8.2.2 后端开发
- [ ] 实现数据库模型定义
- [ ] 创建数据库迁移脚本
- [ ] 实现文件上传API
- [ ] 实现AI服务调用模块
- [ ] 开发协调器Agent
- [ ] 开发合同分析Agent
- [ ] 开发发票分析Agent
- [ ] 开发交叉验证Agent
- [ ] 实现WebSocket实时通信
- [ ] 添加异常处理和日志记录

#### 8.2.3 前端开发
- [ ] 创建基础布局组件
- [ ] 实现文件拖拽上传
- [ ] 开发进度显示组件
- [ ] 创建结果展示表格
- [ ] 实现图表可视化
- [ ] 添加状态管理
- [ ] 实现路由和页面导航
- [ ] 添加响应式设计

#### 8.2.4 AI模型集成
- [ ] 配置阿里云qwen3-vl-8b-thinking API
- [ ] 配置DeepSeek-V3.2-exp API
- [ ] 实现模型调用封装
- [ ] 设计prompt模板
- [ ] 实现结果解析和结构化
- [ ] 添加API调用失败重试机制

#### 8.2.5 测试和部署
- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 性能测试和优化
- [ ] 安全性检查
- [ ] 部署文档编写
- [ ] 用户手册编写

## 9. 关键技术实现

### 9.1 AI模型调用封装
```python
# services/ai_service.py
import httpx
from typing import Dict, Any
from app.core.config import settings

class AIService:
    def __init__(self):
        self.qwen_client = httpx.AsyncClient(
            base_url=settings.QWEN_API_BASE,
            headers={"Authorization": f"Bearer {settings.QWEN_API_KEY}"}
        )
        self.deepseek_client = httpx.AsyncClient(
            base_url=settings.DEEPSEEK_API_BASE,
            headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"}
        )

    async def analyze_contract_image(self, image_path: str) -> Dict[str, Any]:
        # 使用qwen3-vl进行图像分析
        with open(image_path, 'rb') as f:
            image_data = f.read()

        response = await self.qwen_client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3-vl-8b-thinking",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请分析这份合同图像，提取以下关键信息：合同编号、买卖双方、总金额、税率、商品清单"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64.b64encode(image_data).decode()}"
                                }
                            }
                        ]
                    }
                ]
            }
        )

        return response.json()
```

### 9.2 WebSocket实时通信
```python
# services/websocket_service.py
from fastapi import WebSocket
from typing import Dict, Set
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, audit_id: str):
        await websocket.accept()
        self.active_connections[audit_id] = websocket

    def disconnect(self, audit_id: str):
        if audit_id in self.active_connections:
            del self.active_connections[audit_id]

    async def send_progress(self, audit_id: str, progress_data: Dict):
        if audit_id in self.active_connections:
            websocket = self.active_connections[audit_id]
            await websocket.send_text(json.dumps({
                "type": "progress",
                "data": progress_data
            }))

websocket_manager = WebSocketManager()
```

## 10. 部署和运维

### 10.1 Docker容器化
```dockerfile
# Dockerfile.backend
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Dockerfile.frontend
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
```

### 10.2 docker-compose配置
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/audit_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=audit_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.services.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/audit_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

### 10.3 监控和日志
- 使用Prometheus进行性能监控
- 使用ELK Stack进行日志分析
- 配置健康检查和告警机制

## 11. 安全考虑

### 11.1 数据安全
- 文件上传类型和大小限制
- API密钥安全存储
- 数据传输加密(HTTPS)
- 敏感信息脱敏处理

### 11.2 访问控制
- JWT token认证
- API访问频率限制
- 文件访问权限控制
- 操作日志记录

### 11.3 系统安全
- SQL注入防护
- XSS攻击防护
- CSRF防护
- 文件上传安全检查

---

本开发设计文档为智能合同发票审计系统的完整开发指南，涵盖了从需求分析到部署上线的全过程。开发过程中应严格按照文档执行，确保项目质量和进度。