"""
排程引擎主模块
协调排程算法和约束验证

支持预览模式：
- preview_mode=True: 排程结果存入内存缓存，不写入数据库
- preview_mode=False: 排程结果直接写入数据库（原有行为）
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import logging

from .. import models, schemas

logger = logging.getLogger(__name__)
from .algorithms import ForwardScheduler, BackwardScheduler, StableForwardScheduler, sort_orders_by_priority
from .constraints import ConstraintValidator
from .cache import schedule_cache, CachedOperation


class SchedulingEngine:
    """排程引擎"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = ConstraintValidator(db)
    
    def run_scheduling(
        self,
        order_ids: List[int] = None,
        direction: str = "forward",
        consider_capacity: bool = True,
        priority_rule: str = "EDD"
    ) -> schemas.SchedulingResult:
        """
        执行排程
        
        Args:
            order_ids: 要排程的订单ID列表，None表示所有待排订单
            direction: 排程方向 - "forward"(正向) 或 "backward"(逆向)
            consider_capacity: 是否考虑有限产能
            priority_rule: 优先级规则 - EDD, SPT, FIFO, PRIORITY
        
        Returns:
            排程结果
        """
        # 获取要排程的订单 - 只排程计划订单，不排程生产订单
        query = self.db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PLANNED.value,  # 只排程计划订单
            models.ProductionOrder.status.in_([
                models.OrderStatus.CREATED.value,
                models.OrderStatus.SCHEDULED.value
            ])
        )
        
        if order_ids:
            query = query.filter(models.ProductionOrder.id.in_(order_ids))
        
        orders = query.all()
        
        if not orders:
            return schemas.SchedulingResult(
                success=True,
                message="没有需要排程的订单",
                scheduled_orders=0,
                scheduled_operations=0,
                conflicts=[]
            )
        
        # 按优先级排序
        sorted_orders = sort_orders_by_priority(orders, priority_rule)
        
        # 选择排程算法
        if direction == "backward":
            scheduler = BackwardScheduler(self.db)
        else:
            scheduler = ForwardScheduler(self.db)
        
        # 加载现有排程（用于有限产能计算）
        if consider_capacity:
            start_date = datetime.now() - timedelta(days=7)
            end_date = datetime.now() + timedelta(days=90)
            scheduler.load_resource_schedule(start_date, end_date)
        
        # 执行排程
        scheduled_orders = 0
        scheduled_operations = 0
        
        for order in sorted_orders:
            try:
                results = scheduler.schedule_order(order, consider_capacity)
                if results:
                    scheduled_orders += 1
                    scheduled_operations += len(results)
            except Exception as e:
                print(f"排程订单 {order.order_number} 失败: {str(e)}")
        
        # 提交更改
        self.db.commit()
        
        # 验证约束
        violations = self.validator.validate_all(
            order_ids=[o.id for o in sorted_orders]
        )
        
        conflicts = [v.to_dict() for v in violations]
        
        return schemas.SchedulingResult(
            success=True,
            message=f"排程完成，共排程 {scheduled_orders} 个订单，{scheduled_operations} 道工序",
            scheduled_orders=scheduled_orders,
            scheduled_operations=scheduled_operations,
            conflicts=conflicts
        )
    
    def reschedule_operation(
        self,
        operation_id: int,
        new_start: datetime,
        new_resource_id: int = None
    ) -> Dict:
        """
        重新排程单个工序（用于拖拽调整）
        
        Args:
            operation_id: 工序ID
            new_start: 新的开始时间
            new_resource_id: 新的资源ID（可选）
        
        Returns:
            包含成功状态和冲突信息的字典
        """
        operation = self.db.query(models.Operation).filter(
            models.Operation.id == operation_id
        ).first()
        
        if not operation:
            return {
                'success': False,
                'message': '工序不存在',
                'conflicts': []
            }
        
        # 检查订单类型 - 生产订单不允许调整
        order = operation.order
        if order and order.order_type == models.OrderType.PRODUCTION.value:
            return {
                'success': False,
                'message': '生产订单已确认，不允许调整排程',
                'conflicts': []
            }
        
        # 检查约束
        violations = self.validator.check_operation_move(
            operation_id,
            new_start,
            new_resource_id
        )
        
        # 如果有错误级别的违反，不允许移动
        errors = [v for v in violations if v.severity == 'error']
        if errors:
            return {
                'success': False,
                'message': '移动违反约束',
                'conflicts': [v.to_dict() for v in violations]
            }
        
        # 更新工序
        duration = operation.run_time
        old_start = operation.scheduled_start
        new_end = new_start + timedelta(hours=duration)
        
        # 计算偏移量（秒）
        offset_seconds = (new_start - old_start).total_seconds()
        
        operation.scheduled_start = new_start
        operation.scheduled_end = new_end
        
        if new_resource_id:
            operation.resource_id = new_resource_id
        
        # 联动更新：同步移动该订单的所有后续工序
        successors = self.db.query(models.Operation).filter(
            models.Operation.order_id == operation.order_id,
            models.Operation.sequence > operation.sequence
        ).all()
        
        for succ in successors:
            if succ.scheduled_start:
                succ.scheduled_start = succ.scheduled_start + timedelta(seconds=offset_seconds)
                succ.scheduled_end = succ.scheduled_end + timedelta(seconds=offset_seconds)
        
        self.db.commit()
        
        return {
            'success': True,
            'message': '工序已重新排程',
            'conflicts': [v.to_dict() for v in violations]  # 返回警告
        }
    
    def clear_scheduling(self, order_ids: List[int] = None):
        """清除排程结果"""
        query = self.db.query(models.Operation)
        
        if order_ids:
            query = query.filter(models.Operation.order_id.in_(order_ids))
        
        operations = query.all()
        
        for op in operations:
            op.scheduled_start = None
            op.scheduled_end = None
            op.changeover_time = None
            # 注意：不清除 resource_id，保留工序的默认资源分配
            op.status = models.OperationStatus.PENDING.value
        
        # 更新订单状态
        order_query = self.db.query(models.ProductionOrder)
        if order_ids:
            order_query = order_query.filter(models.ProductionOrder.id.in_(order_ids))
        
        for order in order_query.all():
            order.status = models.OrderStatus.CREATED.value
        
        self.db.commit()
        
        return {'message': f'已清除 {len(operations)} 个工序的排程'}
    
    def save_plan(
        self, 
        resource_ids: List[int] = None, 
        product_ids: List[int] = None
    ) -> Dict:
        """
        保存计划 - 将缓存的排程数据写入数据库，并更新订单状态
        
        工作流程：
        1. 如果有缓存数据（预览模式），先将缓存数据写入数据库
        2. 然后更新工序和订单状态为已排程
        
        Args:
            resource_ids: 资源ID列表，保存这些资源上的排程
            product_ids: 产品ID列表，保存这些产品的订单排程
        
        Returns:
            保存结果统计
        """
        # 检查是否有缓存数据需要保存
        if schedule_cache.has_unsaved_changes:
            # 将缓存数据写入数据库
            cached_operations = schedule_cache.get_all_operations()
            
            if cached_operations:
                saved_from_cache = 0
                affected_order_ids = set()
                # 保存缓存时写入启发式产生的全部工序，不按选中资源过滤，与「订单内部关系：始终考虑」结果一致
                for cached_op in cached_operations:
                    # 查找并更新数据库中的工序
                    op = self.db.query(models.Operation).filter(
                        models.Operation.id == cached_op.operation_id
                    ).first()
                    
                    if op:
                        # 检查产品筛选
                        if product_ids:
                            order = self.db.query(models.ProductionOrder).filter(
                                models.ProductionOrder.id == op.order_id
                            ).first()
                            if order and order.product_id not in product_ids:
                                continue
                        
                        # 更新工序的排程数据
                        op.resource_id = cached_op.resource_id
                        op.scheduled_start = cached_op.scheduled_start
                        op.scheduled_end = cached_op.scheduled_end
                        op.changeover_time = cached_op.changeover_time
                        op.status = models.OperationStatus.SCHEDULED.value
                        
                        affected_order_ids.add(op.order_id)
                        saved_from_cache += 1
                
                # 更新受影响订单的状态
                for order_id in affected_order_ids:
                    order = self.db.query(models.ProductionOrder).filter(
                        models.ProductionOrder.id == order_id
                    ).first()
                    if order:
                        order.status = models.OrderStatus.SCHEDULED.value
                
                self.db.commit()
                
                # 清除缓存
                schedule_cache.mark_saved()
                
                return {
                    'success': True,
                    'message': f'已保存 {len(affected_order_ids)} 个订单的 {saved_from_cache} 道工序排程',
                    'saved_orders': len(affected_order_ids),
                    'saved_operations': saved_from_cache
                }
        
        # 如果没有缓存数据，执行原有逻辑（保存已在数据库中的排程）
        if not resource_ids and not product_ids:
            return {
                'success': False,
                'message': '请指定要保存计划的资源或产品',
                'saved_orders': 0,
                'saved_operations': 0
            }
        
        # 找到需要保存的工序（计划订单且已排程）
        query = self.db.query(models.Operation).join(
            models.ProductionOrder,
            models.Operation.order_id == models.ProductionOrder.id
        ).filter(
            # 只处理计划订单
            models.ProductionOrder.order_type == models.OrderType.PLANNED.value,
            # 只处理已排程的工序
            models.Operation.scheduled_start != None,
            # 只处理状态为 pending 或 scheduled 的工序
            models.Operation.status.in_([
                models.OperationStatus.PENDING.value,
                models.OperationStatus.SCHEDULED.value
            ])
        )
        
        # 根据资源筛选
        if resource_ids:
            query = query.filter(models.Operation.resource_id.in_(resource_ids))
        
        # 根据产品筛选
        if product_ids:
            query = query.filter(models.ProductionOrder.product_id.in_(product_ids))
        
        operations = query.all()
        
        if not operations:
            return {
                'success': True,
                'message': '没有找到需要保存的排程',
                'saved_orders': 0,
                'saved_operations': 0
            }
        
        # 收集受影响的订单ID
        affected_order_ids = set()
        saved_count = 0
        
        for op in operations:
            # 更新工序状态为已排程
            op.status = models.OperationStatus.SCHEDULED.value
            affected_order_ids.add(op.order_id)
            saved_count += 1
        
        # 更新受影响订单的状态为已排程
        for order_id in affected_order_ids:
            order = self.db.query(models.ProductionOrder).filter(
                models.ProductionOrder.id == order_id
            ).first()
            
            if order:
                order.status = models.OrderStatus.SCHEDULED.value
        
        self.db.commit()
        
        return {
            'success': True,
            'message': f'已保存 {len(affected_order_ids)} 个订单的 {saved_count} 道工序排程',
            'saved_orders': len(affected_order_ids),
            'saved_operations': saved_count
        }

    def cancel_plan(
        self, 
        resource_ids: List[int] = None, 
        product_ids: List[int] = None
    ) -> Dict:
        """
        取消计划 - 根据资源和/或产品清除排程
        
        取消计划订单和已排程订单的排程（不影响生产订单），并且只清除尚未开始的排程。
        取消后，订单可以重新被计划。
        
        Args:
            resource_ids: 资源ID列表，清除这些资源上的排程
            product_ids: 产品ID列表，清除这些产品的订单排程
        
        Returns:
            取消结果统计
        """
        if not resource_ids and not product_ids:
            return {
                'success': False,
                'message': '请指定要取消计划的资源或产品',
                'cancelled_orders': 0,
                'cancelled_operations': 0
            }
        
        # 找到需要取消的工序
        # 只处理计划订单（不包含生产订单），包括已排程状态的订单
        query = self.db.query(models.Operation).join(
            models.ProductionOrder,
            models.Operation.order_id == models.ProductionOrder.id
        ).filter(
            # 只处理计划订单（排除生产订单）
            models.ProductionOrder.order_type == models.OrderType.PLANNED.value,
            # 只处理已排程的工序
            models.Operation.scheduled_start != None
        )
        
        # 根据资源筛选
        if resource_ids:
            query = query.filter(models.Operation.resource_id.in_(resource_ids))
        
        # 根据产品筛选
        if product_ids:
            query = query.filter(models.ProductionOrder.product_id.in_(product_ids))
        
        operations = query.all()
        
        if not operations:
            return {
                'success': True,
                'message': '没有找到需要取消的排程',
                'cancelled_orders': 0,
                'cancelled_operations': 0
            }
        
        # 收集受影响的订单ID
        affected_order_ids = set()
        cancelled_count = 0
        
        for op in operations:
            # 检查工序是否已经开始（如果已开始则不能取消）
            if op.status in [models.OperationStatus.IN_PROGRESS.value, models.OperationStatus.COMPLETED.value]:
                continue
            
            # 清除排程信息，但保留 resource_id（工序的默认资源分配）
            op.scheduled_start = None
            op.scheduled_end = None
            op.changeover_time = 0
            op.status = models.OperationStatus.PENDING.value
            # 注意：不清除 resource_id，这样工序可以被重新排程到同一资源
            
            affected_order_ids.add(op.order_id)
            cancelled_count += 1
        
        # 更新受影响订单的状态
        # 如果订单的所有工序都被取消了排程，则更新订单状态为 CREATED
        for order_id in affected_order_ids:
            order = self.db.query(models.ProductionOrder).filter(
                models.ProductionOrder.id == order_id
            ).first()
            
            if order:
                # 检查该订单是否还有已排程的工序
                scheduled_ops = self.db.query(models.Operation).filter(
                    models.Operation.order_id == order_id,
                    models.Operation.scheduled_start != None
                ).count()
                
                if scheduled_ops == 0:
                    order.status = models.OrderStatus.CREATED.value
        
        self.db.commit()
        
        return {
            'success': True,
            'message': f'已取消 {len(affected_order_ids)} 个订单的 {cancelled_count} 道工序排程',
            'cancelled_orders': len(affected_order_ids),
            'cancelled_operations': cancelled_count
        }

    def reschedule_resource(self, resource_ids: List[int], strategy: str):
        """对资源上的工序重新进行策略排程"""
        # 这里实现基于资源的重排逻辑
        # 简化版：清除这些资源上的排程，然后按照策略重新运行排程
        # 找到受影响的订单
        affected_operations = self.db.query(models.Operation).filter(
            models.Operation.resource_id.in_(resource_ids)
        ).all()
        
        affected_order_ids = list(set([op.order_id for op in affected_operations]))
        
        if not affected_order_ids:
            return {"success": True, "message": "所选资源上没有订单"}
            
        # 清除这些订单的排程
        self.clear_scheduling(affected_order_ids)
        
        # 按照新策略重新排程
        return self.run_scheduling(
            order_ids=affected_order_ids,
            priority_rule=strategy
        )

    def auto_plan(self, request: schemas.AutoPlanRequest):
        """执行自动计划"""
        # Debug logs removed to avoid GBK encoding errors on Windows
        if request.plan_type == "heuristic":
            # 检查是否是稳定向前计划
            if request.heuristic_id == "stable_forward":
                return self._run_stable_forward_scheduling(request)
            else:
                # 其他启发式算法
                message = f"执行启发式算法: {request.heuristic_id}"
                
                # 根据启发式类型选择排序规则
                priority_rule = "EDD"
                if request.heuristic_id == "rule1":
                    priority_rule = "SPT"  # 最短作业优先
                elif request.heuristic_id == "rule2":
                    priority_rule = "EDD"  # 最早交期优先
                elif request.heuristic_id == "rule4":
                    priority_rule = "PRIORITY"  # 瓶颈资源优先（按优先级）
                
                result = self.run_scheduling(priority_rule=priority_rule)
                return {
                    "success": True, 
                    "message": message,
                    "scheduled_orders": result.scheduled_orders,
                    "scheduled_operations": result.scheduled_operations
                }
        else:
            # 执行优化器
            message = f"执行优化器，配置: {request.optimizer_config}"
            result = self.run_scheduling(priority_rule="PRIORITY")
            return {
                "success": True, 
                "message": message,
                "scheduled_orders": result.scheduled_orders,
                "scheduled_operations": result.scheduled_operations
            }
    
    def _run_stable_forward_scheduling(self, request: schemas.AutoPlanRequest):
        """
        执行稳定向前计划 (Stable Forward Scheduling)
        
        基于 SAP S4 DS 的稳定向前计划启发式算法.
        
        策略参数说明（参照 SAP PP/DS 详细计划策略参数文件）：
        
        1. sorting_rule (排序规则): 
           - 订单优先级: 按订单优先级字段排序，优先级高的订单先排程
        
        2. planning_mode (计划模式):
           - 查找槽位: 在资源的现有排程中搜索足够大的空闲时间段（有限产能）
        
        3. planning_direction (计划方向):
           - 向前: 从期望日期开始，向未来方向搜索可用时间
           - 向后: 从期望日期开始，向过去方向搜索可用时间
        
        4. expected_date (期望日期):
           - 当前日期: 使用系统当前日期时间作为排程起点
           - 指定日期: 使用订单的最早开始日期或交期作为排程起点
        
        5. order_internal_relation (订单内部关系):
           - 不考虑: 只排选中资源上的工序，不自动调整同订单的其他工序
           - 始终考虑: 排程时维护同订单内所有工序的时间关系，自动调整关联工序
        
        6. sub_planning_mode (子计划模式):
           - 根据调度模式调度相关操作: 关联工序使用相同的排程模式（有限产能）
           - 以无限方式调度相关操作: 关联工序使用无限产能模式排程
        
        7. error_handling (计划出错的操作):
           - 立即终止: 当某工序无法排程时，立即停止整个排程操作
        """
        # 从配置中获取参数
        config = request.optimizer_config or {}
        
        # 基本算法参数
        finite_capacity = config.get('finite_capacity', True)
        resolve_backlog = config.get('resolve_backlog', True)
        resolve_overload = config.get('resolve_overload', True)
        preserve_scheduled = config.get('preserve_scheduled', True)
        sorting_rule = config.get('sorting_rule', '订单优先级')
        planning_horizon = config.get('planning_horizon', 90)
        
        # 策略参数
        planning_mode = config.get('planning_mode', '查找槽位')
        planning_direction = config.get('planning_direction', '向前')
        expected_date = config.get('expected_date', '当前日期')
        order_internal_relation = config.get('order_internal_relation', '不考虑')
        sub_planning_mode = config.get('sub_planning_mode', '根据调度模式调度相关操作')
        error_handling = config.get('error_handling', '立即终止')
        schedule_selected_resources_only = config.get('schedule_selected_resources_only', True)
        
        # 根据排序规则映射到算法参数
        sorting_rule_mapping = {
            '订单优先级': 'PRIORITY',
            'EDD': 'EDD',
            'SPT': 'SPT',
            'FIFO': 'FIFO',
            'PRIORITY': 'PRIORITY'
        }
        algorithm_sorting_rule = sorting_rule_mapping.get(sorting_rule, 'PRIORITY')
        logger.info(
            "[run_heuristic] sorting_rule from config=%r -> algorithm=%s",
            sorting_rule, algorithm_sorting_rule
        )
        
        # 根据计划方向设置
        direction = 'forward' if planning_direction == '向前' else 'backward'
        
        # 根据计划模式设置（当前只支持查找槽位=有限产能）
        use_finite_capacity = (planning_mode == '查找槽位')
        
        # 订单内部关系处理：
        # - "始终考虑": 排程选中资源上的工序时，自动调整同订单的前置/后续工序以维护时间关系
        # - "不考虑": 只排选中资源上的工序，其他工序保持不变
        adjust_related_operations = (order_internal_relation == '始终考虑')
        
        # 子计划模式处理：
        # - "根据调度模式调度相关操作": 关联工序也使用有限产能模式排程
        # - "以无限方式调度相关操作": 关联工序使用无限产能模式，不考虑资源负荷
        infinite_capacity_for_related = (sub_planning_mode == '以无限方式调度相关操作')
        
        # 创建稳定向前计划器
        scheduler = StableForwardScheduler(
            db=self.db,
            finite_capacity=use_finite_capacity and finite_capacity,
            resolve_backlog=resolve_backlog,
            resolve_overload=resolve_overload,
            preserve_scheduled=preserve_scheduled,
            sorting_rule=algorithm_sorting_rule,
            planning_horizon=planning_horizon
        )
        
        # 设置策略参数到 scheduler
        scheduler.direction = direction
        scheduler.expected_date_mode = expected_date
        # 指定日期时使用的具体日期（由策略配置中的日期选择器传入）
        expected_date_value = config.get('expected_date_value')
        if expected_date_value and expected_date == '指定日期':
            try:
                if isinstance(expected_date_value, str):
                    expected_date_value = expected_date_value.replace('.', '-')
                    scheduler.expected_date_value = datetime.strptime(expected_date_value, '%Y-%m-%d')
                else:
                    scheduler.expected_date_value = expected_date_value
            except Exception:
                scheduler.expected_date_value = None
        else:
            scheduler.expected_date_value = None
        scheduler.order_internal_relation = order_internal_relation
        scheduler.adjust_related_operations = adjust_related_operations
        scheduler.infinite_capacity_for_related = infinite_capacity_for_related
        scheduler.error_handling = error_handling
        
        # 获取要排程的订单 - 只排程计划订单
        query = self.db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PLANNED.value,
            models.ProductionOrder.status.in_([
                models.OrderStatus.CREATED.value,
                models.OrderStatus.SCHEDULED.value
            ])
        )
        
        # 获取显示区间（用于"订单内部关系=不考虑"时过滤订单）
        display_start_date = config.get('display_start_date')
        display_end_date = config.get('display_end_date')
        
        # 解析日期字符串
        display_start = None
        display_end = None
        if display_start_date:
            try:
                if isinstance(display_start_date, str):
                    # 处理格式如 "2026.02.04" 或 "2026-02-04"
                    display_start_date = display_start_date.replace('.', '-')
                    display_start = datetime.strptime(display_start_date, '%Y-%m-%d')
            except:
                pass
        if display_end_date:
            try:
                if isinstance(display_end_date, str):
                    display_end_date = display_end_date.replace('.', '-')
                    display_end = datetime.strptime(display_end_date, '%Y-%m-%d')
                    # 将结束日期设为当天的最后时刻
                    display_end = display_end.replace(hour=23, minute=59, second=59)
            except:
                pass
        
        # 如果没有提供显示区间，使用默认值（当前日期 + 11 天，即显示到 02-15）
        # 这是为了在"订单内部关系=不考虑"时，只排程显示区间内的订单
        if display_start is None:
            display_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if display_end is None:
            # 默认显示区间：当前日期 + 11 天
            display_end = display_start + timedelta(days=11)
            display_end = display_end.replace(hour=23, minute=59, second=59)
        
        # 方案C：将显示区间传给排程器，排程阶段严格限制在显示区间内
        scheduler.display_start_date = display_start
        scheduler.display_end_date = display_end
        
        # 只排程选中资源上的工序
        # 如果指定了资源，找到需要在这些资源上加工的订单
        target_operation_ids = None  # 要排程的工序ID列表
        
        # Debug logs removed to avoid GBK encoding errors
        
        if request.resource_ids and schedule_selected_resources_only:
            # 只排选中资源上的工序 - 找到选中资源上的所有工序
            target_operations = self.db.query(models.Operation).filter(
                models.Operation.resource_id.in_(request.resource_ids)
            ).all()
            
            # 有显示区间时，只排程交期在显示区间内的订单（不论「订单内部关系」为不考虑或始终考虑）
            if display_start and display_end:
                filtered_operations = []
                for op in target_operations:
                    order = self.db.query(models.ProductionOrder).filter(
                        models.ProductionOrder.id == op.order_id
                    ).first()
                    if order:
                        # Only include operations with due_date within display range
                        due_date_in_range = (
                            order.due_date and 
                            display_start <= order.due_date <= display_end
                        )
                        if due_date_in_range:
                            filtered_operations.append(op)
                target_operations = filtered_operations
            
            target_operation_ids = [op.id for op in target_operations]
            
            # 获取这些工序所属的订单
            order_ids = list(set([op.order_id for op in target_operations]))
            
            if order_ids:
                query = query.filter(models.ProductionOrder.id.in_(order_ids))
            else:
                # 没有找到工序，尝试通过工作中心匹配
                resource_work_centers = self.db.query(models.Resource.work_center_id).filter(
                    models.Resource.id.in_(request.resource_ids)
                ).distinct().all()
                work_center_ids = [wc[0] for wc in resource_work_centers if wc[0] is not None]
                
                if work_center_ids:
                    # 找到工艺路线中需要这些工作中心的订单
                    routing_order_ids = self.db.query(models.Operation.order_id).join(
                        models.RoutingOperation,
                        models.Operation.routing_operation_id == models.RoutingOperation.id
                    ).filter(
                        models.RoutingOperation.work_center_id.in_(work_center_ids)
                    ).distinct().all()
                    routing_order_ids = [oid[0] for oid in routing_order_ids]
                    
                    if routing_order_ids:
                        query = query.filter(models.ProductionOrder.id.in_(routing_order_ids))
        elif request.resource_ids:
            # 不仅限于选中资源，找到所有相关订单
            # 1. 获取指定资源对应的工作中心
            resource_work_centers = self.db.query(models.Resource.work_center_id).filter(
                models.Resource.id.in_(request.resource_ids)
            ).distinct().all()
            work_center_ids = [wc[0] for wc in resource_work_centers if wc[0] is not None]
            
            # 2. 找到工艺路线中需要使用这些工作中心的订单
            if work_center_ids:
                from sqlalchemy import or_
                
                # 找到已分配给这些资源的订单
                assigned_order_ids = self.db.query(models.Operation.order_id).filter(
                    models.Operation.resource_id.in_(request.resource_ids)
                ).distinct().all()
                assigned_order_ids = [oid[0] for oid in assigned_order_ids]
                
                # 找到工艺路线中需要这些工作中心的订单
                routing_order_ids = self.db.query(models.Operation.order_id).join(
                    models.RoutingOperation,
                    models.Operation.routing_operation_id == models.RoutingOperation.id
                ).filter(
                    models.RoutingOperation.work_center_id.in_(work_center_ids)
                ).distinct().all()
                routing_order_ids = [oid[0] for oid in routing_order_ids]
                
                all_affected_ids = list(set(assigned_order_ids + routing_order_ids))
                
                if all_affected_ids:
                    query = query.filter(models.ProductionOrder.id.in_(all_affected_ids))
        
        orders = query.all()
        
        if not orders:
            return {
                "success": True,
                "message": "稳定向前计划：没有需要排程的订单",
                "scheduled_orders": 0,
                "scheduled_operations": 0,
                "details": {},
                "preview_mode": False
            }
        
        # 检查是否是预览模式（默认启用预览模式）
        preview_mode = config.get('preview_mode', True)
        
        # 执行稳定向前计划
        # 传递目标工序ID列表和策略参数
        results = scheduler.schedule_orders(
            orders, 
            target_operation_ids=target_operation_ids,
            selected_resource_ids=request.resource_ids
        )
        
        # 立即终止：若有订单因找不到可用时间槽而失败，视为排程失败，回滚且不写入缓存，返回错误提示
        failed_details = [d for d in results.get('details', []) if not d.get('success')]
        if error_handling == '立即终止' and failed_details:
            self.db.rollback()
            failed_parts = [
                f"{d.get('order_number', '')}（{d.get('error', '')}）"
                for d in failed_details
            ]
            error_message = "显示区间内产能已用尽，排程已终止。以下订单无法排程：" + "；".join(failed_parts)
            return {
                "success": False,
                "message": error_message,
                "scheduled_orders": results['scheduled_orders'],
                "scheduled_operations": results['scheduled_operations'],
                "backlog_resolved": results['backlog_resolved'],
                "overload_resolved": results['overload_resolved'],
                "conflicts": [],
                "details": results.get('details', []),
                "preview_mode": preview_mode,
                "has_unsaved_changes": False,
                "_engine_version": "v5",
                "_filtered_ops_count": len(target_operation_ids) if target_operation_ids else 0
            }
        
        if preview_mode:
            # 预览模式：将排程结果存入缓存，然后回滚数据库更改
            cached_operations = []
            
            # 从排程结果的 details 中提取已排程的工序信息
            for order_result in results.get('details', []):
                if order_result.get('success') and order_result.get('operations'):
                    for op_info in order_result['operations']:
                        op = self.db.query(models.Operation).filter(
                            models.Operation.id == op_info['operation_id']
                        ).first()
                        
                        if op:
                            start_time = datetime.fromisoformat(op_info['start'])
                            end_time = datetime.fromisoformat(op_info['end'])
                            
                            cached_op = CachedOperation(
                                operation_id=op.id,
                                order_id=op.order_id,
                                resource_id=op_info['resource_id'],
                                scheduled_start=start_time,
                                scheduled_end=end_time,
                                changeover_time=op_info.get('changeover_time', 0),
                                status='scheduled'
                            )
                            cached_operations.append(cached_op)
            
            # 保存到缓存（使用合并模式，保留其他资源的缓存数据）
            message = f"稳定向前计划完成：排程 {results['scheduled_orders']} 个订单，{results['scheduled_operations']} 道工序"
            schedule_cache.set_schedule(cached_operations, message, merge=True)
            
            # 回滚数据库更改
            self.db.rollback()
            
            # 验证约束（使用缓存数据）
            violations = []  # 预览模式下暂不验证约束
            
            if results['backlog_resolved'] > 0:
                message += f"，解决 {results['backlog_resolved']} 个积压"
            if results['overload_resolved'] > 0:
                message += f"，解决 {results['overload_resolved']} 个过载"
            message += "（未保存，请点击'保存计划'确认）"
        else:
            # 非预览模式：直接提交更改
            self.db.commit()
            
            # 验证约束
            violations = self.validator.validate_all(
                order_ids=[o.id for o in orders]
            )
            
            message = f"稳定向前计划完成：排程 {results['scheduled_orders']} 个订单，{results['scheduled_operations']} 道工序"
            if results['backlog_resolved'] > 0:
                message += f"，解决 {results['backlog_resolved']} 个积压"
            if results['overload_resolved'] > 0:
                message += f"，解决 {results['overload_resolved']} 个过载"
        
        return {
            "success": True,
            "message": message,
            "scheduled_orders": results['scheduled_orders'],
            "scheduled_operations": results['scheduled_operations'],
            "backlog_resolved": results['backlog_resolved'],
            "overload_resolved": results['overload_resolved'],
            "conflicts": [v.to_dict() for v in violations] if violations else [],
            "details": results.get('details', []),
            "preview_mode": preview_mode,
            "has_unsaved_changes": schedule_cache.has_unsaved_changes if preview_mode else False,
            "_engine_version": "v5",
            "_filtered_ops_count": len(target_operation_ids) if target_operation_ids else 0
        }
    
    def get_gantt_data(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        view_type: str = "order",  # "order" 或 "resource"
        include_cache: bool = True  # 是否包含缓存的未保存排程
    ) -> schemas.GanttData:
        """
        获取甘特图数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            view_type: 视图类型 - "order"(按订单) 或 "resource"(按资源)
            include_cache: 是否包含缓存的未保存排程数据
        
        Returns:
            甘特图数据
        """
        tasks = []
        links = []
        
        # 默认时间范围
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now() + timedelta(days=30)
        
        # 获取缓存的排程数据（如果有）
        cached_ops = {}
        if include_cache and schedule_cache.has_unsaved_changes:
            for cached_op in schedule_cache.get_all_operations():
                cached_ops[cached_op.operation_id] = cached_op
        
        if view_type == "order":
            tasks, links = self._get_order_view_data(start_date, end_date, cached_ops)
        elif view_type == "product":
            tasks, links = self._get_product_view_data(start_date, end_date, cached_ops)
        else:
            tasks, links = self._get_resource_view_data(start_date, end_date, cached_ops)
        
        return schemas.GanttData(
            data=tasks, 
            links=links,
            has_unsaved_changes=schedule_cache.has_unsaved_changes
        )
    
    def _get_order_view_data(
        self,
        start_date: datetime,
        end_date: datetime,
        cached_ops: Dict[int, 'CachedOperation'] = None
    ) -> tuple:
        """获取订单视图的甘特图数据
        
        Args:
            cached_ops: 缓存的工序排程数据 {operation_id: CachedOperation}
        """
        cached_ops = cached_ops or {}
        tasks = []
        links = []
        
        # 获取有排程的计划订单和所有生产订单
        orders = self.db.query(models.ProductionOrder).filter(
            (
                (models.ProductionOrder.order_type == models.OrderType.PLANNED.value) &
                (models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value)
            ) | (
                models.ProductionOrder.order_type == models.OrderType.PRODUCTION.value
            )
        ).all()
        
        # 状态颜色映射 - 区分计划订单和生产订单
        planned_colors = {
            'pending': '#909399',
            'scheduled': '#409EFF',
            'in_progress': '#E6A23C',
            'completed': '#67C23A'
        }
        # 生产订单使用灰色系 (已锁定)
        production_colors = {
            'pending': '#9CA3AF',
            'scheduled': '#6B7280',  # 灰色
            'in_progress': '#4B5563',
            'completed': '#374151'
        }
        
        for order in orders:
            is_production = order.order_type == models.OrderType.PRODUCTION.value
            status_colors = production_colors if is_production else planned_colors
            order_type_label = "[生产]" if is_production else "[计划]"
            
            # 生产订单使用确认时间，计划订单使用排程时间
            if is_production and order.confirmed_start and order.confirmed_end:
                # 生产订单：使用确认的时间
                order_start = order.confirmed_start
                order_end = order.confirmed_end
                
                # 获取工序（可能没有详细排程）
                operations = self.db.query(models.Operation).filter(
                    models.Operation.order_id == order.id
                ).order_by(models.Operation.sequence).all()
            else:
                # 计划订单：使用排程的时间
                operations = self.db.query(models.Operation).filter(
                    models.Operation.order_id == order.id,
                    models.Operation.scheduled_start != None
                ).order_by(models.Operation.sequence).all()
                
                if not operations:
                    continue
                
                # 计算订单的开始和结束时间
                order_start = min(op.scheduled_start for op in operations)
                order_end = max(op.scheduled_end for op in operations)
            
            # 计算进度
            completed_ops = sum(1 for op in operations if op.status == 'completed')
            progress = completed_ops / len(operations) if operations else 0
            
            # 添加订单任务
            tasks.append(schemas.GanttTask(
                id=f"order_{order.id}",
                text=f"{order_type_label} {order.order_number} - {order.product.name if order.product else ''}",
                start_date=order_start.strftime("%Y-%m-%d %H:%M"),
                end_date=order_end.strftime("%Y-%m-%d %H:%M"),
                progress=progress,
                type="project",
                order_id=order.id,
                status=order.status,
                color='#6B7280' if is_production else None  # 生产订单灰色
            ))
            
            # 添加工序任务
            prev_op_id = None
            for op in operations:
                resource_name = op.resource.name if op.resource else "未分配"
                
                # 生产订单工序可能没有排程时间，使用订单时间均分
                if op.scheduled_start and op.scheduled_end:
                    op_start = op.scheduled_start
                    op_end = op.scheduled_end
                elif is_production:
                    # 根据工序顺序均分时间
                    total_duration = (order_end - order_start).total_seconds()
                    op_count = len(operations)
                    op_duration = total_duration / op_count if op_count > 0 else 0
                    op_idx = operations.index(op)
                    op_start = order_start + timedelta(seconds=op_duration * op_idx)
                    op_end = op_start + timedelta(seconds=op_duration)
                else:
                    continue
                
                # 如果有切换时间，先添加切换工序（dummy product）
                # 注意：排程时间已经包含了切换时间，所以：
                # - 切换时段：scheduled_start 到 scheduled_start + changeover_time
                # - 实际加工：scheduled_start + changeover_time 到 scheduled_end
                changeover_time = getattr(op, 'changeover_time', 0) or 0
                
                if changeover_time > 0 and not is_production:
                    changeover_duration = timedelta(hours=changeover_time)
                    changeover_start = op_start
                    changeover_end = op_start + changeover_duration
                    actual_op_start = changeover_end  # 实际加工从切换结束后开始
                    
                    # 添加切换工序任务
                    tasks.append(schemas.GanttTask(
                        id=f"changeover_{op.id}",
                        text=f"🔄 切换 ({changeover_time:.1f}h)",
                        start_date=changeover_start.strftime("%Y-%m-%d %H:%M"),
                        end_date=changeover_end.strftime("%Y-%m-%d %H:%M"),
                        parent=f"order_{order.id}",
                        progress=1.0 if op.status in ['completed', 'in_progress'] else 0,
                        operation_id=op.id,
                        resource_id=op.resource_id,
                        status='changeover',
                        color='#F59E0B',  # 橙黄色
                        task_type='changeover',
                        order_type=order.order_type,
                        changeover_time=changeover_time,
                        work_hours=changeover_time
                    ))
                    
                    # 切换工序到实际工序的链接
                    links.append(schemas.GanttLink(
                        id=f"link_changeover_{op.id}",
                        source=f"changeover_{op.id}",
                        target=f"op_{op.id}",
                        type="0"
                    ))
                    
                    # 实际工序从切换结束后开始
                    tasks.append(schemas.GanttTask(
                        id=f"op_{op.id}",
                        text=f"{op.sequence} {op.name} ({resource_name})",
                        start_date=actual_op_start.strftime("%Y-%m-%d %H:%M"),
                        end_date=op_end.strftime("%Y-%m-%d %H:%M"),
                        parent=f"order_{order.id}",
                        progress=1.0 if op.status == 'completed' else 0,
                        operation_id=op.id,
                        resource_id=op.resource_id,
                        status=op.status,
                        color=status_colors.get(op.status, '#6B7280' if is_production else '#409EFF'),
                        task_type='operation',
                        order_type=order.order_type,
                        changeover_time=changeover_time,
                        work_hours=op.run_time
                    ))
                else:
                    # 没有切换时间，直接显示工序
                    tasks.append(schemas.GanttTask(
                        id=f"op_{op.id}",
                        text=f"{op.sequence} {op.name} ({resource_name})",
                        start_date=op_start.strftime("%Y-%m-%d %H:%M"),
                        end_date=op_end.strftime("%Y-%m-%d %H:%M"),
                        parent=f"order_{order.id}",
                        progress=1.0 if op.status == 'completed' else 0,
                        operation_id=op.id,
                        resource_id=op.resource_id,
                        status=op.status,
                        color=status_colors.get(op.status, '#6B7280' if is_production else '#409EFF'),
                        task_type='operation',
                        order_type=order.order_type,
                        changeover_time=changeover_time,
                        work_hours=op.run_time
                    ))
                
                # 添加工序之间的链接
                if prev_op_id:
                    links.append(schemas.GanttLink(
                        id=f"link_{prev_op_id}_{op.id}",
                        source=f"op_{prev_op_id}",
                        target=f"op_{op.id}",
                        type="0"
                    ))
                prev_op_id = op.id
        
        return tasks, links
    
    def _get_resource_view_data(
        self,
        start_date: datetime,
        end_date: datetime,
        cached_ops: Dict[int, 'CachedOperation'] = None
    ) -> tuple:
        """获取资源视图的甘特图数据
        
        工序显示逻辑：
        1. 直接使用 operations.resource_id 来确定工序属于哪个资源
        2. 如果 resource_id 为空，则通过工作中心找默认资源（兜底逻辑）
        3. 如果有缓存数据，优先使用缓存中的排程时间
        """
        cached_ops = cached_ops or {}
        tasks = []
        links = []
        
        # 获取所有资源（按ID排序，确保顺序一致）
        resources = self.db.query(models.Resource).order_by(models.Resource.id).all()
        
        # 建立工作中心到第一个资源的映射（用于兜底：当 resource_id 为空时使用）
        work_center_to_first_resource = {}
        for resource in resources:
            if resource.work_center_id not in work_center_to_first_resource:
                work_center_to_first_resource[resource.work_center_id] = resource.id
        
        # 构建缓存中工序按资源分组的映射
        # 用于在有缓存时，按缓存中的resource_id来分组工序
        cached_ops_by_resource = {}
        for op_id, cached_op in cached_ops.items():
            res_id = cached_op.resource_id
            if res_id not in cached_ops_by_resource:
                cached_ops_by_resource[res_id] = set()
            cached_ops_by_resource[res_id].add(op_id)
        
        for resource in resources:
            # 资源作为父任务
            tasks.append(schemas.GanttTask(
                id=f"resource_{resource.id}",
                text=f"{resource.name} ({resource.work_center.name if resource.work_center else ''})",
                start_date=start_date.strftime("%Y-%m-%d %H:%M"),
                end_date=end_date.strftime("%Y-%m-%d %H:%M"),
                type="project",
                resource_id=resource.id
            ))
            
            # 获取该资源的工序
            # 混合模式：缓存中的工序用缓存数据，其他工序用数据库数据
            # 关键：不在缓存中的工序应该显示数据库中的原始数据
            
            if cached_ops:
                # 有缓存数据：混合显示缓存和数据库的工序
                all_operations = []
                
                # 1. 获取缓存中分配到该资源的工序
                cached_op_ids_for_resource = cached_ops_by_resource.get(resource.id, set())
                
                for op_id in cached_op_ids_for_resource:
                    cached_op = cached_ops[op_id]
                    # 不再因排程时间在显示区间外就跳过，否则运行启发式后该资源上的订单会变少
                    # 从数据库获取工序详情
                    op = self.db.query(models.Operation).filter(
                        models.Operation.id == op_id
                    ).first()
                    if op:
                        all_operations.append(op)
                
                # 2. 添加不在缓存中但数据库中属于该资源的工序（未被排程影响的工序）
                # 注意：只排除缓存中的工序ID，不排除所有缓存键
                from sqlalchemy import or_
                cached_op_ids_list = list(cached_ops.keys()) if cached_ops else []
                
                db_operations = self.db.query(models.Operation).join(
                    models.ProductionOrder,
                    models.Operation.order_id == models.ProductionOrder.id
                ).filter(
                    models.Operation.resource_id == resource.id,
                    or_(
                        # 已排程工序：排程时间在显示区间内
                        (models.Operation.scheduled_start != None) & 
                        (models.Operation.scheduled_start <= end_date) &
                        (models.Operation.scheduled_end >= start_date),
                        # 待排程工序：使用订单交货期作为显示时间
                        (models.Operation.scheduled_start == None) & 
                        (models.ProductionOrder.due_date >= start_date) &
                        (models.ProductionOrder.due_date <= end_date)
                    )
                ).all()
                
                # 过滤掉已经在缓存中的工序（避免重复显示）
                for op in db_operations:
                    if op.id not in cached_op_ids_list:
                        all_operations.append(op)
                
                # 3. 与“无缓存”分支一致：兜底添加 resource_id 为空但属于该工作中心的待排程工序，避免运行启发式后订单变少
                pending_without_resource = []
                is_first_resource_in_wc = work_center_to_first_resource.get(resource.work_center_id) == resource.id
                if is_first_resource_in_wc:
                    pending_without_resource = self.db.query(models.Operation).join(
                        models.RoutingOperation,
                        models.Operation.routing_operation_id == models.RoutingOperation.id
                    ).join(
                        models.ProductionOrder,
                        models.Operation.order_id == models.ProductionOrder.id
                    ).filter(
                        models.Operation.resource_id == None,
                        models.RoutingOperation.work_center_id == resource.work_center_id,
                        models.ProductionOrder.due_date >= start_date,
                        models.ProductionOrder.due_date <= end_date
                    ).all()
                for op in pending_without_resource:
                    if op.id not in cached_op_ids_list:
                        all_operations.append(op)
            else:
                # 没有缓存数据：从数据库获取
                from sqlalchemy import or_
                operations_with_resource = self.db.query(models.Operation).join(
                    models.ProductionOrder,
                    models.Operation.order_id == models.ProductionOrder.id
                ).filter(
                    models.Operation.resource_id == resource.id,
                    or_(
                        # 已排程工序：排程时间在显示区间内
                        (models.Operation.scheduled_start != None) & 
                        (models.Operation.scheduled_start <= end_date) &
                        (models.Operation.scheduled_end >= start_date),
                        # 待排程工序：使用订单交货期作为显示时间
                        (models.Operation.scheduled_start == None) & 
                        (models.ProductionOrder.due_date >= start_date) &
                        (models.ProductionOrder.due_date <= end_date)
                    )
                ).all()
                
                # 兜底逻辑：获取 resource_id 为空但属于该资源工作中心的工序
                pending_without_resource = []
                is_first_resource_in_wc = work_center_to_first_resource.get(resource.work_center_id) == resource.id
                
                if is_first_resource_in_wc:
                    pending_without_resource = self.db.query(models.Operation).join(
                        models.RoutingOperation,
                        models.Operation.routing_operation_id == models.RoutingOperation.id
                    ).join(
                        models.ProductionOrder,
                        models.Operation.order_id == models.ProductionOrder.id
                    ).filter(
                        models.Operation.resource_id == None,
                        models.RoutingOperation.work_center_id == resource.work_center_id,
                        models.ProductionOrder.due_date >= start_date,
                        models.ProductionOrder.due_date <= end_date
                    ).all()
                
                all_operations = operations_with_resource + pending_without_resource
            
            # 按排程时间排序（待排程的放在后面）
            # 对于缓存中的工序，使用缓存的时间排序
            def get_sort_key(op):
                if op.id in cached_ops:
                    return (cached_ops[op.id].scheduled_start or datetime.max, op.id)
                return (op.scheduled_start if op.scheduled_start else datetime.max, op.id)
            
            all_operations.sort(key=get_sort_key)
            
            for op in all_operations:
                order = op.order
                order_number = order.order_number if order else ""
                is_production = order.order_type == models.OrderType.PRODUCTION.value if order else False
                
                # 检查缓存中是否有该工序的数据（预览模式）
                cached_op = cached_ops.get(op.id)
                if cached_op:
                    # 使用缓存的排程数据
                    op_scheduled_start = cached_op.scheduled_start
                    op_scheduled_end = cached_op.scheduled_end
                    op_changeover_time = cached_op.changeover_time
                    op_status = cached_op.status
                    op_resource_id = cached_op.resource_id
                    is_scheduled = True
                    is_preview = True  # 标记为预览数据
                else:
                    # 使用数据库中的数据
                    op_scheduled_start = op.scheduled_start
                    op_scheduled_end = op.scheduled_end
                    op_changeover_time = getattr(op, 'changeover_time', 0) or 0
                    op_status = op.status
                    op_resource_id = op.resource_id
                    is_scheduled = op.scheduled_start is not None and op.scheduled_end is not None
                    is_preview = False
                
                # 待排程工序：使用订单交货日期作为显示时间
                if not is_scheduled:
                    if order and order.due_date:
                        # 使用交货日期作为显示时间
                        display_start = order.due_date.replace(hour=8, minute=0, second=0)
                        display_end = order.due_date.replace(hour=8, minute=0, second=0) + timedelta(hours=op.run_time)
                    else:
                        # 没有交货日期，跳过
                        continue
                    
                    # 添加待排程工序任务（时长列用作业时间 run_time，与排程后一致）
                    tasks.append(schemas.GanttTask(
                        id=f"op_{op.id}",
                        text=f"{order_number} - {op.sequence} {op.name}",
                        start_date=display_start.strftime("%Y-%m-%d %H:%M"),
                        end_date=display_end.strftime("%Y-%m-%d %H:%M"),
                        parent=f"resource_{resource.id}",
                        progress=0,
                        operation_id=op.id,
                        order_id=op.order_id,
                        resource_id=resource.id,
                        product_id=order.product_id if order else None,
                        status=op.status,
                        task_type='operation',
                        order_type=order.order_type if order else None,
                        order_status=order.status if order else None,
                        changeover_time=0,
                        work_hours=op.run_time
                    ))
                else:
                    # 已排程工序的逻辑（使用缓存数据或数据库数据）
                    # 预览模式下不添加特殊标记，直接显示在原始订单上
                    # 用户通过"保存计划"按钮确认后才会写入数据库
                    
                    if op_changeover_time > 0 and not is_production:
                        changeover_duration = timedelta(hours=op_changeover_time)
                        changeover_start = op_scheduled_start
                        changeover_end = op_scheduled_start + changeover_duration
                        actual_op_start = changeover_end
                        
                        # 添加切换工序任务（时长为切换时间）
                        tasks.append(schemas.GanttTask(
                            id=f"changeover_{op.id}",
                            text=f"🔄 {order_number} 切换",
                            start_date=changeover_start.strftime("%Y-%m-%d %H:%M"),
                            end_date=changeover_end.strftime("%Y-%m-%d %H:%M"),
                            parent=f"resource_{resource.id}",
                            progress=1.0 if op_status in ['completed', 'in_progress'] else 0,
                            operation_id=op.id,
                            order_id=op.order_id,
                            resource_id=resource.id,
                            product_id=order.product_id if order else None,
                            status='changeover',
                            color='#F59E0B',  # 橙黄色
                            task_type='changeover',
                            order_type=order.order_type if order else None,
                            order_status=order.status if order else None,
                            changeover_time=op_changeover_time,
                            is_preview=is_preview,
                            work_hours=op_changeover_time
                        ))
                        
                        # 实际工序从切换结束后开始（时长列用作业时间）
                        tasks.append(schemas.GanttTask(
                            id=f"op_{op.id}",
                            text=f"{order_number} - {op.sequence} {op.name}",
                            start_date=actual_op_start.strftime("%Y-%m-%d %H:%M"),
                            end_date=op_scheduled_end.strftime("%Y-%m-%d %H:%M"),
                            parent=f"resource_{resource.id}",
                            progress=1.0 if op_status == 'completed' else 0,
                            operation_id=op.id,
                            order_id=op.order_id,
                            resource_id=resource.id,
                            product_id=order.product_id if order else None,
                            status=op_status,
                            task_type='operation',
                            order_type=order.order_type if order else None,
                            order_status=order.status if order else None,
                            changeover_time=op_changeover_time,
                            is_preview=is_preview,
                            work_hours=op.run_time
                        ))
                    else:
                        # 没有切换时间，直接显示工序（时长列用作业时间）
                        tasks.append(schemas.GanttTask(
                            id=f"op_{op.id}",
                            text=f"{order_number} - {op.sequence} {op.name}",
                            start_date=op_scheduled_start.strftime("%Y-%m-%d %H:%M"),
                            end_date=op_scheduled_end.strftime("%Y-%m-%d %H:%M"),
                            parent=f"resource_{resource.id}",
                            progress=1.0 if op_status == 'completed' else 0,
                            operation_id=op.id,
                            order_id=op.order_id,
                            resource_id=resource.id,
                            product_id=order.product_id if order else None,
                            status=op_status,
                            task_type='operation',
                            order_type=order.order_type if order else None,
                            order_status=order.status if order else None,
                            changeover_time=op_changeover_time,
                            is_preview=is_preview,
                            work_hours=op.run_time
                        ))
        
        return tasks, links
    
    def get_kpi_data(self) -> schemas.KPIDashboard:
        """获取KPI仪表板数据"""
        # 资源利用率
        resource_utilization = self._calculate_resource_utilization()
        
        # 订单KPI
        order_kpi = self._calculate_order_kpi()
        
        # 平均提前期
        avg_lead_time = self._calculate_avg_lead_time()
        
        # 按日产能负荷
        capacity_load = self._calculate_capacity_load_by_day()
        
        return schemas.KPIDashboard(
            resource_utilization=resource_utilization,
            order_kpi=order_kpi,
            avg_lead_time_hours=avg_lead_time,
            capacity_load_by_day=capacity_load
        )
    
    def _calculate_resource_utilization(self) -> List[schemas.ResourceUtilization]:
        """计算资源利用率（未来7天，含缓存预览排程和生产订单）"""
        result = []

        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)

        resources = self.db.query(models.Resource).all()

        # 读取缓存排程（预览模式）
        cached_ops: Dict[int, object] = {}
        cached_ops_by_resource: Dict[int, list] = {}
        if schedule_cache.has_unsaved_changes:
            for cached_op in schedule_cache.get_all_operations():
                cached_ops[cached_op.operation_id] = cached_op
                res_id = cached_op.resource_id
                if res_id not in cached_ops_by_resource:
                    cached_ops_by_resource[res_id] = []
                cached_ops_by_resource[res_id].append(cached_op)

        for resource in resources:
            total_capacity = resource.capacity_per_day * 7
            scheduled_hours = 0.0

            # ---- 收集该资源在7天窗口内的工时 ----
            if cached_ops:
                # 有缓存：优先使用缓存时间
                for cached_op in cached_ops_by_resource.get(resource.id, []):
                    s = cached_op.scheduled_start
                    e = cached_op.scheduled_end
                    if s and e:
                        # 与窗口取交集
                        overlap_s = max(s, start_date)
                        overlap_e = min(e, end_date)
                        if overlap_e > overlap_s:
                            scheduled_hours += (overlap_e - overlap_s).total_seconds() / 3600

                # 数据库中不在缓存里的已排程工序（含计划订单和生产订单工序）
                cached_ids = list(cached_ops.keys())
                db_ops = self.db.query(models.Operation).filter(
                    models.Operation.resource_id == resource.id,
                    models.Operation.scheduled_start != None,
                    models.Operation.scheduled_start < end_date,
                    models.Operation.scheduled_end > start_date,
                    ~models.Operation.id.in_(cached_ids) if cached_ids else True
                ).all()
                for op in db_ops:
                    overlap_s = max(op.scheduled_start, start_date)
                    overlap_e = min(op.scheduled_end, end_date)
                    if overlap_e > overlap_s:
                        scheduled_hours += (overlap_e - overlap_s).total_seconds() / 3600
            else:
                # 无缓存：直接读数据库（计划订单工序 + 生产订单工序均含）
                db_ops = self.db.query(models.Operation).filter(
                    models.Operation.resource_id == resource.id,
                    models.Operation.scheduled_start != None,
                    models.Operation.scheduled_start < end_date,
                    models.Operation.scheduled_end > start_date
                ).all()
                for op in db_ops:
                    overlap_s = max(op.scheduled_start, start_date)
                    overlap_e = min(op.scheduled_end, end_date)
                    if overlap_e > overlap_s:
                        scheduled_hours += (overlap_e - overlap_s).total_seconds() / 3600

            # 生产订单：工序若无 scheduled_start/end，用订单 confirmed_start/end 均分工时
            prod_orders = self.db.query(models.ProductionOrder).filter(
                models.ProductionOrder.order_type == models.OrderType.PRODUCTION.value,
                models.ProductionOrder.confirmed_start != None,
                models.ProductionOrder.confirmed_end != None
            ).all()
            for order in prod_orders:
                ops = self.db.query(models.Operation).filter(
                    models.Operation.order_id == order.id,
                    models.Operation.resource_id == resource.id,
                    models.Operation.scheduled_start == None
                ).all()
                if not ops:
                    continue
                order_dur = (order.confirmed_end - order.confirmed_start).total_seconds()
                op_dur_each = order_dur / len(ops) if ops else 0
                for idx, op in enumerate(ops):
                    op_s = order.confirmed_start + timedelta(seconds=op_dur_each * idx)
                    op_e = op_s + timedelta(seconds=op_dur_each)
                    overlap_s = max(op_s, start_date)
                    overlap_e = min(op_e, end_date)
                    if overlap_e > overlap_s:
                        scheduled_hours += (overlap_e - overlap_s).total_seconds() / 3600

            # 待排程工序（已分配资源但无排程时间），用交货期代替
            exclude_ids = list(cached_ops.keys()) if cached_ops else []
            pending_with_resource = self.db.query(models.Operation).filter(
                models.Operation.resource_id == resource.id,
                models.Operation.scheduled_start == None,
                ~models.Operation.id.in_(exclude_ids) if exclude_ids else True
            ).all()
            for op in pending_with_resource:
                order = op.order
                if order and order.due_date and op.run_time:
                    op_s = order.due_date.replace(hour=8, minute=0, second=0, microsecond=0)
                    op_e = op_s + timedelta(hours=op.run_time)
                    overlap_s = max(op_s, start_date)
                    overlap_e = min(op_e, end_date)
                    if overlap_e > overlap_s:
                        scheduled_hours += (overlap_e - overlap_s).total_seconds() / 3600

            # 待排程工序（未分配资源，通过工作中心匹配），用交货期代替
            if resource.work_center_id:
                pending_without_resource = self.db.query(models.Operation).join(
                    models.RoutingOperation,
                    models.Operation.routing_operation_id == models.RoutingOperation.id
                ).filter(
                    models.Operation.resource_id == None,
                    models.Operation.scheduled_start == None,
                    models.RoutingOperation.work_center_id == resource.work_center_id
                ).all()
                for op in pending_without_resource:
                    order = op.order
                    if order and order.due_date and op.run_time:
                        op_s = order.due_date.replace(hour=8, minute=0, second=0, microsecond=0)
                        op_e = op_s + timedelta(hours=op.run_time)
                        overlap_s = max(op_s, start_date)
                        overlap_e = min(op_e, end_date)
                        if overlap_e > overlap_s:
                            scheduled_hours += (overlap_e - overlap_s).total_seconds() / 3600

            utilization = (scheduled_hours / total_capacity * 100) if total_capacity > 0 else 0

            result.append(schemas.ResourceUtilization(
                resource_id=resource.id,
                resource_name=resource.name,
                work_center_name=resource.work_center.name if resource.work_center else "",
                total_capacity_hours=total_capacity,
                scheduled_hours=round(scheduled_hours, 1),
                utilization_percent=round(utilization, 1)
            ))

        return result
    
    def _calculate_order_kpi(self) -> schemas.OrderKPI:
        """计算订单KPI（含缓存预览排程和生产订单）"""
        total = self.db.query(models.ProductionOrder).count()

        # 读取缓存（如果有预览排程则工序时间以缓存为准）
        cached_ops: Dict[int, object] = {}
        if schedule_cache.has_unsaved_changes:
            for cached_op in schedule_cache.get_all_operations():
                cached_ops[cached_op.operation_id] = cached_op

        # 统计"已排程"订单：计划订单status=SCHEDULED，或生产订单有confirmed_end
        planned_scheduled = self.db.query(models.ProductionOrder).filter(
            models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value
        ).all()

        production_orders = self.db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PRODUCTION.value,
            models.ProductionOrder.confirmed_end != None
        ).all()

        # 合并去重（生产订单可能已是SCHEDULED状态）
        all_scheduled_ids = set(o.id for o in planned_scheduled)
        for o in production_orders:
            all_scheduled_ids.add(o.id)

        scheduled = len(all_scheduled_ids)

        # 如果有缓存，把缓存中涉及的订单也算入已排程
        if cached_ops:
            cached_order_ids = set()
            for cached_op in cached_ops.values():
                op_db = self.db.query(models.Operation).filter(
                    models.Operation.id == cached_op.operation_id
                ).first()
                if op_db:
                    cached_order_ids.add(op_db.order_id)
            all_scheduled_ids |= cached_order_ids
            scheduled = len(all_scheduled_ids)

        on_time = 0
        delayed = 0

        # 遍历所有订单：已排程的用实际完工时间，待排程的用交货期作为预计完工时间
        all_orders = self.db.query(models.ProductionOrder).all()

        for order in all_orders:
            if not order.due_date:
                continue

            last_op = self.db.query(models.Operation).filter(
                models.Operation.order_id == order.id
            ).order_by(models.Operation.sequence.desc()).first()

            if not last_op:
                continue

            # 确定完工时间：优先缓存 > scheduled_end > confirmed_end > 交货期（待排程）
            if last_op.id in cached_ops:
                finish_time = cached_ops[last_op.id].scheduled_end
            elif last_op.scheduled_end:
                finish_time = last_op.scheduled_end
            elif order.confirmed_end:
                finish_time = order.confirmed_end
            else:
                # 待排程订单：以交货期当天08:00作为预计完工时间
                finish_time = order.due_date.replace(hour=8, minute=0, second=0, microsecond=0)

            if finish_time <= order.due_date:
                on_time += 1
            else:
                delayed += 1

        on_time_rate = (on_time / total * 100) if total > 0 else 0

        return schemas.OrderKPI(
            total_orders=total,
            scheduled_orders=scheduled,
            on_time_orders=on_time,
            delayed_orders=delayed,
            on_time_rate=round(on_time_rate, 1)
        )
    
    def _calculate_avg_lead_time(self) -> float:
        """计算平均提前期（含缓存预览排程和生产订单）"""
        # 读取缓存
        cached_ops: Dict[int, object] = {}
        if schedule_cache.has_unsaved_changes:
            for cached_op in schedule_cache.get_all_operations():
                cached_ops[cached_op.operation_id] = cached_op

        # 收集所有有效订单：计划订单(SCHEDULED) + 生产订单(有confirmed时间) + 缓存中的订单
        planned_orders = self.db.query(models.ProductionOrder).filter(
            models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value
        ).all()

        production_orders = self.db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PRODUCTION.value,
            models.ProductionOrder.confirmed_end != None
        ).all()

        order_ids = set(o.id for o in planned_orders) | set(o.id for o in production_orders)

        if cached_ops:
            for cached_op in cached_ops.values():
                op_db = self.db.query(models.Operation).filter(
                    models.Operation.id == cached_op.operation_id
                ).first()
                if op_db:
                    order_ids.add(op_db.order_id)

        if not order_ids:
            return 0.0

        # 扩展到所有订单（含待排程），待排程订单用交货期估算提前期
        all_orders = self.db.query(models.ProductionOrder).all()

        total_lead_time = 0.0
        count = 0

        for order in all_orders:
            operations = self.db.query(models.Operation).filter(
                models.Operation.order_id == order.id
            ).all()

            start_times = []
            end_times = []

            for op in operations:
                if op.id in cached_ops:
                    c = cached_ops[op.id]
                    if c.scheduled_start:
                        start_times.append(c.scheduled_start)
                    if c.scheduled_end:
                        end_times.append(c.scheduled_end)
                elif op.scheduled_start and op.scheduled_end:
                    start_times.append(op.scheduled_start)
                    end_times.append(op.scheduled_end)

            # 生产订单无工序时间则用 confirmed_start/end
            if not start_times and order.confirmed_start and order.confirmed_end:
                start_times.append(order.confirmed_start)
                end_times.append(order.confirmed_end)

            # 待排程订单：用所有工序的 run_time 之和估算提前期，以交货期为结束
            if not start_times and order.due_date and operations:
                total_run_hours = sum(op.run_time for op in operations if op.run_time)
                if total_run_hours > 0:
                    est_end = order.due_date.replace(hour=8, minute=0, second=0, microsecond=0)
                    est_start = est_end - timedelta(hours=total_run_hours)
                    start_times.append(est_start)
                    end_times.append(est_end)

            if start_times and end_times:
                lead_time = (max(end_times) - min(start_times)).total_seconds() / 3600
                total_lead_time += lead_time
                count += 1

        return round(total_lead_time / count, 1) if count > 0 else 0.0
    
    def _calculate_capacity_load_by_day(self) -> dict:
        """计算每日产能负荷（未来14天，含缓存预览排程和生产订单）"""
        result = {}

        window_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        window_end = window_start + timedelta(days=14)

        resources = self.db.query(models.Resource).all()
        total_capacity_per_day = sum(r.capacity_per_day for r in resources)

        # 读取缓存
        cached_ops: Dict[int, object] = {}
        if schedule_cache.has_unsaved_changes:
            for cached_op in schedule_cache.get_all_operations():
                cached_ops[cached_op.operation_id] = cached_op

        # 初始化每日结构
        for day_offset in range(14):
            day = window_start + timedelta(days=day_offset)
            result[day.strftime("%Y-%m-%d")] = 0.0

        def _add_hours_to_days(s, e):
            """将 [s, e) 跨越的工时按天累计到 result"""
            if not s or not e or e <= s:
                return
            cur = max(s, window_start)
            end = min(e, window_end)
            while cur < end:
                day_key = cur.strftime("%Y-%m-%d")
                next_day = (cur.replace(hour=0, minute=0, second=0, microsecond=0)
                            + timedelta(days=1))
                seg_end = min(next_day, end)
                if day_key in result:
                    result[day_key] += (seg_end - cur).total_seconds() / 3600
                cur = seg_end

        # 1) 数据库中已排程工序
        db_ops = self.db.query(models.Operation).filter(
            models.Operation.scheduled_start != None,
            models.Operation.scheduled_start < window_end,
            models.Operation.scheduled_end > window_start
        ).all()

        cached_ids = set(cached_ops.keys())
        for op in db_ops:
            if op.id in cached_ids:
                continue  # 以缓存为准，跳过
            _add_hours_to_days(op.scheduled_start, op.scheduled_end)

        # 2) 缓存工序
        for cached_op in cached_ops.values():
            _add_hours_to_days(cached_op.scheduled_start, cached_op.scheduled_end)

        # 3) 生产订单（工序无时间时，用 confirmed_start/end 的持续时长作为负荷）
        prod_orders = self.db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PRODUCTION.value,
            models.ProductionOrder.confirmed_start != None,
            models.ProductionOrder.confirmed_end != None
        ).all()
        for order in prod_orders:
            ops = self.db.query(models.Operation).filter(
                models.Operation.order_id == order.id,
                models.Operation.scheduled_start == None
            ).all()
            if not ops:
                continue
            order_dur = (order.confirmed_end - order.confirmed_start).total_seconds()
            op_dur_each = order_dur / len(ops) if ops else 0
            for idx, op in enumerate(ops):
                op_s = order.confirmed_start + timedelta(seconds=op_dur_each * idx)
                op_e = op_s + timedelta(seconds=op_dur_each)
                _add_hours_to_days(op_s, op_e)

        # 4) 待排程工序（已分配资源但无排程时间），用交货期代替
        pending_with_resource = self.db.query(models.Operation).filter(
            models.Operation.resource_id != None,
            models.Operation.scheduled_start == None,
            ~models.Operation.id.in_(list(cached_ids)) if cached_ids else True
        ).all()
        for op in pending_with_resource:
            order = op.order
            if order and order.due_date and op.run_time:
                op_s = order.due_date.replace(hour=8, minute=0, second=0, microsecond=0)
                op_e = op_s + timedelta(hours=op.run_time)
                _add_hours_to_days(op_s, op_e)

        # 5) 待排程工序（未分配资源），用交货期代替
        pending_without_resource = self.db.query(models.Operation).filter(
            models.Operation.resource_id == None,
            models.Operation.scheduled_start == None
        ).all()
        for op in pending_without_resource:
            order = op.order
            if order and order.due_date and op.run_time:
                op_s = order.due_date.replace(hour=8, minute=0, second=0, microsecond=0)
                op_e = op_s + timedelta(hours=op.run_time)
                _add_hours_to_days(op_s, op_e)

        # 组装最终结果
        final = {}
        for date_key, used in result.items():
            final[date_key] = {
                'total_capacity': total_capacity_per_day,
                'used_capacity': round(used, 1),
                'utilization': round(used / total_capacity_per_day * 100, 1) if total_capacity_per_day > 0 else 0
            }

        return final

    def get_utilization_data(
        self,
        resource_ids: List[int] = None,
        start_date: datetime = None,
        end_date: datetime = None,
        zoom_level: int = 1
    ) -> Dict:
        """
        获取资源利用率时间序列数据
        
        Args:
            resource_ids: 资源ID列表，None表示所有资源
            start_date: 开始日期
            end_date: 结束日期
            zoom_level: 缩放级别 (0=小时, 1=4小时, 2=天, 3=周, 4=月)
        
        Returns:
            资源利用率数据
        """
        # 默认时间范围
        if not start_date:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if not end_date:
            end_date = start_date + timedelta(days=30)
        
        # 根据缩放级别确定时间槽大小（小时）
        slot_hours_map = {
            0: 1,    # 小时视图 - 1小时
            1: 4,    # 4小时视图 - 4小时
            2: 8,    # 天视图 - 8小时（一个工作日）
            3: 24,   # 周视图 - 24小时（一天）
            4: 168   # 月视图 - 168小时（一周）
        }
        slot_hours = slot_hours_map.get(zoom_level, 4)
        
        # 获取资源
        query = self.db.query(models.Resource)
        if resource_ids:
            query = query.filter(models.Resource.id.in_(resource_ids))
        resources = query.all()
        
        # 建立工作中心到资源的映射（用于待排程工序）
        work_center_to_resource = {}
        for resource in resources:
            if resource.work_center_id and resource.work_center_id not in work_center_to_resource:
                work_center_to_resource[resource.work_center_id] = resource
        
        # 获取缓存的排程数据（如果有）
        cached_ops = {}
        cached_ops_by_resource = {}
        if schedule_cache.has_unsaved_changes:
            for cached_op in schedule_cache.get_all_operations():
                cached_ops[cached_op.operation_id] = cached_op
                res_id = cached_op.resource_id
                if res_id not in cached_ops_by_resource:
                    cached_ops_by_resource[res_id] = []
                cached_ops_by_resource[res_id].append(cached_op)
        
        result = []
        
        for resource in resources:
            # 收集该资源的所有工序（包括已排程和待排程）
            all_operations = []
            
            if cached_ops:
                # 有缓存数据时：优先使用缓存中的排程数据
                # 1. 从缓存中获取分配到该资源的工序
                cached_ops_for_resource = cached_ops_by_resource.get(resource.id, [])
                for cached_op in cached_ops_for_resource:
                    if cached_op.scheduled_start and cached_op.scheduled_end:
                        all_operations.append({
                            'start': cached_op.scheduled_start,
                            'end': cached_op.scheduled_end,
                            'run_time': (cached_op.scheduled_end - cached_op.scheduled_start).total_seconds() / 3600
                        })
                
                # 2. 添加数据库中该资源的已排程工序（不在缓存中的）
                db_scheduled = self.db.query(models.Operation).filter(
                    models.Operation.resource_id == resource.id,
                    models.Operation.scheduled_start != None,
                    models.Operation.scheduled_end != None,
                    ~models.Operation.id.in_(list(cached_ops.keys())) if cached_ops else True
                ).all()
                
                for op in db_scheduled:
                    all_operations.append({
                        'start': op.scheduled_start,
                        'end': op.scheduled_end,
                        'run_time': op.run_time
                    })
            else:
                # 没有缓存数据时：使用数据库中的排程数据
                # 1. 已排程的工序（有 scheduled_start/scheduled_end）
                scheduled_operations = self.db.query(models.Operation).filter(
                    models.Operation.resource_id == resource.id,
                    models.Operation.scheduled_start != None,
                    models.Operation.scheduled_end != None
                ).all()
                
                for op in scheduled_operations:
                    all_operations.append({
                        'start': op.scheduled_start,
                        'end': op.scheduled_end,
                        'run_time': op.run_time
                    })
                
                # 2. 待排程的工序（已分配资源但没有排程时间）
                pending_with_resource = self.db.query(models.Operation).filter(
                    models.Operation.resource_id == resource.id,
                    models.Operation.scheduled_start == None  # 没有排程时间
                ).all()
                
                for op in pending_with_resource:
                    # 使用订单交货日期作为计划时间
                    order = op.order
                    if order and order.due_date:
                        display_start = order.due_date.replace(hour=8, minute=0, second=0, microsecond=0)
                        display_end = display_start + timedelta(hours=op.run_time)
                        all_operations.append({
                            'start': display_start,
                            'end': display_end,
                            'run_time': op.run_time
                        })
                
                # 3. 待排程的工序（没有分配资源，通过工作中心匹配）
                pending_without_resource = self.db.query(models.Operation).join(
                    models.RoutingOperation,
                    models.Operation.routing_operation_id == models.RoutingOperation.id
                ).filter(
                    models.Operation.resource_id == None,  # 未分配资源
                    models.RoutingOperation.work_center_id == resource.work_center_id  # 通过工作中心匹配
                ).all()
                
                for op in pending_without_resource:
                    # 使用订单交货日期作为计划时间
                    order = op.order
                    if order and order.due_date:
                        display_start = order.due_date.replace(hour=8, minute=0, second=0, microsecond=0)
                        display_end = display_start + timedelta(hours=op.run_time)
                        all_operations.append({
                            'start': display_start,
                            'end': display_end,
                            'run_time': op.run_time
                        })
            
            # 按时间槽计算利用率
            time_slots = []
            current = start_date
            while current < end_date:
                slot_end = current + timedelta(hours=slot_hours)
                
                # 计算该时间段内的工时（重叠就累加）
                total_hours = 0
                for op_data in all_operations:
                    op_start = op_data['start']
                    op_end = op_data['end']
                    
                    # 检查是否与时间槽重叠
                    if op_start < slot_end and op_end > current:
                        # 计算重叠部分
                        overlap_start = max(op_start, current)
                        overlap_end = min(op_end, slot_end)
                        if overlap_end > overlap_start:
                            total_hours += (overlap_end - overlap_start).total_seconds() / 3600
                
                # 利用率 = 总工时 / 时间槽大小
                utilization = total_hours / slot_hours
                
                time_slots.append({
                    "start": current.strftime("%Y-%m-%d %H:%M"),
                    "end": slot_end.strftime("%Y-%m-%d %H:%M"),
                    "utilization": round(utilization, 2)  # 不限制上限，真实反映超载情况
                })
                
                current = slot_end
            
            result.append({
                "resource_id": resource.id,
                "resource_name": resource.name,
                "description": resource.description or "",
                "capacity": resource.capacity_per_day,
                "time_slots": time_slots
            })
        
        return {"data": result}

    def reschedule_with_links(
        self,
        operation_id: int,
        new_start: datetime,
        new_resource_id: int = None,
        strategy: str = "EDD",
        move_linked_operations: bool = True
    ) -> Dict:
        """
        联动调整工序（支持策略）
        
        Args:
            operation_id: 工序ID
            new_start: 新的开始时间
            new_resource_id: 新的资源ID（可选）
            strategy: 策略（EDD, SPT, FIFO, PRIORITY）
            move_linked_operations: 是否联动移动关联工序
        
        Returns:
            包含成功状态和冲突信息的字典
        """
        operation = self.db.query(models.Operation).filter(
            models.Operation.id == operation_id
        ).first()
        
        if not operation:
            return {
                'success': False,
                'message': '工序不存在',
                'conflicts': []
            }
        
        # 检查订单类型 - 生产订单不允许调整
        order = operation.order
        if order and order.order_type == models.OrderType.PRODUCTION.value:
            return {
                'success': False,
                'message': '生产订单已确认，不允许调整排程',
                'conflicts': []
            }
        
        # 检查约束
        violations = self.validator.check_operation_move(
            operation_id,
            new_start,
            new_resource_id
        )
        
        # 如果有错误级别的违反，不允许移动
        errors = [v for v in violations if v.severity == 'error']
        if errors:
            return {
                'success': False,
                'message': '移动违反约束',
                'conflicts': [v.to_dict() for v in violations]
            }
        
        # 更新工序
        duration = operation.run_time
        old_start = operation.scheduled_start
        new_end = new_start + timedelta(hours=duration)
        
        # 计算偏移量（秒）
        offset_seconds = (new_start - old_start).total_seconds() if old_start else 0
        
        operation.scheduled_start = new_start
        operation.scheduled_end = new_end
        
        if new_resource_id:
            operation.resource_id = new_resource_id
        
        # 联动更新：根据策略同步移动关联工序
        if move_linked_operations and offset_seconds != 0:
            # 获取同一订单的所有后续工序
            successors = self.db.query(models.Operation).filter(
                models.Operation.order_id == operation.order_id,
                models.Operation.sequence > operation.sequence
            ).all()
            
            for succ in successors:
                if succ.scheduled_start:
                    succ.scheduled_start = succ.scheduled_start + timedelta(seconds=offset_seconds)
                    succ.scheduled_end = succ.scheduled_end + timedelta(seconds=offset_seconds)
            
            # 根据策略可能需要额外处理
            if strategy == "EDD":
                # EDD策略：检查是否会导致超期
                last_op = self.db.query(models.Operation).filter(
                    models.Operation.order_id == operation.order_id
                ).order_by(models.Operation.sequence.desc()).first()
                
                if last_op and last_op.scheduled_end and order.due_date:
                    if last_op.scheduled_end > order.due_date:
                        violations.append(type('Violation', (), {
                            'severity': 'warning',
                            'to_dict': lambda: {
                                'type': 'due_date',
                                'message': f'移动后订单将超过交货期',
                                'severity': 'warning'
                            }
                        })())
        
        self.db.commit()
        
        return {
            'success': True,
            'message': '工序已重新排程（联动更新）',
            'conflicts': [v.to_dict() for v in violations]
        }

    def _get_product_view_data(
        self,
        start_date: datetime,
        end_date: datetime,
        cached_ops: Dict[int, 'CachedOperation'] = None
    ) -> tuple:
        """获取产品视图的甘特图数据"""
        cached_ops = cached_ops or {}
        tasks = []
        links = []
        
        # 获取所有资源，建立工作中心到资源的映射（与资源视图保持一致）
        resources = self.db.query(models.Resource).all()
        work_center_to_resource = {}  # work_center_id -> resource (1:1关系)
        for resource in resources:
            work_center_to_resource[resource.work_center_id] = resource
        
        # 获取所有产品
        products = self.db.query(models.Product).all()
        
        for product in products:
            # 获取该产品的所有订单（按工序时间筛选：已排程用排程时间，待排程用交货期）
            from sqlalchemy import or_
            orders = self.db.query(models.ProductionOrder).filter(
                models.ProductionOrder.product_id == product.id,
                or_(
                    # 已排程订单：有工序排程时间在显示区间内
                    models.ProductionOrder.id.in_(
                        self.db.query(models.Operation.order_id).filter(
                            models.Operation.scheduled_start != None,
                            models.Operation.scheduled_start <= end_date,
                            models.Operation.scheduled_end >= start_date
                        ).distinct()
                    ),
                    # 待排程订单：交货期在显示区间内
                    (models.ProductionOrder.due_date >= start_date) &
                    (models.ProductionOrder.due_date <= end_date)
                )
            ).all()
            
            if not orders:
                continue
            
            # 收集该产品下所有订单的工序（已排程+待排程，按时间筛选）
            all_operations_with_time = []  # 用于计算产品时间范围
            order_operations_map = {}  # 订单ID -> 工序列表
            
            for order in orders:
                # 获取该订单在显示区间内的工序（已排程+待排程）
                buffer_start = start_date - timedelta(days=7)
                operations = self.db.query(models.Operation).filter(
                    models.Operation.order_id == order.id,
                    or_(
                        # 已排程工序：排程时间与显示区间重叠，或结束于区间前 7 天内
                        (models.Operation.scheduled_start != None) & 
                        (models.Operation.scheduled_start <= end_date) &
                        (models.Operation.scheduled_end >= buffer_start),
                        # 待排程工序：订单交货期在显示区间内
                        (models.Operation.scheduled_start == None) & 
                        (order.due_date >= start_date) &
                        (order.due_date <= end_date)
                    )
                ).order_by(models.Operation.sequence).all()
                
                if operations:
                    order_operations_map[order.id] = {
                        'order': order,
                        'operations': operations
                    }
                    
                    # 收集有时间信息的工序（用于计算产品时间范围）
                    for op in operations:
                        if op.scheduled_start and op.scheduled_end:
                            all_operations_with_time.append(op)
                        elif order.due_date:
                            # 待排程工序使用交货日期
                            all_operations_with_time.append({
                                'scheduled_start': order.due_date.replace(hour=8, minute=0, second=0),
                                'scheduled_end': order.due_date.replace(hour=8, minute=0, second=0) + timedelta(hours=op.run_time),
                                'is_pending': True
                            })
            
            if not order_operations_map:
                continue
            
            # 计算产品的时间范围
            if all_operations_with_time:
                starts = []
                ends = []
                for item in all_operations_with_time:
                    if isinstance(item, dict):
                        starts.append(item['scheduled_start'])
                        ends.append(item['scheduled_end'])
                    else:
                        starts.append(item.scheduled_start)
                        ends.append(item.scheduled_end)
                
                product_start = min(starts)
                product_end = max(ends)
            else:
                # 如果没有任何时间信息，使用默认范围
                product_start = start_date
                product_end = end_date
            
            # 添加产品作为父任务
            tasks.append(schemas.GanttTask(
                id=f"product_{product.id}",
                text=f"{product.name} ({len(order_operations_map)} 订单)",
                start_date=product_start.strftime("%Y-%m-%d %H:%M"),
                end_date=product_end.strftime("%Y-%m-%d %H:%M"),
                type="project",
                product_id=product.id
            ))
            
            # 添加该产品下的订单工序
            for order_id, data in order_operations_map.items():
                order = data['order']
                operations = data['operations']
                is_production = order.order_type == models.OrderType.PRODUCTION.value
                
                for op in operations:
                    is_scheduled = op.scheduled_start is not None and op.scheduled_end is not None
                    
                    # 获取资源信息
                    if op.resource:
                        # 已分配资源
                        resource_name = op.resource.name
                        resource_id = op.resource_id
                    else:
                        # 待排程工序：通过工艺路线获取工作中心，然后获取该工作中心对应的资源（1:1关系）
                        routing_op = self.db.query(models.RoutingOperation).filter(
                            models.RoutingOperation.id == op.routing_operation_id
                        ).first()
                        if routing_op and routing_op.work_center_id in work_center_to_resource:
                            # 获取该工作中心对应的资源（与资源视图保持一致的映射）
                            matched_resource = work_center_to_resource[routing_op.work_center_id]
                            resource_name = matched_resource.name
                            resource_id = matched_resource.id
                        else:
                            resource_name = "未分配"
                            resource_id = None
                    
                    if is_scheduled:
                        # 已排程工序
                        tasks.append(schemas.GanttTask(
                            id=f"op_{op.id}",
                            text=f"{order.order_number} - {op.sequence} {op.name} ({resource_name})",
                            start_date=op.scheduled_start.strftime("%Y-%m-%d %H:%M"),
                            end_date=op.scheduled_end.strftime("%Y-%m-%d %H:%M"),
                            parent=f"product_{product.id}",
                            progress=1.0 if op.status == 'completed' else 0,
                            operation_id=op.id,
                            order_id=op.order_id,
                            resource_id=resource_id,
                            product_id=product.id,
                            status=op.status,
                            task_type='operation',
                            order_type=order.order_type,
                            order_status=order.status,
                            work_hours=op.run_time
                        ))
                    else:
                        # 待排程工序：使用交货日期作为显示时间
                        if order.due_date:
                            display_start = order.due_date.replace(hour=8, minute=0, second=0)
                            display_end = display_start + timedelta(hours=op.run_time)
                            
                            tasks.append(schemas.GanttTask(
                                id=f"op_{op.id}",
                                text=f"{order.order_number} - {op.sequence} {op.name} ({resource_name})",
                                start_date=display_start.strftime("%Y-%m-%d %H:%M"),
                                end_date=display_end.strftime("%Y-%m-%d %H:%M"),
                                parent=f"product_{product.id}",
                                progress=0,
                                operation_id=op.id,
                                order_id=op.order_id,
                                resource_id=resource_id,
                                product_id=product.id,
                                status=op.status,
                                task_type='operation',
                                order_type=order.order_type,
                                order_status=order.status,
                                work_hours=op.run_time
                            ))
        
        return tasks, links
