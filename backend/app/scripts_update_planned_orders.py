from datetime import datetime

from .database import SessionLocal
from .models import ProductionOrder, OrderType, OrderStatus


def main() -> None:
    session = SessionLocal()
    try:
        # 交货期区间：2026-03-09 ~ 2026-03-20（含）
        start = datetime(2026, 3, 9)
        end = datetime(2026, 3, 20, 23, 59, 59)

        q = (
            session.query(ProductionOrder)
            .filter(
                ProductionOrder.order_type == OrderType.PLANNED.value,
                ProductionOrder.due_date >= start,
                ProductionOrder.due_date <= end,
            )
        )

        orders = q.all()
        print(
            f"Found {len(orders)} planned orders "
            f"in range 2026-03-09 ~ 2026-03-20."
        )
        if not orders:
            return

        updated = 0
        for o in orders:
            # “待排程”对应为：计划订单且状态重置为 created
            if o.status != OrderStatus.CREATED.value:
                o.status = OrderStatus.CREATED.value
                updated += 1

        session.commit()
        print(f"Updated {updated} orders to status 'created' (待排程).")
    finally:
        session.close()


if __name__ == "__main__":
    main()

