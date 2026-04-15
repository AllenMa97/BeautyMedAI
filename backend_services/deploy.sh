#!/bin/bash
# Lansee Backend Services 部署脚本

set -e  # 遇到错误时停止执行

echo "==========================================="
echo "Lansee Backend Services 部署脚本"
echo "==========================================="

# 检查是否以root权限运行（如果需要）
if [[ $EUID -eq 0 ]]; then
   echo "警告: 请勿以root用户运行此脚本" 
   exit 1
fi

# 检查必需的命令
command -v python3 >/dev/null 2>&1 || { echo >&2 "需要安装python3，但未找到。中止。"; exit 1; }
command -v pip >/dev/null 2>&1 || { echo >&2 "需要安装pip，但未找到。中止。"; exit 1; }

# 设置变量
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$PROJECT_DIR/.env"
VENV_DIR="$PROJECT_DIR/venv"

echo "项目目录: $PROJECT_DIR"

# 1. 创建虚拟环境
echo ""
echo "步骤 1: 创建Python虚拟环境..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "虚拟环境已创建: $VENV_DIR"
else
    echo "虚拟环境已存在: $VENV_DIR"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 2. 安装依赖
echo ""
echo "步骤 2: 安装Python依赖..."
pip install --upgrade pip
pip install -r "$PROJECT_DIR/requirements.txt"

# 3. 检查并创建环境配置文件
echo ""
echo "步骤 3: 检查环境配置..."

if [ ! -f "$ENV_FILE" ]; then
    echo "创建默认环境配置文件..."
    cat > "$ENV_FILE" << EOF
# Lansee Backend Services 环境配置文件

# 项目配置
PROJECT_NAME=Lansee Backend Services
VERSION=1.0.0
API_V1_STR=/api/v1

# 安全配置 - 请在生产环境中更换为安全的密钥
SECRET_KEY=change_this_to_a_secure_random_string_for_production
JWT_SECRET_KEY=change_this_to_a_secure_random_string_for_jwt
JWT_REFRESH_SECRET_KEY=change_this_to_a_secure_random_string_for_jwt_refresh
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# PostgreSQL数据库配置
DATABASE_URL=postgresql://lansee_user:lansee_pass@localhost/lansee_db

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 算法服务配置
ALGORITHM_SERVICE_URL=http://127.0.0.1:6732

# CORS配置
BACKEND_CORS_ORIGINS=["http://localhost", "http://localhost:3000", "http://127.0.0.1:3000"]

# 速率限制
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# 会话超时
SESSION_TIMEOUT_HOURS=24

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

# GPU配置
ENABLE_GPU_MANAGEMENT=false
MAX_CONCURRENT_GPU_TASKS=4

# 系统资源限制
MAX_UPLOAD_SIZE=50
MAX_SESSION_MESSAGES=1000
EOF
    echo "已创建默认环境配置文件: $ENV_FILE"
    echo "请根据您的环境修改配置文件"
fi

# 4. 初始化数据库
echo ""
echo "步骤 4: 初始化数据库..."
python "$PROJECT_DIR/init_db.py"

# 5. 运行数据库迁移（如果使用Alembic）
echo ""
echo "步骤 5: 运行数据库迁移..."
# alembic revision --autogenerate -m "Initial migration"
# alembic upgrade head

# 6. 收集静态文件（如果有）
echo ""
echo "步骤 6: 准备服务..."

# 7. 启动服务
echo ""
echo "==========================================="
echo "部署完成!"
echo "==========================================="
echo ""
echo "要启动服务，请运行:"
echo "  cd $PROJECT_DIR"
echo "  source $VENV_DIR/bin/activate"
echo "  python run_server.py --host 0.0.0.0 --port 8000"
echo ""
echo "或者使用uvicorn直接启动:"
echo "  cd $PROJECT_DIR"
echo "  source $VENV_DIR/bin/activate"
echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "API文档地址: http://0.0.0.0:8000/api/v1/docs"
echo ""
echo "注意: 请确保以下服务正在运行:"
echo "- PostgreSQL 数据库"
echo "- Redis 服务（如果使用缓存）"
echo "- MinIO/S3 服务（如果使用对象存储）"
echo "- 算法服务（algorithm_services）"
echo ""

# 询问是否立即启动服务
read -p "是否立即启动服务? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "启动服务..."
    python "$PROJECT_DIR/run_server.py" --host 0.0.0.0 --port 8000
fi