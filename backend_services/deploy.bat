@echo off
REM Lansee Backend Services Windows 部署脚本

echo ===========================================
echo Lansee Backend Services Windows 部署脚本
echo ===========================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python。请先安装Python 3.8或更高版本。
    pause
    exit /b 1
)

REM 检查pip是否安装
pip --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到pip。
    pause
    exit /b 1
)

REM 设置变量
set PROJECT_DIR=%~dp0
set ENV_FILE=%PROJECT_DIR%.env
set VENV_DIR=%PROJECT_DIR%venv

echo 项目目录: %PROJECT_DIR%

REM 1. 创建虚拟环境
echo.
echo 步骤 1: 创建Python虚拟环境...
if not exist "%VENV_DIR%" (
    python -m venv "%VENV_DIR%"
    echo 虚拟环境已创建: %VENV_DIR%
) else (
    echo 虚拟环境已存在: %VENV_DIR%
)

REM 激活虚拟环境
call "%VENV_DIR%\Scripts\activate.bat"

REM 2. 安装依赖
echo.
echo 步骤 2: 安装Python依赖...
python -m pip install --upgrade pip
pip install -r "%PROJECT_DIR%requirements.txt"

REM 3. 检查并创建环境配置文件
echo.
echo 步骤 3: 检查环境配置...

if not exist "%ENV_FILE%" (
    echo 创建默认环境配置文件...
    echo. > "%ENV_FILE%"
    echo # Lansee Backend Services 环境配置文件 >> "%ENV_FILE%"
    echo. >> "%ENV_FILE%"
    echo # 项目配置 >> "%ENV_FILE%"
    echo PROJECT_NAME=Lansee Backend Services >> "%ENV_FILE%"
    echo VERSION=1.0.0 >> "%ENV_FILE%"
    echo API_V1_STR=/api/v1 >> "%ENV_FILE%"
    echo. >> "%ENV_FILE%"
    echo # 安全配置 - 请在生产环境中更换为安全的密钥 >> "%ENV_FILE%"
    echo SECRET_KEY=change_this_to_a_secure_random_string_for_production >> "%ENV_FILE%"
    echo JWT_SECRET_KEY=change_this_to_a_secure_random_string_for_jwt >> "%ENV_FILE%"
    echo JWT_REFRESH_SECRET_KEY=change_this_to_a_secure_random_string_for_jwt_refresh >> "%ENV_FILE%"
    echo ALGORITHM=HS256 >> "%ENV_FILE%"
    echo ACCESS_TOKEN_EXPIRE_MINUTES=30 >> "%ENV_FILE%"
    echo REFRESH_TOKEN_EXPIRE_DAYS=7 >> "%ENV_FILE%"
    echo. >> "%ENV_FILE%"
    echo # PostgreSQL数据库配置 >> "%ENV_FILE%"
    echo DATABASE_URL=postgresql://lansee_user:lansee_pass@localhost/lansee_db >> "%ENV_FILE%"
    echo. >> "%ENV_FILE%"
    echo # Redis配置 >> "%ENV_FILE%"
    echo REDIS_URL=redis://localhost:6379/0 >> "%ENV_FILE%"
    echo. >> "%ENV_FILE%"
    echo # 算法服务配置 >> "%ENV_FILE%"
    echo ALGORITHM_SERVICE_URL=http://127.0.0.1:6732 >> "%ENV_FILE%"
    echo. >> "%ENV_FILE%"
    echo # CORS配置 >> "%ENV_FILE%"
    echo BACKEND_CORS_ORIGINS=["http://localhost", "http://localhost:3000", "http://127.0.0.1:3000"] >> "%ENV_FILE%"
    echo. >> "%ENV_FILE%"
    echo # 速率限制 >> "%ENV_FILE%"
    echo RATE_LIMIT_REQUESTS=100 >> "%ENV_FILE%"
    echo RATE_LIMIT_WINDOW=60 >> "%ENV_FILE%"
    echo. >> "%ENV_FILE%"
    echo # 会话超时 >> "%ENV_FILE%"
    echo SESSION_TIMEOUT_HOURS=24 >> "%ENV_FILE%"
    echo. >> "%ENV_FILE%"
    echo # 对象存储配置 >> "%ENV_FILE%"
    echo STORAGE_TYPE=minio  >> "%ENV_FILE%"
    echo MINIO_ENDPOINT=localhost:9000 >> "%ENV_FILE%"
    echo MINIO_ACCESS_KEY=minioadmin >> "%ENV_FILE%"
    echo MINIO_SECRET_KEY=minioadmin >> "%ENV_FILE%"
    echo MINIO_SECURE=false >> "%ENV_FILE%"
    echo STORAGE_BUCKET_NAME=lansee-chatbot >> "%ENV_FILE%"
    echo. >> "%ENV_FILE%"
    echo # RAG配置 >> "%ENV_FILE%"
    echo RAG_TOP_K=5 >> "%ENV_FILE%"
    echo RAG_SIMILARITY_THRESHOLD=0.7 >> "%ENV_FILE%"
    echo RAG_SEARCH_STRATEGY=hybrid >> "%ENV_FILE%"
    echo. >> "%ENV_FILE%"
    echo # GPU配置 >> "%ENV_FILE%"
    echo ENABLE_GPU_MANAGEMENT=false >> "%ENV_FILE%"
    echo MAX_CONCURRENT_GPU_TASKS=4 >> "%ENV_FILE%"
    echo. >> "%ENV_FILE%"
    echo # 系统资源限制 >> "%ENV_FILE%"
    echo MAX_UPLOAD_SIZE=50 >> "%ENV_FILE%"
    echo MAX_SESSION_MESSAGES=1000 >> "%ENV_FILE%"
    echo.
    echo 已创建默认环境配置文件: %ENV_FILE%
    echo 请根据您的环境修改配置文件
)

REM 4. 初始化数据库
echo.
echo 步骤 4: 初始化数据库...
python "%PROJECT_DIR%init_db.py"

REM 5. 运行数据库迁移（如果使用Alembic）
echo.
echo 步骤 5: 运行数据库迁移...
REM alembic revision --autogenerate -m "Initial migration"
REM alembic upgrade head

REM 6. 准备服务
echo.
echo 步骤 6: 准备服务...

echo.
echo ===========================================
echo 部署完成!
echo ===========================================
echo.
echo 要启动服务，请运行:
echo   cd %PROJECT_DIR%
echo   call %VENV_DIR%\Scripts\activate.bat
echo   python run_server.py --host 0.0.0.0 --port 8000
echo.
echo 或者使用uvicorn直接启动:
echo   cd %PROJECT_DIR%
echo   call %VENV_DIR%\Scripts\activate.bat
echo   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
echo.
echo API文档地址: http://0.0.0.0:8000/api/v1/docs
echo.
echo 注意: 请确保以下服务正在运行:
echo - PostgreSQL 数据库
echo - Redis 服务（如果使用缓存）
echo - MinIO/S3 服务（如果使用对象存储）
echo - 算法服务（algorithm_services）
echo.

REM 询问是否立即启动服务
set /p start_now="是否立即启动服务? (y/n): "
if /i "%start_now%"=="y" (
    echo 启动服务...
    python "%PROJECT_DIR%run_server.py" --host 0.0.0.0 --port 8000
)

pause