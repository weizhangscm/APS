# -*- coding: utf-8 -*-
import requests
import json
import time

print("等待服务重新加载...")
time.sleep(5)

url = 'http://localhost:8000/api/scheduling/auto-plan'
data = {
    'plan_type': 'heuristic',
    'heuristic_id': 'stable_forward',
    'optimizer_config': {
        'display_start_date': '2026-02-04',
        'display_end_date': '2026-02-15',
        'order_internal_relation': '不考虑'
    },
    'resource_ids': [3]
}

print('发送请求...')
response = requests.post(url, json=data)
result = response.json()

print()
print('='*60)
print('调试信息:')
print('='*60)
print('_debug_version:', result.get('_debug_version'))
print('_debug_request_optimizer_config:', result.get('_debug_request_optimizer_config'))
print('_debug_display_start:', result.get('_debug_display_start'))
print('_debug_display_end:', result.get('_debug_display_end'))
print('_debug_order_relation:', result.get('_debug_order_relation'))
print()
print('scheduled_orders:', result.get('scheduled_orders'))
