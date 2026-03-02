from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from ..database import get_db
from .. import models, schemas

router = APIRouter()


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
    db: Session = Depends(get_db)
):
    """获取所有资源"""
    query = db.query(models.Resource).options(joinedload(models.Resource.work_center))
    if work_center_id:
        query = query.filter(models.Resource.work_center_id == work_center_id)
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
    
    # Check if work center exists
    work_center = db.query(models.WorkCenter).filter(models.WorkCenter.id == resource.work_center_id).first()
    if not work_center:
        raise HTTPException(status_code=400, detail="工作中心不存在")
    
    db_resource = models.Resource(**resource.model_dump())
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


# ==================== Products ====================

@router.get("/products", response_model=List[schemas.Product])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取所有产品"""
    return db.query(models.Product).offset(skip).limit(limit).all()


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
    
    db_product = models.Product(**product.model_dump())
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
    db: Session = Depends(get_db)
):
    """获取所有工艺路线"""
    query = db.query(models.Routing).options(
        joinedload(models.Routing.product),
        joinedload(models.Routing.operations).joinedload(models.RoutingOperation.work_center),
        joinedload(models.Routing.operations).joinedload(models.RoutingOperation.resource)
    )
    if product_id:
        query = query.filter(models.Routing.product_id == product_id)
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
    
    routing_data = routing.model_dump(exclude={'operations'})
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

def _resolve_work_center_from_resource(db: Session, resource_id: int = None, work_center_id: int = None) -> int:
    """若提供 resource_id 则从资源推导 work_center_id，否则校验 work_center_id。"""
    if resource_id is not None:
        resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
        if not resource:
            raise HTTPException(status_code=400, detail="资源不存在")
        return resource.work_center_id
    if work_center_id is None:
        raise HTTPException(status_code=400, detail="请选择资源")
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
