from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from ..database import get_db
from .. import schemas
from ..scheduler.engine import SchedulingEngine
from ..scheduler.constraints import ConstraintValidator

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
    return engine.reschedule_operation(
        operation_id=request.operation_id,
        new_start=request.new_start,
        new_resource_id=request.new_resource_id
    )


@router.get("/gantt-data", response_model=schemas.GanttData)
def get_gantt_data(
    view_type: str = Query("order", description="视图类型: order(订单视图) 或 resource(资源视图)"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    获取甘特图数据
    
    - **view_type**: 视图类型 - order(按订单显示) 或 resource(按资源显示)
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    """
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
def get_kpi_dashboard(db: Session = Depends(get_db)):
    """获取KPI仪表板数据"""
    engine = SchedulingEngine(db)
    return engine.get_kpi_data()


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
    return engine.auto_plan(request)


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
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    zoom_level: int = Query(1, description="缩放级别: 0=小时, 1=4小时, 2=天, 3=周, 4=月"),
    db: Session = Depends(get_db)
):
    """
    获取资源利用率数据
    
    - **resource_ids**: 资源ID列表，逗号分隔
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **zoom_level**: 缩放级别 (0=小时, 1=4小时, 2=天, 3=周, 4=月)
    """
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
