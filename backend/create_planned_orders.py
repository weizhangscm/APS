"""
创建 20 个计划订单：交货期 2026.3.9 - 2026.3.13，数量小于 100
"""
import sys
import os
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app import models

# 交货期范围 2026-03-09 至 2026-03-13（当天 23:59）
DUE_DATE_START = datetime(2026, 3, 9, 23, 59, 0)
DUE_DATE_END = datetime(2026, 3, 13, 23, 59, 0)
COUNT = 20
QUANTITY_MAX = 99  # 数量小于 100

# 工序名称到默认资源ID（与 orders 路由一致）
OPERATION_NAME_TO_RESOURCE = {
    "冲压下料": 7,
    "折弯成型": 8,
    "焊接": 9,
}


def get_next_pln_order_number(db):
    """获取下一个可用的 PLN 订单号（PLN2026xxxx）"""
    orders = (
        db.query(models.ProductionOrder.order_number)
        .filter(models.ProductionOrder.order_number.like("PLN2026%"))
        .all()
    )
    max_num = 0
    for (order_number,) in orders:
        try:
            suffix = order_number[7:]  # "PLN2026" 后四位
            n = int(suffix)
            if n > max_num:
                max_num = n
        except ValueError:
            continue
    return f"PLN2026{str(max_num + 1).zfill(4)}"


def main():
    db = SessionLocal()
    try:
        products = db.query(models.Product).all()
        if not products:
            print("错误: 没有产品主数据，请先运行 init_demo_data.py")
            return

        # 工作中心到第一个资源的映射
        all_resources = db.query(models.Resource).order_by(models.Resource.id).all()
        work_center_to_first_resource = {}
        for res in all_resources:
            if res.work_center_id not in work_center_to_first_resource:
                work_center_to_first_resource[res.work_center_id] = res.id

        created = []
        due_dates = [
            datetime(2026, 3, 9, 23, 59, 0),
            datetime(2026, 3, 10, 23, 59, 0),
            datetime(2026, 3, 11, 23, 59, 0),
            datetime(2026, 3, 12, 23, 59, 0),
            datetime(2026, 3, 13, 23, 59, 0),
        ]

        for i in range(COUNT):
            order_number = get_next_pln_order_number(db)
            product = random.choice(products)
            quantity = random.randint(1, QUANTITY_MAX)
            due_date = random.choice(due_dates)
            priority = random.randint(1, 10)

            routing = (
                db.query(models.Routing)
                .filter(
                    models.Routing.product_id == product.id,
                    models.Routing.is_active == 1,
                )
                .first()
            )
            if not routing:
                print(f"  跳过 {order_number}: 产品 {product.name} 没有有效工艺路线")
                continue

            order = models.ProductionOrder(
                order_number=order_number,
                order_type=models.OrderType.PLANNED.value,
                product_id=product.id,
                quantity=quantity,
                due_date=due_date,
                priority=priority,
                status=models.OrderStatus.CREATED.value,
                description=f"{product.name} 计划订单",
            )
            db.add(order)
            db.commit()
            db.refresh(order)

            routing_ops = (
                db.query(models.RoutingOperation)
                .filter(models.RoutingOperation.routing_id == routing.id)
                .order_by(models.RoutingOperation.sequence)
                .all()
            )

            for routing_op in routing_ops:
                run_time = routing_op.setup_time + (
                    routing_op.run_time_per_unit * quantity
                )
                default_resource_id = (
                    getattr(routing_op, "resource_id", None)
                    or OPERATION_NAME_TO_RESOURCE.get(
                        routing_op.name,
                        work_center_to_first_resource.get(routing_op.work_center_id),
                    )
                )
                op = models.Operation(
                    order_id=order.id,
                    routing_operation_id=routing_op.id,
                    resource_id=default_resource_id,
                    sequence=routing_op.sequence,
                    name=routing_op.name,
                    setup_time=routing_op.setup_time,
                    run_time=run_time,
                    status=models.OperationStatus.PENDING.value,
                )
                db.add(op)
            db.commit()

            created.append(
                (order_number, product.name, quantity, due_date.strftime("%Y-%m-%d"))
            )
            print(f"  已创建 {order_number}: {product.name}, 数量={quantity}, 交期={due_date.date()}")

        print(f"\n共创建 {len(created)} 个计划订单（交货期 2026-03-09 ~ 2026-03-13，数量 < 100）")
    except Exception as e:
        db.rollback()
        print(f"创建失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
