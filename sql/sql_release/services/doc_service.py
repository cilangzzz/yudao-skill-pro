#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档生成服务模块

功能:
1. 生成发版说明文档
2. 生成时间段整合报告
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from models.release_record import ReleaseRecord
from utils.logger import get_logger

logger = get_logger(__name__)


class DocService:
    """文档生成服务"""

    def __init__(self, output_dir: str):
        """
        初始化文档服务

        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_release_note(
        self,
        record: ReleaseRecord,
        output_name: Optional[str] = None,
    ) -> Path:
        """
        生成发版说明

        Args:
            record: 发版记录
            output_name: 输出文件名

        Returns:
            输出文件路径
        """
        if output_name is None:
            output_name = f"release_{record.release_date.strftime('%Y%m%d')}.md"

        output_path = self.output_dir / output_name

        content = self._render_release_note(record)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"发版说明已生成: {output_path}")
        return output_path

    def generate_period_report(
        self,
        records: List[ReleaseRecord],
        start_date: str,
        end_date: str,
        output_name: Optional[str] = None,
    ) -> Path:
        """
        生成时间段整合报告

        Args:
            records: 发版记录列表
            start_date: 开始日期
            end_date: 结束日期
            output_name: 输出文件名

        Returns:
            输出文件路径
        """
        if output_name is None:
            output_name = f"period_report_{start_date}_{end_date}.md"

        output_path = self.output_dir / output_name

        content = self._render_period_report(records, start_date, end_date)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"时间段报告已生成: {output_path}")
        return output_path

    def _render_release_note(self, record: ReleaseRecord) -> str:
        """渲染发版说明"""
        lines = [
            f"# SQL 发版说明",
            "",
            f"**发版日期**: {record.release_date.strftime('%Y-%m-%d')}",
            f"**发版ID**: {record.id}",
            f"**日期范围**: {record.start_date} ~ {record.end_date}",
            "",
            "## 概述",
            "",
            f"本次发版共包含 **{record.file_count}** 个 SQL 文件。",
            "",
        ]

        # 分类统计
        if record.by_category:
            lines.append("## 分类统计")
            lines.append("")
            lines.append("| 分类 | 文件数 |")
            lines.append("|------|-------|")
            for cat, count in record.by_category.items():
                lines.append(f"| {cat} | {count} |")
            lines.append("")

        # 文件清单
        if record.files:
            lines.append("## 文件清单")
            lines.append("")
            lines.append("| 序号 | 文件名 | 表名 | 分类 |")
            lines.append("|-----|-------|------|------|")
            for i, f in enumerate(record.files, 1):
                lines.append(
                    f"| {i} | {f['name']} | {f.get('table_name', '-')} | {f.get('category', '-')} |"
                )
            lines.append("")

        # 发版说明
        lines.append("## 发版说明")
        lines.append("")
        lines.append(record.notes or "(无)")
        lines.append("")

        # 页脚
        lines.append("---")
        lines.append(f"*本说明由 SQL 发版工具自动生成 @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return '\n'.join(lines)

    def _render_period_report(
        self,
        records: List[ReleaseRecord],
        start_date: str,
        end_date: str,
    ) -> str:
        """渲染时间段报告"""
        lines = [
            f"# SQL 发版时间段报告",
            "",
            f"**报告时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**日期范围**: {start_date} ~ {end_date}",
            "",
        ]

        # 统计概览
        total_files = sum(r.file_count for r in records)
        unique_tables = set()
        for r in records:
            unique_tables.update(r.by_table.keys())

        lines.append("## 统计概览")
        lines.append("")
        lines.append(f"- **发版次数**: {len(records)}")
        lines.append(f"- **文件总数**: {total_files}")
        lines.append(f"- **涉及表数**: {len(unique_tables)}")
        lines.append("")

        # 发版历史
        if records:
            lines.append("## 发版历史")
            lines.append("")
            lines.append("| 发版日期 | 日期范围 | 文件数 | 说明 |")
            lines.append("|---------|---------|-------|------|")
            for r in records:
                lines.append(
                    f"| {r.release_date.strftime('%Y-%m-%d')} | "
                    f"{r.start_date} ~ {r.end_date} | "
                    f"{r.file_count} | {r.notes or '-'} |"
                )
            lines.append("")

        # 整合文件清单
        all_files = []
        seen_files = set()
        for r in records:
            for f in r.files:
                if f['name'] not in seen_files:
                    seen_files.add(f['name'])
                    all_files.append(f)

        if all_files:
            lines.append("## 整合文件清单")
            lines.append("")
            lines.append(f"共 {len(all_files)} 个唯一文件:")
            lines.append("")
            lines.append("| 序号 | 文件名 | 表名 | 分类 |")
            lines.append("|-----|-------|------|------|")
            for i, f in enumerate(all_files, 1):
                lines.append(
                    f"| {i} | {f['name']} | {f.get('table_name', '-')} | {f.get('category', '-')} |"
                )
            lines.append("")

        # 页脚
        lines.append("---")
        lines.append(f"*本报告由 SQL 发版工具自动生成*")

        return '\n'.join(lines)