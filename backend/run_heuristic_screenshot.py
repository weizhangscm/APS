# Run heuristic per screenshot: strategy + selection (display 2026.02.16-02.22, resource CNC机床-1, 10 products)
# Strategy: order_internal_relation=不考虑, expected_date=指定日期 2026-02-16, etc.
# 与界面一致：先「取消计划」再跑启发式（否则库里已有排程，显示区间内空档少，只排 1 单）。
import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.database import SessionLocal
from app import models, schemas
from app.scheduler.engine import SchedulingEngine

# 是否在跑启发式前先取消该资源上的计划（与界面「取消计划」后跑启发式一致）
CANCEL_PLAN_FIRST = True

def main():
    db = SessionLocal()
    resource = db.query(models.Resource).filter(models.Resource.name == 'CNC机床-1').first()
    if not resource:
        print("Resource CNC机床-1 not found")
        db.close()
        return
    resource_ids = [resource.id]

    if CANCEL_PLAN_FIRST:
        engine = SchedulingEngine(db)
        cancel_result = engine.cancel_plan(resource_ids=resource_ids)
        print("=== 先取消计划（与界面一致）===")
        print("Cancel result:", cancel_result.get("message"), "cancelled_ops:", cancel_result.get("cancelled_operations"))
        print()

    config = {
        'finite_capacity': True,
        'resolve_backlog': True,
        'resolve_overload': True,
        'preserve_scheduled': True,
        'sorting_rule': '订单优先级',
        'planning_mode': '查找槽位',
        'planning_direction': '向前',
        'expected_date': '指定日期',
        'expected_date_value': '2026-02-16',
        'order_internal_relation': '不考虑',
        'sub_planning_mode': '根据调度模式调度相关操作',
        'error_handling': '立即终止',
        'planning_horizon': 90,
        'schedule_selected_resources_only': True,
        'display_start_date': '2026-02-16',
        'display_end_date': '2026-02-22',
        'preview_mode': True,
    }
    request = schemas.AutoPlanRequest(
        plan_type='heuristic',
        heuristic_id='stable_forward',
        resource_ids=resource_ids,
        optimizer_config=config,
    )
    engine = SchedulingEngine(db)
    result = engine.auto_plan(request)

    print("=== Strategy (from screenshot) ===")
    print("Sorting: order priority | Mode: find slot | Direction: forward")
    print("Expected date: specified 2026-02-16 | Order internal: not consider")
    print("Sub-plan: by scheduling mode | On error: terminate")
    print("Selection: display 2026-02-16~2026-02-22, resource CNC机床-1, 10 products (API has no product filter)")
    print()
    print("=== Result ===")
    print("Success:", result.get('success'))
    print("Message:", result.get('message'))
    print("Scheduled orders:", result.get('scheduled_orders'))
    print("Scheduled operations:", result.get('scheduled_operations'))
    print("Preview:", result.get('preview_mode'))
    print("Unsaved:", result.get('has_unsaved_changes'))
    details = result.get('details', [])
    print("Order details count:", len(details))
    for i, d in enumerate(details[:15]):
        err = d.get('error', '')
        print("  ", d.get('order_number'), "success=", d.get('success'), "ops=", d.get('operations_count'), err and ("error=" + err) or "")
    if details and result.get('success'):
        first = next((d for d in details if d.get('success') and d.get('operations')), None)
        if first:
            print("First order ops (start~end):")
            for op in (first.get('operations') or [])[:5]:
                print("   ", op.get('operation_name'), op.get('start'), "~", op.get('end'))
    print()
    print("=== Strategy compliance ===")
    in_range = True
    if details:
        for d in details:
            for op in d.get('operations') or []:
                s, e = op.get('start'), op.get('end')
                if s and e:
                    try:
                        start = datetime.fromisoformat(s.replace('Z', '+00:00'))
                        end = datetime.fromisoformat(e.replace('Z', '+00:00'))
                        if start.tzinfo: start = start.replace(tzinfo=None)
                        if end.tzinfo: end = end.replace(tzinfo=None)
                        if start.date() < datetime(2026,2,16).date() or end.date() > datetime(2026,2,22).date():
                            in_range = False
                            break
                    except Exception: pass
            if not in_range: break
    print("All ops within display range [2026-02-16, 2026-02-22]:", in_range)
    print("Order internal = not consider (only selected resource ops): OK from config")
    print("Expected date 2026-02-16: OK from config")
    db.close()

if __name__ == '__main__':
    main()
