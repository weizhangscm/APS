# 生产订单默认状态修改 - 更改说明

## 概述

根据需求，对生产订单（order_type='production'）的默认状态进行修改，使得：
- 新创建的生产订单默认状态为"已排程"（scheduled）
- 生产订单的所有工序默认状态为"已排程"（scheduled）
- 历史数据中的所有生产订单及其工序状态已更新
- 计划订单（order_type='planned'）不受影响

## 修改的文件

### 1. backend/app/routers/orders.py

#### 修改点 1: create_order 函数（第73-80行）
**功能**: 创建新订单时，如果是生产订单，自动设置状态为"已排程"

**修改前**:
```python
# Create order
db_order = models.ProductionOrder(**order.model_dump())
db.add(db_order)
db.commit()
db.refresh(db_order)
```

**修改后**:
```python
# Create order
order_data = order.model_dump()
# 生产订单默认状态为已排程
if order_data.get('order_type') == models.OrderType.PRODUCTION.value:
    order_data['status'] = models.OrderStatus.SCHEDULED.value
db_order = models.ProductionOrder(**order_data)
db.add(db_order)
db.commit()
db.refresh(db_order)
```

#### 修改点 2: create_order 函数 - 工序创建（第103-131行）
**功能**: 创建订单工序时，如果是生产订单，工序状态默认为"已排程"

**修改前**:
```python
# Create operations for this order
for routing_op in routing_ops:
    run_time = routing_op.setup_time + (routing_op.run_time_per_unit * order.quantity)
    
    # ... resource allocation logic ...
    
    db_operation = models.Operation(
        order_id=db_order.id,
        routing_operation_id=routing_op.id,
        resource_id=default_resource_id,
        sequence=routing_op.sequence,
        name=routing_op.name,
        setup_time=routing_op.setup_time,
        run_time=run_time,
        status=schemas.OperationStatus.PENDING.value  # 总是pending
    )
    db.add(db_operation)
```

**修改后**:
```python
# Create operations for this order
is_production = db_order.order_type == models.OrderType.PRODUCTION.value

for routing_op in routing_ops:
    run_time = routing_op.setup_time + (routing_op.run_time_per_unit * order.quantity)
    
    # ... resource allocation logic ...
    
    # 生产订单的工序默认状态为已排程
    operation_status = schemas.OperationStatus.SCHEDULED.value if is_production else schemas.OperationStatus.PENDING.value
    
    db_operation = models.Operation(
        order_id=db_order.id,
        routing_operation_id=routing_op.id,
        resource_id=default_resource_id,
        sequence=routing_op.sequence,
        name=routing_op.name,
        setup_time=routing_op.setup_time,
        run_time=run_time,
        status=operation_status  # 根据订单类型设置状态
    )
    db.add(db_operation)
```

#### 修改点 3: convert_to_production 函数（第217-229行）
**功能**: 将计划订单转换为生产订单时，同时更新订单和工序状态为"已排程"

**修改前**:
```python
# 转换订单类型
db_order.order_type = models.OrderType.PRODUCTION.value

db.commit()
db.refresh(db_order)

return db_order
```

**修改后**:
```python
# 转换订单类型
db_order.order_type = models.OrderType.PRODUCTION.value
# 生产订单状态应为已排程
db_order.status = models.OrderStatus.SCHEDULED.value

# 将所有工序状态更新为已排程
for operation in operations:
    operation.status = models.OperationStatus.SCHEDULED.value

db.commit()
db.refresh(db_order)

return db_order
```

### 2. backend/init_demo_data.py

**说明**: 此文件已经正确实现了生产订单的状态设置逻辑（第300行和第369行），无需修改。

- 第300行：订单创建时根据类型设置状态
  ```python
  status=models.OrderStatus.SCHEDULED.value if order_data["order_type"] == models.OrderType.PRODUCTION.value else models.OrderStatus.CREATED.value
  ```

- 第369行：工序创建时根据订单类型设置状态
  ```python
  status=models.OperationStatus.SCHEDULED.value if is_production else models.OperationStatus.PENDING.value
  ```

## 新增的文件

### 1. backend/migrate_production_orders_to_scheduled.py

**功能**: 迁移脚本，将历史数据中的所有生产订单及其工序状态更新为"已排程"

**使用方法**:
```bash
cd backend
python migrate_production_orders_to_scheduled.py
```

**执行结果**:
- 更新了 15 个生产订单状态：created -> scheduled
- 更新了 75 个工序状态：pending -> scheduled
- 验证了计划订单未受影响（42个计划订单）

### 2. backend/verify_production_orders.py

**功能**: 验证脚本，检查生产订单和工序的状态是否正确

**使用方法**:
```bash
cd backend
python verify_production_orders.py
```

**验证内容**:
- 所有生产订单状态为"scheduled"
- 所有生产订单工序状态为"scheduled"
- 计划订单未受影响

### 3. backend/test_api_production_order.py

**功能**: API测试脚本，验证通过API创建生产订单的行为

**使用方法**:
```bash
cd backend
python test_api_production_order.py
```

**测试内容**:
1. 通过API创建生产订单，验证状态为"scheduled"
2. 通过API将计划订单转换为生产订单，验证状态更新

## 影响范围

### 受影响的功能
1. **创建生产订单** (`POST /api/orders/`)
   - 生产订单默认状态：created -> scheduled
   - 生产订单工序默认状态：pending -> scheduled

2. **转换为生产订单** (`POST /api/orders/{order_id}/convert-to-production`)
   - 转换后订单状态保持为：scheduled
   - 转换后工序状态更新为：scheduled

3. **历史数据**
   - 所有现有生产订单状态已更新
   - 所有现有生产订单工序状态已更新

### 不受影响的功能
1. **计划订单** (order_type='planned')
   - 创建时状态仍为：created
   - 工序状态仍为：pending
   - 排程后由排程引擎更新状态

2. **排程引擎** (backend/app/scheduler/engine.py)
   - 只排程计划订单，不排程生产订单
   - 逻辑保持不变

3. **其他订单操作**
   - 订单列表查询
   - 订单详情查询
   - 订单更新
   - 订单删除

## 验证结果

### 迁移验证（2026-03-02执行）

```
================================================================================
迁移完成!
更新了 15 个订单状态
更新了 75 个工序状态
================================================================================

验证结果:
生产订单总数: 15
状态为已排程的生产订单: 15
[OK] 所有生产订单状态都已更新为已排程
生产订单工序总数: 75
状态为已排程的工序: 75
[OK] 所有生产订单工序状态都已更新为已排程

验证计划订单未受影响:
计划订单总数: 42
状态为已排程的计划订单: 42
[OK] 计划订单状态由排程引擎管理，未受影响
```

### 状态验证

```
生产订单总数: 15
生产订单状态分布:
  scheduled: 15

所有生产订单状态为已排程: True
所有生产订单工序状态为已排程: True

[成功] 所有生产订单及其工序的状态都已正确设置为已排程！
```

## 总结

所有修改已完成并验证通过：

✓ 新创建的生产订单默认状态为"已排程"
✓ 新创建的生产订单工序默认状态为"已排程"
✓ 转换为生产订单时状态正确更新
✓ 历史数据已全部更新
✓ 计划订单功能未受影响
✓ 排程引擎逻辑未受影响

## 备注

- 生产订单在系统中代表"已下达"的订单，时间已确定，不应再由排程引擎调整
- 计划订单在系统中代表"待排程"的订单，时间未确定，需要排程引擎分配时间
- 订单状态为"scheduled"表示该订单已有排程时间（对于生产订单，这是默认状态）
- 工序状态为"scheduled"表示该工序已有排程时间（对于生产订单工序，这是默认状态）
