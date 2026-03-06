from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


# Enums
class OrderType(str, Enum):
    """订单类型"""
    PLANNED = "planned"      # 计划订单 - 待排程
    PRODUCTION = "production"  # 生产订单 - 已下达


class OrderStatus(str, Enum):
    CREATED = "created"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OperationStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# WorkCenter Schemas
class WorkCenterBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None


class WorkCenterCreate(WorkCenterBase):
    pass


class WorkCenterUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class WorkCenter(WorkCenterBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Resource Schemas
class ResourceBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    work_center_id: int
    capacity_per_day: float = 8.0
    efficiency: float = 1.0
    description: Optional[str] = None


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    work_center_id: Optional[int] = None
    capacity_per_day: Optional[float] = None
    efficiency: Optional[float] = None
    description: Optional[str] = None


class Resource(ResourceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResourceWithWorkCenter(Resource):
    work_center: Optional[WorkCenter] = None


# Shift Schemas
class ShiftBase(BaseModel):
    resource_id: int
    shift_code: str = Field(..., max_length=50)
    shift_name: str = Field(..., max_length=100)
    start_time: str = Field(..., max_length=10)   # "HH:mm"
    end_time: str = Field(..., max_length=10)     # "HH:mm"
    break_time: int = 0                           # 休息时间(分钟)


class ShiftCreate(ShiftBase):
    pass


class ShiftUpdate(BaseModel):
    resource_id: Optional[int] = None
    shift_code: Optional[str] = Field(None, max_length=50)
    shift_name: Optional[str] = Field(None, max_length=100)
    start_time: Optional[str] = Field(None, max_length=10)
    end_time: Optional[str] = Field(None, max_length=10)
    break_time: Optional[int] = None


class Shift(ShiftBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShiftWithResource(Shift):
    resource: Optional[Resource] = None


# Product Schemas
class ProductBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    unit: str = "PCS"


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    unit: Optional[str] = None


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# RoutingOperation Schemas
class RoutingOperationBase(BaseModel):
    sequence: int
    name: str = Field(..., max_length=100)
    work_center_id: Optional[int] = None  # 可选，若提供 resource_id 则由后端推导
    resource_id: Optional[int] = None     # 指定资源（与 DS资源 一致）
    setup_time: float = 0.0
    run_time_per_unit: float
    description: Optional[str] = None


class RoutingOperationCreate(RoutingOperationBase):
    pass


class RoutingOperationUpdate(BaseModel):
    sequence: Optional[int] = None
    name: Optional[str] = Field(None, max_length=100)
    work_center_id: Optional[int] = None
    resource_id: Optional[int] = None
    setup_time: Optional[float] = None
    run_time_per_unit: Optional[float] = None
    description: Optional[str] = None


class RoutingOperation(RoutingOperationBase):
    id: int
    routing_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoutingOperationWithWorkCenter(RoutingOperation):
    work_center: Optional[WorkCenter] = None
    resource: Optional["Resource"] = None


# Routing Schemas
class RoutingBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    product_id: int
    version: str = "1.0"
    is_active: int = 1
    description: Optional[str] = None


class RoutingCreate(RoutingBase):
    operations: Optional[List[RoutingOperationCreate]] = None


class RoutingUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    product_id: Optional[int] = None
    version: Optional[str] = None
    is_active: Optional[int] = None
    description: Optional[str] = None


class Routing(RoutingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoutingWithOperations(Routing):
    operations: List[RoutingOperationWithWorkCenter] = []
    product: Optional[Product] = None


# Operation Schemas
class OperationBase(BaseModel):
    order_id: int
    routing_operation_id: int
    resource_id: Optional[int] = None
    sequence: int
    name: str = Field(..., max_length=100)
    setup_time: float = 0.0
    run_time: float
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    status: OperationStatus = OperationStatus.PENDING


class OperationCreate(OperationBase):
    pass


class OperationUpdate(BaseModel):
    resource_id: Optional[int] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    status: Optional[OperationStatus] = None


class Operation(OperationBase):
    id: int
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OperationWithDetails(Operation):
    resource: Optional[Resource] = None


# ProductionOrder Schemas
class ProductionOrderBase(BaseModel):
    order_number: str = Field(..., max_length=50)
    order_type: OrderType = OrderType.PLANNED
    product_id: int
    quantity: float
    due_date: datetime
    earliest_start: Optional[datetime] = None
    priority: int = 5
    status: OrderStatus = OrderStatus.CREATED
    confirmed_start: Optional[datetime] = None  # 生产订单确认开始时间
    confirmed_end: Optional[datetime] = None    # 生产订单确认结束时间
    description: Optional[str] = None


class ProductionOrderCreate(ProductionOrderBase):
    pass


class ProductionOrderUpdate(BaseModel):
    order_type: Optional[OrderType] = None
    product_id: Optional[int] = None
    quantity: Optional[float] = None
    due_date: Optional[datetime] = None
    earliest_start: Optional[datetime] = None
    priority: Optional[int] = None
    status: Optional[OrderStatus] = None
    confirmed_start: Optional[datetime] = None
    confirmed_end: Optional[datetime] = None
    description: Optional[str] = None


class ProductionOrder(ProductionOrderBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductionOrderWithOperations(ProductionOrder):
    product: Optional[Product] = None
    operations: List[OperationWithDetails] = []


# 转换为生产订单的请求
class ConvertToProductionRequest(BaseModel):
    confirmed_start: Optional[datetime] = None  # 不填则使用排程的开始时间
    confirmed_end: Optional[datetime] = None    # 不填则使用排程的结束时间


# Scheduling Schemas
class SchedulingDirection(str, Enum):
    FORWARD = "forward"
    BACKWARD = "backward"


class SchedulingRequest(BaseModel):
    order_ids: Optional[List[int]] = None  # None means all orders
    direction: SchedulingDirection = SchedulingDirection.FORWARD
    consider_capacity: bool = True
    priority_rule: str = "EDD"  # EDD, SPT, FIFO


class SchedulingResult(BaseModel):
    success: bool
    message: str
    scheduled_orders: int
    scheduled_operations: int
    conflicts: List[dict] = []


class OperationReschedule(BaseModel):
    operation_id: int
    new_start: datetime
    new_resource_id: Optional[int] = None


# Gantt Chart Data
class GanttTask(BaseModel):
    id: str
    text: str
    start_date: str
    end_date: str
    parent: Optional[str] = None
    progress: float = 0
    type: Optional[str] = None
    order_id: Optional[int] = None
    operation_id: Optional[int] = None
    resource_id: Optional[int] = None
    product_id: Optional[int] = None  # 产品ID - 用于按产品过滤
    status: Optional[str] = None
    color: Optional[str] = None
    task_type: Optional[str] = None  # "operation", "changeover", "project"
    order_type: Optional[str] = None  # "planned", "production"
    order_status: Optional[str] = None  # 订单状态: "created", "scheduled", "in_progress", "completed", "cancelled"
    changeover_time: Optional[float] = None  # 切换时间（小时）
    is_preview: bool = False  # 是否是预览模式下的临时数据
    work_hours: Optional[float] = None  # 作业时间（小时），用于时长列显示，避免用日历跨度导致“排程后总时长变大”的误解


class GanttLink(BaseModel):
    id: str
    source: str
    target: str
    type: str = "0"  # 0=finish-to-start


class GanttData(BaseModel):
    data: List[GanttTask]
    links: List[GanttLink]
    has_unsaved_changes: bool = False  # 是否有未保存的排程更改


# KPI Schemas
class ResourceUtilization(BaseModel):
    resource_id: int
    resource_name: str
    work_center_name: str
    total_capacity_hours: float
    scheduled_hours: float
    utilization_percent: float


class OrderKPI(BaseModel):
    total_orders: int
    scheduled_orders: int
    on_time_orders: int
    delayed_orders: int
    on_time_rate: float


class KPIDashboard(BaseModel):
    resource_utilization: List[ResourceUtilization]
    order_kpi: OrderKPI
    avg_lead_time_hours: float
    capacity_load_by_day: dict


# DS View Requests
class ResourceRescheduleRequest(BaseModel):
    resource_ids: List[int]
    strategy: str


class AutoPlanRequest(BaseModel):
    plan_type: str  # "heuristic" or "optimizer"
    heuristic_id: Optional[str] = None
    optimizer_config: Optional[dict] = None
    resource_ids: Optional[List[int]] = None


class CancelPlanRequest(BaseModel):
    """取消计划请求"""
    resource_ids: Optional[List[int]] = None  # 要取消排程的资源ID列表
    product_ids: Optional[List[int]] = None   # 要取消排程的产品ID列表


class SavePlanRequest(BaseModel):
    """保存计划请求"""
    resource_ids: Optional[List[int]] = None  # 要保存排程的资源ID列表
    product_ids: Optional[List[int]] = None   # 要保存排程的产品ID列表


# 新增：联动调整工序请求
class RescheduleWithLinksRequest(BaseModel):
    operation_id: int
    new_start: datetime
    new_resource_id: Optional[int] = None
    strategy: str = "EDD"
    move_linked_operations: bool = True


# 新增：资源利用率时间槽
class UtilizationTimeSlot(BaseModel):
    start: str
    end: str
    utilization: float


# 新增：资源利用率数据
class ResourceUtilizationData(BaseModel):
    resource_id: int
    resource_name: str
    description: Optional[str] = None
    capacity: float = 24
    time_slots: List[UtilizationTimeSlot] = []


# 新增：资源利用率响应
class UtilizationResponse(BaseModel):
    data: List[ResourceUtilizationData]


# 新增：产品视图甘特图任务（包含产品ID）
class GanttTaskWithProduct(GanttTask):
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    sequence: Optional[int] = None


# ==================== Setup Matrix Schemas ====================

# Setup Group Schemas
class SetupGroupBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None


class SetupGroupCreate(SetupGroupBase):
    pass


class SetupGroupUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class SetupGroup(SetupGroupBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Product Setup Group Schemas
class ProductSetupGroupBase(BaseModel):
    product_id: int
    setup_group_id: int
    work_center_id: Optional[int] = None


class ProductSetupGroupCreate(ProductSetupGroupBase):
    pass


class ProductSetupGroup(ProductSetupGroupBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProductSetupGroupWithDetails(ProductSetupGroup):
    product: Optional[Product] = None
    setup_group: Optional[SetupGroup] = None
    work_center: Optional[WorkCenter] = None


# Setup Matrix Schemas
class SetupMatrixBase(BaseModel):
    from_setup_group_id: int
    to_setup_group_id: int
    resource_id: Optional[int] = None
    work_center_id: Optional[int] = None
    changeover_time: float = Field(..., ge=0, description="切换时间(小时)")
    description: Optional[str] = None


class SetupMatrixCreate(SetupMatrixBase):
    pass


class SetupMatrixUpdate(BaseModel):
    from_setup_group_id: Optional[int] = None
    to_setup_group_id: Optional[int] = None
    resource_id: Optional[int] = None
    work_center_id: Optional[int] = None
    changeover_time: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None


class SetupMatrix(SetupMatrixBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SetupMatrixWithDetails(SetupMatrix):
    from_setup_group: Optional[SetupGroup] = None
    to_setup_group: Optional[SetupGroup] = None
    resource: Optional[Resource] = None
    work_center: Optional[WorkCenter] = None


# Setup Matrix Query Response
class SetupMatrixGrid(BaseModel):
    """矩阵网格视图"""
    setup_groups: List[SetupGroup]
    matrix: dict  # {from_group_id: {to_group_id: changeover_time}}
    resource_id: Optional[int] = None
    work_center_id: Optional[int] = None
