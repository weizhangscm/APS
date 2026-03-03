"""
更新所有订单的交货期时间为23:59
保持日期不变，只修改时间部分
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from app import models
from datetime import datetime

def update_due_date_times():
    """更新所有订单的交货期时间为23:59"""
    db = SessionLocal()
    
    try:
        # 获取所有订单
        orders = db.query(models.ProductionOrder).all()
        
        print(f"找到 {len(orders)} 个订单")
        print("-" * 80)
        
        updated_count = 0
        
        for order in orders:
            if order.due_date:
                old_due_date = order.due_date
                # 保持日期不变，只修改时间为23:59:00
                new_due_date = order.due_date.replace(hour=23, minute=59, second=0, microsecond=0)
                
                # 只有时间真的不同才更新
                if old_due_date != new_due_date:
                    order.due_date = new_due_date
                    updated_count += 1
                    
                    order_type_label = "生产订单" if order.order_type == "production" else "计划订单"
                    print(f"[更新] {order_type_label} {order.order_number}")
                    print(f"  原交货期: {old_due_date.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"  新交货期: {new_due_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if updated_count > 0:
            db.commit()
            print("-" * 80)
            print(f"[OK] 成功更新 {updated_count} 个订单的交货期时间")
        else:
            print("-" * 80)
            print("[OK] 所有订单的交货期时间已经是23:59，无需更新")
        
        # 验证结果
        print("\n验证更新结果:")
        print("-" * 80)
        orders_check = db.query(models.ProductionOrder).all()
        non_2359_count = 0
        
        for order in orders_check:
            if order.due_date:
                if order.due_date.hour != 23 or order.due_date.minute != 59:
                    non_2359_count += 1
                    print(f"[警告] {order.order_number} 交货期时间不是23:59: {order.due_date}")
        
        if non_2359_count == 0:
            print("[OK] 所有订单的交货期时间均为23:59")
        else:
            print(f"[警告] 仍有 {non_2359_count} 个订单的交货期时间不是23:59")
        
    except Exception as e:
        db.rollback()
        print(f"[错误] 更新失败: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 80)
    print("更新所有订单的交货期时间为23:59")
    print("=" * 80)
    print()
    
    update_due_date_times()
    
    print()
    print("=" * 80)
    print("更新完成")
    print("=" * 80)
