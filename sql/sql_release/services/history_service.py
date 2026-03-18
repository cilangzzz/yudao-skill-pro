#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史服务模块

功能:
1. YAML 格式存储历史记录（主存储）
2. Markdown 格式生成（视图）
3. 双格式同步机制
"""

import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from models.release_record import ReleaseRecord
from utils.date_utils import parse_date
from utils.logger import get_logger

logger = get_logger(__name__)


class HistoryService:
    """历史服务"""

    def __init__(self, history_dir: str):
        """
        初始化历史服务

        Args:
            history_dir: 历史记录目录
        """
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)

        self.yaml_path = self.history_dir / "releases.yaml"
        self.md_path = self.history_dir / "release_history.md"

    def save(self, record: ReleaseRecord) -> bool:
        """
        保存发版记录

        Args:
            record: 发版记录

        Returns:
            是否成功
        """
        try:
            # 1. 保存到 YAML
            self._save_to_yaml(record)

            # 2. 更新 Markdown
            self._update_markdown(record)

            logger.info(f"发版记录已保存: {record.id}")
            return True

        except Exception as e:
            logger.error(f"保存发版记录失败: {e}")
            return False

    def _save_to_yaml(self, record: ReleaseRecord) -> None:
        """保存到 YAML 文件"""
        # 加载现有记录
        records = self.load_all()

        # 添加新记录（放在最前面）
        records.insert(0, record)

        # 写入文件
        data = {
            'version': '2.0',
            'updated': datetime.now().isoformat(),
            'releases': [r.to_yaml_data() for r in records]
        }

        with open(self.yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        logger.debug(f"YAML 已保存: {self.yaml_path}")

    def _update_markdown(self, record: ReleaseRecord) -> None:
        """更新 Markdown 文件"""
        # 如果文件不存在，创建初始文件
        if not self.md_path.exists():
            self._create_initial_markdown()

        # 读取现有内容
        with open(self.md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 生成新的时间线行
        new_row = self._generate_timeline_row(record)

        # 在时间线表格中插入新行
        content = self._insert_timeline_row(content, new_row)

        # 生成详细记录
        detail = self._generate_detail_section(record)

        # 在详细记录部分插入新记录
        content = self._insert_detail_section(content, detail)

        # 写回文件
        with open(self.md_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.debug(f"Markdown 已更新: {self.md_path}")

    def load_all(self) -> List[ReleaseRecord]:
        """
        加载所有发版记录

        Returns:
            发版记录列表（按时间倒序）
        """
        if not self.yaml_path.exists():
            return []

        try:
            with open(self.yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            releases = data.get('releases', [])
            return [ReleaseRecord.from_dict(r) for r in releases]

        except Exception as e:
            logger.error(f"加载发版记录失败: {e}")
            return []

    def get_latest(self) -> Optional[ReleaseRecord]:
        """
        获取最新的发版记录

        Returns:
            最新的发版记录
        """
        records = self.load_all()
        return records[0] if records else None

    def get_by_date_range(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> List[ReleaseRecord]:
        """
        按日期范围获取发版记录

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            发版记录列表
        """
        records = self.load_all()
        result = []

        start = parse_date(start_date) if start_date else None
        end = parse_date(end_date) if end_date else None

        for record in records:
            record_date = parse_date(record.start_date)
            if record_date:
                if start and record_date < start:
                    continue
                if end and record_date > end:
                    continue
                result.append(record)

        return result

    def _create_initial_markdown(self) -> None:
        """创建初始 Markdown 文件"""
        content = """# SQL 发版历史记录

> 本文件由 sql_release 工具自动生成和维护

## 发版时间线

| 发版日期 | SQL 日期范围 | 文件数 | 说明 |
|---------|-------------|-------|------|

---

## 详细记录

*后续发版将在此记录详细信息*
"""
        with open(self.md_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_timeline_row(self, record: ReleaseRecord) -> str:
        """生成时间线表格行"""
        date = record.release_date.strftime('%Y-%m-%d')
        notes = record.notes or '-'
        return f"| {date} | {record.start_date} ~ {record.end_date} | {record.file_count} | {notes} |"

    def _insert_timeline_row(self, content: str, new_row: str) -> str:
        """在时间线表格中插入新行"""
        import re

        # 查找时间线表格
        pattern = r'(## 发版时间线\n\n\|[^\n]+\n\|[^\n]+\n)'
        match = re.search(pattern, content)

        if match:
            insert_pos = match.end()
            return content[:insert_pos] + new_row + '\n' + content[insert_pos:]

        return content

    def _generate_detail_section(self, record: ReleaseRecord) -> str:
        """生成详细记录部分"""
        lines = [
            f"### {record.release_date.strftime('%Y-%m-%d')} 发版",
            "",
            f"- **发版时间**: {record.release_date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **SQL 日期范围**: {record.start_date} ~ {record.end_date}",
            f"- **文件总数**: {record.file_count}",
            "",
        ]

        # 分类统计
        if record.by_category:
            lines.append("**分类统计**:")
            for cat, count in record.by_category.items():
                lines.append(f"- {cat}: {count} 个")
            lines.append("")

        # 文件列表
        if record.files:
            lines.append("**涉及文件**:")
            lines.append("| 序号 | 文件名 | 表名 | 分类 |")
            lines.append("|-----|-------|------|------|")
            for i, f in enumerate(record.files, 1):
                lines.append(f"| {i} | {f['name']} | {f.get('table_name', '-')} | {f.get('category', '-')} |")
            lines.append("")

        # 发版说明
        lines.append(f"**发版说明**: {record.notes or '(无)'}")
        lines.append("")
        lines.append("---")
        lines.append("")

        return '\n'.join(lines)

    def _insert_detail_section(self, content: str, detail: str) -> str:
        """在详细记录部分插入新记录"""
        import re

        # 查找详细记录部分
        pattern = r'(## 详细记录\n)'
        match = re.search(pattern, content)

        if match:
            insert_pos = match.end()
            return content[:insert_pos] + '\n' + detail + content[insert_pos:]

        return content + '\n' + detail