"""检查缓存中的排程数据"""
import sys
sys.path.insert(0, '.')

from app.scheduler.cache import schedule_cache

def check_cache():
    """检查缓存状态"""
    print("=" * 60)
    print("缓存状态检查")
    print("=" * 60)
    
    print(f"\n有未保存的更改: {schedule_cache.has_unsaved_changes}")
    
    all_ops = schedule_cache.get_all_operations()
    print(f"缓存中的工序数量: {len(all_ops)}")
    
    if all_ops:
        print("\n缓存中的工序 (前20个):")
        for op in all_ops[:20]:
            print(f"  工序ID={op.operation_id}, 订单ID={op.order_id}, "
                  f"资源ID={op.resource_id}, "
                  f"开始={op.scheduled_start}, 结束={op.scheduled_end}")
        
        # 按资源分组
        by_resource = {}
        for op in all_ops:
            if op.resource_id not in by_resource:
                by_resource[op.resource_id] = []
            by_resource[op.resource_id].append(op)
        
        print("\n按资源分组:")
        for res_id, ops in sorted(by_resource.items()):
            print(f"  资源 {res_id}: {len(ops)} 个工序")

if __name__ == '__main__':
    check_cache()
