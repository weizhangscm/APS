# -*- coding: utf-8 -*-
"""
测试显示区间过滤
"""
import requests
import json

url = 'http://localhost:8000/api/scheduling/auto-plan'
data = {
    'plan_type': 'heuristic',
    'heuristic_id': 'stable_forward',
    'optimizer_config': {
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
    'resource_ids': [3]
}

print("="*80)
print("测试显示区间过滤")
print("="*80)
print(f"显示区间: 2026-02-04 ~ 2026-02-15")
print(f"订单内部关系: 不考虑")
print("="*80)

response = requests.post(url, json=data)
result = response.json()

print(f"\n排程订单数: {result.get('scheduled_orders')}")
print(f"排程工序数: {result.get('scheduled_operations')}")

if result.get('details'):
    print(f"\n排程的订单:")
    for detail in result.get('details', []):
        print(f"  - {detail.get('order_number')}")
