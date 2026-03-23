"""位置主数据校验：所有业务 location 字段须为 locations 表中的 code。"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models

# 系统默认位置代码（无位置/全局矩阵回退时使用；须存在于 locations 主数据）
PRIMARY_LOCATION_CODE = "1001"


def normalize_location_code(code: Optional[str]) -> Optional[str]:
    if code is None:
        return None
    s = str(code).strip()
    return s or None


def require_location_code(db: Session, code: Optional[str], field_label: str = "位置") -> str:
    c = normalize_location_code(code)
    if not c:
        raise HTTPException(status_code=422, detail=f"{field_label}必填，且须为已维护的位置代码")
    row = db.query(models.Location).filter(models.Location.code == c).first()
    if not row:
        raise HTTPException(status_code=422, detail=f"{field_label}「{c}」不存在于位置主数据，请先在「位置」菜单维护")
    return c


def optional_location_code(
    db: Session, code: Optional[str], field_label: str = "位置"
) -> Optional[str]:
    c = normalize_location_code(code)
    if c is None:
        return None
    require_location_code(db, c, field_label)
    return c


def matrix_location_for_resource(resource: Optional[models.Resource]) -> str:
    """切换矩阵匹配用：资源无位置时用 PRIMARY_LOCATION_CODE。"""
    if resource is None:
        return PRIMARY_LOCATION_CODE
    c = normalize_location_code(resource.location)
    return c or PRIMARY_LOCATION_CODE
