# 购物车接口 (AppCartController)

> 记录会员用户在 App 端的购物车（表 `trade_cart`），仅 App 端提供接口（无 admin Controller）。购物车项在提交结算时被 `TradeOrderUpdateServiceImpl.createOrder` 引用，下单后通过 `TradeOrderItemDO.cartId` 关联回溯（见 [data-model.md](data-model.md) 的 CartDO 一节）。

## 接口路径前缀
/app-api/trade/cart  (Controller: AppCartController，`@Tag(name = "用户 App - 购物车")`)

## 1. 购物车操作（全部以登录用户 `getLoginUserId()` 为数据归属）

### 1.1 添加购物车商品
- **路径**: POST /app-api/trade/cart/add
- **权限**: 仅需 App 登录（无 `@PreAuthorize`）
- **说明**: 按 `userId + skuId` 维度添加购物车项；同 SKU 已存在时合并数量

**请求参数 (AppCartAddReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| skuId | Long | 是 | @NotNull("商品 SKU 编号不能为空") | 商品 SKU 编号 |
| count | Integer | 是 | @NotNull("数量不能为空")、@Min(1) | 新增购买数量 |

**响应**: CommonResult&lt;Long&gt;（购物车项编号，已存在时返回已有记录的 id）

**业务逻辑**（`CartServiceImpl#addCart`）:
1. 按 `userId + skuId` 查询已有购物车项 `CartDO`。
2. 计算合并后的数量：已存在时为 `已有 count + 本次 count`，否则为本次 count；调用 `checkProductSku` 校验（见 1.8 说明）。
3. 已存在：更新该记录的数量并重新置为选中（`selected = true`），返回原记录 id。
4. 不存在：插入新记录，`spuId` 取自校验通过的 SKU（`sku.getSpuId()`），`selected = true`。

### 1.2 更新购物车商品数量
- **路径**: PUT /app-api/trade/cart/update-count
- **权限**: 仅需 App 登录
- **说明**: 修改指定购物车项的购买数量

**请求参数 (AppCartUpdateCountReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull("编号不能为空") | 购物车项编号 |
| count | Integer | 是 | @NotNull("数量不能为空")、@Min(1) | 目标购买数量 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**（`CartServiceImpl#updateCartCount`）:
1. 按 `id + userId` 查询购物车项，不存在抛 `CARD_ITEM_NOT_FOUND`（1_011_002_000「购物车项不存在」）。
2. 按目标数量调用 `checkProductSku` 校验 SKU 存在与库存。
3. 仅更新 `count` 字段。

### 1.3 更新购物车商品选中
- **路径**: PUT /app-api/trade/cart/update-selected
- **权限**: 仅需 App 登录
- **说明**: 批量勾选 / 取消勾选购物车项

**请求参数 (AppCartUpdateSelectedReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| ids | Collection&lt;Long&gt; | 是 | @NotNull("编号列表不能为空") | 购物车项编号列表 |
| selected | Boolean | 是 | @NotNull("是否选中不能为空") | 目标选中状态 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**: `cartMapper.updateByIds(ids, userId, ...)` 按 `ids + userId` 批量更新 `selected` 字段，不校验 SKU。

### 1.4 重置购物车商品
- **路径**: PUT /app-api/trade/cart/reset
- **权限**: 仅需 App 登录
- **说明**: 将某个购物车项切换为另一个 SKU 并设置数量（规格变更场景），整体在一个事务内完成

**请求参数 (AppCartResetReqVO)**:

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|-----|------|------|---------|------|
| id | Long | 是 | @NotNull("编号不能为空") | 原购物车项编号 |
| skuId | Long | 是 | @NotNull("商品 SKU 编号不能为空") | 新的商品 SKU 编号 |
| count | Integer | 是 | @NotNull("数量不能为空")、@Min(1) | 新的购买数量 |

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**（`CartServiceImpl#resetCart`，`@Transactional(rollbackFor = Exception.class)`）:
1. 按 `id + userId` 查询原购物车项，不存在抛 `CARD_ITEM_NOT_FOUND`；删除该记录。
2. 按 `userId + 新 skuId` 查询是否已有购物车项：已存在则走 `updateCartCount` 合并数量；不存在则走 `addCart` 新建。

### 1.5 删除购物车商品
- **路径**: DELETE /app-api/trade/cart/delete
- **权限**: 仅需 App 登录
- **说明**: 批量删除当前用户的购物车项（标记删除）

**请求参数**: Query 参数 `ids`（List&lt;Long&gt;，必填，购物车项编号，如 `1024,2048`）

**响应**: CommonResult&lt;Boolean&gt;（固定 true）

**业务逻辑**（`CartServiceImpl#deleteCart`）: 按 `ids + userId` 查询归属当前用户的购物车项，列表为空直接返回（不报错），否则按查到的记录 id 集合 `deleteByIds` 批量标记删除——传入不属于本人或已删除的 id 会被静默忽略。

### 1.6 查询用户在购物车中的商品数量
- **路径**: GET /app-api/trade/cart/get-count
- **权限**: 仅需 App 登录
- **说明**: 返回当前用户购物车商品总数量（`selectSumByUserId` 对 `count` 求和）
- **响应**: CommonResult&lt;Integer&gt;
- **备注**: 源码 `CartServiceImpl#getCartCount` 留有 `// TODO 芋艿：需要算上 selected`，当前求和不区分是否选中；角标展示如需只统计选中项，需在扩展时自行过滤。

### 1.7 查询用户的购物车列表
- **路径**: GET /app-api/trade/cart/list
- **权限**: 仅需 App 登录
- **说明**: 返回当前用户购物车列表，按有效 / 失效拆分，并拼接 SPU、SKU 信息

**响应**: CommonResult&lt;AppCartListRespVO&gt;

| 字段 | 类型 | 说明 |
|-----|------|------|
| validList | List&lt;Cart&gt; | 有效购物车项列表 |
| invalidList | List&lt;Cart&gt; | 失效购物车项列表 |
| Cart.id | Long | 购物车项编号 |
| Cart.count | Integer | 商品购买数量 |
| Cart.selected | Boolean | 是否选中 |
| Cart.spu | AppProductSpuBaseRespVO | 商品 SPU 信息 |
| Cart.sku | AppProductSkuBaseRespVO | 商品 SKU 信息 |

**业务逻辑**（`CartServiceImpl#getCartList(Long userId)`）:
1. 查询当前用户全部购物车项，按 id 倒序排序；为空时直接返回空 `validList` / `invalidList`。
2. 通过 `ProductSpuApi.getSpuList`、`ProductSkuApi.getSkuList`（跨模块 API）批量查询 SPU、SKU。
3. 延迟删除：SPU 已被删除的购物车项在本次查询中直接 `deleteById` 移除并从结果剔除（SKU 被删除不剔除，因为用户仍可通过 SPU 换选其它 SKU）。
4. `TradeCartConvert#convertList` 按 SPU / SKU 是否查询得到，将购物车项分入 `validList` 或 `invalidList`。

**内部复用**: `CartService#getCartList(Long userId, Set<Long> ids)` 供订单结算流程（`TradeOrderUpdateServiceImpl#createOrder`）按 id 集合取当前用户的购物车项，不经过 Controller 暴露。

### 1.8 SKU 校验规则（checkProductSku）
`CartServiceImpl#checkProductSku(skuId, count)` 在添加（1.1）、改数量（1.2）、重置（1.4，经 addCart/updateCartCount 间接调用）时执行：

1. `ProductSkuApi.getSku(skuId)` 查不到 SKU → 抛 `SKU_NOT_EXISTS`（product 模块错误码）。
2. `count > sku.getStock()` → 抛 `SKU_STOCK_NOT_ENOUGH`（product 模块错误码）。

## 2. 错误码汇总

| 错误码 | 常量 | 说明 | 抛出位置 |
|-------|------|------|---------|
| 1_011_002_000 | `CARD_ITEM_NOT_FOUND`（trade 模块） | 购物车项不存在 | updateCartCount、resetCart |
| product 模块 `SKU_NOT_EXISTS` | — | 商品 SKU 不存在 | checkProductSku |
| product 模块 `SKU_STOCK_NOT_ENOUGH` | — | 商品库存不足 | checkProductSku |

## 3. 相关文档
- [api-trade-order.md](api-trade-order.md) - 交易订单（下单时消费购物车）
- [data-model.md](data-model.md) - CartDO（trade_cart）表结构与 ER 关系
