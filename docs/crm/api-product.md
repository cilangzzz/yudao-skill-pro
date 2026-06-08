# 产品管理 API

## 概述

产品管理维护企业的产品信息和分类体系。产品被商机和合同引用，支持多级分类、价格管理、状态控制等功能。

## Controller

| Controller | 路径前缀 | 说明 |
|------------|----------|------|
| CrmProductController | `/crm/product` | 产品管理接口 |
| CrmProductCategoryController | `/crm/product-category` | 产品分类接口 |

## 接口列表

### 产品管理

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 创建产品 | POST | `/crm/product/create` | `crm:product:create` | 创建产品 |
| 更新产品 | PUT | `/crm/product/update` | `crm:product:update` | 编辑产品信息 |
| 删除产品 | DELETE | `/crm/product/delete` | `crm:product:delete` | 删除产品 |
| 获取产品详情 | GET | `/crm/product/get` | `crm:product:query` | 查询产品详情 |
| 产品分页查询 | GET | `/crm/product/page` | `crm:product:query` | 按名称、分类等条件过滤 |
| 产品列表查询 | GET | `/crm/product/list` | `crm:product:query` | 轻量级列表 |

### 产品分类

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 创建分类 | POST | `/crm/product-category/create` | `crm:product:category:create` | 创建产品分类 |
| 更新分类 | PUT | `/crm/product-category/update` | `crm:product:category:update` | 编辑分类 |
| 删除分类 | DELETE | `/crm/product-category/delete` | `crm:product:category:delete` | 删除分类 |
| 获取分类详情 | GET | `/crm/product-category/get` | `crm:product:category:query` | 查询分类详情 |
| 分类列表查询 | GET | `/crm/product-category/list` | `crm:product:category:query` | 查询分类树 |

## 核心数据模型

### CrmProductDO

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| name | VARCHAR | 产品名称 |
| no | VARCHAR | 产品编码 |
| unit | INT | 单位 |
| price | DECIMAL | 价格 |
| status | INT | 状态 |
| category_id | BIGINT | 分类ID |
| description | VARCHAR | 产品描述 |
| owner_user_id | BIGINT | 负责人用户编号 |

### CrmProductCategoryDO

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| name | VARCHAR | 分类名称 |
| parent_id | BIGINT | 父分类ID |
| sort | INT | 排序 |

## 业务规则

1. **多级分类**：通过 parent_id 实现分类的树形结构
2. **产品引用**：产品被 crm_business_product 和 crm_contract_product 关联引用，删除前需检查是否被引用
3. **状态控制**：产品支持启用/禁用状态，禁用的产品不能被商机或合同新增引用

## 关键文件

| 文件 | 说明 |
|------|------|
| `service/product/CrmProductService.java` | 产品服务接口 |
| `service/product/CrmProductCategoryService.java` | 产品分类服务接口 |
| `controller/admin/product/CrmProductController.java` | 产品控制器 |
| `controller/admin/product/CrmProductCategoryController.java` | 产品分类控制器 |
| `dal/dataobject/product/CrmProductDO.java` | 产品实体类 |
| `dal/dataobject/product/CrmProductCategoryDO.java` | 产品分类实体类 |
