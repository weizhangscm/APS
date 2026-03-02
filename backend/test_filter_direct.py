# -*- coding: utf-8 -*-
"""
直接调用引擎测试过滤逻辑（绕过API）
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.database import SessionLocal
from app import models, schemas
from app.scheduler.engine import SchedulingEngine

db = SessionLocal()

print("="*80)
print("直接测试引擎的过滤逻辑")
print("="*80)

# 创建请求对象
request = schemas.AutoPlanRequest(
    plan_type='heuristic',
    heuristic_id='stable_forward',
    optimizer_config={
        'finite_capacity': True,
        'preserve_scheduled': True,
        'sorting_rule': '订单优先级',
        'planning_direction': '向前',
        'expected_date': '当前日期',
        'order_internal_relation': '不考虑',
        'sub_planning_mode': '根据调度模式调度相关操作',
        'schedule_selected_resources_only': True,
        'display_start_date': '2026-02-04',
        'display_end_date': '2026-02-15'
    },
    resource_ids=[3]
)

print(f"显示区间: 2026-02-04 ~ 2026-02-15")
print(f"订单内部关系: 不考虑")
print(f"资源: CNC机床-3 (ID=3)")
print("="*80)

# 调用引擎
engine = SchedulingEngine(db)
result = engine.auto_plan(request)

print(f"\n排程订单数: {result.get('scheduled_orders')}")
print(f"排程工序数: {result.get('scheduled_operations')}")

if result.get('details'):
    print(f"\n排程的订单:")
    for detail in result.get('details', []):
        order_num = detail.get('order_number')
        ops = detail.get('operations', [])
        if ops:
            start = ops[0].get('start', '')[:16].replace('T', ' ')
            end = ops[0].get('end', '')[:16].replace('T', ' ')
            print(f"  - {order_num}: {start} ~ {end}")

db.close()
