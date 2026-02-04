# -*- coding: utf-8 -*-
"""检查缓存中的资源分配情况"""
import sys
sys.path.insert(0, '.')

from app.scheduler.cache import schedule_cache
from app.database import SessionLocal
from app import models

db = SessionLocal()

print("=== 缓存状态 ===")
status = schedule_cache.get_status()
print(f"有未保存的更改: {status['has_unsaved_changes']}")
print(f"缓存的工序数量: {status['cached_operations']}")
print(f"影响的订单数量: {status['affected_orders']}")

if status['has_unsaved_changes']:
    print("\n=== 缓存中的工序详情 ===")
    cached_ops = schedule_cache.get_all_operations()
    
    # 统计每个资源的工序数量
    resource_count = {}
    for op in cached_ops:
        res_id = op.resource_id
        if res_id not in resource_count:
            resource_count[res_id] = []
        resource_count[res_id].append(op.operation_id)
    
    # 获取资源名称
    resources = db.query(models.Resource).all()
    resource_names = {r.id: r.name for r in resources}
    
    print("\n按资源分组的缓存工序:")
    for res_id, op_ids in sorted(resource_count.items()):
        res_name = resource_names.get(res_id, f"Unknown({res_id})")
        print(f"\n{res_name} (ID={res_id}): {len(op_ids)} 个工序")
        
        # 查询这些工序的订单信息
        for op_id in op_ids[:5]:  # 只显示前5个
            op = db.query(models.Operation).filter(models.Operation.id == op_id).first()
            if op:
                order = op.order
                # 检查数据库中的原始 resource_id
                db_resource_id = op.resource_id
                db_resource_name = resource_names.get(db_resource_id, "None")
                
                cached_op = next((c for c in cached_ops if c.operation_id == op_id), None)
                cached_resource_name = resource_names.get(cached_op.resource_id, "None") if cached_op else "N/A"
                
                print(f"  - {order.order_number} - {op.name}: DB资源={db_resource_name}({db_resource_id}), 缓存资源={cached_resource_name}({cached_op.resource_id if cached_op else 'N/A'})")
        
        if len(op_ids) > 5:
            print(f"  ... 还有 {len(op_ids) - 5} 个工序")

    # 特别检查 CNC机床-3 的工序是否在缓存中
    print("\n=== 检查原本在 CNC机床-3 的工序 ===")
    cnc3_ops = db.query(models.Operation).filter(models.Operation.resource_id == 3).all()
    print(f"数据库中 CNC机床-3 的工序数量: {len(cnc3_ops)}")
    
    for op in cnc3_ops:
        order = op.order
        cached_op = next((c for c in cached_ops if c.operation_id == op.id), None)
        if cached_op:
            cached_res_name = resource_names.get(cached_op.resource_id, "Unknown")
            print(f"  {order.order_number} - {op.name}: 缓存中资源已变为 {cached_res_name}({cached_op.resource_id})")
        else:
            print(f"  {order.order_number} - {op.name}: 不在缓存中（保持原样）")

db.close()
