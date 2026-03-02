"""按订单号删除订单（会级联删除其工序）"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app import models

ORDER_NUMBER = "PLN22448157"

def main():
    db = SessionLocal()
    try:
        order = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_number == ORDER_NUMBER
        ).first()
        if not order:
            print(f"未找到订单: {ORDER_NUMBER}")
            return
        order_id = order.id
        ops_count = db.query(models.Operation).filter(models.Operation.order_id == order_id).count()
        db.delete(order)
        db.commit()
        print(f"已删除订单 {ORDER_NUMBER} (id={order_id})，及其 {ops_count} 道工序。")
    finally:
        db.close()

if __name__ == "__main__":
    main()
