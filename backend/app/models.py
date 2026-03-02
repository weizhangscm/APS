from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base


class User(Base):
    """用户"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class OrderType(str, enum.Enum):
    """订单类型"""
    PLANNED = "planned"      # 计划订单 - 待排程，时间未确定
    PRODUCTION = "production"  # 生产订单 - 已下达，时间已确定


class OrderStatus(str, enum.Enum):
    CREATED = "created"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OperationStatus(str, enum.Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class WorkCenter(Base):
    """工作中心 - 生产车间或区域"""
    __tablename__ = "work_centers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    resources = relationship("Resource", back_populates="work_center", cascade="all, delete-orphan")


class Resource(Base):
    """资源 - 具体的机器或工人"""
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    work_center_id = Column(Integer, ForeignKey("work_centers.id"), nullable=False)
    capacity_per_day = Column(Float, default=8.0)  # 每天可用小时数
    efficiency = Column(Float, default=1.0)  # 效率系数
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    work_center = relationship("WorkCenter", back_populates="resources")
    operations = relationship("Operation", back_populates="resource")


class Product(Base):
    """产品主数据"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    unit = Column(String(20), default="PCS")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    routings = relationship("Routing", back_populates="product", cascade="all, delete-orphan")
    orders = relationship("ProductionOrder", back_populates="product")


class Routing(Base):
    """工艺路线 - 产品的生产工艺"""
    __tablename__ = "routings"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    version = Column(String(20), default="1.0")
    is_active = Column(Integer, default=1)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="routings")
    operations = relationship("RoutingOperation", back_populates="routing", cascade="all, delete-orphan")


class RoutingOperation(Base):
    """工艺路线工序 - 工艺路线中的具体工序定义"""
    __tablename__ = "routing_operations"

    id = Column(Integer, primary_key=True, index=True)
    routing_id = Column(Integer, ForeignKey("routings.id"), nullable=False)
    sequence = Column(Integer, nullable=False)  # 工序顺序
    name = Column(String(100), nullable=False)
    work_center_id = Column(Integer, ForeignKey("work_centers.id"), nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=True)  # 指定资源（DS工艺路线用）
    setup_time = Column(Float, default=0.0)  # 准备时间(小时)
    run_time_per_unit = Column(Float, nullable=False)  # 单件加工时间(小时)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    routing = relationship("Routing", back_populates="operations")
    work_center = relationship("WorkCenter")
    resource = relationship("Resource")


class ProductionOrder(Base):
    """订单 - 包含计划订单和生产订单"""
    __tablename__ = "production_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    order_type = Column(String(20), default=OrderType.PLANNED.value)  # 订单类型
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    due_date = Column(DateTime, nullable=False)
    earliest_start = Column(DateTime, nullable=True)
    priority = Column(Integer, default=5)  # 1-10, 1最高优先级
    status = Column(String(20), default=OrderStatus.CREATED.value)
    # 生产订单的确认时间（仅生产订单有效）
    confirmed_start = Column(DateTime, nullable=True)
    confirmed_end = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="orders")
    operations = relationship("Operation", back_populates="order", cascade="all, delete-orphan")


class Operation(Base):
    """工序实例 - 生产订单的具体工序"""
    __tablename__ = "operations"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("production_orders.id"), nullable=False)
    routing_operation_id = Column(Integer, ForeignKey("routing_operations.id"), nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=True)
    sequence = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    setup_time = Column(Float, default=0.0)  # 基础准备时间
    changeover_time = Column(Float, default=0.0)  # 产品切换时间（来自Setup Matrix）
    run_time = Column(Float, nullable=False)  # 总加工时间
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    status = Column(String(20), default=OperationStatus.PENDING.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = relationship("ProductionOrder", back_populates="operations")
    routing_operation = relationship("RoutingOperation")
    resource = relationship("Resource", back_populates="operations")


class SetupGroup(Base):
    """切换组 - 将具有相似切换特性的产品分组"""
    __tablename__ = "setup_groups"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    products = relationship("ProductSetupGroup", back_populates="setup_group")


class ProductSetupGroup(Base):
    """产品-切换组关联 - 一个产品在不同工作中心可能属于不同切换组"""
    __tablename__ = "product_setup_groups"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    setup_group_id = Column(Integer, ForeignKey("setup_groups.id"), nullable=False)
    work_center_id = Column(Integer, ForeignKey("work_centers.id"), nullable=True)  # 可选，为空表示全局
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product")
    setup_group = relationship("SetupGroup", back_populates="products")
    work_center = relationship("WorkCenter")


class SetupMatrix(Base):
    """切换矩阵 - 定义从一个切换组切换到另一个切换组的时间"""
    __tablename__ = "setup_matrix"

    id = Column(Integer, primary_key=True, index=True)
    from_setup_group_id = Column(Integer, ForeignKey("setup_groups.id"), nullable=False)
    to_setup_group_id = Column(Integer, ForeignKey("setup_groups.id"), nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=True)  # 可选，为空表示工作中心级别
    work_center_id = Column(Integer, ForeignKey("work_centers.id"), nullable=True)  # 可选
    changeover_time = Column(Float, nullable=False)  # 切换时间（小时）
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    from_setup_group = relationship("SetupGroup", foreign_keys=[from_setup_group_id])
    to_setup_group = relationship("SetupGroup", foreign_keys=[to_setup_group_id])
    resource = relationship("Resource")
    work_center = relationship("WorkCenter")
