#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL 文件扫描器

功能:
1. 递归扫描 SQL 源目录
2. 按日期范围过滤文件
3. 按目录自动分类（table/create, table/update, index, seq, data）
"""

import os
import fnmatch
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from models.sql_file import SqlFile, SqlCategory
from utils.date_utils import is_date_in_range, parse_date
from utils.logger import get_logger

logger = get_logger(__name__)

# 目录名到分类的映射
DIR_CATEGORY_MAP = {
    'create': 'table_create',
    'update': 'table_update',
    'index': 'index',
    'seq': 'sequence',
    'data': 'data_init',
    'view': 'view',
}


@dataclass
class ScanResult:
    """扫描结果"""
    files: List[SqlFile]
    by_category: Dict[str, List[SqlFile]]  # 按目录分类
    by_directory: Dict[str, List[SqlFile]]  # 按源目录名
    total_count: int
    filtered_count: int


class SqlScanner:
    """SQL 文件扫描器"""

    def __init__(
        self,
        source_dirs: List[str],
        exclude_files: List[str] = None,
        exclude_dirs: List[str] = None,
    ):
        """
        初始化扫描器

        Args:
            source_dirs: 源目录列表
            exclude_files: 排除的文件模式列表
            exclude_dirs: 排除的目录名列表
        """
        self.source_dirs = [Path(d) for d in source_dirs]
        self.exclude_files = set(exclude_files or [])
        self.exclude_dirs = set(exclude_dirs or [])

    def _get_category_from_dir(self, dir_path: Path) -> str:
        """
        从目录路径获取分类名称

        Args:
            dir_path: 目录路径

        Returns:
            分类名称
        """
        path_parts = dir_path.parts

        # 从路径中查找分类关键词
        for part in reversed(path_parts):
            if part in DIR_CATEGORY_MAP:
                return DIR_CATEGORY_MAP[part]

        # 默认返回目录名
        return dir_path.name

    def scan(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        categories: Optional[Set[str]] = None,
    ) -> ScanResult:
        """
        扫描 SQL 文件

        Args:
            start_date: 开始日期 (YYYY_MM_DD)
            end_date: 结束日期 (YYYY_MM_DD)
            categories: 要包含的分类（None 表示全部）

        Returns:
            扫描结果
        """
        # 解析日期范围
        start = parse_date(start_date) if start_date else None
        end = parse_date(end_date) if end_date else None

        all_files: List[SqlFile] = []
        by_category: Dict[str, List[SqlFile]] = {}
        by_directory: Dict[str, List[SqlFile]] = {}

        for source_dir in self.source_dirs:
            if not source_dir.exists():
                logger.warning(f"目录不存在: {source_dir}")
                continue

            logger.info(f"扫描目录: {source_dir}")

            # 获取该源目录的分类
            dir_category = self._get_category_from_dir(source_dir)

            dir_files = self._scan_directory(
                source_dir, start, end, categories, dir_category
            )

            # 按源目录分组（使用分类名）
            by_directory[dir_category] = dir_files

            all_files.extend(dir_files)

            # 按分类分组（与目录分组相同）
            if dir_category not in by_category:
                by_category[dir_category] = []
            by_category[dir_category].extend(dir_files)

        # 按日期排序
        all_files.sort(key=lambda x: x.date or datetime.min)

        logger.info(f"扫描完成: 共 {len(all_files)} 个文件")

        return ScanResult(
            files=all_files,
            by_category=by_category,
            by_directory=by_directory,
            total_count=len(all_files),
            filtered_count=len(all_files),
        )

    def _scan_directory(
        self,
        directory: Path,
        start: Optional[datetime],
        end: Optional[datetime],
        categories: Optional[Set[str]],
        dir_category: str,
    ) -> List[SqlFile]:
        """
        扫描单个目录

        Args:
            directory: 目录路径
            start: 开始日期
            end: 结束日期
            categories: 分类过滤
            dir_category: 目录分类

        Returns:
            文件列表
        """
        files: List[SqlFile] = []

        for root, dirs, filenames in os.walk(directory):
            # 过滤目录
            dirs[:] = [d for d in dirs if not self._should_exclude_dir(d)]

            for filename in filenames:
                # 只处理 .sql 文件
                if not filename.endswith('.sql'):
                    continue

                # 检查是否排除
                if self._should_exclude_file(filename):
                    continue

                file_path = Path(root) / filename
                sql_file = SqlFile.from_path(file_path)

                # 设置目录分类
                sql_file.category = SqlCategory.from_string(dir_category)

                # 日期过滤
                if sql_file.date and not is_date_in_range(sql_file.date, start, end):
                    continue

                # 分类过滤
                if categories and dir_category not in categories:
                    continue

                files.append(sql_file)

        return files

    def _should_exclude_file(self, filename: str) -> bool:
        """检查文件是否应该被排除"""
        for pattern in self.exclude_files:
            if fnmatch.fnmatch(filename, pattern):
                return True
            if pattern in filename:
                return True
        return False

    def _should_exclude_dir(self, dirname: str) -> bool:
        """检查目录是否应该被排除"""
        return dirname in self.exclude_dirs

    def list_files(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> None:
        """
        列出文件（用于预览）

        Args:
            start_date: 开始日期
            end_date: 结束日期
        """
        result = self.scan(start_date, end_date)

        print(f"\n找到 {result.total_count} 个符合条件的 SQL 文件:")
        print("=" * 80)

        for category, files in result.by_category.items():
            if not files:
                continue

            print(f"\n分类: {category} ({len(files)} 个文件)")
            print("-" * 60)

            for f in sorted(files, key=lambda x: x.date or datetime.min):
                date_str = f.date.strftime('%Y-%m-%d') if f.date else '无日期'
                print(f"  {date_str} | {f.name}")