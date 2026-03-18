#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发版服务模块

功能:
1. 协调扫描、合并、记录流程
2. 提供预览和执行模式
"""

from typing import List, Optional

from config.config_loader import get_config
from core.merger import SqlMerger
from core.scanner import SqlScanner, ScanResult
from models.release_record import ReleaseRecord
from models.sql_file import SqlFile
from utils.date_utils import get_next_date
from utils.logger import get_logger
from services.history_service import HistoryService

logger = get_logger(__name__)


class ReleaseService:
    """发版服务"""

    def __init__(self, config=None):
        """
        初始化发版服务

        Args:
            config: 配置对象（默认使用全局配置）
        """
        self.config = config or get_config()

        # 初始化组件
        self._init_components()

    def _init_components(self):
        """初始化组件"""
        # 获取配置
        master_root = self.config.get_path('paths.master_root')
        output_root = self.config.get_path('paths.output_root')
        history_root = self.config.get_path('paths.history_root')

        # 源目录列表
        categories = self.config.get('paths.categories', {})
        self.source_dirs = [
            str(master_root / rel_path)
            for rel_path in categories.values()
        ]

        # 过滤配置
        self.exclude_files = self.config.get('filters.exclude_files', [])
        self.exclude_dirs = self.config.get('filters.exclude_dirs', [])

        # 输出配置
        self.subfolder = self.config.get('output.subfolder', True)
        self.add_timestamp = self.config.get('output.add_timestamp', True)

        # 创建组件
        self.scanner = SqlScanner(
            source_dirs=self.source_dirs,
            exclude_files=self.exclude_files,
            exclude_dirs=self.exclude_dirs,
        )

        # merger 延迟初始化
        self._merger = None
        self._output_root = str(output_root)
        self.history_service = HistoryService(str(history_root))

    @property
    def merger(self):
        """延迟初始化 merger"""
        if self._merger is None:
            self._merger = SqlMerger(
                self._output_root,
                subfolder=self.subfolder,
            )
        return self._merger

    def create_merger(self, subfolder: bool = True, append_mode: bool = False):
        """
        创建新的 merger 实例

        Args:
            subfolder: 是否按日期创建子文件夹
            append_mode: 是否追加模式
        """
        return SqlMerger(
            self._output_root,
            subfolder=subfolder,
            append_mode=append_mode,
        )

    def preview(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> ScanResult:
        """
        预览要发布的文件

        Args:
            start_date: 开始日期 (YYYY_MM_DD)
            end_date: 结束日期 (YYYY_MM_DD)

        Returns:
            扫描结果
        """
        logger.info(f"预览模式: {start_date} ~ {end_date}")

        result = self.scanner.scan(start_date, end_date)

        # 显示预览
        self._display_preview(result)

        return result

    def merge(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        notes: str = "",
        save_history: bool = True,
        subfolder: bool = True,
        append_mode: bool = False,
        add_timestamp: bool = True,
    ) -> dict:
        """
        执行合并发版

        Args:
            start_date: 开始日期 (YYYY_MM_DD)
            end_date: 结束日期 (YYYY_MM_DD)
            notes: 发版说明
            save_history: 是否保存历史记录
            subfolder: 是否按日期创建子文件夹
            append_mode: 是否追加模式
            add_timestamp: 是否添加时间戳

        Returns:
            执行结果字典
        """
        logger.info(f"执行合并: {start_date} ~ {end_date}")

        # 1. 扫描文件
        result = self.scanner.scan(start_date, end_date)

        if not result.files:
            logger.warning("没有找到符合条件的文件")
            return {'success': False, 'message': '没有找到符合条件的文件'}

        # 2. 创建 merger（根据参数）
        merger = self.create_merger(subfolder=subfolder, append_mode=append_mode)

        # 3. 合并文件（按分类）
        output_files = merger.merge_by_category(result.by_category, add_timestamp=add_timestamp)

        # 4. 记录历史
        record = None
        if save_history:
            record = ReleaseRecord.create(
                start_date=start_date or '',
                end_date=end_date or '',
                sql_files=result.files,
                notes=notes,
            )
            self.history_service.save(record)

        # 5. 返回结果
        return {
            'success': True,
            'file_count': len(result.files),
            'output_files': [str(p) for p in output_files],
            'output_dir': str(merger.output_dir),
            'record_id': record.id if record else None,
        }

    def _display_preview(self, result: ScanResult) -> None:
        """显示预览结果"""
        print(f"\n预览结果: 共 {result.total_count} 个文件")
        print("=" * 80)

        for directory, files in result.by_directory.items():
            if not files:
                continue

            print(f"\n目录: {directory} ({len(files)} 个文件)")
            print("-" * 60)

            from datetime import datetime
            for f in sorted(files, key=lambda x: x.date or datetime.min):
                date_str = f.date.strftime('%Y-%m-%d') if f.date else '无日期'
                print(f"  {date_str} | {f.name}")

        print("\n分类统计:")
        for cat, files in result.by_category.items():
            print(f"  {cat}: {len(files)} 个")

    def get_latest_end_date(self) -> Optional[str]:
        """
        获取最后一次发版的结束日期

        Returns:
            结束日期字符串
        """
        record = self.history_service.get_latest()
        if record:
            return record.end_date
        return None

    def get_suggested_start_date(self) -> Optional[str]:
        """
        获取建议的开始日期（上次发版结束日期 + 1 天）

        Returns:
            建议的开始日期
        """
        latest_end = self.get_latest_end_date()
        if latest_end:
            return get_next_date(latest_end)
        return None