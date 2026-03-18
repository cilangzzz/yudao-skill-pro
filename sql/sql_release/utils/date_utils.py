#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日期工具模块

功能:
1. 日期解析和格式化
2. 日期范围计算
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple


# 支持的日期格式
DATE_FORMATS = [
    '%Y_%m_%d',      # 2026_03_18
    '%Y-%m-%d',      # 2026-03-18
    '%Y%m%d',        # 20260318
]


def parse_date(date_str: str) -> Optional[datetime]:
    """
    解析日期字符串

    支持格式:
    - YYYY_MM_DD (2026_03_18)
    - YYYY-MM-DD (2026-03-18)
    - YYYYMMDD (20260318)

    Args:
        date_str: 日期字符串

    Returns:
        日期对象，解析失败返回 None
    """
    if not date_str:
        return None

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def format_date(date: datetime, fmt: str = '%Y_%m_%d') -> str:
    """
    格式化日期

    Args:
        date: 日期对象
        fmt: 输出格式（默认 YYYY_MM_DD）

    Returns:
        格式化后的日期字符串
    """
    return date.strftime(fmt)


def get_next_date(date_str: str) -> str:
    """
    获取下一个日期（日期 + 1 天）

    Args:
        date_str: 日期字符串 (YYYY_MM_DD)

    Returns:
        下一天的日期字符串
    """
    date = parse_date(date_str)
    if date is None:
        return date_str

    next_date = date + timedelta(days=1)
    return format_date(next_date)


def get_prev_date(date_str: str) -> str:
    """
    获取上一个日期（日期 - 1 天）

    Args:
        date_str: 日期字符串 (YYYY_MM_DD)

    Returns:
        前一天的日期字符串
    """
    date = parse_date(date_str)
    if date is None:
        return date_str

    prev_date = date - timedelta(days=1)
    return format_date(prev_date)


def is_date_in_range(
    date: datetime,
    start: Optional[datetime],
    end: Optional[datetime]
) -> bool:
    """
    检查日期是否在范围内

    Args:
        date: 要检查的日期
        start: 开始日期（包含）
        end: 结束日期（包含）

    Returns:
        是否在范围内
    """
    if start and date < start:
        return False
    if end and date > end:
        return False
    return True


def parse_date_range(
    start_str: Optional[str],
    end_str: Optional[str]
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    解析日期范围

    Args:
        start_str: 开始日期字符串
        end_str: 结束日期字符串

    Returns:
        (开始日期, 结束日期) 元组
    """
    start = parse_date(start_str) if start_str else None
    end = parse_date(end_str) if end_str else None
    return start, end


def normalize_date_format(date_str: str, target_fmt: str = '%Y_%m_%d') -> str:
    """
    标准化日期格式

    将任意支持的日期格式转换为目标格式

    Args:
        date_str: 原始日期字符串
        target_fmt: 目标格式

    Returns:
        标准化后的日期字符串
    """
    date = parse_date(date_str)
    if date is None:
        return date_str
    return format_date(date, target_fmt)


def extract_date_from_filename(filename: str) -> Optional[str]:
    """
    从文件名中提取日期

    Args:
        filename: 文件名

    Returns:
        日期字符串 (YYYY_MM_DD)，未找到返回 None
    """
    # 匹配 YYYY_MM_DD 格式
    pattern = r'(\d{4}_\d{2}_\d{2})'
    match = re.search(pattern, filename)

    if match:
        return match.group(1)
    return None