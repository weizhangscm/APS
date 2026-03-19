from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional, List
import logging

from ..database import get_db


def _normalize_same_day_range(start_date, end_date):
    if start_date is not None and end_date is not None:
 
        if isinstance(start_date, date) and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
 
        if isinstance(end_date, date) and not isinstance(end_date, datetime):
            end_date = datetime.combine(end_date, datetime.min.time())
 
        if start_date.date() == end_date.date():
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
 
    return start_date, end_date
from .. import schemas
from ..scheduler.engine import SchedulingEngine
from ..scheduler.constraints import ConstraintValidator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("[SCHEDULING_ROUTER] Module loaded - version 2026-02-04-v5")

router = APIRouter()


@router.post("/run", response_model=schemas.SchedulingResult)
def run_scheduling(
    request: schemas.SchedulingRequest,
    db: Session = Depends(get_db)
):
    """
    执行排程
    
    - **order_ids**: 要排程的订单ID列表，不填则排程所有待排订单
    - **direction**: 排程方向 - forward(正向) 或 backward(逆向)
    - **consider_capacity**: 是否考虑有限产能
    - **priority_rule**: 优先级规则 - EDD(最早交期), SPT(最短加工时间), FIFO(先进先出), PRIORITY(按优先级)
    """
    engine = SchedulingEngine(db)
    
    result = engine.run_scheduling(
        order_ids=request.order_ids,
        direction=request.direction.value,
        consider_capacity=request.consider_capacity,
        priority_rule=request.priority_rule
    )
    
    return result


@router.post("/clear")
def clear_scheduling(
    order_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    """清除排程结果"""
    engine = SchedulingEngine(db)
    return engine.clear_scheduling(order_ids)


@router.post("/reschedule-operation")
def reschedule_operation(
    request: schemas.OperationReschedule,
    db: Session = Depends(get_db)
):
    """
    重新排程单个工序（用于拖拽调整）
    
    - **operation_id**: 工序ID
    - **new_start**: 新的开始时间
    - **new_resource_id**: 新的资源ID（可选，不填则保持原资源）
    """
    engine = SchedulingEngine(db)
    # 这里再加一层保护，确保无论引擎内部发生什么错误，都不会返回 HTTP 500
    try:
        return engine.reschedule_operation(
            operation_id=request.operation_id,
            new_start=request.new_start,
            new_resource_id=request.new_resource_id
        )
    except Exception as e:
        # 最终兜底：返回结构化业务错误
        from ..scheduler.constraints import ConstraintViolation
        violation = ConstraintViolation(
            violation_type='internal_error',
            severity='error',
            message=f'调整工序时发生系统错误：{e}',
            operation_id=request.operation_id
        )
        return {
            'success': False,
            'message': violation.message,
            'conflicts': [violation.to_dict()]
        }


@router.get("/gantt-data", response_model=schemas.GanttData)
def get_gantt_data(
    view_type: str = Query("order", description="视图类型: order(订单视图) 或 resource(资源视图)"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    获取甘特图数据
    
    - **view_type**: 视图类型 - order(按订单显示) 或 resource(按资源显示)
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - 当 start_date 与 end_date 为同一天时，时间区间按 00:00 - 23:59:59 处理
    """
    start_date, end_date = _normalize_same_day_range(start_date, end_date)
    engine = SchedulingEngine(db)
    return engine.get_gantt_data(
        start_date=start_date,
        end_date=end_date,
        view_type=view_type
    )


@router.get("/validate")
def validate_scheduling(
    order_ids: Optional[str] = Query(None, description="订单ID列表，逗号分隔"),
    db: Session = Depends(get_db)
):
    """验证排程约束"""
    validator = ConstraintValidator(db)
    
    order_id_list = None
    if order_ids:
        order_id_list = [int(id.strip()) for id in order_ids.split(",")]
    
    violations = validator.validate_all(order_ids=order_id_list)
    
    return {
        "total_violations": len(violations),
        "errors": len([v for v in violations if v.severity == "error"]),
        "warnings": len([v for v in violations if v.severity == "warning"]),
        "violations": [v.to_dict() for v in violations]
    }


@router.get("/kpi", response_model=schemas.KPIDashboard)
def get_kpi_dashboard(
    db: Session = Depends(get_db),
    due_date_start: Optional[str] = Query(None, description="交期区间开始日期 YYYY-MM-DD"),
    due_date_end: Optional[str] = Query(None, description="交期区间结束日期 YYYY-MM-DD"),
    schedule_date_start: Optional[str] = Query(None, description="日期区间开始日期 YYYY-MM-DD（用于资源利用率/产能负荷/资源利用详情，按排程时间窗口过滤）"),
    schedule_date_end: Optional[str] = Query(None, description="日期区间结束日期 YYYY-MM-DD（用于资源利用率/产能负荷/资源利用详情，按排程时间窗口过滤）"),
):
    """获取KPI仪表板数据。

    - 订单 KPI / 平均提前期：按交期区间（due_date_start/end）过滤，保持原有口径不变
    - 资源利用率 / 每日产能负荷 / 资源利用详情：按日期区间（schedule_date_start/end）过滤排程计划落在区间内的生产订单与计划订单
    """
    engine = SchedulingEngine(db)
    return engine.get_kpi_data(
        due_date_start=due_date_start,
        due_date_end=due_date_end,
        schedule_date_start=schedule_date_start,
        schedule_date_end=schedule_date_end,
    )


@router.post("/reschedule-resource")
def reschedule_resource(
    request: schemas.ResourceRescheduleRequest,
    db: Session = Depends(get_db)
):
    """
    对指定资源上的工序重新进行策略排程
    """
    engine = SchedulingEngine(db)
    return engine.reschedule_resource(
        resource_ids=request.resource_ids,
        strategy=request.strategy
    )


@router.post("/auto-plan")
def auto_plan(
    request: schemas.AutoPlanRequest,
    db: Session = Depends(get_db)
):
    """
    执行自动排程（启发式或优化器）
    """
    engine = SchedulingEngine(db)
    result = engine.auto_plan(request)
    return result


@router.post("/cancel-plan")
def cancel_plan(
    request: schemas.CancelPlanRequest,
    db: Session = Depends(get_db)
):
    """
    取消计划 - 根据资源和/或产品清除排程
    
    取消计划订单和已排程订单的排程（不影响生产订单），并且只清除尚未开始的排程。
    取消后，订单可以重新被计划。
    
    - **resource_ids**: 资源ID列表，清除这些资源上的排程
    - **product_ids**: 产品ID列表，清除这些产品的订单排程
    """
    engine = SchedulingEngine(db)
    return engine.cancel_plan(
        resource_ids=request.resource_ids,
        product_ids=request.product_ids
    )


@router.post("/save-plan")
def save_plan(
    request: schemas.SavePlanRequest,
    db: Session = Depends(get_db)
):
    """
    保存计划 - 将缓存的排程数据写入数据库
    
    如果有预览模式的缓存数据，会先将缓存写入数据库，然后更新状态。
    
    - **resource_ids**: 资源ID列表，保存这些资源上的排程
    - **product_ids**: 产品ID列表，保存这些产品的订单排程
    """
    engine = SchedulingEngine(db)
    return engine.save_plan(
        resource_ids=request.resource_ids,
        product_ids=request.product_ids
    )


@router.post("/discard-plan")
def discard_plan():
    """
    丢弃计划 - 清除缓存的排程更改
    
    用于取消排程操作的结果，不保存到数据库。
    """
    from ..scheduler.cache import schedule_cache
    
    if schedule_cache.has_unsaved_changes:
        cached_count = len(schedule_cache.get_all_operations())
        schedule_cache.clear()
        return {
            'success': True,
            'message': f'已丢弃 {cached_count} 道工序的排程更改',
            'discarded_operations': cached_count
        }
    else:
        return {
            'success': True,
            'message': '没有需要丢弃的排程更改',
            'discarded_operations': 0
        }


@router.get("/cache-status")
def get_cache_status():
    """
    获取缓存状态 - 检查是否有未保存的排程
    """
    from ..scheduler.cache import schedule_cache
    return schedule_cache.get_status()


@router.get("/utilization")
def get_utilization_data(
    resource_ids: Optional[str] = Query(None, description="资源ID列表，逗号分隔"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    zoom_level: int = Query(1, description="缩放级别: 0=小时, 1=4小时, 2=天, 3=周, 4=月"),
    db: Session = Depends(get_db)
):
    """
    获取资源利用率数据
    
    - **resource_ids**: 资源ID列表，逗号分隔
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **zoom_level**: 缩放级别 (0=小时, 1=4小时, 2=天, 3=周, 4=月)
    - 当 start_date 与 end_date 为同一天时，时间区间按 00:00 - 23:59:59 处理
    """
    start_date, end_date = _normalize_same_day_range(start_date, end_date)
    engine = SchedulingEngine(db)
    
    resource_id_list = None
    if resource_ids:
        resource_id_list = [int(id.strip()) for id in resource_ids.split(",")]
    
    return engine.get_utilization_data(
        resource_ids=resource_id_list,
        start_date=start_date,
        end_date=end_date,
        zoom_level=zoom_level
    )


@router.post("/reschedule-with-links")
def reschedule_with_links(
    request: schemas.RescheduleWithLinksRequest,
    db: Session = Depends(get_db)
):
    """
    联动调整工序（支持策略）
    
    - **operation_id**: 工序ID
    - **new_start**: 新的开始时间
    - **new_resource_id**: 新的资源ID（可选）
    - **strategy**: 策略（EDD, SPT, FIFO, PRIORITY）
    - **move_linked_operations**: 是否联动移动关联工序
    """
    engine = SchedulingEngine(db)
    return engine.reschedule_with_links(
        operation_id=request.operation_id,
        new_start=request.new_start,
        new_resource_id=request.new_resource_id,
        strategy=request.strategy,
        move_linked_operations=request.move_linked_operations
    )
