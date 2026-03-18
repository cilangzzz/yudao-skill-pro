#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL 文件模型

功能:
1. 定义 SQL 文件分类枚举
2. 定义 SQL 文件数据模型
3. 提供文件解析方法
"""

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class SqlCategory(Enum):
    """SQL 文件分类"""
    TABLE_CREATE = "table_create"      # 建表语句
    TABLE_UPDATE = "table_update"      # 表结构更新
    INDEX = "index"                    # 索引
    SEQUENCE = "sequence"              # 序列
    DATA_INIT = "data_init"            # 数据初始化
    VIEW = "view"                      # 视图
    UNKNOWN = "unknown"                # 未知类型

    @classmethod
    def from_string(cls, value: str) -> 'SqlCategory':
        """从字符串获取分类"""
        for member in cls:
            if member.value == value:
                return member
        return cls.UNKNOWN


class SqlDatabase(Enum):
    """数据库类型"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"          # PostgreSQL / Kingbase
    KINGBASE = "kingbase"
    GENERIC = "generic"                # 通用 SQL


@dataclass
class SqlFile:
    """
    SQL 文件模型

    Attributes:
        path: 文件路径
        name: 文件名
        date: 解析的日期
        table_name: 关联的表名
        category: SQL 分类
        database: 数据库类型
        content: 文件内容
        size: 文件大小（字节）
        checksum: MD5 校验和
    """
    path: Path
    name: str
    date: Optional[datetime] = None
    table_name: Optional[str] = None
    category: SqlCategory = SqlCategory.UNKNOWN
    database: SqlDatabase = SqlDatabase.GENERIC
    content: str = ""
    size: int = 0
    checksum: str = ""

    # 文件名正则模式
    _FILENAME_PATTERN = re.compile(
        r'^(?P<date>\d{4}_\d{2}_\d{2})_'
        r'(?P<table>[a-z_]+?)'
        r'(?P<type>_(?:create|update|idx|seq))?'
        r'(?P<db>_pg)?'
        r'\.sql$'
    )

    @classmethod
    def from_path(cls, file_path: Path) -> 'SqlFile':
        """
        从文件路径创建 SqlFile 实例

        Args:
            file_path: 文件路径

        Returns:
            SqlFile 实例
        """
        file_path = Path(file_path)
        name = file_path.name

        # 解析文件名
        date, table_name, category, database = cls._parse_filename(name)

        # 读取文件内容
        content = ""
        size = 0
        checksum = ""

        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                size = file_path.stat().st_size
                checksum = hashlib.md5(content.encode()).hexdigest()
            except Exception:
                pass

        return cls(
            path=file_path,
            name=name,
            date=date,
            table_name=table_name,
            category=category,
            database=database,
            content=content,
            size=size,
            checksum=checksum
        )

    @classmethod
    def _parse_filename(cls, filename: str) -> tuple:
        """
        解析文件名

        Args:
            filename: 文件名

        Returns:
            (日期, 表名, 分类, 数据库类型)
        """
        match = cls._FILENAME_PATTERN.match(filename)

        if not match:
            return None, None, SqlCategory.UNKNOWN, SqlDatabase.GENERIC

        # 解析日期
        date_str = match.group('date')
        try:
            date = datetime.strptime(date_str, '%Y_%m_%d')
        except ValueError:
            date = None

        # 解析表名
        table_name = match.group('table')

        # 解析类型
        type_suffix = match.group('type')
        category = cls._determine_category(type_suffix, filename)

        # 解析数据库
        db_suffix = match.group('db')
        database = SqlDatabase.POSTGRESQL if db_suffix else SqlDatabase.GENERIC

        return date, table_name, category, database

    @staticmethod
    def _determine_category(type_suffix: Optional[str], filename: str) -> SqlCategory:
        """
        确定 SQL 文件分类

        Args:
            type_suffix: 类型后缀
            filename: 文件名

        Returns:
            SQL 分类
        """
        if type_suffix:
            suffix_map = {
                '_create': SqlCategory.TABLE_CREATE,
                '_update': SqlCategory.TABLE_UPDATE,
                '_idx': SqlCategory.INDEX,
                '_seq': SqlCategory.SEQUENCE,
            }
            return suffix_map.get(type_suffix, SqlCategory.UNKNOWN)

        # 根据文件名推断
        if '_seq' in filename:
            return SqlCategory.SEQUENCE
        if '_idx' in filename:
            return SqlCategory.INDEX

        return SqlCategory.DATA_INIT

    def to_dict(self) -> dict:
        """
        转换为字典

        Returns:
            字典表示
        """
        return {
            'path': str(self.path),
            'name': self.name,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'table_name': self.table_name,
            'category': self.category.value,
            'database': self.database.value,
            'size': self.size,
            'checksum': self.checksum,
        }

    def __str__(self) -> str:
        return f"SqlFile({self.name}, {self.category.value}, {self.date})"

    def __repr__(self) -> str:
        return self.__str__()