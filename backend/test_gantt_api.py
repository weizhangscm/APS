"""测试Gantt API调用"""
import requests
import json

def test_gantt():
    """测试gantt-data API"""
    url = "http://localhost:8000/api/scheduling/gantt-data"
    
    params = {
        "view_type": "resource",
        "start_date": "2026-02-09",
        "end_date": "2026-02-15"
    }
    
    print("发送请求到:", url)
    print("参数:", params)
    
    try:
        response = requests.get(url, params=params)
        print("\n响应状态码:", response.status_code)
        data = response.json()
        print("has_unsaved_changes:", data.get('has_unsaved_changes'))
        print("数据条数:", len(data.get('data', [])))
        
        # 查找CNC机床-1相关的数据
        cnc1_tasks = [t for t in data.get('data', []) if 'CNC机床-1' in t.get('text', '') or t.get('resource_id') == 1]
        print("\nCNC机床-1相关任务:")
        for task in cnc1_tasks[:10]:
            print(f"  {task.get('id')}: {task.get('text')}, start={task.get('start_date')}, end={task.get('end_date')}")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == '__main__':
    test_gantt()
