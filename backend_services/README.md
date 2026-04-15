# Lansee 后端服务 (Backend Services)

## 概述

Lansee 后端服务是对话助手项目的中间层服务，负责处理用户认证、会话管理、API网关、并发控制、数据缓存、GPU资源管理等功能。

## 架构

```
前端 <- HTTP/REST API -> 后端服务 <- HTTP/gRPC -> 算法服务
```

## 功能特性

### 1. 用户认证与授权
- JWT Token认证
- OAuth2密码流
- 权限角色管理
- 密码加密存储

### 2. 会话管理
- 会话生命周期管理
- 会话数据持久化
- 会话状态同步

### 3. LLM API管理
- 多LLM提供商支持
- API密钥管理
- 调用统计与计费
- 模型切换与负载均衡

### 4. 并发管理与任务队列
- 请求限流控制
- 异步任务处理
- 任务优先级管理

### 5. GPU设备管理
- GPU资源监控
- 任务调度分配
- 资源利用率优化

### 6. 对象存储
- 文件上传/下载
- 存储空间管理
- 安全访问控制

### 7. 高频数据缓存
- Redis缓存策略
- 数据预热机制
- 缓存失效策略

### 8. 服务健康检查
- 系统指标监控
- 依赖服务检查
- 自动故障检测

### 9. 后台管理
- 用户管理
- 系统监控
- 配置管理
- 审计日志

## API端点

### 认证相关
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/refresh` - 刷新Token
- `GET /api/v1/auth/me` - 获取当前用户信息

### 用户管理
- `GET /api/v1/users/` - 获取用户列表
- `GET /api/v1/users/{user_id}` - 获取特定用户
- `PUT /api/v1/users/{user_id}` - 更新用户信息
- `DELETE /api/v1/users/{user_id}` - 删除用户

### 会话管理
- `POST /api/v1/sessions/` - 创建会话
- `GET /api/v1/sessions/` - 获取用户会话列表
- `GET /api/v1/sessions/{session_id}` - 获取特定会话
- `PUT /api/v1/sessions/{session_id}` - 更新会话
- `DELETE /api/v1/sessions/{session_id}` - 删除会话

### 聊天相关
- `POST /api/v1/chat/completions` - 聊天完成
- `POST /api/v1/chat/stream` - 流式聊天
- `GET /api/v1/chat/history/{session_id}` - 获取聊天历史

### LLM管理
- `POST /api/v1/llm/chat/completions` - LLM聊天完成
- `GET /api/v1/llm/providers` - 获取提供商列表
- `GET /api/v1/llm/providers/{provider_name}/models` - 获取模型列表
- `GET /api/v1/llm/providers/{provider_name}/health` - 检查提供商健康状态

### 健康检查
- `GET /api/v1/health` - 基本健康检查
- `GET /api/v1/health/system` - 系统健康状态
- `GET /api/v1/health/services` - 服务健康状态
- `GET /api/v1/health/detailed` - 详细健康状态

### 管理员面板
- `GET /api/v1/admin/` - 管理员仪表板
- `GET /api/v1/admin/users` - 用户管理
- `GET /api/v1/admin/system-stats` - 系统统计
- `GET /api/v1/admin/config` - 系统配置

## 环境变量配置

```bash
# 项目配置
PROJECT_NAME=Lansee Backend Services
VERSION=1.0.0
API_V1_STR=/api/v1

# 安全配置
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_REFRESH_SECRET_KEY=your-jwt-refresh-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/dbname

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 算法服务配置
ALGORITHM_SERVICE_URL=http://127.0.0.1:6732

# 对象存储配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
STORAGE_BUCKET_NAME=lansee-chatbot
```

## 启动服务

### 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python run_server.py --host 0.0.0.0 --port 3002 --reload
```

## 默认登录账号

- **用户名**: admin
- **密码**: admin123

> 注意: 首次启动时，系统会自动创建此默认管理员账户。

### Docker部署
```bash
# 构建镜像
docker build -t lansee-backend-services .

# 运行容器
docker run -d -p 3002:3002 --env-file .env lansee-backend-services
```

## 依赖

- Python 3.8+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- MinIO
- Celery (可选)

## 测试

```bash
# 运行测试
pytest tests/
```

## 安全考虑

- HTTPS强制使用
- CORS策略配置
- SQL注入防护
- XSS攻击防护
- 请求频率限制
- 敏感数据加密