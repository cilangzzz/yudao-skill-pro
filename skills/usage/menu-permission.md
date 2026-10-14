---
design:
  - path: skills/design/crud-designer.md
    reason: 权限标识规范 {模块}:{名}:{操作}、错误码段号、各层命名
  - path: skills/design/db-designer.md
    reason: 建表 SQL 字段类型与默认值约定（菜单 SQL 的字段类型需保持一致）
  - path: skills/design/entity-designer.md
    reason: 命名转换规则（菜单路径 → DO 字段名）
module_guide:
  mapping:
    system: docs/system/code-patterns.md
patterns: []
usage_hint: 该文档是「为新功能/新模块添加后台管理菜单与按钮」的专用规范，无需指定目标模块。涉及 system 模块接口细节时自动加载 system 模块的 code-patterns.md。
---

# 菜单权限 SQL 新增规范

> 为后台管理系统（`system_menu` 表）新增菜单与按钮权限的标准流程：逐级查找上级父菜单 ID → 序列插入菜单（type=2）→ 序列插入按钮（type=3）。
>
> 本文档统一了 [skills/usage/entity-implementation.md](entity-implementation.md) §3.8 与 [skills/usage/new-module.md](new-module.md) §5.3 中"假设父菜单 ID 为 100"的占位写法，给出可执行的查找脚本与序列插入模板。

---

## 适用场景

| 场景 | 何时使用本文档 |
|-----|----------------|
| 单实体扩展 | 在 [entity-implementation.md](entity-implementation.md) 流程末尾追加菜单权限配置时 |
| 新增模块 | 在 [new-module.md](new-module.md) 流程末尾追加完整目录→菜单→按钮层级时 |
| 临时补充菜单 | 不涉及代码变更，仅需在某个父菜单下新增一个子功能或按钮时 |

---

## 前置准备

开始前需要明确：

| 信息 | 示例 | 说明 |
|-----|------|------|
| 父菜单链路（按层级顺序） | 系统管理 → 基础设施 → 文件管理 | 每一级菜单的 `name`，用于逐级定位 `id` |
| 目标模块英文名 | `infra` | 用于权限标识 `{模块}` 段 |
| 功能英文名 | `file` | 用于权限标识 `{功能}` 段、组件路径、菜单名 |
| 功能中文名 | `文件` | 用于菜单/按钮显示名 |
| 图标 | `ep:folder` | 参考 Element Plus Icon，可省略 |
| 组件路径 | `infra/file/index` | 前端 Vue 组件路径 |

> 父菜单不存在时，需先建父级菜单——参见 [踩坑点 §1](#1-父菜单不存在或类型不对)。

---

## 一、核心流程

```
┌─────────────────────────────────────────┐
│ 1. 逐级查找父菜单 ID                      │
│    系统管理 → 基础设施 → 文件管理           │
│    各级 name 查到对应 id                  │
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│ 2. 插入菜单（type=2）                     │
│    parent_id = 父菜单 id                  │
│    获取新菜单 id（LAST_INSERT_ID）         │
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│ 3. 序列插入按钮（type=3，5 条）             │
│    parent_id = 新菜单 id                  │
│    查询/新增/修改/删除/导出                 │
└─────────────────────────────────────────┘
```

**事务**：上述 1+5 条 INSERT 必须在同一事务中执行，任一失败回滚，避免出现"菜单存在但按钮缺失"的孤儿状态。

---

## 二、查找父菜单 ID

### 2.1 单级精确查找（推荐）

```sql
-- 查找「文件管理」菜单的 id，前提是已知其父菜单「基础设施」id = 1010
SELECT id
FROM system_menu
WHERE name = '文件管理'
  AND parent_id = 1010
  AND type = 2
LIMIT 1;
```

### 2.2 逐级链路查找（已知全部层级 name）

```sql
-- 步骤 A：查找「系统管理」id（顶级目录）
SELECT id FROM system_menu
WHERE name = '系统管理' AND parent_id = 0 AND type = 1;
-- 假设返回 1

-- 步骤 B：查找「基础设施」id（parent = 1）
SELECT id FROM system_menu
WHERE name = '基础设施' AND parent_id = 1 AND type = 1;
-- 假设返回 1010

-- 步骤 C：查找「文件管理」id（parent = 1010）
SELECT id FROM system_menu
WHERE name = '文件管理' AND parent_id = 1010 AND type = 2;
-- 假设返回 1011
```

### 2.3 一次查出整条链路（MySQL 8.0+ 递归 CTE）

```sql
WITH RECURSIVE menu_path AS (
    -- 起点：目标菜单的精确匹配
    SELECT id, parent_id, name, type, 0 AS depth
    FROM system_menu
    WHERE name = '文件管理' AND type = 2

    UNION ALL

    -- 递归：向上找父菜单
    SELECT m.id, m.parent_id, m.name, m.type, mp.depth + 1
    FROM system_menu m
    INNER JOIN menu_path mp ON m.id = mp.parent_id
)
SELECT depth, id, name, type
FROM menu_path
ORDER BY depth DESC;
-- 结果示例：
-- depth=2  id=1     name=系统管理     type=1
-- depth=1  id=1010  name=基础设施     type=1
-- depth=0  id=1011  name=文件管理     type=2
```

> 若环境是 MySQL 5.7 或 Doris 等不支持递归 CTE，请使用 §2.2 逐级查询。

---

## 三、插入菜单（type=2）

### 3.1 完整字段版（推荐）

```sql
INSERT INTO system_menu (
    name, permission, type, sort, parent_id,
    path, icon, component, component_name,
    status, visible, keep_alive, always_show,
    creator, create_time, updater, update_time, deleted
)
VALUES (
    '文件管理', '', 2, 0, 1010,                   -- name, permission, type=菜单, sort, parent_id
    'file', 'ep:folder', 'infra/file/index', 'FileManagement',  -- path, icon, component, component_name
    0, b'1', b'1', b'1',                          -- status=正常, 可见/缓存/总是显示
    'admin', NOW(), 'admin', NOW(), b'0'          -- 审计字段
);

-- 立即捕获新菜单的 id
SET @menuId = LAST_INSERT_ID();
```

### 3.2 极简字段版

适用于手工补 SQL 或对字段不熟悉的场景（缺少的字段由 `use_vioce` / `keep_alive` / `always_show` 等默认值填充）：

```sql
INSERT INTO system_menu (name, permission, type, sort, parent_id, path, icon, component, status)
VALUES ('文件管理', '', 2, 0, 1010, 'file', 'ep:folder', 'infra/file/index', 0);

SET @menuId = LAST_INSERT_ID();
```

> 字段含义与 MenuTypeEnum 详见 [docs/system/api-permission.md §2.1](../../docs/system/api-permission.md)。

---

## 四、序列插入按钮（type=3）

按钮必须挂在「菜单」节点（type=2）下，**不能**挂在「目录」下。在 §三 拿到 `@menuId` 后，按以下顺序逐条插入：

```sql
-- 1. 查询
INSERT INTO system_menu (name, permission, type, sort, parent_id, status, visible, keep_alive, always_show,
                        creator, create_time, updater, update_time, deleted)
VALUES ('文件查询', 'infra:file:query', 3, 1, @menuId, 0, b'1', b'1', b'1',
        'admin', NOW(), 'admin', NOW(), b'0');

-- 2. 新增
INSERT INTO system_menu (name, permission, type, sort, parent_id, status, visible, keep_alive, always_show,
                        creator, create_time, updater, update_time, deleted)
VALUES ('文件新增', 'infra:file:create', 3, 2, @menuId, 0, b'1', b'1', b'1',
        'admin', NOW(), 'admin', NOW(), b'0');

-- 3. 修改
INSERT INTO system_menu (name, permission, type, sort, parent_id, status, visible, keep_alive, always_show,
                        creator, create_time, updater, update_time, deleted)
VALUES ('文件修改', 'infra:file:update', 3, 3, @menuId, 0, b'1', b'1', b'1',
        'admin', NOW(), 'admin', NOW(), b'0');

-- 4. 删除
INSERT INTO system_menu (name, permission, type, sort, parent_id, status, visible, keep_alive, always_show,
                        creator, create_time, updater, update_time, deleted)
VALUES ('文件删除', 'infra:file:delete', 3, 4, @menuId, 0, b'1', b'1', b'1',
        'admin', NOW(), 'admin', NOW(), b'0');

-- 5. 导出
INSERT INTO system_menu (name, permission, type, sort, parent_id, status, visible, keep_alive, always_show,
                        creator, create_time, updater, update_time, deleted)
VALUES ('文件导出', 'infra:file:export', 3, 5, @menuId, 0, b'1', b'1', b'1',
        'admin', NOW(), 'admin', NOW(), b'0');
```

### 按钮命名与排序约定

| sort | 操作 | permission 后缀 |
|------|------|----------------|
| 1 | 查询 | `query` |
| 2 | 新增 | `create` |
| 3 | 修改 | `update` |
| 4 | 删除 | `delete` |
| 5 | 导出 | `export` |

> 如需额外的 `import` / `print` 等按钮，按 sort 递增追加即可。

---

## 五、权限标识规范

**格式**：`{模块}:{功能}:{操作}`

**操作关键字枚举**（与 sort 顺序一致）：

| 操作 | 关键字 | 含义 |
|-----|-------|------|
| 查询 | `query` | 列表、详情、导出前的查询 |
| 新增 | `create` | 创建 |
| 修改 | `update` | 更新 |
| 删除 | `delete` | 删除 |
| 导出 | `export` | 导出 Excel |

**示例**：

```
system:user:query    # 后台用户查询
system:user:create   # 后台用户新增
infra:file:query     # 文件查询
infra:file:delete    # 文件删除
pay:order:export     # 支付订单导出
```

> 完整命名规范见 [skills/design/crud-designer.md §naming_standards](../design/crud-designer.md)。

---

## 六、完整示例

为 `infra` 模块新增「文件管理」功能（父菜单链：系统管理 → 基础设施 → 文件管理）。

```sql
START TRANSACTION;

-- ============ 步骤 1：逐级查找父菜单 ID ============
-- 已知：系统管理 id=1，基础设施 id=1010
-- 验证：文件管理 id 是否已存在（避免重复）
SELECT id FROM system_menu WHERE name = '文件管理' AND parent_id = 1010 AND type = 2;
-- 若返回非空：菜单已存在，跳过步骤 2

-- ============ 步骤 2：插入菜单 ============
INSERT INTO system_menu (name, permission, type, sort, parent_id, path, icon, component, component_name,
                       status, visible, keep_alive, always_show,
                       creator, create_time, updater, update_time, deleted)
VALUES ('文件管理', '', 2, 0, 1010, 'file', 'ep:folder', 'infra/file/index', 'FileManagement',
        0, b'1', b'1', b'1',
        'admin', NOW(), 'admin', NOW(), b'0');

SET @menuId = LAST_INSERT_ID();

-- ============ 步骤 3：序列插入 5 个按钮 ============
INSERT INTO system_menu (name, permission, type, sort, parent_id, status, visible, keep_alive, always_show,
                        creator, create_time, updater, update_time, deleted)
VALUES ('文件查询', 'infra:file:query', 3, 1, @menuId, 0, b'1', b'1', b'1', 'admin', NOW(), 'admin', NOW(), b'0');

INSERT INTO system_menu (name, permission, type, sort, parent_id, status, visible, keep_alive, always_show,
                        creator, create_time, updater, update_time, deleted)
VALUES ('文件新增', 'infra:file:create', 3, 2, @menuId, 0, b'1', b'1', b'1', 'admin', NOW(), 'admin', NOW(), b'0');

INSERT INTO system_menu (name, permission, type, sort, parent_id, status, visible, keep_alive, always_show,
                        creator, create_time, updater, update_time, deleted)
VALUES ('文件修改', 'infra:file:update', 3, 3, @menuId, 0, b'1', b'1', b'1', 'admin', NOW(), 'admin', NOW(), b'0');

INSERT INTO system_menu (name, permission, type, sort, parent_id, status, visible, keep_alive, always_show,
                        creator, create_time, updater, update_time, deleted)
VALUES ('文件删除', 'infra:file:delete', 3, 4, @menuId, 0, b'1', b'1', b'1', 'admin', NOW(), 'admin', NOW(), b'0');

INSERT INTO system_menu (name, permission, type, sort, parent_id, status, visible, keep_alive, always_show,
                        creator, create_time, updater, update_time, deleted)
VALUES ('文件导出', 'infra:file:export', 3, 5, @menuId, 0, b'1', b'1', b'1', 'admin', NOW(), 'admin', NOW(), b'0');

COMMIT;

-- ============ 步骤 4：分配给超级管理员角色（可选）============
-- 默认超级管理员 role_id=1（具体视业务而定）
INSERT INTO system_role_menu (role_id, menu_id)
SELECT 1, id FROM system_menu
WHERE permission LIKE 'infra:file:%' OR id = @menuId;
```

---

## 七、踩坑点

### 1. 父菜单不存在或类型不对

**症状**：`parent_id` 引用了不存在的菜单或父菜单是按钮（type=3）。

**处理**：

- 父菜单不存在：递归往上建（按链路查找直至找到已存在的层级，再从下一级开始 INSERT）
- 父菜单类型不对：MenuDO 要求父菜单必须是 `type=1`（目录）或 `type=2`（菜单），按钮下不能挂任何节点。错误码 `1_002_001_005` 对应「父菜单的类型必须是目录或者菜单」。

### 2. 同一父菜单下名称重复

**症状**：业务方在不同分支误用了同一个中文名。

**处理**：执行前先查 `SELECT name FROM system_menu WHERE parent_id = ? AND name = ?`；错误码 `1_002_001_000`。

### 3. 同一父菜单下组件名重复

**症状**：不同功能用了同一个 `component_name`，导致前端路由冲突。

**处理**：执行前查 `SELECT component_name FROM system_menu WHERE component_name = ?`；错误码 `1_002_001_006`。

### 4. 按钮权限缓存未清理

**症状**：新增按钮后角色授权仍报"无权限"。

**处理**：菜单权限缓存按 `permission` 字段做 key，新增按钮后需清空 `MenuService` 的本地缓存（一般重启服务或调用 `clearMenuCache()`）。参见 [docs/system/code-patterns.md §缓存管理](../../docs/system/code-patterns.md)。

### 5. `@menuId` 跨连接失效

**症状**：业务代码中 `@menuId` 取到 `null` 或上一个连接的值。

**原因**：MySQL 用户变量 `SET @x = ...` 是**会话级**的，只在同一个数据库连接内有效。批量执行工具（如 Navicat 多窗口）可能使用不同连接。

**处理**：

- 单次会话内执行：把步骤 2、3 放在同一个 SQL 窗口
- 跨会话：用 `INSERT ... ; SELECT LAST_INSERT_ID() INTO @menuId` 强制同连接
- 应用层：交给代码生成器（MyBatis-Plus）执行，避免手工变量

### 6. 多租户场景

**症状**：新建租户下看不到刚插入的菜单。

**原因**：`system_menu` 表继承 `TenantBaseDO`，`tenant_id` 默认 0 是平台菜单，**不要**手动给平台菜单指定非 0 的 `tenant_id`。

**处理**：平台级菜单直接省略该列（自动为 0）；租户级菜单通过「租户套餐-菜单」复制机制由框架自动同步，不要直接 INSERT。

---

## 八、相关文档

- 上游流程：[skills/usage/entity-implementation.md](entity-implementation.md) §3.8（单实体实现末尾）· [skills/usage/new-module.md](new-module.md) §5.3（新增模块末尾）
- 接口与校验：[docs/system/api-permission.md §2 菜单管理](../../docs/system/api-permission.md)
- 数据模型：[docs/system/data-model.md](../../docs/system/data-model.md)（`system_menu` / `system_role_menu` 表结构）
- 命名规范：[skills/design/crud-designer.md §naming_standards](../design/crud-designer.md)
- 权限注解：Controller 中 `@PreAuthorize("@ss.hasPermission('infra:file:create')")` 示例见 [quick-start.md §3.6](quick-start.md)