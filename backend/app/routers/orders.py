from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from ..database import get_db
from .. import models, schemas

router = APIRouter()


# ==================== Production Orders ====================

@router.get("/", response_model=List[schemas.ProductionOrderWithOperations])
def get_orders(
    skip: int = 0, 
    limit: int = 100, 
    status: str = None,
    order_type: str = None,
    db: Session = Depends(get_db)
):
    """获取所有订单
    
    - **order_type**: 订单类型过滤 - planned(计划订单) 或 production(生产订单)
    - **status**: 状态过滤
    """
    query = db.query(models.ProductionOrder).options(
        joinedload(models.ProductionOrder.product),
        joinedload(models.ProductionOrder.operations).joinedload(models.Operation.resource)
    )
    if status:
        query = query.filter(models.ProductionOrder.status == status)
    if order_type:
        query = query.filter(models.ProductionOrder.order_type == order_type)
    return query.order_by(models.ProductionOrder.due_date).offset(skip).limit(limit).all()


@router.get("/{order_id}", response_model=schemas.ProductionOrderWithOperations)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """获取单个生产订单"""
    order = db.query(models.ProductionOrder).options(
        joinedload(models.ProductionOrder.product),
        joinedload(models.ProductionOrder.operations).joinedload(models.Operation.resource)
    ).filter(models.ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="生产订单不存在")
    return order


@router.post("/", response_model=schemas.ProductionOrderWithOperations)
def create_order(order: schemas.ProductionOrderCreate, db: Session = Depends(get_db)):
    """创建生产订单并自动生成工序"""
    # Check if order number already exists
    existing = db.query(models.ProductionOrder).filter(
        models.ProductionOrder.order_number == order.order_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="订单号已存在")
    
    # Check product exists
    product = db.query(models.Product).filter(models.Product.id == order.product_id).first()
    if not product:
        raise HTTPException(status_code=400, detail="产品不存在")
    
    # Get active routing for product
    routing = db.query(models.Routing).filter(
        models.Routing.product_id == order.product_id,
        models.Routing.is_active == 1
    ).first()
    if not routing:
        raise HTTPException(status_code=400, detail="产品没有有效的工艺路线")
    
    # Create order
    order_data = order.model_dump()
    # 生产订单默认状态为已排程
    if order_data.get('order_type') == models.OrderType.PRODUCTION.value:
        order_data['status'] = models.OrderStatus.SCHEDULED.value
    db_order = models.ProductionOrder(**order_data)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Get routing operations
    routing_ops = db.query(models.RoutingOperation).filter(
        models.RoutingOperation.routing_id == routing.id
    ).order_by(models.RoutingOperation.sequence).all()
    
    # 工序名称到资源ID的映射（只针对钣金车间的工序需要特殊匹配）
    # 其他工序使用工作中心的第一个资源作为默认值
    OPERATION_NAME_TO_RESOURCE = {
        # 钣金车间 (WC 2) - 需要根据工序名称匹配特定资源类型
        '冲压下料': 7,      # 冲床-1
        '折弯成型': 8,      # 折弯机-1
        '焊接': 9,          # 焊接工位-1
    }
    
    # 建立工作中心到第一个资源的映射（兜底逻辑）
    all_resources = db.query(models.Resource).order_by(models.Resource.id).all()
    work_center_to_first_resource = {}
    for res in all_resources:
        if res.work_center_id not in work_center_to_first_resource:
            work_center_to_first_resource[res.work_center_id] = res.id
    
    # Create operations for this order
    is_production = db_order.order_type == models.OrderType.PRODUCTION.value
    
    for routing_op in routing_ops:
        run_time = routing_op.setup_time + (routing_op.run_time_per_unit * order.quantity)
        
        # 优先使用工艺路线工序指定的资源，否则按工序名称匹配，否则用工作中心第一个资源
        default_resource_id = (
            getattr(routing_op, "resource_id", None)
            or OPERATION_NAME_TO_RESOURCE.get(
                routing_op.name,
                work_center_to_first_resource.get(routing_op.work_center_id),
            )
        )
        
        # 生产订单的工序默认状态为已排程
        operation_status = schemas.OperationStatus.SCHEDULED.value if is_production else schemas.OperationStatus.PENDING.value
        
        db_operation = models.Operation(
            order_id=db_order.id,
            routing_operation_id=routing_op.id,
            resource_id=default_resource_id,  # 预分配默认资源
            sequence=routing_op.sequence,
            name=routing_op.name,
            setup_time=routing_op.setup_time,
            run_time=run_time,
            status=operation_status
        )
        db.add(db_operation)
    
    db.commit()
    db.refresh(db_order)
    
    # Return with operations
    return db.query(models.ProductionOrder).options(
        joinedload(models.ProductionOrder.product),
        joinedload(models.ProductionOrder.operations).joinedload(models.Operation.resource)
    ).filter(models.ProductionOrder.id == db_order.id).first()


@router.put("/{order_id}", response_model=schemas.ProductionOrder)
def update_order(order_id: int, order: schemas.ProductionOrderUpdate, db: Session = Depends(get_db)):
    """更新生产订单"""
    db_order = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="生产订单不存在")
    
    update_data = order.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_order, key, value)
    
    db.commit()
    db.refresh(db_order)
    return db_order


@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    """删除订单"""
    db_order = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    db.delete(db_order)
    db.commit()
    return {"message": "订单已删除"}


@router.post("/{order_id}/convert-to-production", response_model=schemas.ProductionOrder)
def convert_to_production(
    order_id: int, 
    request: schemas.ConvertToProductionRequest = None,
    db: Session = Depends(get_db)
):
    """
    将计划订单转换为生产订单
    
    - 计划订单必须已排程
    - 转换后订单类型变为 production，时间变为确认时间
    - 转换后不可再通过排程引擎调整
    """
    db_order = db.query(models.ProductionOrder).filter(
        models.ProductionOrder.id == order_id
    ).first()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if db_order.order_type == models.OrderType.PRODUCTION.value:
        raise HTTPException(status_code=400, detail="该订单已是生产订单")
    
    if db_order.status != models.OrderStatus.SCHEDULED.value:
        raise HTTPException(status_code=400, detail="计划订单必须先完成排程才能转为生产订单")
    
    # 获取排程的开始和结束时间
    operations = db.query(models.Operation).filter(
        models.Operation.order_id == order_id,
        models.Operation.scheduled_start != None
    ).all()
    
    if not operations:
        raise HTTPException(status_code=400, detail="订单没有排程信息")
    
    scheduled_start = min(op.scheduled_start for op in operations)
    scheduled_end = max(op.scheduled_end for op in operations)
    
    # 使用请求中的时间或排程时间
    if request:
        db_order.confirmed_start = request.confirmed_start or scheduled_start
        db_order.confirmed_end = request.confirmed_end or scheduled_end
    else:
        db_order.confirmed_start = scheduled_start
        db_order.confirmed_end = scheduled_end
    
    # 转换订单类型
    db_order.order_type = models.OrderType.PRODUCTION.value
    # 生产订单状态应为已排程
    db_order.status = models.OrderStatus.SCHEDULED.value
    
    # 将所有工序状态更新为已排程
    for operation in operations:
        operation.status = models.OperationStatus.SCHEDULED.value
    
    db.commit()
    db.refresh(db_order)
    
    return db_order


# ==================== Operations ====================

@router.get("/{order_id}/operations", response_model=List[schemas.OperationWithDetails])
def get_order_operations(order_id: int, db: Session = Depends(get_db)):
    """获取订单的所有工序"""
    operations = db.query(models.Operation).options(
        joinedload(models.Operation.resource)
    ).filter(models.Operation.order_id == order_id).order_by(models.Operation.sequence).all()
    return operations


@router.put("/operations/{operation_id}", response_model=schemas.Operation)
def update_operation(operation_id: int, operation: schemas.OperationUpdate, db: Session = Depends(get_db)):
    """更新工序"""
    db_operation = db.query(models.Operation).filter(models.Operation.id == operation_id).first()
    if not db_operation:
        raise HTTPException(status_code=404, detail="工序不存在")
    
    update_data = operation.model_dump(exclude_unset=True)
    
    # Convert enum to string if status is provided
    if 'status' in update_data and update_data['status']:
        update_data['status'] = update_data['status'].value if hasattr(update_data['status'], 'value') else update_data['status']
    
    for key, value in update_data.items():
        setattr(db_operation, key, value)
    
    db.commit()
    db.refresh(db_operation)
    return db_operation


@router.get("/all-operations/", response_model=List[schemas.OperationWithDetails])
def get_all_operations(
    skip: int = 0,
    limit: int = 500,
    resource_id: int = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """获取所有工序"""
    query = db.query(models.Operation).options(
        joinedload(models.Operation.resource)
    )
    if resource_id:
        query = query.filter(models.Operation.resource_id == resource_id)
    if status:
        query = query.filter(models.Operation.status == status)
    return query.order_by(models.Operation.scheduled_start).offset(skip).limit(limit).all()
