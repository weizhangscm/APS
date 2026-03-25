"""
用户认证 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
import hashlib
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, Field
import secrets
import base64

from ..database import get_db
from .. import models

router = APIRouter()
security = HTTPBearer(auto_error=False)

# 简单的 token 存储 (生产环境应使用 Redis 或 JWT)
active_tokens = {}

ALLOWED_DATE_FORMATS: List[str] = [
    "YYYY-MM-DD",
    "MM/DD/YYYY",
    "DD/MM/YYYY",
    "DD.MM.YYYY",
    "YYYY/MM/DD",
    "YYYY年MM月DD日",
]

ALLOWED_TIME_FORMATS: List[str] = ["24h", "12h"]


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    date_format: Optional[str] = Field(None, max_length=40)
    time_format: Optional[str] = Field(None, max_length=10)
    user_timezone: Optional[str] = Field(None, max_length=80)


def _user_public_dict(user: models.User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "department": user.department,
        "date_format": user.date_format,
        "time_format": user.time_format,
        "user_timezone": user.user_timezone,
        "is_admin": user.is_admin,
    }

def hash_password(password: str) -> str:
    """哈希密码"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return hash_password(plain_password) == hashed_password

def create_token() -> str:
    """创建访问令牌"""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """获取当前用户"""
    if not credentials:
        return None
    
    token = credentials.credentials
    user_id = active_tokens.get(token)
    
    if not user_id:
        return None
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    return user

def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """要求认证"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    user_id = active_tokens.get(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
        )
    
    return user


def require_admin(user: models.User = Depends(require_auth)) -> models.User:
    """要求当前用户为管理员"""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return user


@router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(models.User).filter(models.User.username == username).first()
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已禁用",
        )
    
    # 创建令牌
    token = create_token()
    active_tokens[token] = user.id
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_public_dict(user),
    }


@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """用户登出"""
    if credentials and credentials.credentials in active_tokens:
        del active_tokens[credentials.credentials]
    return {"message": "已登出"}


@router.get("/me")
def get_current_user_info(user: models.User = Depends(require_auth)):
    """获取当前用户信息"""
    return {
        **_user_public_dict(user),
        "is_active": user.is_active,
        "created_at": user.created_at,
        "last_login": user.last_login,
    }


@router.patch("/profile")
def update_profile(
    body: ProfileUpdate,
    user: models.User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """更新个人信息（不含用户名、密码）"""
    data = body.model_dump(exclude_unset=True)

    if "full_name" in data:
        data["full_name"] = (data["full_name"] or "").strip() or None
    if "department" in data:
        data["department"] = (data["department"] or "").strip() or None

    if "email" in data:
        email = (data["email"] or "").strip() or None
        data["email"] = email
        if email:
            other = (
                db.query(models.User)
                .filter(models.User.email == email, models.User.id != user.id)
                .first()
            )
            if other:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该邮箱已被其他用户使用",
                )

    if "date_format" in data:
        df = (data["date_format"] or "").strip() or None
        data["date_format"] = df
        if df and df not in ALLOWED_DATE_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的日期格式",
            )

    if "time_format" in data:
        tf = (data["time_format"] or "").strip() or None
        data["time_format"] = tf
        if tf and tf not in ALLOWED_TIME_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的时间格式",
            )

    if "user_timezone" in data:
        tz = (data["user_timezone"] or "").strip() or None
        data["user_timezone"] = tz
        if tz:
            try:
                ZoneInfo(tz)
            except ZoneInfoNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的时区",
                )

    for key, value in data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return {"message": "已保存", "user": _user_public_dict(user)}


@router.post("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    user: models.User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """修改密码"""
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误",
        )
    
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度至少6位",
        )
    
    user.hashed_password = hash_password(new_password)
    db.commit()
    
    return {"message": "密码修改成功"}


# 初始化默认管理员账户
def init_default_user(db: Session):
    """初始化默认用户"""
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin:
        admin = models.User(
            username="admin",
            email="admin@weaps.com",
            hashed_password=hash_password("admin123"),
            full_name="系统管理员",
            is_active=True,
            is_admin=True
        )
        db.add(admin)
        db.commit()
        print("已创建默认管理员账户: admin / admin123")
