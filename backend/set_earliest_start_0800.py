"""将刚创建的五笔连接器计划订单的开始时间设为各自交货日 08:00"""
import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.database import SessionLocal
from app import models

ORDER_NUMBERS = [
    "PLN2026030201",
    "PLN2026030302",
    "PLN2026030403",
    "PLN2026030504",
    "PLN2026030605",
]

def main():
    db = SessionLocal()
    try:
        for order_number in ORDER_NUMBERS:
            order = db.query(models.ProductionOrder).filter(
                models.ProductionOrder.order_number == order_number
            ).first()
            if not order:
                print(f"未找到订单: {order_number}")
                continue
            # 开始时间 = 交货日 08:00
            due = order.due_date
            earliest_start = due.replace(hour=8, minute=0, second=0, microsecond=0)
            order.earliest_start = earliest_start
            print(f"  {order_number}  交货日期 {due.date()}  开始时间 08:00")
        db.commit()
        print("已将所有 5 笔订单的开始时间设为 08:00。")
    finally:
        db.close()

if __name__ == "__main__":
    main()
