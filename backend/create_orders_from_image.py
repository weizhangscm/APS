"""按图片创建计划订单：产品=连接器，交货日期/数量/优先级如图"""
import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.database import SessionLocal
from app import models, schemas

# 图片数据：产品 连接器，交货日期 2026.3.2~3.6，数量 20，优先级 4,3,1,5,2
ORDERS = [
    {"due_date": "2026-03-02", "quantity": 20, "priority": 4},
    {"due_date": "2026-03-03", "quantity": 20, "priority": 3},
    {"due_date": "2026-03-04", "quantity": 20, "priority": 1},
    {"due_date": "2026-03-05", "quantity": 20, "priority": 5},
    {"due_date": "2026-03-06", "quantity": 20, "priority": 2},
]

def main():
    db = SessionLocal()
    try:
        product = db.query(models.Product).filter(models.Product.name == "连接器").first()
        if not product:
            print("未找到产品「连接器」，请先在主数据中创建该产品。")
            return
        product_id = product.id
        routing = db.query(models.Routing).filter(
            models.Routing.product_id == product_id,
            models.Routing.is_active == 1
        ).first()
        if not routing:
            print("产品「连接器」没有有效的工艺路线，请先配置工艺路线。")
            return

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

        routing_ops = db.query(models.RoutingOperation).filter(
            models.RoutingOperation.routing_id == routing.id
        ).order_by(models.RoutingOperation.sequence).all()

        created = []
        for i, row in enumerate(ORDERS):
            due = datetime.strptime(row["due_date"], "%Y-%m-%d").replace(hour=0, minute=0, second=0)
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
            )
            db.add(db_order)
            db.flush()

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

            created.append((order_number, row["due_date"], row["quantity"], row["priority"]))

        db.commit()
        print(f"已创建 {len(created)} 个计划订单（产品：连接器）：")
        for order_number, due, qty, pri in created:
            print(f"  {order_number}  交货日期 {due}  数量 {qty}  优先级 {pri}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
