#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL 文件合并器

功能:
1. 合并多个 SQL 文件
2. 生成合并后的输出文件
3. 添加文件分隔和注释
4. 支持时间戳和追加模式
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from models.sql_file import SqlFile
from utils.logger import get_logger

logger = get_logger(__name__)


class SqlMerger:
    """SQL 文件合并器"""

    def __init__(
        self,
        output_dir: str,
        subfolder: bool = True,
        append_mode: bool = False,
    ):
        """
        初始化合并器

        Args:
            output_dir: 输出目录
            subfolder: 是否按日期创建子文件夹
            append_mode: 是否追加模式（追加到现有文件）
        """
        self.base_output_dir = Path(output_dir)
        self.subfolder = subfolder
        self.append_mode = append_mode

        # 设置输出目录
        if subfolder:
            today = datetime.now().strftime('%Y%m%d')
            self.output_dir = self.base_output_dir / today
        else:
            self.output_dir = self.base_output_dir

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_output_filename(
        self,
        category: Optional[str],
        add_timestamp: bool = True,
    ) -> str:
        """
        生成输出文件名

        Args:
            category: 分类名称
            add_timestamp: 是否添加时间戳

        Returns:
            文件名
        """
        # 基础文件名
        if category:
            base_name = f"{category}_merged"
        else:
            base_name = "merged"

        # 添加时间戳
        if add_timestamp:
            timestamp = datetime.now().strftime('_%H%M%S')
            return f"{base_name}{timestamp}.sql"
        else:
            return f"{base_name}.sql"

    def merge(
        self,
        sql_files: List[SqlFile],
        output_name: str = None,
        category: Optional[str] = None,
        add_timestamp: bool = True,
    ) -> Path:
        """
        合并 SQL 文件

        Args:
            sql_files: SQL 文件列表
            output_name: 输出文件名（可选，覆盖自动生成）
            category: 分类名称（用于命名）
            add_timestamp: 是否添加时间戳

        Returns:
            输出文件路径
        """
        if not sql_files:
            logger.warning("没有文件需要合并")
            return None

        # 生成输出文件名
        if output_name:
            output_filename = output_name
        else:
            output_filename = self._get_output_filename(category, add_timestamp)

        output_path = self.output_dir / output_filename

        # 选择写入模式
        write_mode = 'a' if self.append_mode else 'w'

        logger.info(f"合并 {len(sql_files)} 个文件到 {output_path} (模式: {write_mode})")

        try:
            with open(output_path, write_mode, encoding='utf-8') as f:
                # 追加模式下先添加分隔
                if self.append_mode and output_path.exists():
                    f.write(f"\n\n-- {'=' * 60}\n")
                    f.write(f"-- 追加内容 @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"-- {'=' * 60}\n\n")

                # 写入头部注释
                self._write_header(f, sql_files, category)

                # 写入每个文件
                for sql_file in sql_files:
                    self._write_file(f, sql_file)

            logger.info(f"合并完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"合并失败: {e}")
            raise

    def _write_header(
        self,
        output_file,
        sql_files: List[SqlFile],
        category: Optional[str],
    ) -> None:
        """写入头部注释"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        output_file.write(f"-- SQL 文件合并输出\n")
        output_file.write(f"-- 生成时间: {now}\n")
        output_file.write(f"-- 文件数量: {len(sql_files)}\n")

        if category:
            output_file.write(f"-- 分类: {category}\n")

        # 写入文件列表
        output_file.write(f"--\n")
        output_file.write(f"-- 包含的文件:\n")
        for f in sql_files:
            date_str = f.date.strftime('%Y-%m-%d') if f.date else '无日期'
            output_file.write(f"--   {date_str} | {f.name}\n")

        output_file.write(f"--\n\n")

    def _write_file(self, output_file, sql_file: SqlFile) -> None:
        """写入单个文件"""
        # 写入分隔线和文件信息
        output_file.write(f"-- {'=' * 60}\n")
        output_file.write(f"-- 文件: {sql_file.name}\n")
        output_file.write(f"-- 表名: {sql_file.table_name or '未知'}\n")
        output_file.write(f"-- 分类: {sql_file.category.value}\n")
        if sql_file.date:
            output_file.write(f"-- 日期: {sql_file.date.strftime('%Y-%m-%d')}\n")
        output_file.write(f"-- {'=' * 60}\n\n")

        # 写入文件内容
        if sql_file.content:
            output_file.write(sql_file.content)

            # 确保有换行
            if not sql_file.content.endswith('\n'):
                output_file.write('\n')

            output_file.write('\n')
        else:
            output_file.write(f"-- (文件为空或无法读取)\n\n")

    def merge_by_category(
        self,
        files_by_category: dict,
        add_timestamp: bool = True,
    ) -> List[Path]:
        """
        按分类合并文件

        Args:
            files_by_category: 按分类分组的文件字典
            add_timestamp: 是否添加时间戳

        Returns:
            输出文件路径列表
        """
        output_paths = []

        for category, files in files_by_category.items():
            if files:
                path = self.merge(files, category=category, add_timestamp=add_timestamp)
                if path:
                    output_paths.append(path)

        return output_paths

    def merge_to_single(
        self,
        sql_files: List[SqlFile],
        output_name: str = None,
        add_timestamp: bool = True,
    ) -> Path:
        """
        合并所有文件到单个文件

        Args:
            sql_files: SQL 文件列表
            output_name: 输出文件名
            add_timestamp: 是否添加时间戳

        Returns:
            输出文件路径
        """
        return self.merge(sql_files, output_name=output_name, add_timestamp=add_timestamp)