"""
提猫直播助手 - 日志管理模块
负责应用日志的配置和管理
"""

import os
import logging
import logging.handlers
from typing import Optional
from pathlib import Path


def setup_logger(
    name: str = __name__,
    log_file: str = None,
    log_level: str = 'INFO',
    max_size: int = 10,
    backup_count: int = 5
) -> logging.Logger:
    """设置日志记录器"""
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 如果已经有处理器，直接返回
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        try:
            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            # 创建轮转文件处理器
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_size * 1024 * 1024,  # 转换为字节
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        except Exception as e:
            logger.warning(f"无法创建文件日志处理器: {e}")
    
    return logger


def get_logger(name: str = __name__) -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)


class LoggerMixin:
    """日志混入类"""
    
    @property
    def logger(self) -> logging.Logger:
        """获取日志记录器"""
        return logging.getLogger(self.__class__.__name__)