# SQL 发版工具

> 重构版本 - 基于 Python 的 SQL 文件管理和发版工具
> Version: 3.0 - 支持多项目

## 快速开始

### Windows 用户（推荐）

使用 `run.bat` 脚本一键运行：

```bash
# 查看帮助
run.bat --help

# 查看项目信息
run.bat info

# 查看状态
run.bat status

# 预览文件
run.bat merge --preview --start 2026_03_01

# 执行合并
run.bat merge --start 2026_03_01 --end 2026_03_18 --notes "发版说明"
```

### 多项目使用

支持在多个项目间切换：

```bash
# 使用指定配置文件
python sql_release_cli.py -c /path/to/settings.yaml info

# 使用项目 ID（需先注册）
python sql_release_cli.py -p ruoyi-vue-pro info
```

### 命令行用户

```bash
# 安装依赖
pip install -r requirements.txt

# 查看帮助
python sql_release_cli.py --help
```

## 功能特性

- **文件扫描**: 自动识别 `sql/master` 目录下的 SQL 文件格式
- **日期过滤**: 按日期范围筛选文件
- **自动分类**: 根据文件名自动识别 SQL 类型（建表、更新、索引、序列等）
- **历史记录**: YAML + Markdown 双格式存储发版历史
- **报告生成**: 支持时间段整合报告生成
- **统一 CLI**: 命令行工具，一键操作

## 安装

```bash
# 安装依赖
pip install -r requirements.txt
```

## 命令列表

| 命令 | 说明 | 示例 |
|------|------|------|
| `info` | 显示当前项目信息 | `run.bat info` |
| `status` | 显示当前状态 | `run.bat status` |
| `merge --preview` | 预览要发布的文件 | `run.bat merge --preview --start 2026_03_01` |
| `merge` | 执行合并发版 | `run.bat merge --start 2026_03_01 --end 2026_03_18` |
| `history` | 查看发版历史 | `run.bat history` |
| `report` | 生成时间段报告 | `run.bat report --start 2026_01 --end 2026_03` |
| `init-history` | 初始化历史记录 | `run.bat init-history` |
| `projects` | 列出已注册项目 | `run.bat projects` |

## 全局选项

| 选项 | 说明 |
|------|------|
| `-c, --config` | 指定配置文件路径 |
| `-p, --project` | 指定项目 ID |

## merge 命令选项

| 选项 | 说明 |
|------|------|
| `--start` | 开始日期 (YYYY_MM_DD) |
| `--end` | 结束日期 (YYYY_MM_DD) |
| `--preview` | 预览模式，不执行合并 |
| `--notes` | 发版说明 |
| `--no-subfolder` | 不在 output 下创建日期子文件夹 |
| `--append` | 追加模式，追加到现有文件 |
| `--no-timestamp` | 文件名不添加时间戳 |

**示例**：

```bash
# 默认：创建日期子文件夹 + 添加时间戳
run.bat merge --start 2026_03_19 --end 2026_03_25
# 输出: output/20260318/unknown_merged_143052.sql

# 不创建子文件夹，不添加时间戳
run.bat merge --start 2026_03_19 --no-subfolder --no-timestamp
# 输出: output/unknown_merged.sql

# 追加到现有文件
run.bat merge --start 2026_03_19 --append --no-timestamp
```

## 使用方法

### 预览文件

```bash
# 预览要发布的文件
run.bat merge --preview --start 2026_03_01

# 预览指定日期范围
run.bat merge --preview --start 2026_03_01 --end 2026_03_18
```

### 执行合并

```bash
# 合并 SQL 文件
run.bat merge --start 2026_03_01 --end 2026_03_18

# 带发版说明
run.bat merge --start 2026_03_01 --end 2026_03_18 --notes "新增信件索引"
```

### 查看历史

```bash
# 查看所有发版历史
run.bat history

# 查看指定时间范围
run.bat history --start 2026_01 --end 2026_03
```

### 生成报告

```bash
# 生成时间段整合报告
run.bat report --start 2026_01_01 --end 2026_03_18
```

### 其他命令

```bash
# 显示状态
run.bat status

# 初始化历史记录
run.bat init-history
```

## 目录结构

```
sql_release/
├── sql_release_cli.py      # CLI 入口
├── config/
│   ├── settings.yaml       # 配置文件
│   └── config_loader.py    # 配置加载器
├── core/
│   ├── scanner.py          # SQL 文件扫描器
│   └── merger.py           # SQL 合并器
├── services/
│   ├── release_service.py  # 发版服务
│   ├── history_service.py  # 历史服务
│   └── doc_service.py      # 文档生成服务
├── models/
│   ├── sql_file.py         # SQL 文件模型
│   └── release_record.py   # 发版记录模型
├── utils/
│   ├── logger.py           # 日志工具
│   └── date_utils.py       # 日期工具
├── history/                # 历史记录存储
│   ├── releases.yaml       # YAML 格式
│   └── release_history.md  # Markdown 格式
└── output/                 # 输出目录
```

## SQL 源文件目录结构

```
sql/master/
├── data/                      # 数据初始化 (data_init)
│   ├── 2026_01_15_fz_letter_data.sql
│   └── 2026_02_20_sys_menu_data.sql
├── index/                     # 索引 (index)
│   ├── 2026_02_07_fz_letter_reply_idx.sql
│   └── 2026_03_10_fz_handle_unit_idx.sql
├── seq/                       # 序列 (sequence)
│   ├── 2025_08_15_fz_letter_seq.sql
│   └── 2026_01_20_fz_reply_seq.sql
├── table/
│   ├── create/                # 建表语句 (table_create)
│   │   ├── 2025_08_01_fz_letter_create.sql
│   │   └── 2026_01_10_fz_handle_unit_create.sql
│   └── update/                # 表结构更新 (table_update)
│       ├── 2026_03_09_fz_letter_handle_update.sql
│       └── 2026_03_15_sys_user_update.sql
├── view/                      # 视图 (view)
│   ├── 2025_09_01_v_letter_list.sql
│   └── 2026_02_01_v_user_stats.sql
└── mysql/                     # MySQL 版本 (默认排除)
    └── ...
```

**重要**：文件分类由**源目录**决定，不是文件名后缀。

| 源目录 | 输出分类 | 说明 |
|--------|----------|------|
| `table/create/` | `table_create` | 建表语句 |
| `table/update/` | `table_update` | 表结构更新 |
| `index/` | `index` | 索引 |
| `seq/` | `sequence` | 序列 |
| `data/` | `data_init` | 数据初始化 |
| `view/` | `view` | 视图 |

## SQL 文件命名规则

### 标准格式

```
{YYYY_MM_DD}_{表名}_{操作类型}{数据库版本}.sql
```

### 组成部分

| 部分 | 格式 | 说明 | 示例 |
|------|------|------|------|
| 日期 | `YYYY_MM_DD` | 文件创建日期 | `2026_03_18` |
| 表名 | 小写字母+下划线 | 关联的数据库表名 | `fz_letter`, `sys_user` |
| 操作类型 | 可选后缀 | 标识操作类型 | `_create`, `_update`, `_idx`, `_seq` |
| 数据库版本 | 可选后缀 | 数据库类型标识 | `_pg` (PostgreSQL/Kingbase) |

### 操作类型后缀

| 后缀 | 说明 | 目录位置 |
|------|------|----------|
| `_create` | 建表语句 | `table/create/` |
| `_update` | 表结构更新 | `table/update/` |
| `_idx` | 索引 | `index/` |
| `_seq` | 序列 | `seq/` |
| 无后缀 | 数据初始化或其他 | `data/` 或其他 |

### 数据库版本后缀

| 后缀 | 说明 |
|------|------|
| 无后缀 | 通用 SQL 或 MySQL 格式 |
| `_pg` | PostgreSQL / Kingbase 格式 |

### 命名示例

```
# 建表语句
2025_08_01_fz_letter_create.sql          # MySQL/通用建表
2025_08_01_fz_letter_create_pg.sql       # PostgreSQL/Kingbase 建表

# 表结构更新
2026_03_09_fz_letter_handle_update.sql   # 表结构更新
2026_03_09_fz_letter_handle_update_pg.sql

# 索引
2026_02_07_fz_letter_reply_idx.sql       # 索引语句
2026_02_07_fz_letter_reply_idx_pg.sql

# 序列
2025_08_15_fz_letter_seq.sql             # 序列语句
2025_08_15_fz_letter_seq_pg.sql

# 数据初始化
2026_01_15_fz_letter_data.sql            # 数据初始化
2026_01_15_fz_letter_data_pg.sql

# 视图
2025_09_01_v_letter_list.sql             # 视图定义
```

### 命名规范

1. **日期格式固定**：必须使用 `YYYY_MM_DD` 格式，用下划线分隔
2. **表名小写**：表名使用小写字母，单词间用下划线连接
3. **后缀顺序**：操作类型在前，数据库版本在后
4. **文件扩展名**：统一使用 `.sql` 小写

## 配置说明

编辑 `config/settings.yaml` 文件:

```yaml
# 项目元信息
project:
  id: "gaxx-pro"              # 项目唯一标识
  name: "法制系统"             # 项目名称
  description: "法制办信件管理系统"

# 路径配置
paths:
  master_root: "../master"    # SQL 源文件目录
  output_root: "./output"     # 输出目录

  # 目录结构模式: by_operation | by_database | flat
  structure_mode: "by_operation"

# 发版模式: incremental | full
release:
  mode: "incremental"         # 增量发版

# 过滤配置
filters:
  exclude_dirs:
    - "mysql"                 # 排除 MySQL 目录
```

## 发版流程

```
1. 查看上次发版结束日期
   $ run.bat status

2. 预览要发布的文件
   $ run.bat merge --preview --start 2026_03_19

3. 执行合并
   $ run.bat merge --start 2026_03_19 --end 2026_03_25 --notes "发版说明"

4. 查看历史记录
   $ run.bat history
```

## 输出文件

合并后生成的文件：

| 文件 | 说明 |
|------|------|
| `output/YYYYMMDD/table_create_merged.sql` | 建表语句（来自 table/create 目录） |
| `output/YYYYMMDD/table_update_merged.sql` | 表更新语句（来自 table/update 目录） |
| `output/YYYYMMDD/index_merged.sql` | 索引语句（来自 index 目录） |
| `output/YYYYMMDD/sequence_merged.sql` | 序列语句（来自 seq 目录） |
| `output/YYYYMMDD/data_init_merged.sql` | 数据初始化（来自 data 目录） |
| `history/releases.yaml` | YAML 格式历史记录 |
| `history/release_history.md` | Markdown 格式历史记录 |

**注意**：分类由**源目录**决定，不是文件名后缀。

## 与原工具的关系

本工具是全新重构版本，原 `sql/tools/` 目录下的工具保留不变。

主要改进:
- 外部配置文件，无需修改代码
- 完整的历史记录（YAML + Markdown 双格式）
- 自动文件分类和识别
- 时间段整合报告生成
- 模块化架构，易于扩展
- **v3.0**: 支持多项目配置

## 多项目支持

### 新项目接入步骤

1. 复制 `sql_release/` 目录到新项目

2. 修改 `config/settings.yaml`：

```yaml
project:
  id: "new-project"           # 项目唯一标识
  name: "新项目名称"
  description: "项目描述"

paths:
  master_root: "../master"
  structure_mode: "by_database"  # 根据项目结构调整

  # 按数据库类型分类时
  categories:
    postgresql: "postgresql"
    mysql: "mysql"
    oracle: "oracle"
```

3. 测试配置：

```bash
python sql_release_cli.py info
python sql_release_cli.py merge --preview
```

### 目录结构模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `by_operation` | 按操作类型分类 | gaxx-pro 等 |
| `by_database` | 按数据库类型分类 | ruoyi-vue-pro 等 |
| `flat` | 扁平结构 | 简单项目 |

### 发版模式

| 模式 | 说明 |
|------|------|
| `incremental` | 增量发版，按日期范围筛选 |
| `full` | 全量发版，不按日期筛选 |

## 版本历史

- v3.0.0 (2026-03-18): 多项目支持，支持多种目录结构
- v2.0.0 (2026-03-18): 重构版本，全新架构