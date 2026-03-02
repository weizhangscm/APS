"""测试API调用"""
import requests
import json

def test_auto_plan():
    """测试auto-plan API"""
    url = "http://localhost:8000/api/scheduling/auto-plan"
    
    payload = {
        "plan_type": "heuristic",
        "heuristic_id": "stable_forward",
        "optimizer_config": {
            "finite_capacity": True,
            "resolve_backlog": True,
            "resolve_overload": True,
            "preserve_scheduled": True,
            "sorting_rule": "订单优先级",
            "planning_mode": "查找槽位",
            "planning_direction": "向前",
            "expected_date": "当前日期",
            "order_internal_relation": "不考虑",
            "sub_planning_mode": "根据调度模式调度相关操作",
            "error_handling": "立即终止",
            "planning_horizon": 90,
            "schedule_selected_resources_only": True
        },
        "resource_ids": [3]  # CNC机床-3
    }
    
    print("发送请求到:", url)
    print("请求数据:", json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(url, json=payload)
        print("\n响应状态码:", response.status_code)
        print("响应内容:", json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == '__main__':
    test_auto_plan()
