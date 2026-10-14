---
name: db-ops
description: |
  yudao-skill-pro 的数据库操作技能：通过解析 application.yaml 自动获取数据库凭证，
  本地直连或经 badseal/ssh-skill 中转到 dev/prod 环境执行 SQL，最后通过 SQL 自检验证程序成果。

  触发场景：
  - 用户提出"执行 SQL"、"建表"、"插入数据"、"查询数据"等
  - 用户要求"验证程序成果"、"确认表结构"、"对比数据"
  - 任何涉及 yudao 项目数据库修改、查询、DDL、DML 的请求

  实现机制：
  - 本技能本身不包含可执行脚本，agent 直接调用系统命令（mysql/psql/sqlplus 等）
  - 远程环境委托给 badseal/ssh-skill（agent 自动检测/安装）
---

# 数据库操作技能 (db-ops)

> 本技能提供一套**安全的工作流**让 agent 在 yudao 项目中执行数据库操作。技能本身只是文档与流程指引，**真正的执行依赖**：
> - 本地环境：DB 客户端（mysql / psql / sqlplus / sqlcmd 等）
> - 远程环境：[badseal/ssh-skill](https://github.com/badseal/ssh-skill)（首次使用前会自动检测与安装）

---

## 快速上手

### 这是什么

一个**轻量级指引技能**，让 Claude Code 在 yudao 项目里安全地执行数据库操作。它本身**不包含可执行脚本**，而是：

- **约定工作流**：解析 yaml → 选择连接方式 → dry-run → 执行 → 自检
- **委托底层操作**：本地 DB 客户端、远程 [badseal/ssh-skill](https://github.com/badseal/ssh-skill)

### 何时触发

agent 看到以下意图时会自动调用本技能：

- "帮我跑一下 SQL"、"建表"、"插入测试数据"
- "验证一下表结构"、"对比数据"
- 任何涉及 yudao 数据库的 DDL / DML / DQL

### 首次使用

agent 会自动检查以下 3 件事：

| 检查 | 缺失时 agent 行为 |
|-----|-----------------|
| `.claude/skills/ssh-skill/` 是否存在 | 提示运行 `npx skills add https://github.com/badseal/ssh-skill --skill ssh-skill` |
| `mysql` / `psql` / `sqlplus` 等客户端是否安装 | 询问用户安装方式 |
| 当前激活的 profile 与 SSH 别名 | 询问用户 |

用户需提前配置：

```bash
# ~/.ssh/config 中预先添加（如需远程连接）
Host yudao-dev-db
  HostName dev-db.internal
  User op
  IdentityFile ~/.ssh/id_rsa
```

### 故障排查

| 症状 | 可能原因 | 处理 |
|-----|---------|-----|
| `ssh-skill not found` | 未安装 | `npx skills add ...` |
| `mysql: command not found` | 客户端缺失 | 安装 mysql-client |
| `permission denied` | DB 用户权限不足 | 切换有权限的 profile 或申请授权 |
| `connection refused` | host/port 错 / SSH 别名错 | 核对 application-{profile}.yaml 与 ~/.ssh/config |
| `YES-DESTRUCTIVE required` | prod DDL 未带 token | 重新执行并显式输入 token |

---

## 0. 前置检查（每次对话首次使用时）

agent 必须先做以下 4 项检查，并在结果汇总后再继续：

### 0.1 检测 badseal/ssh-skill 是否已安装

```bash
ls -d .claude/skills/ssh-skill 2>/dev/null \
  || ls -d ~/.claude/skills/ssh-skill 2>/dev/null \
  || echo "NOT_INSTALLED"
```

- **已安装**：跳过 0.2
- **未安装**：执行 0.2

### 0.2 安装 badseal/ssh-skill（未安装时执行一次）

```bash
npx skills add https://github.com/badseal/ssh-skill --skill ssh-skill
```

> 安装位置：项目级 `.claude/skills/ssh-skill/`（如需用户级用 `--global`）。
> 安装后告知用户：badseal/ssh-skill 的官方文档地址 https://github.com/badseal/ssh-skill

### 0.3 检测本地 DB 客户端

```bash
for cmd in mysql psql sqlplus sqlcmd disql ksql; do
  command -v "$cmd" >/dev/null && echo "$cmd: $(command -v $cmd)" || echo "$cmd: NOT FOUND"
done
```

若当前 profile 需要的客户端缺失，**询问用户安装方式**而非直接放弃。

### 0.4 询问目标环境

agent 必须向用户确认：
- **profile**：local / dev / staging / prod（从 application.yaml 的 `spring.profiles.active` 推断，但允许覆盖）
- **SSH 别名**（仅 dev/prod 必需）：用户在 `~/.ssh/config` 中配置的 Host 别名（约定为 `yudao-{profile}-db`）

---

## 1. 解析数据库配置

agent 用 Read 工具读取：

```
yudao-server/src/main/resources/application.yaml           # 拿 spring.profiles.active
yudao-server/src/main/resources/application-{profile}.yaml # 拿 spring.datasource.dynamic.datasource.master.{url,username,password}
```

提取字段：

| 字段 | 用途 |
|-----|------|
| `url` | JDBC URL |
| `username` | DB 用户 |
| `password` | DB 密码 |
| `profile` | 当前激活的 profile |

### DB 类型自动检测（agent 自行判断）

| JDBC URL 前缀 | DB 类型 | 客户端命令 |
|--------------|--------|----------|
| `jdbc:mysql://` | mysql | `mysql` |
| `jdbc:postgresql://` | postgresql | `psql` |
| `jdbc:oracle:` | oracle | `sqlplus` |
| `jdbc:sqlserver://` | sqlserver | `sqlcmd` |
| `jdbc:dm://` | dm | `disql` |
| `jdbc:kingbase8://` | kingbase | `ksql` |

### 解析 JDBC URL

URL 形如 `jdbc:mysql://host:port/database?param=value`，agent 用 grep/正则提取 host / port / database：

```bash
echo "jdbc:mysql://127.0.0.1:3306/yudao?useUnicode=true" \
  | sed -E 's|jdbc:[^:]+://([^:/]+):?([0-9]*)/([^?]+)?.*|\1 \2 \3|'
# 输出: 127.0.0.1 3306 yudao
```

---

## 2. 构造连接命令

### 2.1 本地直连（profile=local）

```bash
mysql -h <host> -P <port> -u <username> -p<password> -D <database> --default-character-set=utf8mb4
psql  "host=<host> port=<port> user=<username> password=<password> dbname=<database>"
```

**重要**：agent 必须把密码传入**命令行参数或环境变量**（如 `MYSQL_PWD` / `PGPASSWORD`），**不得 echo 出密码到对话中**。

### 2.2 远程连接（dev/prod/staging）

通过 badseal/ssh-skill 调用（**禁止裸 ssh**）：

```
/ssh-skill:<alias> <remote_command>
```

或在 Bash 工具中：

```bash
python .claude/skills/ssh-skill/scripts/ssh_execute.py \
  --alias <alias> --command "<remote_db_command>"
```

agent 在远程服务器上执行时，**默认假设 `~/.my.cnf` / `~/.pgpass` 已预置凭证**，不再重复传密码。

---

## 3. 执行 SQL

### 3.1 默认 dry-run

agent 在执行任何 SQL 前必须先展示：

```
=== DRY-RUN ===
profile: <profile>
db_type: <type>
host: <host>:<port>
database: <database>
sql: <用户的 SQL>
EXPLAIN（仅 SELECT）:
<EXPLAIN 输出>
```

**等待用户明确确认后才执行**。

### 3.2 写操作（DDL/DML）

agent 必须：

1. 检查 SQL 类型（用 `awk` / `grep` 简单判断 `CREATE|DROP|ALTER|TRUNCATE|INSERT|UPDATE|DELETE`）
2. 询问用户是否执行 + 在 prod 环境下额外询问 `YES-DESTRUCTIVE` token
3. 用 BEGIN/ROLLBACK 包住 SQL，等用户 OK 再 COMMIT：
   ```
   START TRANSACTION;
   <SQL>;
   -- (让用户检查)
   COMMIT;  -- 或 ROLLBACK;
   ```
4. 记录到 `sql/db-ops.log`

### 3.3 执行示例（mysql 本地）

```bash
# dry-run
mysql -h 127.0.0.1 -P 3306 -u root -p"$MYSQL_PWD" -D yudao \
  -e "DESCRIBE system_user"

# 写操作事务
mysql -h 127.0.0.1 -P 3306 -u root -p"$MYSQL_PWD" -D yudao <<EOF
START TRANSACTION;
INSERT INTO system_user(username, password, nickname, status)
VALUES ('test_user', '...', '测试', 0);
-- 等待用户确认
COMMIT;
EOF
```

### 3.4 执行示例（psql 通过 badseal/ssh-skill）

```
/ssh-skill:yudao-dev-db psql -h <internal-host> -U <user> -d <database> -c "SELECT 1"
```

---

## 4. SQL 自检（验证程序成果）

执行后必须自检，按操作类型分类：

| 操作类型 | 自动自检 SQL | 用户可选 |
|---------|------------|---------|
| CREATE TABLE | `DESCRIBE <table>` + `SHOW CREATE TABLE <table>` | 用户给 SELECT |
| ALTER TABLE | `DESCRIBE <table>` 对比变更字段 | 用户给 SELECT |
| CREATE INDEX | `SHOW INDEX FROM <table>` | — |
| INSERT/UPDATE/DELETE | `SELECT COUNT(*)` 或受影响行验证 | 用户给 SELECT |
| SELECT | 直接展示结果 | — |
| DROP/TRUNCATE | `SHOW TABLES LIKE '<table>'` 确认不存在 | — |

自检结果以**表格**形式呈现，与用户预期对比：

| 列名 | 实际值 | 预期值 | 一致 |
|-----|-------|-------|------|

---

## 5. 安全护栏（agent 必须遵守）

### 5.1 凭证脱敏

- 对话中打印 SQL 时，密码字段替换为 `***`
- bash 命令中通过变量传递密码（不 echo）
- 日志中已脱敏

### 5.2 默认只读

- SELECT / SHOW / DESCRIBE / EXPLAIN 直接执行
- 写操作必须二次确认
- DDL 与 prod 环境必须额外 token

### 5.3 prod 强化

`profile=prod` + DDL 时，必须要求用户输入 `YES-DESTRUCTIVE` 才继续。

### 5.4 审计日志

agent 在每次执行后追加一行到 `sql/db-ops.log`：

```
[2026-10-14 12:34:56] [local] [DDL] [mysql] [confirmed]
  SQL: CREATE TABLE ...
```

---

## 6. 完整工作流示例（agent 视角）

```
1. 用户："帮我在 yudao 数据库新建一张 system_demo 表"
2. agent：
   a. 执行 §0 前置检查（检测 ssh-skill、DB 客户端、询问 profile/SSH 别名）
   b. Read application.yaml → spring.profiles.active=local
   c. Read application-local.yaml → 拿到 url/username/password
   d. 检测 DB 类型=mysql，host=127.0.0.1, db=yudao
   e. dry-run：展示 CREATE TABLE SQL + 影响估算
   f. 用户确认
   g. 执行 CREATE TABLE
   h. 自动 DESCRIBE system_demo 验证
   i. 追加审计日志
3. 输出：表结构表格 + "✓ 已创建并验证"
```

---

## 7. 相关文档

- 应用配置：[yudao-server/src/main/resources/application.yaml](../../yudao-server/src/main/resources/application.yaml)
- 错误码规范：[../design/crud-designer.md](../design/crud-designer.md)
- 设计模式：[../design/patterns/factory-pattern.md](../design/patterns/factory-pattern.md)
- badseal/ssh-skill 仓库：https://github.com/badseal/ssh-skill
- 菜单权限 SQL（如何新增菜单对照表）：[../usage/menu-permission.md](../usage/menu-permission.md)