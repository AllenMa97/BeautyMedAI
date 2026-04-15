import json
import logging
import os
from logging.handlers import TimedRotatingFileHandler

import platform

def setup_logging(project_name, service_name="ai-backend"):
    """
    设置日志记录器。

    :param project_name: 项目名称，用于确定日志文件存储的目录
    :param service_name: 服务名称，默认为 "ai-backend"，用于指定日志记录器的名称和日志文件名
    :return: 配置好的日志记录器对象
    """
    # 定义日志文件存储的目录路径
    # 根据操作系统动态生成日志目录
    if platform.system() == "Windows": 
        # 本地测试保存路径 - 改为服务专属目录
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 拼接项目文件夹下的 logs 目录
        log_dir = os.path.join(current_dir, 'logs', project_name)
    else:
        log_dir = f"/var/log/aiiiin/{project_name}"

    # 创建日志目录，如果目录已存在则不会报错
    os.makedirs(log_dir, exist_ok=True)
    
    # 拼接日志文件的完整路径
    log_file = os.path.join(log_dir, f"{service_name}.log")
    
    # 获取指定名称的日志记录器
    logger = logging.getLogger(service_name)
    # 设置日志记录器的日志级别为 INFO
    logger.setLevel(logging.INFO)
    
    # 如果服务名称为 "ai-backend"
    if service_name == "ai-backend":
        # 定义日志消息的格式化字符串，包含时间戳、日志级别、服务名称、消息内容和上下文信息
        formatter = logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "service": "%(service)s", "message": "%(message)s", "context": "%(context)s"}')
    else:

        # 定义其他服务名称的日志消息格式化字符串，包含时间戳、日志级别和消息内容
        formatter = logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}')
    
    # 创建一个按时间轮转的文件处理器，每天午夜轮转一次，保留最近 30 天的日志文件
    file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=30)
    # 为文件处理器设置日志消息的格式化方式
    file_handler.setFormatter(formatter)
    # 将文件处理器添加到日志记录器中
    logger.addHandler(file_handler)

    # 创建一个控制台处理器，用于将日志消息输出到控制台
    console_handler = logging.StreamHandler()
    # 为控制台处理器设置日志消息的格式化方式
    console_handler.setFormatter(formatter)
    # 将控制台处理器添加到日志记录器中
    logger.addHandler(console_handler)
    
    # 测试日志是否正确打印
    logger.info("Logger setup completed", extra={
        "service": service_name,  # 确保传递 service 字段
        "context": json.dumps({"service_name": service_name})  # 确保传递 context 字段
    })
    
    # 返回配置好的日志记录器对象
    return logger
