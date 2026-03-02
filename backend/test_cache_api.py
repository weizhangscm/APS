"""通过API检查缓存状态"""
import requests
import json

def test_cache():
    """测试缓存状态API"""
    url = "http://localhost:8000/api/scheduling/cache-status"
    
    print("检查缓存状态:", url)
    
    try:
        response = requests.get(url)
        print("响应状态码:", response.status_code)
        print("响应内容:", json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"请求失败: {e}")

def test_gantt():
    """测试甘特图API"""
    url = "http://localhost:8000/api/scheduling/gantt-data"
    params = {
        "view_type": "resource",
        "start_date": "2026-02-05",
        "end_date": "2026-02-15"
    }
    
    print("\n获取甘特图数据:", url)
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        print("响应状态码:", response.status_code)
        print("has_unsaved_changes:", data.get('has_unsaved_changes'))
        
        # 查找CNC机床-3相关的数据
        cnc3_tasks = [t for t in data.get('data', []) 
                      if 'CNC机床-3' in t.get('text', '') or t.get('resource_id') == 3]
        print(f"\nCNC机床-3相关任务 ({len(cnc3_tasks)} 个):")
        for task in cnc3_tasks:
            print(f"  {task.get('id')}: {task.get('text')}")
            print(f"    start={task.get('start_date')}, end={task.get('end_date')}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == '__main__':
    test_cache()
    test_gantt()
