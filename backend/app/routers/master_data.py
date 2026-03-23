from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from ..database import get_db
from .. import models, schemas
from ..services.location_catalog import (
    normalize_location_code,
    optional_location_code,
    require_location_code,
)

router = APIRouter()


# ==================== Locations 位置主数据 ====================


@router.get("/locations", response_model=List[schemas.Location])
def get_locations(skip: int = 0, limit: int = 500, db: Session = Depends(get_db)):
    return (
        db.query(models.Location)
        .order_by(models.Location.code)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/locations/{code}", response_model=schemas.Location)
def get_location(code: str, db: Session = Depends(get_db)):
    row = db.query(models.Location).filter(models.Location.code == code).first()
    if not row:
        raise HTTPException(status_code=404, detail="位置不存在")
    return row


@router.post("/locations", response_model=schemas.Location)
def create_location(loc: schemas.LocationCreate, db: Session = Depends(get_db)):
    c = normalize_location_code(loc.code)
    if not c:
        raise HTTPException(status_code=422, detail="位置代码不能为空")
    if db.query(models.Location).filter(models.Location.code == c).first():
        raise HTTPException(status_code=400, detail="位置代码已存在")
    row = models.Location(code=c, description=loc.description)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/locations/{code}", response_model=schemas.Location)
def update_location(code: str, loc: schemas.LocationUpdate, db: Session = Depends(get_db)):
    row = db.query(models.Location).filter(models.Location.code == code).first()
    if not row:
        raise HTTPException(status_code=404, detail="位置不存在")
    data = loc.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/locations/{code}")
def delete_location(code: str, db: Session = Depends(get_db)):
    row = db.query(models.Location).filter(models.Location.code == code).first()
    if not row:
        raise HTTPException(status_code=404, detail="位置不存在")
    if code == "1001":
        raise HTTPException(status_code=400, detail="不能删除系统默认位置 1001")
    db.delete(row)
    db.commit()
    return {"message": "位置已删除"}


# ==================== Work Centers ====================

@router.get("/work-centers", response_model=List[schemas.WorkCenter])
def get_work_centers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取所有工作中心"""
    return db.query(models.WorkCenter).offset(skip).limit(limit).all()


@router.get("/work-centers/{work_center_id}", response_model=schemas.WorkCenter)
def get_work_center(work_center_id: int, db: Session = Depends(get_db)):
    """获取单个工作中心"""
    work_center = db.query(models.WorkCenter).filter(models.WorkCenter.id == work_center_id).first()
    if not work_center:
        raise HTTPException(status_code=404, detail="工作中心不存在")
    return work_center


@router.post("/work-centers", response_model=schemas.WorkCenter)
def create_work_center(work_center: schemas.WorkCenterCreate, db: Session = Depends(get_db)):
    """创建工作中心"""
    # Check if code already exists
    existing = db.query(models.WorkCenter).filter(models.WorkCenter.code == work_center.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="工作中心编码已存在")
    
    db_work_center = models.WorkCenter(**work_center.model_dump())
    db.add(db_work_center)
    db.commit()
    db.refresh(db_work_center)
    return db_work_center


@router.put("/work-centers/{work_center_id}", response_model=schemas.WorkCenter)
def update_work_center(work_center_id: int, work_center: schemas.WorkCenterUpdate, db: Session = Depends(get_db)):
    """更新工作中心"""
    db_work_center = db.query(models.WorkCenter).filter(models.WorkCenter.id == work_center_id).first()
    if not db_work_center:
        raise HTTPException(status_code=404, detail="工作中心不存在")
    
    update_data = work_center.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_work_center, key, value)
    
    db.commit()
    db.refresh(db_work_center)
    return db_work_center


@router.delete("/work-centers/{work_center_id}")
def delete_work_center(work_center_id: int, db: Session = Depends(get_db)):
    """删除工作中心"""
    db_work_center = db.query(models.WorkCenter).filter(models.WorkCenter.id == work_center_id).first()
    if not db_work_center:
        raise HTTPException(status_code=404, detail="工作中心不存在")
    
    db.delete(db_work_center)
    db.commit()
    return {"message": "工作中心已删除"}


# ==================== Resources ====================

@router.get("/resources", response_model=List[schemas.ResourceWithWorkCenter])
def get_resources(
    skip: int = 0,
    limit: int = 100,
    work_center_id: int = None,
    location: str = None,
    db: Session = Depends(get_db),
):
    """获取所有资源"""
    query = db.query(models.Resource).options(joinedload(models.Resource.work_center))
    if work_center_id:
        query = query.filter(models.Resource.work_center_id == work_center_id)
    if location:
        loc = normalize_location_code(location)
        if loc:
            query = query.filter(models.Resource.location == loc)
    return query.offset(skip).limit(limit).all()


@router.get("/resources/{resource_id}", response_model=schemas.ResourceWithWorkCenter)
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    """获取单个资源"""
    resource = db.query(models.Resource).options(
        joinedload(models.Resource.work_center)
    ).filter(models.Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")
    return resource


@router.post("/resources", response_model=schemas.Resource)
def create_resource(resource: schemas.ResourceCreate, db: Session = Depends(get_db)):
    """创建资源"""
    # Check if code already exists
    existing = db.query(models.Resource).filter(models.Resource.code == resource.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="资源编码已存在")

    data = resource.model_dump()
    if data.get("location"):
        data["location"] = optional_location_code(db, data["location"], "资源位置")
    db_resource = models.Resource(**data)
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource


@router.put("/resources/{resource_id}", response_model=schemas.Resource)
def update_resource(resource_id: int, resource: schemas.ResourceUpdate, db: Session = Depends(get_db)):
    """更新资源"""
    db_resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not db_resource:
        raise HTTPException(status_code=404, detail="资源不存在")
    
    update_data = resource.model_dump(exclude_unset=True)
    if "location" in update_data and update_data["location"]:
        update_data["location"] = optional_location_code(
            db, update_data["location"], "资源位置"
        )
    elif "location" in update_data and update_data["location"] in ("", None):
        update_data["location"] = None
    for key, value in update_data.items():
        setattr(db_resource, key, value)

    db.commit()
    db.refresh(db_resource)
    return db_resource


@router.delete("/resources/{resource_id}")
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    """删除资源"""
    db_resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not db_resource:
        raise HTTPException(status_code=404, detail="资源不存在")
    
    db.delete(db_resource)
    db.commit()
    return {"message": "资源已删除"}


# ==================== Shifts 班次 ====================

@router.get("/shifts", response_model=List[schemas.ShiftWithResource])
def get_shifts(
    skip: int = 0,
    limit: int = 500,
    resource_id: int = None,
    db: Session = Depends(get_db)
):
    """获取所有班次"""
    query = db.query(models.Shift).options(joinedload(models.Shift.resource))
    if resource_id is not None:
        query = query.filter(models.Shift.resource_id == resource_id)
    return query.offset(skip).limit(limit).all()


@router.get("/shifts/{shift_id}", response_model=schemas.ShiftWithResource)
def get_shift(shift_id: int, db: Session = Depends(get_db)):
    """获取单个班次"""
    shift = db.query(models.Shift).options(
        joinedload(models.Shift.resource)
    ).filter(models.Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="班次不存在")
    return shift


@router.post("/shifts", response_model=schemas.ShiftWithResource)
def create_shift(shift: schemas.ShiftCreate, db: Session = Depends(get_db)):
    """创建班次"""
    resource = db.query(models.Resource).filter(models.Resource.id == shift.resource_id).first()
    if not resource:
        raise HTTPException(status_code=400, detail="资源不存在")
    loc = require_location_code(db, shift.location, "班次位置")
    rloc = normalize_location_code(resource.location)
    if rloc and loc != rloc:
        raise HTTPException(status_code=400, detail="班次位置须与所属资源位置一致")
    data = shift.model_dump()
    data["location"] = loc
    db_shift = models.Shift(**data)
    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)
    # 重新加载以带出 resource
    return db.query(models.Shift).options(
        joinedload(models.Shift.resource)
    ).filter(models.Shift.id == db_shift.id).first()


@router.put("/shifts/{shift_id}", response_model=schemas.ShiftWithResource)
def update_shift(shift_id: int, shift: schemas.ShiftUpdate, db: Session = Depends(get_db)):
    """更新班次"""
    db_shift = db.query(models.Shift).filter(models.Shift.id == shift_id).first()
    if not db_shift:
        raise HTTPException(status_code=404, detail="班次不存在")
    update_data = shift.model_dump(exclude_unset=True)
    if "resource_id" in update_data and update_data["resource_id"] is not None:
        resource = db.query(models.Resource).filter(models.Resource.id == update_data["resource_id"]).first()
        if not resource:
            raise HTTPException(status_code=400, detail="资源不存在")
    if "location" in update_data:
        if not update_data["location"] or not str(update_data["location"]).strip():
            raise HTTPException(status_code=422, detail="班次位置不能为空")
        update_data["location"] = require_location_code(
            db, update_data["location"], "班次位置"
        )
    for key, value in update_data.items():
        setattr(db_shift, key, value)
    res = (
        db.query(models.Resource)
        .filter(models.Resource.id == db_shift.resource_id)
        .first()
    )
    if res:
        rloc = normalize_location_code(res.location)
        sloc = normalize_location_code(db_shift.location)
        if rloc and sloc and rloc != sloc:
            raise HTTPException(status_code=400, detail="班次位置须与所属资源位置一致")
    db.commit()
    db.refresh(db_shift)
    return db.query(models.Shift).options(
        joinedload(models.Shift.resource)
    ).filter(models.Shift.id == db_shift.id).first()


@router.delete("/shifts/{shift_id}")
def delete_shift(shift_id: int, db: Session = Depends(get_db)):
    """删除班次"""
    db_shift = db.query(models.Shift).filter(models.Shift.id == shift_id).first()
    if not db_shift:
        raise HTTPException(status_code=404, detail="班次不存在")
    db.delete(db_shift)
    db.commit()
    return {"message": "班次已删除"}


# ==================== Products ====================

@router.get("/products", response_model=List[schemas.Product])
def get_products(
    skip: int = 0,
    limit: int = 100,
    location: str = None,
    db: Session = Depends(get_db),
):
    """获取所有产品"""
    q = db.query(models.Product)
    if location:
        loc = normalize_location_code(location)
        if loc:
            q = q.filter(models.Product.location == loc)
    return q.offset(skip).limit(limit).all()


@router.get("/products/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """获取单个产品"""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    return product


@router.post("/products", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    """创建产品"""
    existing = db.query(models.Product).filter(models.Product.code == product.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="产品编码已存在")

    data = product.model_dump()
    if data.get("location"):
        data["location"] = optional_location_code(db, data["location"], "产品位置")
    db_product = models.Product(**data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.put("/products/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product: schemas.ProductUpdate, db: Session = Depends(get_db)):
    """更新产品"""
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="产品不存在")
    
    update_data = product.model_dump(exclude_unset=True)
    if "location" in update_data and update_data["location"]:
        update_data["location"] = optional_location_code(
            db, update_data["location"], "产品位置"
        )
    elif "location" in update_data and update_data["location"] in ("", None):
        update_data["location"] = None
    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """删除产品"""
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="产品不存在")
    
    db.delete(db_product)
    db.commit()
    return {"message": "产品已删除"}


# ==================== Routings ====================

@router.get("/routings", response_model=List[schemas.RoutingWithOperations])
def get_routings(
    skip: int = 0,
    limit: int = 100,
    product_id: int = None,
    location: str = None,
    db: Session = Depends(get_db),
):
    """获取所有工艺路线"""
    query = db.query(models.Routing).options(
        joinedload(models.Routing.product),
        joinedload(models.Routing.operations).joinedload(models.RoutingOperation.work_center),
        joinedload(models.Routing.operations).joinedload(models.RoutingOperation.resource),
    )
    if product_id:
        query = query.filter(models.Routing.product_id == product_id)
    if location:
        loc = normalize_location_code(location)
        if loc:
            query = query.filter(models.Routing.location == loc)
    return query.offset(skip).limit(limit).all()


@router.get("/routings/{routing_id}", response_model=schemas.RoutingWithOperations)
def get_routing(routing_id: int, db: Session = Depends(get_db)):
    """获取单个工艺路线"""
    routing = db.query(models.Routing).options(
        joinedload(models.Routing.product),
        joinedload(models.Routing.operations).joinedload(models.RoutingOperation.work_center),
        joinedload(models.Routing.operations).joinedload(models.RoutingOperation.resource)
    ).filter(models.Routing.id == routing_id).first()
    if not routing:
        raise HTTPException(status_code=404, detail="工艺路线不存在")
    return routing


@router.post("/routings", response_model=schemas.Routing)
def create_routing(routing: schemas.RoutingCreate, db: Session = Depends(get_db)):
    """创建工艺路线"""
    existing = db.query(models.Routing).filter(models.Routing.code == routing.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="工艺路线编码已存在")
    
    # Check product exists
    product = db.query(models.Product).filter(models.Product.id == routing.product_id).first()
    if not product:
        raise HTTPException(status_code=400, detail="产品不存在")
    
    routing_data = routing.model_dump(exclude={"operations"})
    routing_data["location"] = require_location_code(
        db, routing_data.get("location"), "工艺路线位置"
    )
    db_routing = models.Routing(**routing_data)
    db.add(db_routing)
    db.commit()
    db.refresh(db_routing)
    
    # Create operations if provided
    if routing.operations:
        for op_data in routing.operations:
            data = op_data.model_dump()
            data["work_center_id"] = _resolve_work_center_from_resource(
                db, data.get("resource_id"), data.get("work_center_id")
            )
            db_operation = models.RoutingOperation(routing_id=db_routing.id, **data)
            db.add(db_operation)
        db.commit()
    
    return db_routing


@router.put("/routings/{routing_id}", response_model=schemas.Routing)
def update_routing(routing_id: int, routing: schemas.RoutingUpdate, db: Session = Depends(get_db)):
    """更新工艺路线"""
    db_routing = db.query(models.Routing).filter(models.Routing.id == routing_id).first()
    if not db_routing:
        raise HTTPException(status_code=404, detail="工艺路线不存在")
    
    update_data = routing.model_dump(exclude_unset=True)
    if "location" in update_data and update_data["location"] is not None:
        if not str(update_data["location"]).strip():
            raise HTTPException(status_code=422, detail="工艺路线位置不能为空")
        update_data["location"] = require_location_code(
            db, update_data["location"], "工艺路线位置"
        )
    for key, value in update_data.items():
        setattr(db_routing, key, value)

    db.commit()
    db.refresh(db_routing)
    return db_routing


@router.delete("/routings/{routing_id}")
def delete_routing(routing_id: int, db: Session = Depends(get_db)):
    """删除工艺路线"""
    db_routing = db.query(models.Routing).filter(models.Routing.id == routing_id).first()
    if not db_routing:
        raise HTTPException(status_code=404, detail="工艺路线不存在")
    
    db.delete(db_routing)
    db.commit()
    return {"message": "工艺路线已删除"}


# ==================== Routing Operations ====================

def _resolve_work_center_from_resource(
    db: Session, resource_id: int = None, work_center_id: int = None
) -> Optional[int]:
    """若提供 resource_id 则优先用资源的工作中心；资源未关联工作中心时可仅指定资源（work_center_id 可为空）。"""
    if resource_id is not None:
        resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
        if not resource:
            raise HTTPException(status_code=400, detail="资源不存在")
        if resource.work_center_id is not None:
            return resource.work_center_id
        if work_center_id is not None:
            wc = db.query(models.WorkCenter).filter(models.WorkCenter.id == work_center_id).first()
            if not wc:
                raise HTTPException(status_code=400, detail="工作中心不存在")
            return work_center_id
        return None
    if work_center_id is None:
        raise HTTPException(status_code=400, detail="请选择资源或工作中心")
    wc = db.query(models.WorkCenter).filter(models.WorkCenter.id == work_center_id).first()
    if not wc:
        raise HTTPException(status_code=400, detail="工作中心不存在")
    return work_center_id


@router.post("/routings/{routing_id}/operations", response_model=schemas.RoutingOperation)
def create_routing_operation(
    routing_id: int, 
    operation: schemas.RoutingOperationCreate, 
    db: Session = Depends(get_db)
):
    """为工艺路线添加工序（支持传 resource_id，与 DS资源 一致）"""
    routing = db.query(models.Routing).filter(models.Routing.id == routing_id).first()
    if not routing:
        raise HTTPException(status_code=404, detail="工艺路线不存在")
    data = operation.model_dump()
    data["work_center_id"] = _resolve_work_center_from_resource(
        db, data.get("resource_id"), data.get("work_center_id")
    )
    db_operation = models.RoutingOperation(routing_id=routing_id, **data)
    db.add(db_operation)
    db.commit()
    db.refresh(db_operation)
    return db_operation


@router.put("/routing-operations/{operation_id}", response_model=schemas.RoutingOperation)
def update_routing_operation(
    operation_id: int, 
    operation: schemas.RoutingOperationUpdate, 
    db: Session = Depends(get_db)
):
    """更新工艺路线工序（支持 resource_id，会推导 work_center_id）"""
    db_operation = db.query(models.RoutingOperation).filter(models.RoutingOperation.id == operation_id).first()
    if not db_operation:
        raise HTTPException(status_code=404, detail="工序不存在")
    update_data = operation.model_dump(exclude_unset=True)
    if "resource_id" in update_data or "work_center_id" in update_data:
        merged = {"resource_id": getattr(db_operation, "resource_id", None), "work_center_id": db_operation.work_center_id, **update_data}
        update_data["work_center_id"] = _resolve_work_center_from_resource(
            db, merged.get("resource_id"), merged.get("work_center_id")
        )
    for key, value in update_data.items():
        setattr(db_operation, key, value)
    db.commit()
    db.refresh(db_operation)
    return db_operation


@router.delete("/routing-operations/{operation_id}")
def delete_routing_operation(operation_id: int, db: Session = Depends(get_db)):
    """删除工艺路线工序"""
    db_operation = db.query(models.RoutingOperation).filter(models.RoutingOperation.id == operation_id).first()
    if not db_operation:
        raise HTTPException(status_code=404, detail="工序不存在")
    
    db.delete(db_operation)
    db.commit()
    return {"message": "工序已删除"}
