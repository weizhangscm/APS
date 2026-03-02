# DS订单筛选问题修复说明

## 问题描述

在DS订单数据页面，当筛选状态为"待排程"（created）时，没有显示任何订单。

## 问题根本原因

1. **数据库状态**：所有订单（包括计划订单和生产订单）的订单状态（`status`字段）都是 `scheduled`（已排程）
   - 计划订单：42个，状态都是 `scheduled`
   - 生产订单：15个，状态都是 `scheduled`

2. **工序状态不一致**：虽然订单状态是 `scheduled`，但计划订单的工序状态是 `pending`（待排程）
   - 例如：订单PLN20260008的状态是 `scheduled`，但其6个工序的状态都是 `pending`

3. **显示逻辑 vs 筛选逻辑不匹配**：
   - **显示逻辑**（`getDisplayOrderStatus`函数）：会检查工序状态，如果有工序是 `pending`，就显示订单状态为"待排程"（created）
   - **筛选逻辑**（原来的实现）：使用订单的实际 `status` 字段，不考虑工序状态

## 修复方案

修改 `frontend/src/views/DSOrdersView.vue` 文件：

### 修改1：在前端进行状态筛选

**位置**：第362-397行的 `filteredOrders` computed 属性

**修改内容**：
1. 添加订单类型筛选（在前端完成）
2. 添加状态筛选（基于显示状态 `getDisplayOrderStatus`，而不是实际状态）

```javascript
// 如果设置了订单类型筛选
if (filterOrderType.value) {
  orders = orders.filter(order => order.order_type === filterOrderType.value)
}

// 如果设置了状态筛选（基于显示状态，而不是实际状态）
if (filterStatus.value) {
  orders = orders.filter(order => {
    const displayStatus = getDisplayOrderStatus(order)
    return displayStatus === filterStatus.value
  })
}
```

### 修改2：从后端获取所有订单

**位置**：第463-466行的 `fetchData` 函数

**修改前**：
```javascript
dsFiltersStore.fetchDSOrders(filterStatus.value || null, filterOrderType.value || null)
```

**修改后**：
```javascript
dsFiltersStore.fetchDSOrders(null, null)  // 获取所有订单，筛选在前端完成
```

## 修复效果

修复后：

1. **筛选"待排程"**：会显示所有工序状态为 `pending` 的计划订单
   - 这些订单的订单状态虽然是 `scheduled`，但工序未排程，所以显示为"待排程"

2. **筛选"已排程"**：会显示
   - 所有工序状态为 `scheduled` 的计划订单
   - 所有生产订单（因为生产订单总是显示为"已排程"）

3. **筛选逻辑与显示逻辑一致**：筛选条件使用的是显示状态（`getDisplayOrderStatus`），而不是数据库实际状态

## 示例数据

根据检查结果，修复后：

**筛选"待排程"时会显示**：
- 大多数计划订单（因为它们的工序状态是 `pending`）
- 例如：PLN20260008, PLN20260009, PLN20260017等

**筛选"已排程"时会显示**：
- 工序已全部排程的计划订单（如果有的话）
- 所有15个生产订单（PRD20260001, PRD20260002等）

## 技术说明

### 为什么订单状态和工序状态不一致？

这是系统设计的问题：
1. 排程引擎运行后，会将订单状态更新为 `scheduled`
2. 但如果后续取消排程，订单状态可能仍是 `scheduled`，而工序状态变回 `pending`
3. 前端的 `getDisplayOrderStatus` 函数正确处理了这种不一致，优先显示工序状态

### 为什么在前端筛选而不是后端？

1. **后端API限制**：后端API的状态筛选是基于订单的 `status` 字段
2. **前端已有逻辑**：前端已经有 `getDisplayOrderStatus` 函数来计算显示状态
3. **简单高效**：在前端筛选可以直接使用现有逻辑，无需修改后端API

## 文件修改清单

- ✅ `frontend/src/views/DSOrdersView.vue` - 修改筛选逻辑

## 验证方法

1. 启动前端应用
2. 进入"DS订单数据"页面
3. 在状态筛选下拉框中选择"待排程"
4. 应该能看到工序未排程的计划订单

## 相关问题

如果将来需要更彻底的解决方案，建议：

1. **方案A：修复数据一致性**
   - 当工序状态变为 `pending` 时，订单状态也应该变为 `created`
   - 需要修改排程引擎和取消排程的逻辑

2. **方案B：修改后端API**
   - 后端API支持基于工序状态的筛选
   - 需要修改 `backend/app/routers/orders.py`

当前的前端修复是最简单、最快速的解决方案，不会影响其他功能。
