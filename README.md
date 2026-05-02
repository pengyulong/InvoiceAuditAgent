# 智能合同发票审计系统

## 项目结构

```
InvoiceAuditAgent/
├── frontend/                 # Vue3前端应用
│   ├── src/
│   │   ├── components/      # 可复用组件
│   │   ├── views/          # 页面视图
│   │   ├── stores/         # Pinia状态管理
│   │   ├── services/       # API服务
│   │   ├── utils/          # 工具函数
│   │   ├── types/          # TypeScript类型定义
│   │   └── assets/         # 静态资源
│   ├── public/             # 公共资源
│   └── tests/              # 前端测试
├── backend/                  # Python FastAPI后端
│   ├── app/
│   │   ├── api/v1/         # API路由
│   │   ├── core/           # 核心配置
│   │   ├── services/       # 业务逻辑
│   │   ├── agents/         # AI智能体
│   │   ├── models/         # 数据模型
│   │   └── utils/          # 工具函数
│   ├── tests/              # 后端测试
│   └── scripts/            # 部署脚本
├── docs/                    # 项目文档
├── tests/                   # 集成测试
└── scripts/                 # 项目脚本
```

## 开发阶段

### ✅ 已完成
- [x] 需求分析和技术架构设计
- [x] 项目目录结构创建

### 🚧 进行中
- [ ] UI/UX原型设计（Figma）
- [ ] 前端Vue3项目初始化
- [ ] 后端FastAPI项目初始化

### 📋 待完成
- [ ] 核心功能开发
- [ ] AI模型集成
- [ ] 测试用例编写
- [ ] UAT/SIT测试
- [ ] 部署和文档

## 技术栈

### 前端
- **框架**: Vue 3 + TypeScript
- **UI库**: Element Plus
- **状态管理**: Pinia
- **构建工具**: Vite
- **样式**: Tailwind CSS

### 后端
- **框架**: FastAPI + Python 3.9+
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **缓存**: Redis
- **任务队列**: Celery
- **AI模型**: 阿里云qwen3-vl + DeepSeek-V3.2

### 核心功能
1. 文件上传和管理
2. AI智能分析合同和发票
3. 交叉验证和匹配
4. 审计报告生成
5. 实时进度追踪