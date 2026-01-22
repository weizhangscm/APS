"""
初始化演示数据脚本
创建工作中心、资源、产品、工艺路线和生产订单
"""
import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.database import SessionLocal, init_db
from app import models


def create_demo_data(force=False):
    """创建演示数据"""
    from app.database import engine, Base
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_data = False
        try:
            existing_data = db.query(models.WorkCenter).count() > 0
        except:
            pass
        
        if existing_data:
            if not force:
                print("数据已存在，跳过初始化")
                print("使用 --force 参数强制重新创建数据")
                return
            else:
                print("强制模式：重建数据库结构...")
                db.close()
                # 删除所有表并重建
                Base.metadata.drop_all(bind=engine)
                Base.metadata.create_all(bind=engine)
                db = SessionLocal()
                print("数据库结构已重建")
        else:
            # 确保所有表都存在
            Base.metadata.create_all(bind=engine)
        
        print("开始创建演示数据...")
        
        # ==================== 工作中心 ====================
        work_centers = [
            models.WorkCenter(code="WC001", name="机加工车间", description="CNC加工、车削、铣削"),
            models.WorkCenter(code="WC002", name="钣金车间", description="冲压、折弯、焊接"),
            models.WorkCenter(code="WC003", name="装配车间", description="组装、调试"),
            models.WorkCenter(code="WC004", name="喷涂车间", description="表面处理、喷漆"),
            models.WorkCenter(code="WC005", name="检测车间", description="质量检测、测试"),
            models.WorkCenter(code="WC006", name="包装车间", description="包装、入库"),
        ]
        
        for wc in work_centers:
            db.add(wc)
        db.commit()
        print(f"创建了 {len(work_centers)} 个工作中心")
        
        # Refresh to get IDs
        for wc in work_centers:
            db.refresh(wc)
        
        # ==================== 资源 ====================
        resources = [
            # 机加工车间资源
            models.Resource(code="M001", name="CNC机床-1", work_center_id=work_centers[0].id, capacity_per_day=8.0, efficiency=1.0),
            models.Resource(code="M002", name="CNC机床-2", work_center_id=work_centers[0].id, capacity_per_day=8.0, efficiency=0.95),
            models.Resource(code="M003", name="CNC机床-3", work_center_id=work_centers[0].id, capacity_per_day=8.0, efficiency=0.98),
            models.Resource(code="M004", name="车床-1", work_center_id=work_centers[0].id, capacity_per_day=8.0, efficiency=1.0),
            models.Resource(code="M005", name="车床-2", work_center_id=work_centers[0].id, capacity_per_day=8.0, efficiency=0.95),
            models.Resource(code="M006", name="铣床-1", work_center_id=work_centers[0].id, capacity_per_day=8.0, efficiency=1.0),
            # 钣金车间资源
            models.Resource(code="S001", name="冲床-1", work_center_id=work_centers[1].id, capacity_per_day=8.0, efficiency=1.0),
            models.Resource(code="S002", name="折弯机-1", work_center_id=work_centers[1].id, capacity_per_day=8.0, efficiency=0.95),
            models.Resource(code="S003", name="焊接工位-1", work_center_id=work_centers[1].id, capacity_per_day=8.0, efficiency=1.0),
            models.Resource(code="S004", name="焊接工位-2", work_center_id=work_centers[1].id, capacity_per_day=8.0, efficiency=0.9),
            # 装配车间资源
            models.Resource(code="A001", name="装配工位-1", work_center_id=work_centers[2].id, capacity_per_day=8.0, efficiency=1.0),
            models.Resource(code="A002", name="装配工位-2", work_center_id=work_centers[2].id, capacity_per_day=8.0, efficiency=1.0),
            models.Resource(code="A003", name="装配工位-3", work_center_id=work_centers[2].id, capacity_per_day=8.0, efficiency=0.9),
            models.Resource(code="A004", name="装配工位-4", work_center_id=work_centers[2].id, capacity_per_day=8.0, efficiency=0.95),
            # 喷涂车间资源
            models.Resource(code="C001", name="喷涂线-1", work_center_id=work_centers[3].id, capacity_per_day=8.0, efficiency=1.0),
            models.Resource(code="C002", name="喷涂线-2", work_center_id=work_centers[3].id, capacity_per_day=8.0, efficiency=0.95),
            # 检测车间资源
            models.Resource(code="T001", name="检测设备-1", work_center_id=work_centers[4].id, capacity_per_day=8.0, efficiency=1.0),
            models.Resource(code="T002", name="检测设备-2", work_center_id=work_centers[4].id, capacity_per_day=8.0, efficiency=1.0),
            models.Resource(code="T003", name="检测设备-3", work_center_id=work_centers[4].id, capacity_per_day=8.0, efficiency=0.95),
            # 包装车间资源
            models.Resource(code="P001", name="包装线-1", work_center_id=work_centers[5].id, capacity_per_day=8.0, efficiency=1.0),
            models.Resource(code="P002", name="包装线-2", work_center_id=work_centers[5].id, capacity_per_day=8.0, efficiency=0.95),
        ]
        
        for res in resources:
            db.add(res)
        db.commit()
        print(f"创建了 {len(resources)} 个资源")
        
        # ==================== 产品(物料) ====================
        products = [
            models.Product(code="MAT001", name="精密齿轮", description="高精度齿轮组件", unit="PCS"),
            models.Product(code="MAT002", name="电机外壳", description="铝合金电机外壳", unit="PCS"),
            models.Product(code="MAT003", name="传感器模块", description="温度传感器组件", unit="PCS"),
            models.Product(code="MAT004", name="控制板", description="主控制电路板", unit="PCS"),
            models.Product(code="MAT005", name="轴承座", description="精密轴承座", unit="PCS"),
            models.Product(code="MAT006", name="连接器", description="高速数据连接器", unit="PCS"),
            models.Product(code="MAT007", name="散热器", description="铝制散热模组", unit="PCS"),
            models.Product(code="MAT008", name="机箱", description="不锈钢机箱", unit="PCS"),
            models.Product(code="MAT009", name="电源模块", description="开关电源模块", unit="PCS"),
            models.Product(code="MAT010", name="显示面板", description="LCD显示面板组件", unit="PCS"),
        ]
        
        for prod in products:
            db.add(prod)
        db.commit()
        print(f"创建了 {len(products)} 个产品(物料)")
        
        for prod in products:
            db.refresh(prod)
        
        # ==================== 工艺路线 ====================
        # 工艺路线模板 - 不同类型产品的工序组合
        routing_templates = [
            # 机加工类产品 (齿轮、轴承座)
            {
                "ops": [
                    {"seq": 10, "name": "CNC粗加工", "wc": 0, "setup": 0.5, "run": 0.05},
                    {"seq": 20, "name": "CNC精加工", "wc": 0, "setup": 0.3, "run": 0.08},
                    {"seq": 30, "name": "组装", "wc": 2, "setup": 0.2, "run": 0.03},
                    {"seq": 40, "name": "检测", "wc": 4, "setup": 0.1, "run": 0.02},
                    {"seq": 50, "name": "包装", "wc": 5, "setup": 0.1, "run": 0.01},
                ]
            },
            # 钣金类产品 (外壳、机箱、散热器)
            {
                "ops": [
                    {"seq": 10, "name": "冲压下料", "wc": 1, "setup": 0.4, "run": 0.03},
                    {"seq": 20, "name": "折弯成型", "wc": 1, "setup": 0.3, "run": 0.04},
                    {"seq": 30, "name": "焊接", "wc": 1, "setup": 0.3, "run": 0.05},
                    {"seq": 40, "name": "喷涂", "wc": 3, "setup": 0.2, "run": 0.03},
                    {"seq": 50, "name": "检测", "wc": 4, "setup": 0.1, "run": 0.02},
                    {"seq": 60, "name": "包装", "wc": 5, "setup": 0.1, "run": 0.01},
                ]
            },
            # 电子组装类产品 (控制板、电源模块、显示面板)
            {
                "ops": [
                    {"seq": 10, "name": "零件加工", "wc": 0, "setup": 0.3, "run": 0.04},
                    {"seq": 20, "name": "组装焊接", "wc": 2, "setup": 0.2, "run": 0.06},
                    {"seq": 30, "name": "功能测试", "wc": 4, "setup": 0.15, "run": 0.04},
                    {"seq": 40, "name": "包装", "wc": 5, "setup": 0.1, "run": 0.01},
                ]
            },
            # 精密组件类 (传感器、连接器)
            {
                "ops": [
                    {"seq": 10, "name": "精密加工", "wc": 0, "setup": 0.4, "run": 0.06},
                    {"seq": 20, "name": "装配", "wc": 2, "setup": 0.25, "run": 0.05},
                    {"seq": 30, "name": "精密检测", "wc": 4, "setup": 0.2, "run": 0.03},
                    {"seq": 40, "name": "包装", "wc": 5, "setup": 0.1, "run": 0.01},
                ]
            },
        ]
        
        # 产品与工艺路线映射
        product_routing_map = {
            0: 0,  # 精密齿轮 -> 机加工类
            1: 1,  # 电机外壳 -> 钣金类
            2: 3,  # 传感器模块 -> 精密组件类
            3: 2,  # 控制板 -> 电子组装类
            4: 0,  # 轴承座 -> 机加工类
            5: 3,  # 连接器 -> 精密组件类
            6: 1,  # 散热器 -> 钣金类
            7: 1,  # 机箱 -> 钣金类
            8: 2,  # 电源模块 -> 电子组装类
            9: 2,  # 显示面板 -> 电子组装类
        }
        
        routings = []
        for i, prod in enumerate(products):
            template_idx = product_routing_map[i]
            template = routing_templates[template_idx]
            
            routing = models.Routing(
                code=f"RT{str(i+1).zfill(3)}", 
                name=f"{prod.name}标准工艺", 
                product_id=prod.id,
                version="1.0",
                is_active=1
            )
            db.add(routing)
            db.commit()
            db.refresh(routing)
            routings.append(routing)
            
            for op in template["ops"]:
                routing_op = models.RoutingOperation(
                    routing_id=routing.id,
                    sequence=op["seq"],
                    name=op["name"],
                    work_center_id=work_centers[op["wc"]].id,
                    setup_time=op["setup"],
                    run_time_per_unit=op["run"]
                )
                db.add(routing_op)
            
            db.commit()
        
        print(f"创建了 {len(routings)} 条工艺路线及工序")
        
        # ==================== 订单 (计划订单 + 生产订单) ====================
        base_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        
        # 计划订单 (35个) - 待排程
        planned_orders_data = []
        planned_count = 35
        
        for i in range(planned_count):
            # 随机选择产品
            product_idx = random.randint(0, len(products) - 1)
            product = products[product_idx]
            
            # 随机数量 (50-500)
            quantity = random.randint(5, 50) * 10
            
            # 交期: 5-30天后
            due_days = random.randint(5, 30)
            
            # 优先级 1-10
            priority = random.randint(1, 10)
            
            planned_orders_data.append({
                "order_number": f"PLN2026{str(i+1).zfill(4)}",
                "order_type": models.OrderType.PLANNED.value,
                "product_id": product.id,
                "quantity": quantity,
                "due_date": base_date + timedelta(days=due_days),
                "priority": priority,
                "description": f"{product.name}计划订单"
            })
        
        # 生产订单 (15个) - 已确认时间
        production_orders_data = []
        production_count = 15
        
        for i in range(production_count):
            # 随机选择产品
            product_idx = random.randint(0, len(products) - 1)
            product = products[product_idx]
            
            # 随机数量 (50-300)
            quantity = random.randint(5, 30) * 10
            
            # 交期: 2-15天后
            due_days = random.randint(2, 15)
            
            # 确认开始时间: 1-7天后
            start_days = random.randint(1, min(due_days - 1, 7))
            confirmed_start = base_date + timedelta(days=start_days, hours=random.randint(0, 8))
            
            # 确认结束时间: 开始后1-5天
            duration_days = random.randint(1, min(due_days - start_days, 5))
            confirmed_end = confirmed_start + timedelta(days=duration_days, hours=random.randint(0, 8))
            
            # 优先级 1-5 (生产订单通常优先级更高)
            priority = random.randint(1, 5)
            
            production_orders_data.append({
                "order_number": f"PRD2026{str(i+1).zfill(4)}",
                "order_type": models.OrderType.PRODUCTION.value,
                "product_id": product.id,
                "quantity": quantity,
                "due_date": base_date + timedelta(days=due_days),
                "priority": priority,
                "confirmed_start": confirmed_start,
                "confirmed_end": confirmed_end,
                "description": f"{product.name}生产订单(已下达)"
            })
        
        # 合并并按交期排序
        all_orders_data = planned_orders_data + production_orders_data
        all_orders_data.sort(key=lambda x: x["due_date"])
        
        for order_data in all_orders_data:
            # Create order
            order = models.ProductionOrder(
                order_number=order_data["order_number"],
                order_type=order_data["order_type"],
                product_id=order_data["product_id"],
                quantity=order_data["quantity"],
                due_date=order_data["due_date"],
                priority=order_data["priority"],
                confirmed_start=order_data.get("confirmed_start"),
                confirmed_end=order_data.get("confirmed_end"),
                description=order_data.get("description", ""),
                status=models.OrderStatus.SCHEDULED.value if order_data["order_type"] == models.OrderType.PRODUCTION.value else models.OrderStatus.CREATED.value
            )
            db.add(order)
            db.commit()
            db.refresh(order)
            
            # Get routing for product
            routing = db.query(models.Routing).filter(
                models.Routing.product_id == order_data["product_id"],
                models.Routing.is_active == 1
            ).first()
            
            if routing:
                # Create operations
                routing_ops = db.query(models.RoutingOperation).filter(
                    models.RoutingOperation.routing_id == routing.id
                ).order_by(models.RoutingOperation.sequence).all()
                
                # 生产订单需要分配资源和排程时间
                is_production = order_data["order_type"] == models.OrderType.PRODUCTION.value
                
                if is_production:
                    # 计算每个工序的时间分配
                    confirmed_start = order_data.get("confirmed_start")
                    confirmed_end = order_data.get("confirmed_end")
                    total_duration = (confirmed_end - confirmed_start).total_seconds() if confirmed_start and confirmed_end else 0
                    op_count = len(routing_ops)
                    
                op_start_time = order_data.get("confirmed_start") if is_production else None
                
                for idx, routing_op in enumerate(routing_ops):
                    run_time = routing_op.setup_time + (routing_op.run_time_per_unit * order_data["quantity"])
                    
                    # 为生产订单分配资源
                    resource_id = None
                    scheduled_start = None
                    scheduled_end = None
                    
                    if is_production:
                        # 获取该工作中心的资源列表并随机选择一个
                        work_center_resources = db.query(models.Resource).filter(
                            models.Resource.work_center_id == routing_op.work_center_id
                        ).all()
                        if work_center_resources:
                            selected_resource = random.choice(work_center_resources)
                            resource_id = selected_resource.id
                        else:
                            # 如果找不到对应工作中心的资源，使用任意一个资源
                            any_resource = db.query(models.Resource).first()
                            if any_resource:
                                resource_id = any_resource.id
                        
                        # 计算排程时间 - 确保每个工序都有时间分配
                        if confirmed_start and confirmed_end:
                            op_duration = total_duration / op_count if op_count > 0 else 0
                            scheduled_start = op_start_time if op_start_time else confirmed_start
                            scheduled_end = scheduled_start + timedelta(seconds=op_duration) if op_duration > 0 else scheduled_start + timedelta(hours=run_time)
                            op_start_time = scheduled_end  # 下一个工序从这里开始
                    
                    operation = models.Operation(
                        order_id=order.id,
                        routing_operation_id=routing_op.id,
                        resource_id=resource_id,
                        sequence=routing_op.sequence,
                        name=routing_op.name,
                        setup_time=routing_op.setup_time,
                        run_time=run_time,
                        scheduled_start=scheduled_start,
                        scheduled_end=scheduled_end,
                        status=models.OperationStatus.SCHEDULED.value if is_production else models.OperationStatus.PENDING.value
                    )
                    db.add(operation)
                
                db.commit()
        
        print(f"创建了 {planned_count} 个计划订单")
        print(f"创建了 {production_count} 个生产订单")
        
        # ==================== 切换矩阵 (Setup Matrix) ====================
        # 创建切换组
        setup_groups = [
            models.SetupGroup(code="SG-METAL", name="金属件组", description="金属材质的产品，切换需要更换刀具"),
            models.SetupGroup(code="SG-PLASTIC", name="塑料件组", description="塑料材质的产品"),
            models.SetupGroup(code="SG-LARGE", name="大型件组", description="大型产品，需要调整夹具"),
            models.SetupGroup(code="SG-SMALL", name="小型件组", description="小型产品，精密加工"),
            models.SetupGroup(code="SG-STANDARD", name="标准件组", description="标准规格产品"),
        ]
        
        for sg in setup_groups:
            db.add(sg)
        db.commit()
        
        for sg in setup_groups:
            db.refresh(sg)
        
        print(f"创建了 {len(setup_groups)} 个切换组")
        
        # 将产品分配到切换组
        # 获取所有产品
        all_products = db.query(models.Product).all()
        product_assignments = []
        
        for idx, product in enumerate(all_products):
            # 根据产品特性分配切换组
            if "金属" in product.name or "钢" in product.name or "铝" in product.name:
                group_id = setup_groups[0].id  # 金属件组
            elif "塑料" in product.name or "树脂" in product.name:
                group_id = setup_groups[1].id  # 塑料件组
            elif idx % 5 == 0:
                group_id = setup_groups[2].id  # 大型件组
            elif idx % 5 == 1:
                group_id = setup_groups[3].id  # 小型件组
            else:
                group_id = setup_groups[4].id  # 标准件组
            
            assignment = models.ProductSetupGroup(
                product_id=product.id,
                setup_group_id=group_id,
                work_center_id=None  # 全局分配
            )
            product_assignments.append(assignment)
            db.add(assignment)
        
        db.commit()
        print(f"创建了 {len(product_assignments)} 个产品-切换组分配")
        
        # 创建全局切换矩阵
        # 不同切换组之间的切换时间（小时）
        matrix_data = [
            # 从金属件组切换到其他组
            (setup_groups[0].id, setup_groups[1].id, 1.5, "金属→塑料：需要清洁和更换刀具"),
            (setup_groups[0].id, setup_groups[2].id, 0.5, "金属→大型件：调整夹具"),
            (setup_groups[0].id, setup_groups[3].id, 1.0, "金属→小型件：更换夹具和刀具"),
            (setup_groups[0].id, setup_groups[4].id, 0.3, "金属→标准件：简单调整"),
            # 从塑料件组切换到其他组
            (setup_groups[1].id, setup_groups[0].id, 2.0, "塑料→金属：彻底清洁和更换刀具"),
            (setup_groups[1].id, setup_groups[2].id, 1.0, "塑料→大型件：调整设备"),
            (setup_groups[1].id, setup_groups[3].id, 0.5, "塑料→小型件：简单调整"),
            (setup_groups[1].id, setup_groups[4].id, 0.8, "塑料→标准件：清洁和调整"),
            # 从大型件组切换到其他组
            (setup_groups[2].id, setup_groups[0].id, 0.5, "大型件→金属：调整夹具"),
            (setup_groups[2].id, setup_groups[1].id, 1.0, "大型件→塑料：调整和清洁"),
            (setup_groups[2].id, setup_groups[3].id, 1.5, "大型件→小型件：更换夹具"),
            (setup_groups[2].id, setup_groups[4].id, 0.3, "大型件→标准件：简单调整"),
            # 从小型件组切换到其他组
            (setup_groups[3].id, setup_groups[0].id, 1.0, "小型件→金属：更换刀具和夹具"),
            (setup_groups[3].id, setup_groups[1].id, 0.5, "小型件→塑料：简单调整"),
            (setup_groups[3].id, setup_groups[2].id, 1.5, "小型件→大型件：更换夹具"),
            (setup_groups[3].id, setup_groups[4].id, 0.2, "小型件→标准件：微调"),
            # 从标准件组切换到其他组
            (setup_groups[4].id, setup_groups[0].id, 0.3, "标准件→金属：简单调整"),
            (setup_groups[4].id, setup_groups[1].id, 0.8, "标准件→塑料：清洁和调整"),
            (setup_groups[4].id, setup_groups[2].id, 0.3, "标准件→大型件：简单调整"),
            (setup_groups[4].id, setup_groups[3].id, 0.2, "标准件→小型件：微调"),
        ]
        
        for from_id, to_id, time, desc in matrix_data:
            entry = models.SetupMatrix(
                from_setup_group_id=from_id,
                to_setup_group_id=to_id,
                changeover_time=time,
                description=desc,
                resource_id=None,
                work_center_id=None  # 全局矩阵
            )
            db.add(entry)
        
        db.commit()
        print(f"创建了 {len(matrix_data)} 条切换矩阵记录")
        
        print("\n" + "=" * 50)
        print("演示数据创建完成！")
        print("=" * 50)
        print("数据摘要:")
        print(f"  - 工作中心: {db.query(models.WorkCenter).count()} 个")
        print(f"  - 资源: {db.query(models.Resource).count()} 个")
        print(f"  - 产品(物料): {db.query(models.Product).count()} 个")
        print(f"  - 工艺路线: {db.query(models.Routing).count()} 条")
        planned = db.query(models.ProductionOrder).filter(models.ProductionOrder.order_type == models.OrderType.PLANNED.value).count()
        production = db.query(models.ProductionOrder).filter(models.ProductionOrder.order_type == models.OrderType.PRODUCTION.value).count()
        print(f"  - 计划订单: {planned} 个")
        print(f"  - 生产订单: {production} 个")
        print(f"  - 工序: {db.query(models.Operation).count()} 道")
        print(f"  - 切换组: {db.query(models.SetupGroup).count()} 个")
        print(f"  - 切换矩阵: {db.query(models.SetupMatrix).count()} 条")
        
    except Exception as e:
        db.rollback()
        print(f"创建演示数据失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='初始化APS演示数据')
    parser.add_argument('--force', action='store_true', help='强制重新创建数据（清除现有数据）')
    args = parser.parse_args()
    create_demo_data(force=args.force)
