# 后端服务架构设计方案

## 1. 整体架构概述

```
前端 <- HTTP/REST API -> 后端服务 <- HTTP/gRPC -> 算法服务
```

后端服务将作为中间层，承担以下职责：
- 用户认证与授权
- 会话管理
- API网关与路由
- 并发控制与任务队列
- 数据缓存
- GPU资源管理
- 服务监控与健康检查

## 2. 技术栈选择

- **框架**: FastAPI (高性能，类型提示，自动生成API文档)
- **数据库**: SQLAlchemy + PostgreSQL (主数据存储)
- **缓存**: Redis (高频数据缓存、会话存储)
- **消息队列**: Celery + Redis/RabbitMQ (异步任务处理)
- **认证**: JWT + OAuth2
- **对象存储**: MinIO 或 AWS S3 (文件上传下载)
- **监控**: Prometheus + Grafana (服务监控)

## 3. 项目结构

```
backend_services/
├── app/
│   ├── __init__.py
│   ├── main.py                 # 应用入口
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 配置管理
│   │   ├── security.py         # 安全认证
│   │   ├── database.py         # 数据库连接
│   │   └── cache.py            # 缓存配置
│   ├── api/                    # API路由
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # 认证API
│   │   │   ├── users.py        # 用户管理
│   │   │   ├── sessions.py     # 会话管理
│   │   │   ├── chat.py         # 聊天API
│   │   │   ├── llm.py          # LLM管理API
│   │   │   └── admin.py        # 管理员API
│   ├── models/                 # 数据模型
│   │   ├── user.py             # 用户模型
│   │   ├── session.py          # 会话模型
│   │   ├── message.py          # 消息模型
│   │   └── base.py             # 基础模型
│   ├── schemas/                # Pydantic模型
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── message.py
│   │   └── auth.py
│   ├── services/               # 业务逻辑
│   │   ├── auth_service.py     # 认证服务
│   │   ├── user_service.py     # 用户服务
│   │   ├── session_service.py  # 会话服务
│   │   ├── llm_service.py      # LLM服务
│   │   └── queue_service.py    # 队列服务
│   ├── utils/                  # 工具函数
│   │   ├── jwt_utils.py        # JWT工具
│   │   ├── redis_utils.py      # Redis工具
│   │   ├── validators.py       # 验证器
│   │   └── helpers.py          # 辅助函数
│   ├── workers/                # 异步任务处理器
│   │   ├── celery_app.py       # Celery应用
│   │   ├── tasks.py            # 任务定义
│   │   └── gpu_manager.py      # GPU管理
│   └── middleware/             # 中间件
│       ├── auth_middleware.py  # 认证中间件
│       ├── rate_limit.py       # 限流中间件
│       └── logging.py          # 日志中间件
├── migrations/                 # 数据库迁移
├── tests/                      # 测试文件
├── config/                     # 配置文件
│   ├── settings.py             # 设置
│   └── env.example            # 环境变量示例
├── requirements.txt            # 依赖包
└── Dockerfile                  # 容器化配置
```

## 4. 核心功能模块设计

### 4.1 用户认证与授权模块
- JWT Token认证
- OAuth2密码流
- 权限角色管理
- 密码加密存储
- Token刷新机制

### 4.2 会话管理模块
- 会话生命周期管理
- 会话数据持久化
- 会话状态同步
- 会话清理策略

### 4.3 LLM API管理模块
- LLM提供商抽象层
- API密钥管理
- 调用统计与计费
- 模型切换与负载均衡

### 4.4 并发管理与任务队列
- 请求限流控制
- 异步任务处理
- 任务优先级管理
- 批量处理支持

### 4.5 GPU设备管理
- GPU资源监控
- 任务调度分配
- 资源利用率优化
- 故障转移机制

### 4.6 对象存储模块
- 文件上传/下载
- 存储空间管理
- 文件类型验证
- 安全访问控制

### 4.7 高频数据缓存
- Redis缓存策略
- 数据预热机制
- 缓存失效策略
- 性能优化

### 4.8 服务健康检查
- 系统指标监控
- 依赖服务检查
- 自动故障检测
- 告警通知机制

## 5. API设计规范

### 5.1 认证API
```
POST /api/v1/auth/login          # 用户登录
POST /api/v1/auth/register       # 用户注册
POST /api/v1/auth/refresh        # 刷新Token
GET  /api/v1/auth/me             # 获取当前用户信息
```

### 5.2 会话API
```
GET    /api/v1/sessions          # 获取会话列表
POST   /api/v1/sessions          # 创建新会话
GET    /api/v1/sessions/{id}     # 获取特定会话
PUT    /api/v1/sessions/{id}     # 更新会话
DELETE /api/v1/sessions/{id}     # 删除会话
```

### 5.3 聊天API
```
POST /api/v1/chat/completions    # 聊天完成
POST /api/v1/chat/stream         # 流式聊天
```

### 5.4 管理API
```
GET    /api/v1/admin/users        # 用户管理
GET    /api/v1/admin/sessions     # 会话管理
GET    /api/v1/admin/stats        # 统计信息
GET    /api/v1/admin/health       # 健康检查
```

## 6. 数据库设计

### 6.1 用户表 (users)
- id: UUID
- username: VARCHAR
- email: VARCHAR
- hashed_password: VARCHAR
- role: ENUM
- is_active: BOOLEAN
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

### 6.2 会话表 (sessions)
- id: UUID
- user_id: UUID (外键)
- title: VARCHAR
- metadata: JSONB
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

### 6.3 消息表 (messages)
- id: UUID
- session_id: UUID (外键)
- role: ENUM (user/assistant/system)
- content: TEXT
- tokens: INTEGER
- created_at: TIMESTAMP

## 7. 部署架构

- 负载均衡器 (Nginx/HAProxy)
- 多个后端服务实例
- 数据库集群 (PostgreSQL)
- 缓存集群 (Redis)
- 消息队列 (Celery Workers)
- 监控系统 (Prometheus/Grafana)

## 8. 安全考虑

- HTTPS强制使用
- CORS策略配置
- SQL注入防护
- XSS攻击防护
- 请求频率限制
- 敏感数据加密