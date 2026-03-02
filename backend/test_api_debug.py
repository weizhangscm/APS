# -*- coding: utf-8 -*-
"""
Test API with debug output
"""
import requests
import json

url = 'http://localhost:8000/api/scheduling/auto-plan'
data = {
    'plan_type': 'heuristic',
    'heuristic_id': 'stable_forward',
    'optimizer_config': {
        'display_start_date': '2026-02-04',
        'display_end_date': '2026-02-15',
        'order_internal_relation': '不考虑',
        'preview_mode': False
    },
    'resource_ids': [3]
}

print('Request:')
print(json.dumps(data, indent=2, ensure_ascii=False))

response = requests.post(url, json=data)
result = response.json()

print()
print('Response:')
print('scheduled_orders:', result.get('scheduled_orders'))
print('scheduled_operations:', result.get('scheduled_operations'))
print('_engine_version:', result.get('_engine_version'))
print('_filtered_ops_count:', result.get('_filtered_ops_count'))

# Show details
print()
print('Scheduled operations:')
for detail in result.get('details', []):
    if detail.get('success'):
        order_num = detail.get('order_number', 'Unknown')
        for op_info in detail.get('operations', []):
            print(f'  {order_num}: {op_info["start"]} ~ {op_info["end"]}')
