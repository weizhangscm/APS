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
