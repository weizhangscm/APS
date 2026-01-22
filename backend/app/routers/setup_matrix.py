"""
切换矩阵管理 API
参考 SAP PPDS Setup Matrix 功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from ..database import get_db
from .. import models, schemas

router = APIRouter()


# ==================== Setup Groups ====================

@router.get("/groups", response_model=List[schemas.SetupGroup])
def get_setup_groups(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取所有切换组"""
    return db.query(models.SetupGroup).offset(skip).limit(limit).all()


@router.get("/groups/{group_id}", response_model=schemas.SetupGroup)
def get_setup_group(group_id: int, db: Session = Depends(get_db)):
    """获取单个切换组"""
    group = db.query(models.SetupGroup).filter(models.SetupGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="切换组不存在")
    return group


@router.post("/groups", response_model=schemas.SetupGroup)
def create_setup_group(group: schemas.SetupGroupCreate, db: Session = Depends(get_db)):
    """创建切换组"""
    existing = db.query(models.SetupGroup).filter(models.SetupGroup.code == group.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="切换组代码已存在")
    
    db_group = models.SetupGroup(**group.model_dump())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group


@router.put("/groups/{group_id}", response_model=schemas.SetupGroup)
def update_setup_group(group_id: int, group: schemas.SetupGroupUpdate, db: Session = Depends(get_db)):
    """更新切换组"""
    db_group = db.query(models.SetupGroup).filter(models.SetupGroup.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="切换组不存在")
    
    update_data = group.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_group, key, value)
    
    db.commit()
    db.refresh(db_group)
    return db_group


@router.delete("/groups/{group_id}")
def delete_setup_group(group_id: int, db: Session = Depends(get_db)):
    """删除切换组"""
    db_group = db.query(models.SetupGroup).filter(models.SetupGroup.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="切换组不存在")
    
    db.delete(db_group)
    db.commit()
    return {"message": "切换组已删除"}


# ==================== Product Setup Group Assignments ====================

@router.get("/product-assignments", response_model=List[schemas.ProductSetupGroupWithDetails])
def get_product_setup_groups(
    product_id: Optional[int] = None,
    setup_group_id: Optional[int] = None,
    work_center_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取产品-切换组分配"""
    query = db.query(models.ProductSetupGroup).options(
        joinedload(models.ProductSetupGroup.product),
        joinedload(models.ProductSetupGroup.setup_group),
        joinedload(models.ProductSetupGroup.work_center)
    )
    
    if product_id:
        query = query.filter(models.ProductSetupGroup.product_id == product_id)
    if setup_group_id:
        query = query.filter(models.ProductSetupGroup.setup_group_id == setup_group_id)
    if work_center_id:
        query = query.filter(
            (models.ProductSetupGroup.work_center_id == work_center_id) |
            (models.ProductSetupGroup.work_center_id == None)
        )
    
    return query.all()


@router.post("/product-assignments", response_model=schemas.ProductSetupGroup)
def assign_product_to_group(
    assignment: schemas.ProductSetupGroupCreate,
    db: Session = Depends(get_db)
):
    """将产品分配到切换组"""
    # 检查产品是否存在
    product = db.query(models.Product).filter(models.Product.id == assignment.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    
    # 检查切换组是否存在
    group = db.query(models.SetupGroup).filter(models.SetupGroup.id == assignment.setup_group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="切换组不存在")
    
    # 检查是否已存在相同分配
    existing = db.query(models.ProductSetupGroup).filter(
        models.ProductSetupGroup.product_id == assignment.product_id,
        models.ProductSetupGroup.work_center_id == assignment.work_center_id
    ).first()
    
    if existing:
        # 更新现有分配
        existing.setup_group_id = assignment.setup_group_id
        db.commit()
        db.refresh(existing)
        return existing
    
    db_assignment = models.ProductSetupGroup(**assignment.model_dump())
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment


@router.delete("/product-assignments/{assignment_id}")
def remove_product_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """删除产品-切换组分配"""
    assignment = db.query(models.ProductSetupGroup).filter(
        models.ProductSetupGroup.id == assignment_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="分配不存在")
    
    db.delete(assignment)
    db.commit()
    return {"message": "分配已删除"}


# ==================== Setup Matrix ====================

@router.get("/matrix", response_model=List[schemas.SetupMatrixWithDetails])
def get_setup_matrix_entries(
    resource_id: Optional[int] = None,
    work_center_id: Optional[int] = None,
    from_group_id: Optional[int] = None,
    to_group_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取切换矩阵条目"""
    query = db.query(models.SetupMatrix).options(
        joinedload(models.SetupMatrix.from_setup_group),
        joinedload(models.SetupMatrix.to_setup_group),
        joinedload(models.SetupMatrix.resource),
        joinedload(models.SetupMatrix.work_center)
    )
    
    if resource_id is not None:
        query = query.filter(models.SetupMatrix.resource_id == resource_id)
    if work_center_id is not None:
        query = query.filter(models.SetupMatrix.work_center_id == work_center_id)
    if from_group_id:
        query = query.filter(models.SetupMatrix.from_setup_group_id == from_group_id)
    if to_group_id:
        query = query.filter(models.SetupMatrix.to_setup_group_id == to_group_id)
    
    return query.all()


@router.get("/matrix/grid", response_model=schemas.SetupMatrixGrid)
def get_setup_matrix_grid(
    resource_id: Optional[int] = None,
    work_center_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取切换矩阵网格视图"""
    # 获取所有切换组
    setup_groups = db.query(models.SetupGroup).all()
    
    # 构建查询条件
    query = db.query(models.SetupMatrix)
    if resource_id is not None:
        query = query.filter(models.SetupMatrix.resource_id == resource_id)
    elif work_center_id is not None:
        query = query.filter(
            models.SetupMatrix.work_center_id == work_center_id,
            models.SetupMatrix.resource_id == None
        )
    else:
        # 获取全局矩阵（resource_id 和 work_center_id 都为空）
        query = query.filter(
            models.SetupMatrix.resource_id == None,
            models.SetupMatrix.work_center_id == None
        )
    
    entries = query.all()
    
    # 构建矩阵字典
    matrix = {}
    for entry in entries:
        if entry.from_setup_group_id not in matrix:
            matrix[entry.from_setup_group_id] = {}
        matrix[entry.from_setup_group_id][entry.to_setup_group_id] = entry.changeover_time
    
    return schemas.SetupMatrixGrid(
        setup_groups=[schemas.SetupGroup.model_validate(g) for g in setup_groups],
        matrix=matrix,
        resource_id=resource_id,
        work_center_id=work_center_id
    )


@router.post("/matrix", response_model=schemas.SetupMatrix)
def create_setup_matrix_entry(
    entry: schemas.SetupMatrixCreate,
    db: Session = Depends(get_db)
):
    """创建切换矩阵条目"""
    # 验证切换组存在
    from_group = db.query(models.SetupGroup).filter(
        models.SetupGroup.id == entry.from_setup_group_id
    ).first()
    if not from_group:
        raise HTTPException(status_code=404, detail="源切换组不存在")
    
    to_group = db.query(models.SetupGroup).filter(
        models.SetupGroup.id == entry.to_setup_group_id
    ).first()
    if not to_group:
        raise HTTPException(status_code=404, detail="目标切换组不存在")
    
    # 检查是否已存在
    existing = db.query(models.SetupMatrix).filter(
        models.SetupMatrix.from_setup_group_id == entry.from_setup_group_id,
        models.SetupMatrix.to_setup_group_id == entry.to_setup_group_id,
        models.SetupMatrix.resource_id == entry.resource_id,
        models.SetupMatrix.work_center_id == entry.work_center_id
    ).first()
    
    if existing:
        # 更新现有条目
        existing.changeover_time = entry.changeover_time
        existing.description = entry.description
        db.commit()
        db.refresh(existing)
        return existing
    
    db_entry = models.SetupMatrix(**entry.model_dump())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


@router.post("/matrix/batch")
def batch_update_matrix(
    entries: List[schemas.SetupMatrixCreate],
    db: Session = Depends(get_db)
):
    """批量更新切换矩阵"""
    updated = 0
    created = 0
    
    for entry in entries:
        existing = db.query(models.SetupMatrix).filter(
            models.SetupMatrix.from_setup_group_id == entry.from_setup_group_id,
            models.SetupMatrix.to_setup_group_id == entry.to_setup_group_id,
            models.SetupMatrix.resource_id == entry.resource_id,
            models.SetupMatrix.work_center_id == entry.work_center_id
        ).first()
        
        if existing:
            existing.changeover_time = entry.changeover_time
            existing.description = entry.description
            updated += 1
        else:
            db_entry = models.SetupMatrix(**entry.model_dump())
            db.add(db_entry)
            created += 1
    
    db.commit()
    return {"message": f"已更新 {updated} 条，新建 {created} 条"}


@router.delete("/matrix/{entry_id}")
def delete_setup_matrix_entry(entry_id: int, db: Session = Depends(get_db)):
    """删除切换矩阵条目"""
    entry = db.query(models.SetupMatrix).filter(models.SetupMatrix.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")
    
    db.delete(entry)
    db.commit()
    return {"message": "条目已删除"}


# ==================== Changeover Time Query ====================

@router.get("/changeover-time")
def get_changeover_time(
    from_product_id: int,
    to_product_id: int,
    resource_id: Optional[int] = None,
    work_center_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    查询两个产品之间的切换时间
    
    查找顺序：
    1. 资源级别的切换矩阵
    2. 工作中心级别的切换矩阵
    3. 全局切换矩阵
    4. 如果都没找到，返回0
    """
    # 获取产品的切换组
    def get_setup_group_id(product_id: int, wc_id: Optional[int]) -> Optional[int]:
        # 先找特定工作中心的
        if wc_id:
            assignment = db.query(models.ProductSetupGroup).filter(
                models.ProductSetupGroup.product_id == product_id,
                models.ProductSetupGroup.work_center_id == wc_id
            ).first()
            if assignment:
                return assignment.setup_group_id
        
        # 再找全局的
        assignment = db.query(models.ProductSetupGroup).filter(
            models.ProductSetupGroup.product_id == product_id,
            models.ProductSetupGroup.work_center_id == None
        ).first()
        return assignment.setup_group_id if assignment else None
    
    from_group_id = get_setup_group_id(from_product_id, work_center_id)
    to_group_id = get_setup_group_id(to_product_id, work_center_id)
    
    if not from_group_id or not to_group_id:
        return {"changeover_time": 0.0, "source": "default", "message": "产品未分配切换组"}
    
    # 相同切换组，切换时间为0
    if from_group_id == to_group_id:
        return {"changeover_time": 0.0, "source": "same_group", "message": "相同切换组"}
    
    # 1. 查找资源级别
    if resource_id:
        entry = db.query(models.SetupMatrix).filter(
            models.SetupMatrix.from_setup_group_id == from_group_id,
            models.SetupMatrix.to_setup_group_id == to_group_id,
            models.SetupMatrix.resource_id == resource_id
        ).first()
        if entry:
            return {"changeover_time": entry.changeover_time, "source": "resource"}
    
    # 2. 查找工作中心级别
    if work_center_id:
        entry = db.query(models.SetupMatrix).filter(
            models.SetupMatrix.from_setup_group_id == from_group_id,
            models.SetupMatrix.to_setup_group_id == to_group_id,
            models.SetupMatrix.work_center_id == work_center_id,
            models.SetupMatrix.resource_id == None
        ).first()
        if entry:
            return {"changeover_time": entry.changeover_time, "source": "work_center"}
    
    # 3. 查找全局
    entry = db.query(models.SetupMatrix).filter(
        models.SetupMatrix.from_setup_group_id == from_group_id,
        models.SetupMatrix.to_setup_group_id == to_group_id,
        models.SetupMatrix.resource_id == None,
        models.SetupMatrix.work_center_id == None
    ).first()
    if entry:
        return {"changeover_time": entry.changeover_time, "source": "global"}
    
    return {"changeover_time": 0.0, "source": "not_found", "message": "未找到切换矩阵配置"}
