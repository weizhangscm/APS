# -*- coding: utf-8 -*-
"""
检查为什么启发式排程了 PLN20260011 和 PLN20260005
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.database import SessionLocal
from app import models

db = SessionLocal()

print("="*80)
print("检查 CNC机床-3 上的所有工序及其交货期")
print("="*80)

# 查询 CNC机床-3 上的所有工序
ops_on_cnc3 = db.query(models.Operation).filter(
    models.Operation.resource_id == 3
).all()

print(f"\nCNC机床-3 (ID=3) 上共有 {len(ops_on_cnc3)} 个工序:\n")
print(f"{'订单号':<15} {'交货期':<15} {'订单状态':<12} {'工序状态':<10}")
print("-"*60)

for op in ops_on_cnc3:
    order = db.query(models.ProductionOrder).filter(
        models.ProductionOrder.id == op.order_id
    ).first()
    
    if order:
        due_date_str = order.due_date.strftime('%Y-%m-%d') if order.due_date else 'None'
        print(f"{order.order_number:<15} {due_date_str:<15} {order.status:<12} {op.status:<10}")

print("\n" + "="*80)
print("分析：启发式算法为什么排程了这些订单？")
print("="*80)

print("""
启发式算法的工作逻辑：
1. 查找所有分配到选中资源（CNC机床-3）的工序
2. 获取这些工序所属的订单
3. 对这些订单进行排程

所以，只要工序的 resource_id = 3（CNC机床-3），
无论订单的交货期是多少，都会被算法处理。

这5个订单都有工序分配到 CNC机床-3，所以都被排程了。
""")

print("="*80)
print("显示区间过滤说明")
print("="*80)
print("""
显示区间（2026-02-04 到 2026-02-15）只影响甘特图的显示，
不影响启发式算法的排程范围。

启发式算法会排程所有选中资源上的工序，
而甘特图只显示在显示区间内的工序。

排程前：甘特图根据交货期显示工序位置
- PLN20260030 交货期 02-10 → 显示
- PLN20260004 交货期 02-11 → 显示  
- PLN20260016 交货期 02-14 → 显示
- PLN20260005 交货期 02-24 → 超出区间，不显示
- PLN20260011 交货期 02-26 → 超出区间，不显示

排程后（如果缓存正常）：应该根据排程时间显示
- PLN20260011 排程 02-05~02-06 → 应该显示
- PLN20260016 排程 02-06~02-07 → 应该显示
- PLN20260005 排程 02-07~02-08 → 应该显示
- PLN20260004 排程 02-08 → 应该显示
- PLN20260030 排程 02-08~02-09 → 应该显示
""")

db.close()
