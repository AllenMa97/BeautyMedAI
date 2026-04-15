#!/bin/bash
# FastAPI 服务管理脚本（支持start/stop/restart/debug四模式）
# debug模式：前台运行、实时看日志、保留--reload热重载，适配开发调试
# start模式：后台运行、日志重定向、禁用--reload，适配生产环境

# ===================== 核心配置（无需修改）=====================
export PYTHONPATH=/home/allen/lansee_chatbot
HOST=0.0.0.0
PORT=6732
PROJECT_DIR=/home/allen/lansee_chatbot/algorithm_services
LOG_FILE=/home/allen/lansee_chatbot/logs/fastapi_service.log
ERROR_LOG_FILE=/home/allen/lansee_chatbot/logs/fastapi_service_err.log
# =============================================================================

# 检查端口占用并获取PID
get_pid() {
    lsof -i:${PORT} -t
}

# 生产启动：nohup后台运行、日志重定向、禁用--reload
start() {
    PID=$(get_pid)
    if [ -n "${PID}" ]; then
        echo "❌ FastAPI服务已在运行，端口${PORT}，PID：${PID}"
        exit 1
    fi

    cd ${PROJECT_DIR} || { echo "❌ 项目目录不存在：${PROJECT_DIR}"; exit 1; }
    echo "✅ 【生产模式】开始启动FastAPI服务，端口：${PORT}"
    echo "📜 日志文件：${LOG_FILE}，错误日志：${ERROR_LOG_FILE}"
    echo "🔗 访问文档：http://你的LinuxIP:${PORT}/docs"

    nohup python -m uvicorn main:app --host ${HOST} --port ${PORT} \
        > ${LOG_FILE} 2> ${ERROR_LOG_FILE} &

    sleep 2
    PID=$(get_pid)
    if [ -n "${PID}" ]; then
        echo "🎉 FastAPI服务启动成功，PID：${PID}"
    else
        echo "❌ FastAPI服务启动失败，请查看错误日志：${ERROR_LOG_FILE}"
    fi
}

# 停止服务（通用：兼容start/debug模式的进程停止）
stop() {
    PID=$(get_pid)
    if [ -z "${PID}" ]; then
        echo "❌ FastAPI服务未运行，端口${PORT}无占用"
        exit 1
    fi

    echo "⚡ 正在停止FastAPI服务，PID：${PID}"
    kill ${PID}
    sleep 2

    PID=$(get_pid)
    if [ -z "${PID}" ]; then
        echo "✅ FastAPI服务已成功停止"
    else
        echo "⚠️  优雅停止失败，强制杀死进程PID：${PID}"
        kill -9 ${PID}
        sleep 1
        PID=$(get_pid)
        [ -z "${PID}" ] && echo "✅ FastAPI服务强制停止成功" || echo "❌ 进程杀死失败"
    fi
}

# 重启服务：生产模式专用
restart() {
    echo "🔄 正在重启FastAPI【生产模式】服务..."
    stop
    start
}

# 新增：调试模式 - 前台运行、实时日志、保留--reload热重载
debug() {
    PID=$(get_pid)
    if [ -n "${PID}" ]; then
        echo "❌ 端口${PORT}已被占用，PID：${PID}，请先执行 $0 stop 释放端口"
        exit 1
    fi

    cd ${PROJECT_DIR} || { echo "❌ 项目目录不存在：${PROJECT_DIR}"; exit 1; }
    echo -e "📌 【调试模式】启动FastAPI服务，特性：\n  1. 前台运行，SSH终端实时查看logger.info/报错日志\n  2. 保留--reload，代码修改自动热重载\n  3. 关闭终端/按Ctrl+C即停止服务"
    echo "🔗 访问文档：http://你的LinuxIP:${PORT}/docs"
    echo "⚠️  退出调试模式请按：Ctrl + C"
    echo "=============================================================="

    # 调试核心命令：无nohup、无&、保留--reload，日志直接输出到SSH终端
    python -m uvicorn main:app --reload --host ${HOST} --port ${PORT}
}

# 脚本使用说明（更新四模式）
usage() {
    echo "==================== FastAPI服务管理脚本 ===================="
    echo "使用方法：$0 [start|stop|restart|debug]"
    echo "模式说明："
    echo "  $0 start   # 生产模式：后台运行、日志重定向、禁用热重载"
    echo "  $0 stop    # 通用停止：终止任意模式的服务进程"
    echo "  $0 restart # 生产重启：先停止再启动生产模式"
    echo "  $0 debug   # 调试模式：前台运行、实时日志、保留热重载"
    echo "=============================================================="
    exit 1
}

# 主逻辑：判断传入参数
if [ $# -ne 1 ]; then
    usage
fi

case $1 in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    debug)
        debug
        ;;
    *)
        echo "❌ 无效参数：$1"
        usage
        ;;
esac