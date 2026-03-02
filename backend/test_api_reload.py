# -*- coding: utf-8 -*-
"""
测试 API 调用（使用 requests）
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

print("发送请求到:", url)
print("请求数据:")
print(json.dumps(data, indent=2, ensure_ascii=False))
print()

response = requests.post(url, json=data)
result = response.json()

print("="*60)
print("响应结果:")
print("="*60)
print(f"排程订单数: {result.get('scheduled_orders')}")
print(f"排程工序数: {result.get('scheduled_operations')}")
print(f"消息: {result.get('message')}")

if result.get('details'):
    print(f"\n排程的订单详情:")
    for detail in result.get('details', []):
        order_num = detail.get('order_number')
        ops = detail.get('operations', [])
        if ops:
            start = ops[0].get('start', '')[:16].replace('T', ' ')
            end = ops[0].get('end', '')[:16].replace('T', ' ')
            print(f"  {order_num}: {start} ~ {end}")
