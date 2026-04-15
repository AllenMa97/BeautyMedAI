import logging
import os
from logging.handlers import TimedRotatingFileHandler
import re
import platform


def get_logger(name: str) -> logging.Logger:
    """获取通用日志实例（所有模块复用，兼容所有Python版本，时间100%显示）"""
    # 创建日志目录 - 改为服务专属目录
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 配置日志：强制使用独立logger，不继承父logger的配置
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # 核心：禁止日志向上传递，避免根logger覆盖格式

    # 安全判断：清空已有handlers（彻底避免重复/继承的handler干扰）
    if logger.handlers:
        logger.handlers.clear()

    # 文件处理器：兼容版TimedRotatingFileHandler（解决suffix参数报错）
    # 基础日志文件名（不带日期），按天切分后自动生成 文件名.20260210 格式
    log_file = os.path.join(log_dir, "backend_service.log")
    # when="D" 按天切分，interval=1 每天切分，backupCount=7 保留7天日志
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="D",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    # 兼容所有版本的suffix配置（关键：通过setSuffix+正则匹配实现日期后缀）
    file_handler.suffix = "%Y%m%d"  # 日志文件后缀：20260210
    # 正则匹配后缀，确保切分逻辑生效（必须加，否则suffix不生效）
    file_handler.extMatch = re.compile(r"^\d{8}$")
    file_handler.setLevel(logging.INFO)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 格式器（保留你的时间格式，确保%(asctime)s生效）
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger