#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL 发版工具 - 统一 CLI 入口

Usage:
    sql_release merge --start 2026_03_01 --end 2026_03_18
    sql_release merge --preview
    sql_release history
    sql_release report --start 2026_01 --end 2026_03
"""

import sys
from pathlib import Path

import click

# 添加项目根目录到 Python 路径
_project_dir = Path(__file__).parent
sys.path.insert(0, str(_project_dir))

# 使用绝对导入
from config.config_loader import ConfigLoader, get_config
from services.release_service import ReleaseService
from services.history_service import HistoryService
from services.doc_service import DocService
from utils.logger import init_logger


@click.group()
@click.option('--config', '-c', help='配置文件路径')
@click.option('--project', '-p', help='项目 ID')
@click.pass_context
def cli(ctx, config, project):
    """SQL 发版工具"""
    ctx.ensure_object(dict)

    # 优先级：config > project > 默认
    if config:
        cfg = get_config(config_path=config)
    elif project:
        cfg = ConfigLoader.get_instance(project)
    else:
        cfg = get_config()

    init_logger(cfg.get('logging', {}))
    ctx.obj['config'] = cfg


@cli.command()
@click.option('--start', required=False, help='开始日期 (YYYY_MM_DD)')
@click.option('--end', required=False, help='结束日期 (YYYY_MM_DD)')
@click.option('--preview', is_flag=True, help='预览模式，不执行合并')
@click.option('--notes', default='', help='发版说明')
@click.option('--no-subfolder', is_flag=True, help='不在 output 下创建日期子文件夹')
@click.option('--append', is_flag=True, help='追加模式，追加到现有文件')
@click.option('--no-timestamp', is_flag=True, help='文件名不添加时间戳')
@click.pass_context
def merge(ctx, start, end, preview, notes, no_subfolder, append, no_timestamp):
    """合并 SQL 文件"""
    service = ReleaseService(ctx.obj['config'])

    # 获取建议日期
    if not start:
        suggested = service.get_suggested_start_date()
        if suggested:
            click.echo(f"上次发版结束日期: {service.get_latest_end_date()}")
            click.echo(f"建议开始日期: {suggested}")
            click.echo("")
            start = click.prompt("请输入开始日期", default=suggested)
        else:
            start = click.prompt("请输入开始日期 (YYYY_MM_DD)")

    if preview:
        # 预览模式
        result = service.preview(start, end)
        click.echo(f"\n预览完成，共 {result.total_count} 个文件")
    else:
        # 执行合并
        click.echo(f"正在合并: {start} ~ {end}")
        result = service.merge(
            start, end, notes,
            subfolder=not no_subfolder,
            append_mode=append,
            add_timestamp=not no_timestamp,
        )

        if result['success']:
            click.echo(f"\n合并完成!")
            click.echo(f"  - 文件数: {result['file_count']}")
            click.echo(f"  - 输出目录: {result['output_dir']}")
            click.echo(f"  - 输出文件:")
            for f in result['output_files']:
                click.echo(f"    - {f}")
            if result['record_id']:
                click.echo(f"  - 发版记录: {result['record_id']}")
        else:
            click.echo(f"合并失败: {result['message']}")


@cli.command()
@click.option('--start', help='开始日期 (YYYY_MM_DD)')
@click.option('--end', help='结束日期 (YYYY_MM_DD)')
@click.pass_context
def history(ctx, start, end):
    """查看发版历史"""
    config = ctx.obj['config']
    history_root = config.get_path('paths.history_root')
    service = HistoryService(str(history_root))

    records = service.get_by_date_range(start, end)

    if not records:
        click.echo("暂无发版历史记录")
        return

    click.echo(f"\n发版历史记录 (共 {len(records)} 条):")
    click.echo("-" * 70)

    for r in records:
        click.echo(
            f"  {r.release_date.strftime('%Y-%m-%d')} | "
            f"{r.start_date} ~ {r.end_date} | "
            f"{r.file_count} 文件"
        )


@cli.command()
@click.option('--start', required=True, help='开始日期 (YYYY_MM_DD)')
@click.option('--end', required=True, help='结束日期 (YYYY_MM_DD)')
@click.option('--output', '-o', default='period_report.md', help='输出文件名')
@click.pass_context
def report(ctx, start, end, output):
    """生成时间段报告"""
    config = ctx.obj['config']
    history_root = config.get_path('paths.history_root')
    output_root = config.get_path('paths.output_root')

    history_service = HistoryService(str(history_root))
    doc_service = DocService(str(output_root))

    records = history_service.get_by_date_range(start, end)

    if not records:
        click.echo("指定时间范围内没有发版记录")
        return

    output_path = doc_service.generate_period_report(records, start, end, output)
    click.echo(f"报告已生成: {output_path}")


@cli.command()
@click.pass_context
def status(ctx):
    """显示当前状态"""
    service = ReleaseService(ctx.obj['config'])

    latest_end = service.get_latest_end_date()
    suggested_start = service.get_suggested_start_date()

    click.echo("\nSQL 发版工具状态")
    click.echo("-" * 40)
    if latest_end:
        click.echo(f"上次发版结束日期: {latest_end}")
        click.echo(f"建议本次开始日期: {suggested_start}")
    else:
        click.echo("暂无发版记录")


@cli.command()
@click.pass_context
def info(ctx):
    """显示当前项目信息"""
    config = ctx.obj['config']

    click.echo("\n当前项目信息")
    click.echo("-" * 50)
    click.echo(f"  项目 ID:     {config.get('project.id', 'default')}")
    click.echo(f"  项目名称:    {config.get('project.name', '-')}")
    click.echo(f"  项目描述:    {config.get('project.description', '-')}")
    click.echo(f"  目录结构:    {config.get_structure_mode()}")
    click.echo(f"  发版模式:    {config.get_release_mode()}")
    click.echo(f"  命名模式:    {config.get_naming_mode()}")
    click.echo(f"  源目录:      {config.get_path('paths.master_root')}")
    click.echo(f"  输出目录:    {config.get_path('paths.output_root')}")
    click.echo(f"  历史目录:    {config.get_path('paths.history_root')}")


@cli.command()
@click.pass_context
def projects(ctx):  # noqa: ARG001
    """列出所有已注册项目"""
    registered = ConfigLoader.list_projects()

    click.echo("\n已注册项目")
    click.echo("-" * 60)

    if not registered:
        click.echo("  暂无已注册项目")
        click.echo("\n  使用 ConfigLoader.register_project() 注册项目")
        return

    for pid in registered:
        cfg = ConfigLoader.get_instance(pid)
        name = cfg.get('project.name', pid)
        desc = cfg.get('project.description', '')
        click.echo(f"  {pid:20} | {name:15} | {desc}")


@cli.command()
@click.pass_context
def init_history(ctx):
    """初始化历史记录文件"""
    config = ctx.obj['config']
    history_root = config.get_path('paths.history_root')
    service = HistoryService(str(history_root))

    # 创建空的 YAML 文件
    import yaml
    yaml_path = service.yaml_path
    data = {
        'version': '2.0',
        'updated': None,
        'releases': []
    }

    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True)

    click.echo(f"已初始化: {yaml_path}")


if __name__ == '__main__':
    cli()