"""按表格数据创建计划订单：交货期、数量、优先级见数据，产品随机分配。"""
import sys
import random
sys.path.insert(0, '.')

from datetime import datetime
from app.database import SessionLocal
from app import models

# 截图表格数据：交货期(月/日/年)、数量、优先级
ORDERS = [
    {"due_date": "2026-03-23", "quantity": 79, "priority": 7},
    {"due_date": "2026-03-23", "quantity": 57, "priority": 9},
    {"due_date": "2026-03-23", "quantity": 70, "priority": 5},
    {"due_date": "2026-03-24", "quantity": 93, "priority": 7},
    {"due_date": "2026-03-24", "quantity": 32, "priority": 2},
    {"due_date": "2026-03-24", "quantity": 25, "priority": 8},
    {"due_date": "2026-03-24", "quantity": 83, "priority": 10},
    {"due_date": "2026-03-24", "quantity": 95, "priority": 2},
    {"due_date": "2026-03-25", "quantity": 97, "priority": 2},
    {"due_date": "2026-03-25", "quantity": 47, "priority": 2},
    {"due_date": "2026-03-25", "quantity": 4, "priority": 8},
    {"due_date": "2026-03-25", "quantity": 73, "priority": 1},
    {"due_date": "2026-03-26", "quantity": 24, "priority": 1},
    {"due_date": "2026-03-26", "quantity": 57, "priority": 7},
    {"due_date": "2026-03-26", "quantity": 29, "priority": 9},
    {"due_date": "2026-03-26", "quantity": 18, "priority": 3},
    {"due_date": "2026-03-27", "quantity": 65, "priority": 8},
    {"due_date": "2026-03-27", "quantity": 60, "priority": 4},
    {"due_date": "2026-03-27", "quantity": 36, "priority": 10},
    {"due_date": "2026-03-27", "quantity": 2, "priority": 1},
]


def main():
    db = SessionLocal()
    try:
        # 获取所有有有效工艺路线的产品，用于随机分配
        products_with_routing = []
        products = db.query(models.Product).all()
        for p in products:
            routing = db.query(models.Routing).filter(
                models.Routing.product_id == p.id,
                models.Routing.is_active == 1
            ).first()
            if routing:
                products_with_routing.append((p, routing))

        if not products_with_routing:
            print("未找到任何带有效工艺路线的产品，请先维护产品和工艺路线。")
            return

        # 工序名称到资源ID（与 orders 路由一致）
        OPERATION_NAME_TO_RESOURCE = {
            '冲压下料': 7,
            '折弯成型': 8,
            '焊接': 9,
        }
        all_resources = db.query(models.Resource).order_by(models.Resource.id).all()
        work_center_to_first_resource = {}
        for res in all_resources:
            if res.work_center_id not in work_center_to_first_resource:
                work_center_to_first_resource[res.work_center_id] = res.id

        created = []
        for i, row in enumerate(ORDERS):
            due = datetime.strptime(row["due_date"], "%Y-%m-%d").replace(hour=8, minute=0, second=0, microsecond=0)
            product, routing = random.choice(products_with_routing)
            product_id = product.id

            base = f"PLN{row['due_date'].replace('-', '')}{(i+1):02d}"
            order_number = base
            suffix = 0
            while db.query(models.ProductionOrder).filter(models.ProductionOrder.order_number == order_number).first():
                suffix += 1
                order_number = f"{base}_{suffix}"

            db_order = models.ProductionOrder(
                order_number=order_number,
                order_type=models.OrderType.PLANNED.value,
                product_id=product_id,
                quantity=row["quantity"],
                due_date=due,
                earliest_start=None,
                priority=row["priority"],
                status=models.OrderStatus.CREATED.value,
                description=f"{product.name} 计划订单",
            )
            db.add(db_order)
            db.flush()

            routing_ops = db.query(models.RoutingOperation).filter(
                models.RoutingOperation.routing_id == routing.id
            ).order_by(models.RoutingOperation.sequence).all()

            for routing_op in routing_ops:
                run_time = routing_op.setup_time + (routing_op.run_time_per_unit * row["quantity"])
                default_resource_id = OPERATION_NAME_TO_RESOURCE.get(
                    routing_op.name,
                    work_center_to_first_resource.get(routing_op.work_center_id),
                )
                db_operation = models.Operation(
                    order_id=db_order.id,
                    routing_operation_id=routing_op.id,
                    resource_id=default_resource_id,
                    sequence=routing_op.sequence,
                    name=routing_op.name,
                    setup_time=routing_op.setup_time,
                    run_time=run_time,
                    status=models.OperationStatus.PENDING.value,
                )
                db.add(db_operation)

            created.append((order_number, product.name, row["due_date"], row["quantity"], row["priority"]))

        db.commit()
        print(f"已创建 {len(created)} 个计划订单（产品随机）：")
        for order_number, product_name, due, qty, pri in created:
            print(f"  {order_number}  产品 {product_name}  交货期 {due}  数量 {qty}  优先级 {pri}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
