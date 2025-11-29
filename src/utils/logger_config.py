#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志配置模块
配置loguru日志系统，支持文件轮转、压缩和多级别日志
"""

import sys
from pathlib import Path
from loguru import logger
from src.core.config import settings


def setup_logger():
    """配置日志系统"""
    
    # 移除默认的handler
    logger.remove()
    
    # 创建日志目录
    log_dir = Path(settings.LOG_PATH)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 控制台输出（彩色）
    logger.add(
        sys.stdout,
        format=settings.LOG_FORMAT,
        level=settings.LOG_LEVEL,
        colorize=True,
    )
    
    # 通用日志文件
    logger.add(
        log_dir / "ai4s_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation=settings.LOG_ROTATION,
        retention=f"{settings.LOG_RETENTION} days",
        compression=settings.LOG_COMPRESSION,
        encoding="utf-8",
    )
    
    # 错误日志文件
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation=settings.LOG_ROTATION,
        retention=f"{settings.LOG_RETENTION} days",
        compression=settings.LOG_COMPRESSION,
        encoding="utf-8",
    )
    
    # 性能日志文件（如果启用）
    if settings.ENABLE_PROFILING:
        logger.add(
            log_dir / "performance_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
            level="INFO",
            rotation=settings.LOG_ROTATION,
            retention=f"{settings.LOG_RETENTION} days",
            compression=settings.LOG_COMPRESSION,
            encoding="utf-8",
            filter=lambda record: "PERF" in record["extra"],
        )
    
    logger.info("日志系统初始化完成")


def get_logger(name: str):
    """
    获取指定名称的logger
    
    Args:
        name: logger名称
    
    Returns:
        logger实例
    """
    return logger.bind(name=name)