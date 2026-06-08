# CRM 数据模型

## 实体继承体系

所有 CRM 实体继承 `BaseDO`，包含以下公共字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| creator | VARCHAR | 创建人 |
| create_time | DATETIME | 创建时间 |
| updater | VARCHAR | 更新人 |
| update_time | DATETIME | 更新时间 |
| deleted | BIT | 逻辑删除标记 |

> **注意**：CRM 模块未使用 TenantBaseDO，不涉及多租户。

---

## 数据表清单

### 客户相关

#### crm_customer（客户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| name | VARCHAR | 客户名称 |
| follow_up_status | TINYINT | 跟进状态 |
| contact_last_time | DATETIME | 最后跟进时间 |
| contact_last_content | VARCHAR | 最后跟进内容 |
| contact_next_time | DATETIME | 下次联系时间 |
| owner_user_id | BIGINT | 负责人用户编号 |
| owner_time | DATETIME | 成为负责人时间 |
| lock_status | TINYINT | 锁定状态 |
| deal_status | TINYINT | 成交状态 |
| mobile | VARCHAR | 手机号 |
| telephone | VARCHAR | 电话 |
| qq | VARCHAR | QQ |
| wechat | VARCHAR | 微信 |
| email | VARCHAR | 邮箱 |
| area_id | INT | 地区ID |
| detail_address | VARCHAR | 详细地址 |
| industry_id | INT | 所属行业 |
| level | INT | 客户等级 |
| source | INT | 客户来源 |
| remark | VARCHAR | 备注 |

索引：
- `idx_owner_user_id`（owner_user_id）
- `idx_name`（name）

#### crm_customer_pool_config（客户公海池配置表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| enabled | TINYINT | 是否启用客户公海 |
| contact_expire_days | INT | 未跟进放入公海天数 |
| deal_expire_days | INT | 未成交放入公海天数 |
| notify_enabled | TINYINT | 是否开启提前提醒 |
| notify_days | INT | 提前提醒天数 |

#### crm_customer_limit_config（客户限制配置表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| type | INT | 限制类型（拥有上限/锁定上限） |
| max_count | INT | 最大数量 |
| deal_count_enabled | TINYINT | 是否计入成交客户 |
| user_ids | VARCHAR | 适用用户ID列表 |
| dept_ids | VARCHAR | 适用部门ID列表 |

---

### 线索相关

#### crm_clue（线索表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| name | VARCHAR | 线索名称 |
| follow_up_status | TINYINT | 跟进状态 |
| contact_last_time | DATETIME | 最后跟进时间 |
| contact_last_content | VARCHAR | 最后跟进内容 |
| contact_next_time | DATETIME | 下次联系时间 |
| owner_user_id | BIGINT | 负责人用户编号 |
| transform_status | TINYINT | 转化状态 |
| customer_id | BIGINT | 转化后的客户ID |
| mobile | VARCHAR | 手机号 |
| telephone | VARCHAR | 电话 |
| qq | VARCHAR | QQ |
| wechat | VARCHAR | 微信 |
| email | VARCHAR | 邮箱 |
| area_id | INT | 地区ID |
| detail_address | VARCHAR | 详细地址 |
| industry_id | INT | 所属行业 |
| level | INT | 客户等级 |
| source | INT | 客户来源 |
| remark | VARCHAR | 备注 |

---

### 联系人相关

#### crm_contact（联系人表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| name | VARCHAR | 联系人姓名 |
| customer_id | BIGINT | 客户ID |
| contact_last_time | DATETIME | 最后跟进时间 |
| contact_last_content | VARCHAR | 最后跟进内容 |
| contact_next_time | DATETIME | 下次联系时间 |
| owner_user_id | BIGINT | 负责人用户编号 |
| mobile | VARCHAR | 手机号 |
| telephone | VARCHAR | 电话 |
| email | VARCHAR | 邮箱 |
| qq | BIGINT | QQ |
| wechat | VARCHAR | 微信 |
| area_id | INT | 地区ID |
| detail_address | VARCHAR | 详细地址 |
| sex | INT | 性别 |
| master | TINYINT | 是否关键决策人 |
| post | VARCHAR | 职位 |
| parent_id | BIGINT | 直属上级ID |
| remark | VARCHAR | 备注 |

#### crm_contact_business（联系人商机关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| contact_id | BIGINT | 联系人ID |
| business_id | BIGINT | 商机ID |

---

### 商机相关

#### crm_business（商机表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| name | VARCHAR | 商机名称 |
| customer_id | BIGINT | 客户ID |
| follow_up_status | TINYINT | 跟进状态 |
| contact_last_time | DATETIME | 最后跟进时间 |
| contact_next_time | DATETIME | 下次联系时间 |
| owner_user_id | BIGINT | 负责人用户编号 |
| status_type_id | BIGINT | 商机状态组ID |
| status_id | BIGINT | 商机状态ID |
| end_status | INT | 结束状态（赢单/输单/无效） |
| end_remark | VARCHAR | 结束备注 |
| deal_time | DATETIME | 预计成交日期 |
| total_product_price | DECIMAL | 产品总金额 |
| discount_percent | DECIMAL | 整单折扣 |
| total_price | DECIMAL | 商机总金额 |
| remark | VARCHAR | 备注 |

#### crm_business_status_type（商机状态组表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| name | VARCHAR | 状态组名称 |
| dept_ids | VARCHAR | 使用的部门ID列表 |

#### crm_business_status（商机状态表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| type_id | BIGINT | 状态组ID |
| name | VARCHAR | 状态名称 |
| percent | INT | 赢单率百分比 |
| sort | INT | 排序 |

#### crm_business_product（商机产品关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| business_id | BIGINT | 商机ID |
| product_id | BIGINT | 产品ID |
| count | DECIMAL | 数量 |
| price | DECIMAL | 单价 |

---

### 合同相关

#### crm_contract（合同表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| name | VARCHAR | 合同名称 |
| no | VARCHAR | 合同编号 |
| customer_id | BIGINT | 客户ID |
| business_id | BIGINT | 商机ID |
| contact_last_time | DATETIME | 最后跟进时间 |
| owner_user_id | BIGINT | 负责人用户编号 |
| process_instance_id | VARCHAR | 工作流实例ID |
| audit_status | INT | 审批状态 |
| order_date | DATETIME | 下单日期 |
| start_time | DATETIME | 开始时间 |
| end_time | DATETIME | 结束时间 |
| total_product_price | DECIMAL | 产品总金额 |
| discount_percent | DECIMAL | 整单折扣 |
| total_price | DECIMAL | 合同总金额 |
| sign_contact_id | BIGINT | 客户签约人ID |
| sign_user_id | BIGINT | 公司签约人ID |
| remark | VARCHAR | 备注 |

#### crm_contract_config（合同配置表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| deposit_enabled | TINYINT | 是否开启押金 |
| deposit_percent | DECIMAL | 押金比例 |

#### crm_contract_product（合同产品关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| contract_id | BIGINT | 合同ID |
| product_id | BIGINT | 产品ID |
| count | DECIMAL | 数量 |
| price | DECIMAL | 单价 |

---

### 回款相关

#### crm_receivable（回款表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| no | VARCHAR | 回款编号 |
| plan_id | BIGINT | 回款计划ID |
| customer_id | BIGINT | 客户ID |
| contract_id | BIGINT | 合同ID |
| owner_user_id | BIGINT | 负责人用户编号 |
| return_time | DATETIME | 回款日期 |
| return_type | INT | 回款方式 |
| price | DECIMAL | 回款金额 |
| remark | VARCHAR | 备注 |
| process_instance_id | VARCHAR | 工作流实例ID |
| audit_status | INT | 审批状态 |

#### crm_receivable_plan（回款计划表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| period | INT | 期数 |
| customer_id | BIGINT | 客户ID |
| contract_id | BIGINT | 合同ID |
| owner_user_id | BIGINT | 负责人用户编号 |
| return_time | DATETIME | 计划回款日期 |
| return_type | INT | 计划回款类型 |
| price | DECIMAL | 计划回款金额 |
| receivable_id | BIGINT | 实际回款ID |
| remind_days | INT | 提前提醒天数 |
| remind_time | DATETIME | 提醒日期 |
| remark | VARCHAR | 备注 |

---

### 产品相关

#### crm_product（产品表）

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

#### crm_product_category（产品分类表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| name | VARCHAR | 分类名称 |
| parent_id | BIGINT | 父分类ID |
| sort | INT | 排序 |

---

### 权限与跟进

#### crm_permission（数据权限表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| biz_type | INT | 业务类型 |
| biz_id | BIGINT | 业务ID |
| user_id | BIGINT | 用户ID |
| level | INT | 权限级别 |

索引：
- `idx_biz`（biz_type, biz_id）
- `idx_user`（user_id）

#### crm_follow_up_record（跟进记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键ID |
| biz_type | INT | 业务类型 |
| biz_id | BIGINT | 业务ID |
| type | INT | 跟进类型 |
| content | VARCHAR | 跟进内容 |
| next_time | DATETIME | 下次联系时间 |
| pic_urls | VARCHAR | 图片URL列表 |
| file_urls | VARCHAR | 附件URL列表 |
| business_ids | VARCHAR | 关联商机ID列表 |
| contact_ids | VARCHAR | 关联联系人ID列表 |

---

## ER 关系图

```
crm_customer (客户)
  ├── 1:N ── crm_business (商机)         [customer_id]
  ├── 1:N ── crm_contact (联系人)        [customer_id]
  ├── 1:N ── crm_contract (合同)         [customer_id]
  ├── 1:N ── crm_receivable (回款)       [customer_id]
  └── 1:N ── crm_receivable_plan (回款计划) [customer_id]

crm_clue (线索)
  └── N:1 ── crm_customer (客户)         [customer_id, 转化后关联]

crm_business (商机)
  └── 1:N ── crm_contract (合同)         [business_id]

crm_contract (合同)
  ├── 1:N ── crm_receivable (回款)       [contract_id]
  └── 1:N ── crm_receivable_plan (回款计划) [contract_id]

crm_receivable_plan (回款计划)
  └── 1:1 ── crm_receivable (回款)       [receivable_id]

crm_business_status_type (状态组)
  └── 1:N ── crm_business_status (状态)  [type_id]

crm_product_category (产品分类)
  └── 1:N ── crm_product (产品)          [category_id]

crm_contact (联系人) <──N:N──> crm_business (商机)
  关联表: crm_contact_business [contact_id, business_id]

crm_business (商机) <──N:N──> crm_product (产品)
  关联表: crm_business_product [business_id, product_id]

crm_contract (合同) <──N:N──> crm_product (产品)
  关联表: crm_contract_product [contract_id, product_id]
```

---

## 关系说明

| 关系 | 类型 | 外键 | 说明 |
|------|------|------|------|
| 客户 -> 商机 | 1:N | customer_id | 一个客户可以有多个商机 |
| 客户 -> 联系人 | 1:N | customer_id | 一个客户可以有多个联系人 |
| 客户 -> 合同 | 1:N | customer_id | 一个客户可以签订多个合同 |
| 客户 -> 回款 | 1:N | customer_id | 一个客户可以有多个回款 |
| 商机 -> 合同 | 1:N | business_id | 一个商机可以签订多个合同 |
| 合同 -> 回款 | 1:N | contract_id | 一个合同可以有多个回款 |
| 合同 -> 回款计划 | 1:N | contract_id | 一个合同可以有多个回款计划 |
| 回款计划 -> 回款 | 1:1 | receivable_id | 一个回款计划对应一个实际回款 |
| 状态组 -> 状态 | 1:N | type_id | 一个状态组包含多个状态 |
| 产品分类 -> 产品 | 1:N | category_id | 一个分类下有多个产品 |
| 线索 -> 客户 | N:1 | customer_id | 线索转化为客户 |
| 联系人 <-> 商机 | N:N | contact_business | 多对多关联 |
| 商机 <-> 产品 | N:N | business_product | 多对多关联 |
| 合同 <-> 产品 | N:N | contract_product | 多对多关联 |
