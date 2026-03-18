@echo off
REM SQL 发版工具 - Windows 启动脚本
REM 使用方法: run.bat [命令] [参数]

REM 设置 UTF-8 编码
chcp 65001 >nul 2>&1

REM 设置 Python 路径
set PYTHON=G:\python3.8.10\python.exe

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0

REM 运行 CLI
%PYTHON% "%SCRIPT_DIR%sql_release_cli.py" %*

REM 暂停（如果直接双击运行）
if "%1"=="" pause