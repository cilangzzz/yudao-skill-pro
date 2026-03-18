#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发版记录模型

功能:
1. 定义发版记录数据模型
2. 提供 YAML/字典转换方法
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from .sql_file import SqlFile


@dataclass
class ReleaseRecord:
    """
    发版记录模型

    Attributes:
        id: 发版 ID (UUID)
        release_date: 发版日期时间
        start_date: SQL 开始日期 (YYYY_MM_DD)
        end_date: SQL 结束日期 (YYYY_MM_DD)
        files: 文件列表
        file_count: 文件总数
        by_category: 按分类统计
        by_table: 按表统计
        notes: 发版说明
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    release_date: datetime = field(default_factory=datetime.now)
    start_date: str = ""
    end_date: str = ""
    files: List[Dict] = field(default_factory=list)
    file_count: int = 0
    by_category: Dict[str, int] = field(default_factory=dict)
    by_table: Dict[str, int] = field(default_factory=dict)
    notes: str = ""

    @classmethod
    def create(
        cls,
        start_date: str,
        end_date: str,
        sql_files: List[SqlFile],
        notes: str = ""
    ) -> 'ReleaseRecord':
        """
        创建发版记录

        Args:
            start_date: SQL 开始日期
            end_date: SQL 结束日期
            sql_files: SQL 文件列表
            notes: 发版说明

        Returns:
            发版记录实例
        """
        # 转换文件列表
        files = [f.to_dict() for f in sql_files]

        # 统计分类
        by_category: Dict[str, int] = {}
        for f in sql_files:
            cat = f.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        # 统计表
        by_table: Dict[str, int] = {}
        for f in sql_files:
            if f.table_name:
                by_table[f.table_name] = by_table.get(f.table_name, 0) + 1

        return cls(
            start_date=start_date,
            end_date=end_date,
            files=files,
            file_count=len(sql_files),
            by_category=by_category,
            by_table=by_table,
            notes=notes
        )

    def to_dict(self) -> dict:
        """
        转换为字典

        Returns:
            字典表示
        """
        return {
            'id': self.id,
            'release_date': self.release_date.isoformat(),
            'start_date': self.start_date,
            'end_date': self.end_date,
            'files': self.files,
            'file_count': self.file_count,
            'by_category': self.by_category,
            'by_table': self.by_table,
            'notes': self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ReleaseRecord':
        """
        从字典创建实例

        Args:
            data: 字典数据

        Returns:
            发版记录实例
        """
        release_date = data.get('release_date')
        if isinstance(release_date, str):
            release_date = datetime.fromisoformat(release_date)
        else:
            release_date = datetime.now()

        return cls(
            id=data.get('id', str(uuid.uuid4())[:8]),
            release_date=release_date,
            start_date=data.get('start_date', ''),
            end_date=data.get('end_date', ''),
            files=data.get('files', []),
            file_count=data.get('file_count', data.get('statistics', {}).get('file_count', 0)),
            by_category=data.get('by_category', data.get('statistics', {}).get('by_category', {})),
            by_table=data.get('by_table', data.get('statistics', {}).get('by_table', {})),
            notes=data.get('notes', ''),
        )

    def to_yaml_data(self) -> dict:
        """
        转换为 YAML 友好的格式

        Returns:
            YAML 友好的字典
        """
        return {
            'id': self.id,
            'release_date': self.release_date.strftime('%Y-%m-%d %H:%M:%S'),
            'date_range': f"{self.start_date} ~ {self.end_date}",
            'start_date': self.start_date,
            'end_date': self.end_date,
            'statistics': {
                'file_count': self.file_count,
                'by_category': self.by_category,
                'by_table': self.by_table,
            },
            'files': [
                {
                    'name': f['name'],
                    'table': f.get('table_name'),
                    'category': f.get('category'),
                }
                for f in self.files
            ],
            'notes': self.notes,
        }

    def __str__(self) -> str:
        return f"ReleaseRecord({self.id}, {self.start_date} ~ {self.end_date}, {self.file_count} files)"

    def __repr__(self) -> str:
        return self.__str__()