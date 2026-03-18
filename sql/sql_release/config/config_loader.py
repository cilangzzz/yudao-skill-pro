#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加载器模块

功能:
1. 加载 YAML 配置文件
2. 支持环境变量覆盖
3. 提供配置项访问接口
4. 支持多项目配置实例
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigLoader:
    """配置加载器 - 支持多项目"""

    # 实例缓存：project_id -> ConfigLoader 实例
    _instances: Dict[str, 'ConfigLoader'] = {}
    # 项目注册表：project_id -> config_path
    _project_registry: Dict[str, Path] = {}

    def __new__(cls, config_path: str = None, project_id: str = None):
        """
        支持多项目配置实例

        Args:
            config_path: 配置文件路径
            project_id: 项目 ID（可从配置文件读取）

        Returns:
            ConfigLoader 实例
        """
        # 如果指定了配置文件路径
        if config_path:
            # 从配置文件读取 project_id
            pid = cls._read_project_id(config_path)
            if pid and pid in cls._instances:
                return cls._instances[pid]
            # 创建新实例
            instance = super().__new__(cls)
            if pid:
                cls._instances[pid] = instance
            return instance

        # 如果指定了 project_id
        if project_id and project_id in cls._instances:
            return cls._instances[project_id]

        # 默认创建新实例
        return super().__new__(cls)

    def __init__(self, config_path: str = None, project_id: str = None):  # noqa: ARG002
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径（默认为 config/settings.yaml）
            project_id: 项目 ID
        """
        # 避免重复初始化（实例已存在时）
        if hasattr(self, '_config') and self._config is not None:
            return

        self.config_path = self._find_config(config_path)
        self._load()
        self.project_id = self._config.get('project', {}).get('id', 'default')

    def _find_config(self, config_path: str = None) -> Path:
        """
        查找配置文件

        Args:
            config_path: 指定的配置文件路径

        Returns:
            配置文件的完整路径
        """
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        # 默认查找路径
        base_dir = Path(__file__).parent
        default_path = base_dir / "settings.yaml"

        if default_path.exists():
            return default_path

        raise FileNotFoundError("未找到配置文件 settings.yaml")

    def _load(self) -> None:
        """加载配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

        # 应用环境变量覆盖
        self._apply_env_overrides()

    def _apply_env_overrides(self) -> None:
        """应用环境变量覆盖"""
        # 支持的环境变量映射
        env_mappings = {
            'SQL_RELEASE_MASTER_ROOT': 'paths.master_root',
            'SQL_RELEASE_OUTPUT_ROOT': 'paths.output_root',
            'SQL_RELEASE_LOG_LEVEL': 'logging.level',
        }

        for env_key, config_key in env_mappings.items():
            env_value = os.environ.get(env_key)
            if env_value:
                self._set_nested(config_key, env_value)

    def _set_nested(self, key: str, value: Any) -> None:
        """
        设置嵌套配置项

        Args:
            key: 配置键（点分隔）
            value: 配置值
        """
        keys = key.split('.')
        current = self._config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键（支持点分隔路径）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_all(self) -> Dict:
        """
        获取所有配置

        Returns:
            完整配置字典
        """
        return self._config.copy()

    def get_path(self, key: str, base_dir: Path = None) -> Path:
        """
        获取路径配置项

        Args:
            key: 配置键
            base_dir: 基础目录（默认为配置文件所在目录）

        Returns:
            解析后的绝对路径
        """
        path_str = self.get(key)
        if not path_str:
            raise ValueError(f"配置项不存在: {key}")

        path = Path(path_str)

        # 如果是相对路径，基于配置文件目录解析
        if not path.is_absolute():
            base = base_dir or Path(__file__).parent.parent
            path = base / path

        return path.resolve()

    def reload(self) -> None:
        """重新加载配置"""
        self._load()

    # ==================== 类方法：多项目管理 ====================

    @classmethod
    def _read_project_id(cls, config_path: str) -> Optional[str]:
        """
        从配置文件读取项目 ID

        Args:
            config_path: 配置文件路径

        Returns:
            项目 ID 或 None
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data.get('project', {}).get('id', None)
        except Exception:
            return None

    @classmethod
    def register_project(cls, project_id: str, config_path: str) -> None:
        """
        注册项目配置路径

        Args:
            project_id: 项目 ID
            config_path: 配置文件路径
        """
        cls._project_registry[project_id] = Path(config_path)

    @classmethod
    def get_instance(cls, project_id: str) -> 'ConfigLoader':
        """
        获取指定项目的配置实例

        Args:
            project_id: 项目 ID

        Returns:
            ConfigLoader 实例

        Raises:
            ValueError: 项目未注册
        """
        if project_id in cls._instances:
            return cls._instances[project_id]

        if project_id in cls._project_registry:
            config_path = str(cls._project_registry[project_id])
            return ConfigLoader(config_path=config_path)

        raise ValueError(f"未找到项目配置: {project_id}")

    @classmethod
    def list_projects(cls) -> list:
        """
        列出所有已注册项目

        Returns:
            项目 ID 列表
        """
        return list(cls._project_registry.keys())

    @classmethod
    def clear_cache(cls) -> None:
        """清除实例缓存（用于测试）"""
        cls._instances.clear()

    # ==================== 便捷方法 ====================

    def get_structure_mode(self) -> str:
        """获取目录结构模式"""
        return self.get('paths.structure_mode', 'by_operation')

    def get_release_mode(self) -> str:
        """获取发版模式"""
        return self.get('release.mode', 'incremental')

    def get_naming_mode(self) -> str:
        """获取命名模式"""
        return self.get('naming.mode', 'date_prefix')


# 全局配置实例
_config: Optional[ConfigLoader] = None


def get_config(config_path: str = None) -> ConfigLoader:
    """
    获取全局配置实例

    Args:
        config_path: 配置文件路径

    Returns:
        配置加载器实例
    """
    global _config
    if _config is None:
        _config = ConfigLoader(config_path)
    return _config