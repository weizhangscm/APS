# -*- coding: utf-8 -*-
import requests
import json

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

print('Sending request:')
print(json.dumps(data, indent=2, ensure_ascii=False))

response = requests.post(url, json=data)
result = response.json()

print()
print('Response debug info:')
print('_debug_display_start:', result.get('_debug_display_start'))
print('_debug_display_end:', result.get('_debug_display_end'))
print('_debug_order_relation:', result.get('_debug_order_relation'))
print('scheduled_orders:', result.get('scheduled_orders'))
