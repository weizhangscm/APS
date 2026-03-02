# -*- coding: utf-8 -*-
"""
运行启发式并显示详细排程结果
"""
import requests
import json

# 运行启发式
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
        'display_start_date': '2026-02-04',  # 显示区间开始
        'display_end_date': '2026-02-15'     # 显示区间结束
    },
    'resource_ids': [3]  # CNC机床-3
}

print('='*90)
print('运行启发式排程 - 资源: CNC机床-3 (ID=3)')
print('='*90)

response = requests.post(url, json=data)
result = response.json()

if result.get('success'):
    print(f"排程成功!")
    print(f"排程订单数: {result.get('scheduled_orders')}")
    print(f"排程工序数: {result.get('scheduled_operations')}")
    print()
    print('='*90)
    print('详细排程结果:')
    print('='*90)
    print(f"{'资源':<18} {'订单号':<18} {'工序名':<15} {'开始时间':<22} {'结束时间':<22}")
    print('-'*90)
    
    for detail in result.get('details', []):
        order_number = detail.get('order_number', '')
        for op in detail.get('operations', []):
            resource = op.get('resource_name', '')
            op_name = op.get('operation_name', '')
            start = op.get('start', '')[:16].replace('T', ' ')
            end = op.get('end', '')[:16].replace('T', ' ')
            print(f"{resource:<18} {order_number:<18} {op_name:<15} {start:<22} {end:<22}")
    
    print()
    print('='*90)
    print('说明: 以上是启发式算法计算的排程结果')
    print('      按照策略"向前"排程，从当前日期(2026-02-04/05)开始依次占用资源')
    print('='*90)
else:
    print(f"排程失败: {result.get('message')}")
