# -*- coding: utf-8 -*-
"""直接调用引擎运行启发式并打印排序相关日志（不启动 HTTP 服务）"""
import sys
sys.path.insert(0, '.')

import logging
# 确保调度相关 logger 输出到控制台
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s [%(name)s] %(message)s',
    stream=sys.stdout
)
# 避免 uvicorn 等把级别改掉
logging.getLogger('app.scheduler.engine').setLevel(logging.INFO)
logging.getLogger('app.scheduler.algorithms').setLevel(logging.INFO)

from datetime import datetime
from app.database import SessionLocal
from app import models, schemas
from app.scheduler.engine import SchedulingEngine

def main():
    db = SessionLocal()
    # 装配工位-1 resource_id=11
    resource_ids = [11]
    display_start = '2026-03-02'
    display_end = '2026-03-08'

    request = schemas.AutoPlanRequest(
        plan_type='heuristic',
        heuristic_id='stable_forward',
        resource_ids=resource_ids,
        optimizer_config={
            'finite_capacity': True,
            'resolve_backlog': True,
            'resolve_overload': True,
            'preserve_scheduled': True,
            'sorting_rule': '订单优先级',
            'planning_mode': '查找槽位',
            'planning_direction': '向前',
            'expected_date': '指定日期',
            'expected_date_value': '2026-03-02',
            'order_internal_relation': '始终考虑',
            'sub_planning_mode': '根据调度模式调度相关操作',
            'error_handling': '立即终止',
            'planning_horizon': 90,
            'schedule_selected_resources_only': True,
            'display_start_date': display_start,
            'display_end_date': display_end,
            'preview_mode': True,
        }
    )

    engine = SchedulingEngine(db)
    print('--- 开始运行启发式（下方应出现 [run_heuristic] 和 [schedule_orders] 日志）---')
    result = engine.auto_plan(request)
    print('--- 启发式结束 ---')
    print('success:', result.get('success'), 'scheduled_orders:', result.get('scheduled_orders'))
    db.close()

if __name__ == '__main__':
    main()
