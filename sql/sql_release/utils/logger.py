#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志工具模块

功能:
1. 配置统一的日志格式
2. 支持控制台和文件输出
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "sql_release",
    level: str = "INFO",
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: 日志格式
        log_file: 日志文件路径（可选）

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 设置日志级别
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    logger.setLevel(level_map.get(level.upper(), logging.INFO))

    # 创建格式器
    formatter = logging.Formatter(log_format)

    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 添加文件处理器（如果指定了日志文件）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "sql_release") -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器
    """
    return logging.getLogger(name)


# 模块级别的日志记录器
_logger: Optional[logging.Logger] = None


def init_logger(config: dict = None) -> logging.Logger:
    """
    初始化全局日志记录器

    Args:
        config: 配置字典

    Returns:
        日志记录器
    """
    global _logger

    if config is None:
        config = {}

    _logger = setup_logger(
        level=config.get('level', 'INFO'),
        log_format=config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        log_file=config.get('file'),
    )

    return _logger


def log() -> logging.Logger:
    """
    获取全局日志记录器

    Returns:
        日志记录器
    """
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger