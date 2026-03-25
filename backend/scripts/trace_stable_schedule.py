"""
跟踪稳定向前排程：打印资源可排产段 + 指定订单各工序槽位（不写库，preview）。
"""
import sys
from datetime import date, datetime

sys.path.insert(0, ".")

from app.database import SessionLocal
from app import models, schemas
from app.scheduler.engine import SchedulingEngine
from app.services.working_segments import productive_segments_starting_on_day, segment_templates_for_resource
from app.scheduler.algorithms import SchedulingAlgorithm


def main():
    db = SessionLocal()
    try:
        # 资源：位置 1001（与 DS 筛选一致）；若无则全量
        r1001 = (
            db.query(models.Resource)
            .filter(models.Resource.location == "1001")
            .all()
        )
        resources = r1001 if r1001 else db.query(models.Resource).all()
        resource_ids = [r.id for r in resources]
        print("=== 参与排程的资源 (location=1001 或全部) ===")
        for r in resources:
            print(f"  id={r.id} code={r.code} name={r.name!r} loc={r.location!r} op={r.operating_start}-{r.operating_end}")

        p001 = db.query(models.Resource).filter(models.Resource.code == "P001").first()
        if p001:
            print("\n=== P001 模板 segment_templates_for_resource ===")
            print(segment_templates_for_resource(db, p001.id))
            d = date(2026, 3, 26)
            segs = productive_segments_starting_on_day(db, p001.id, d)
            print(f"=== P001 productive_segments 2026-03-26 ===")
            for s, e in segs:
                print(f"  {s} -> {e}")

        algo = SchedulingAlgorithm(db)
        t_bad = datetime(2026, 3, 26, 1, 49, 0)
        if p001:
            sn = algo._snap_to_next_working_instant(t_bad, p001.id)
            en = algo._add_productive_duration(sn, 0.67, p001.id)
            print(f"\n=== 算法自检：若上一道结束在 {t_bad}，包装线应排到 ===")
            print(f"  snap -> {sn}")
            print(f"  +0.67h -> {en}")

        request = schemas.AutoPlanRequest(
            plan_type="heuristic",
            heuristic_id="stable_forward",
            resource_ids=resource_ids,
            optimizer_config={
                "finite_capacity": True,
                "resolve_backlog": True,
                "resolve_overload": True,
                "preserve_scheduled": True,
                "sorting_rule": "订单优先级",
                "planning_mode": "查找槽位",
                "planning_direction": "向前",
                "expected_date": "指定日期",
                "expected_date_value": "2026-03-25",
                "order_internal_relation": "始终考虑",
                "sub_planning_mode": "根据调度模式调度相关操作",
                "error_handling": "立即终止",
                "planning_horizon": 90,
                "schedule_selected_resources_only": True,
                "preview_mode": True,
                "display_start_date": "2026-03-23",
                "display_end_date": "2026-04-05",
                "order_filter_type": "in_display_range",
            },
        )

        engine = SchedulingEngine(db)
        print("\n=== 运行 stable_forward (preview, 将 rollback) ===")
        result = engine.auto_plan(request)
        print(f"success={result.get('success')} msg={result.get('message')!r}")
        print(f"scheduled_orders={result.get('scheduled_orders')} scheduled_operations={result.get('scheduled_operations')}")

        target_on = "PLN2026032302"
        for dtl in result.get("details") or []:
            if dtl.get("order_number") != target_on:
                continue
            print(f"\n=== 订单 {target_on} 排程明细 ===")
            for op in dtl.get("operations") or []:
                print(
                    f"  op_id={op.get('operation_id')} {op.get('operation_name')!r} "
                    f"res={op.get('resource_name')!r} {op.get('start')} -> {op.get('end')} "
                    f"co={op.get('changeover_time')}"
                )
            break
        else:
            print(f"\n(未在 details 中找到订单 {target_on}，列出前 3 个订单号)")
            for dtl in (result.get("details") or [])[:3]:
                print(f"  {dtl.get('order_number')}: success={dtl.get('success')}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
