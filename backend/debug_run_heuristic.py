"""模拟运行启发式排程"""
import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.database import SessionLocal
from app import models, schemas
from app.scheduler.engine import SchedulingEngine

def run_heuristic():
    """模拟运行启发式"""
    db = SessionLocal()
    
    print("=" * 60)
    print("模拟运行启发式")
    print("=" * 60)
    
    # 获取资源IDs
    resources = db.query(models.Resource).filter(
        models.Resource.name.in_(['CNC机床-1', 'CNC机床-3'])
    ).all()
    resource_ids = [r.id for r in resources]
    print(f"选中的资源: {[r.name for r in resources]}, IDs: {resource_ids}")
    
    # 创建引擎
    engine = SchedulingEngine(db)
    
    # 创建请求
    request = schemas.AutoPlanRequest(
        plan_type='heuristic',
        heuristic_id='stable_forward',
        resource_ids=resource_ids
    )
    
    # 配置
    config = {
        'finite_capacity': True,
        'resolve_backlog': True,
        'resolve_overload': True,
        'preserve_scheduled': True,
        'sorting_rule': '订单优先级',
        'planning_mode': '查找槽位',
        'planning_direction': '向前',
        'expected_date': '当前日期',
        'order_internal_relation': '不考虑',
        'sub_planning_mode': '根据调度模式调度相关操作',
        'error_handling': '立即终止',
        'planning_horizon': 90,
        'schedule_selected_resources_only': True,
        'preview_mode': True
    }
    
    print(f"\n配置: schedule_selected_resources_only={config['schedule_selected_resources_only']}")
    print(f"配置: preserve_scheduled={config['preserve_scheduled']}")
    
    # 将配置放入 request.optimizer_config
    request.optimizer_config = config
    
    # 运行排程
    try:
        result = engine.auto_plan(request)
        print(f"\n排程结果:")
        print(f"  成功: {result.get('success')}")
        print(f"  消息: {result.get('message')}")
        print(f"  排程订单数: {result.get('scheduled_orders')}")
        print(f"  排程工序数: {result.get('scheduled_operations')}")
        print(f"  预览模式: {result.get('preview_mode')}")
        print(f"  有未保存更改: {result.get('has_unsaved_changes')}")
        
        if result.get('details'):
            print(f"\n详情 (前5个):")
            for detail in result['details'][:5]:
                print(f"    {detail}")
    except Exception as e:
        import traceback
        print(f"\n错误: {e}")
        traceback.print_exc()
    
    db.close()

if __name__ == '__main__':
    run_heuristic()
