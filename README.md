# Lansee 对话助手平台

## 项目概述

Lansee 对话助手平台是一个完整的AI对话系统，别名是YISIA，包含前端界面、后端服务和算法服务三个主要组件。

## 架构设计

```
前端界面 <- HTTP/REST API -> 后端服务 <- HTTP/gRPC -> 算法服务
```

## 系统流程图

### 核心路由与规划流程

```
用户输入 (user_input)
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  步骤1: 快速短路检测 (词表匹配)                                    │
│  检测简单问候/确认/感谢等 → is_simple = True                       │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  步骤2: 路由决策 (routing_decision_service)                       │
│  输出: need_plan (是否需要规划), need_search (是否需要搜索)         │
│  同时启动: 内容违规检测 (异步并行)                                  │
└─────────────────────────────────────────────────────────────────┘
    │
    ├── need_plan = False ────────────────────┐
    │                                          ▼
    │                              ┌─────────────────────┐
    │                              │  free_chat (兜底)   │
    │                              │  直接闲聊回复        │
    │                              └─────────────────────┘
    │
    └── need_plan = True ─────────────────────┐
                                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  步骤3: 功能规划 (planner)                                        │
│  Planner 决定调用哪些功能:                                        │
│  - knowledge_retrieval: 知识检索 (医美/产品/成分/功效)              │
│  - product_recommendation: 产品推荐                               │
│  - entity_recognize: 实体识别                                     │
│  - intent_clarify: 意图澄清                                       │
│  - 空调用: 不需要任何功能                                          │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  步骤4: 执行功能 (function_executer_service)                      │
│  按顺序执行 planner 规划的功能                                     │
│  结果存入 session.intermediate_results                           │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  步骤5: 自动选择 Chat 方式                                        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  判断: 是否有 knowledge_retrieval 结果?                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│      │                                                           │
│      ├── 有结果 ────────────────────────────────┐               │
│      │                                          ▼               │
│      │                              ┌─────────────────────┐     │
│      │                              │  knowledge_chat     │     │
│      │                              │  基于知识生成回答    │     │
│      │                              └─────────────────────┘     │
│      │                                                           │
│      └── 无结果 ────────────────────────────────┐               │
│                                                 ▼               │
│                                    ┌─────────────────────┐      │
│                                    │  free_chat (兜底)   │      │
│                                    │  通用闲聊回复       │      │
│                                    └─────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  步骤6: 返回结果 (流式输出)                                       │
│  SSE 流式返回 chat_response                                      │
│  异步更新 session 历史                                           │
└─────────────────────────────────────────────────────────────────┘
```

### 职责划分

| 服务 | 职责 |
|------|------|
| routing_decision_service | 快速分流: need_plan, need_search |
| planner | 功能规划: 决定调用哪些功能 |
| function_executer_service | 执行功能: 按顺序执行规划的功能 |
| 自动路由 (步骤5) | 根据 knowledge_retrieval 结果选择 chat |

### 关键设计原则

1. **知识检索 → 知识问答** - 有 knowledge_retrieval 结果用 knowledge_chat，无结果用 free_chat
2. **异步并行** - 内容违规检测与规划流程并行执行，不阻塞主流程
3. **快速路径** - 简单问题 (need_plan=False) 直接走 free_chat，跳过 planner 调用

## 项目结构

```
lansee_chatbot/
├── algorithm_services/     # 算法服务 (现有)
├── frontend_services/      # 前端服务 (现有 + 增强版)
├── backend_services/       # 后端服务 (新增)
└── management_console/     # 管理控制台 (新增)
```

## 组件说明

### 1. 算法服务 (algorithm_services)
- 基于FastAPI的AI算法服务
- 提供多种AI功能（对话摘要、实体识别、意图识别等）
- 集成多个LLM提供商

### 2. 前端服务 (frontend_services)
- 基于HTML/CSS/JavaScript的对话界面
- 提供用户友好的交互体验
- 支持流式响应显示
- **新增功能**：
  - 会话管理（新建、切换、导出）
  - 会话摘要生成功能
  - 增强的文件上传和预览
  - 主题切换和多语言支持
  - 产品图轮播展示

### 3. 后端服务 (backend_services) - [NEW]
- **用户认证与授权**
  - JWT Token认证
  - OAuth2密码流
  - 权限角色管理
- **会话管理**
  - 会话生命周期管理
  - 会话数据持久化
  - 消息历史记录
  - **新增功能**：
    - 会话摘要生成功能
    - 会话分享功能
    - 会话导出（JSON、TXT、MD格式）
- **LLM API管理**
  - 多提供商支持
  - API密钥管理
  - 调用统计与监控
- **并发管理与任务队列**
  - 异步任务处理
  - 并发控制
  - 任务调度
- **GPU设备管理**
  - GPU资源监控
  - 任务分配
  - 利用率统计
  - 完善的任务优先级和资源分配逻辑
- **对象存储**
  - 本地存储支持
  - AWS S3兼容
  - MinIO支持
  - 统一存储接口
- **高频数据缓存**
  - Redis集成
  - 缓存策略
  - 数据预热
- **服务健康检查**
  - 系统监控
  - 服务状态检查
  - 性能指标
- **后台管理API**
  - 用户管理
  - 系统配置
  - 审计日志
- **PostgreSQL数据库**
  - 完整的表结构设计
  - 用户、会话、消息表
  - RAG相关表（文档、知识库、查询日志等）
  - 资源管理表（模型、数据集、文件等）
  - 数据库迁移脚本
- **RAG模块支持**
  - 文档管理
  - 知识库管理
  - 向量检索
  - 查询日志
- **外部存储集成**
  - OSS/S3等云存储支持
  - 资源文件管理
  - 访问日志记录
- **资源管理API**
  - 资源文件上传/下载
  - 资源类别管理
  - 模型管理
  - 数据集管理
  - GPU状态监控

## 部署指南

### 一键部署（推荐）
```bash
# Linux/macOS
chmod +x deploy_all.sh
./deploy_all.sh

# Windows
deploy_all.bat
```

### 一键启动所有服务
```bash
# Linux/macOS
chmod +x start_all_services.sh
./start_all_services.sh

# Windows
start_all_services.bat
```

### 服务管理
```bash
# 检查服务状态 (Linux/macOS)
./check_services.sh

# 检查服务状态 (Windows)
check_services.bat

# 偲止所有服务 (Windows)
stop_all_services.bat

# 服务管理脚本 (Linux/macOS)
chmod +x service_manager.sh
./service_manager.sh

# 服务管理脚本 (Windows)
service_manager.bat
```

## 服务管理脚本功能

### Linux/macOS 服务管理
```bash
# 启动所有服务
./service_manager.sh start

# 偲止所有服务
./service_manager.sh stop

# 重启所有服务
./service_manager.sh restart

# 检查服务状态
./service_manager.sh status

# 查看日志
./service_manager.sh logs all 50  # 查看所有服务最近50行日志
./service_manager.sh logs backend 20  # 查看后端服务最近20行日志
```

### Windows 服务管理
运行 `service_manager.bat` 启动交互式服务管理界面，提供以下功能：
- 启动/停止/重启所有服务
- 单独管理每个服务
- 检查服务状态
- 查看服务日志

### 手动部署

#### 1. 算法服务
```bash
cd algorithm_services
pip install -r requirements.txt  # 需要创建
uvicorn main:app --host 0.0.0.0 --port 6732
```

#### 2. 后端服务
```bash
cd backend_services
# Windows
deploy.bat

# Linux/macOS
chmod +x deploy.sh
./deploy.sh
```

或者⼿动部署：
```bash
cd backend_services
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
python run_server.py --host 0.0.0.0 --port 3002
```

#### 3. 管理控制台
```bash
cd management_console

# 开发模式启动（使用3003端口）
npm install
npm run dev -- --port 3003

# 生产构建
npm run build
# 部署 dist 目录到Web服务器

# Windows启动脚本
start_dev.bat

# Linux启动脚本
chmod +x start_dev.sh
./start_dev.sh

# 构建生产版本 (Windows)
build_prod.bat

# 构建生产版本 (Linux)
chmod +x build_prod.sh
./build_prod.sh
```

#### 4. 前端服务
```bash
cd frontend_services
# 启动前端服务（使用3001端口）
node server.js --port 3001

# 或使用增强版: enhanced_index.html
```

## 环境配置

### 后端服务配置 (.env)
```env
# 项目配置
PROJECT_NAME=Lansee Backend Services
VERSION=1.0.0
API_V1_STR=/api/v1

# 安全配置
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_REFRESH_SECRET_KEY=your-jwt-refresh-secret-key-here

# PostgreSQL数据库配置
DATABASE_URL=postgresql://user:password@localhost/dbname

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 算法服务配置
ALGORITHM_SERVICE_URL=http://127.0.0.1:6732

# 对象存储配置
STORAGE_TYPE=minio  # local, s3, minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
STORAGE_BUCKET_NAME=lansee-chatbot

# RAG配置
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.7
RAG_SEARCH_STRATEGY=hybrid
```

### 管理控制台配置 (.env)
```env
REACT_APP_API_BASE_URL=http://localhost:3002/api/v1
```

## API端点

### 后端服务API
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/register` - 用户注册
- `GET /api/v1/chat/completions` - 聊天完成
- `GET /api/v1/sessions/` - 会话管理
- `GET /api/v1/sessions/{session_id}/summary` - 会话摘要
- `GET /api/v1/sessions/{session_id}/export` - 导出会话
- `GET /api/v1/resources/files` - 资源文件管理
- `GET /api/v1/resources/categories` - 资源类别管理
- `GET /api/v1/resources/gpu-status` - GPU状态
- `GET /api/v1/admin/users` - 用户管理 (管理员)
- `GET /api/v1/health` - 偡康检查

## 安全考虑

- HTTPS强制使用
- CORS策略配置
- SQL注入防护
- XSS攻击防护
- 请求频率限制
- 敏感数据加密
- JWT Token管理

## 扩展性

- 微服务架构设计
- 模块化组件
- 插件化扩展
- 水平扩展支持
- RAG模块支持
- 多存储后端支持

## 技术栈

### 后端服务
- Python 3.8+
- FastAPI
- SQLAlchemy + PostgreSQL
- Alembic (数据库迁移)
- Redis
- Celery
- pgvector (向量搜索)

### 管理控制台
- React 18
- Material-UI
- React Router
- Axios
- Recharts

### 前端服务
- HTML/CSS/JavaScript
- Marked (Markdown渲染)
- Highlight.js (代码高亮)

## 维护和支持

- 详细的API文档
- 完整的错误处理
- 日志记录
- 性能监控
- 偡康检查
- 数据库迁移脚本
- 部署脚本
- 服务启停脚本

## 许可证

MIT License