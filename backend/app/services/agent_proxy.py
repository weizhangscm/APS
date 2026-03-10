"""
Agent 代理服务：执行排程引擎动作。

支持的动作类型：
- find_delayed_orders: 查找延误订单 engine.get_delayed_orders()
- run_heuristic: 运行启发式排程 engine.auto_plan()
- cancel_plan: 取消计划 engine.cancel_plan()
- save_plan: 保存计划 engine.save_plan()

本模块为纯动作执行器，由 LLM 服务通过 Function Calling 调用。
"""
import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from .. import schemas, models
from ..scheduler.engine import SchedulingEngine

logger = logging.getLogger(__name__)


def _parse_month_day(s: str) -> Optional[str]:
    """将 3.9、3.15 解析为当前年的 YYYY-MM-DD。"""
    if not s or not s.strip():
        return None
    s = s.strip()
    m = re.match(r"^(\d{1,2})\.(\d{1,2})$", s)
    if not m:
        return None
    month, day = int(m.group(1)), int(m.group(2))
    if month < 1 or month > 12 or day < 1 or day > 31:
        return None
    year = datetime.now().year
    return f"{year}-{month:02d}-{day:02d}"


def _resolve_resource_names_to_ids(resource_names: List[str], db) -> List[int]:
    """按名称或编码解析资源 ID 列表。"""
    if not resource_names:
        return []
    from sqlalchemy import or_

    def _alias_to_code(raw: str) -> Optional[str]:
        """
        将英文/别名资源名称映射到资源 code（如 A001）。
        约定：A=Assembly, M=CNC/Machine, C=Coating/Paint, T=Test, P=Packing/Packaging。
        """
        s = (raw or "").strip()
        if not s:
            return None
        s_norm = re.sub(r"\s+", " ", s).strip().lower()

        # e.g. "A001"
        m = re.match(r"^([a-z])\s*0*(\d{1,3})$", s_norm)
        if m:
            return f"{m.group(1).upper()}{int(m.group(2)):03d}"

        # e.g. "CNC-01", "CNC 1"
        m = re.search(r"\bcnc\b\s*[-_ ]?\s*0*(\d{1,3})\b", s_norm)
        if m:
            return f"M{int(m.group(1)):03d}"

        # e.g. "Assembly Station-1", "Assembly-1", "Assemble station 2"
        m = re.search(r"\bassem(?:bly|ble)?\b.*?\b(?:station\b)?\s*[-_ ]?\s*0*(\d{1,3})\b", s_norm)
        if m:
            return f"A{int(m.group(1)):03d}"

        # e.g. "Paint-1", "Coating booth 2"
        m = re.search(r"\b(?:paint|coating)\b.*?\s*[-_ ]?\s*0*(\d{1,3})\b", s_norm)
        if m:
            return f"C{int(m.group(1)):03d}"

        # e.g. "Test-1", "Inspection 3"
        m = re.search(r"\b(?:test|inspection)\b.*?\s*[-_ ]?\s*0*(\d{1,3})\b", s_norm)
        if m:
            return f"T{int(m.group(1)):03d}"

        # e.g. "Pack-1", "Packaging 2"
        m = re.search(r"\b(?:pack|packing|packaging)\b.*?\s*[-_ ]?\s*0*(\d{1,3})\b", s_norm)
        if m:
            return f"P{int(m.group(1)):03d}"

        return None

    ids = []
    for name in resource_names:
        raw = (name or "").strip()
        if not raw:
            continue
        mapped_code = _alias_to_code(raw)
        # 先按：code 精确、name 精确；再按映射后的 code；最后按不区分大小写的 code
        q = db.query(models.Resource).filter(
            or_(models.Resource.code == raw, models.Resource.name == raw)
        )
        r = q.first()
        if not r and mapped_code:
            r = db.query(models.Resource).filter(models.Resource.code == mapped_code).first()
        if not r:
            r = db.query(models.Resource).filter(models.Resource.code.ilike(raw)).first()
        if r:
            ids.append(r.id)
    return list(dict.fromkeys(ids))  # 去重保持顺序


def execute_action(
    action_type: str,
    params: Dict[str, Any],
    db,
    context: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    执行动作并返回结果。
    
    Args:
        action_type: 动作类型 (find_delayed_orders, run_heuristic, cancel_plan, save_plan)
        params: 动作参数
        db: 数据库会话
        context: 上下文信息（locale等）
    
    Returns:
        动作执行结果字典
    """
    engine = SchedulingEngine(db)
    context = context or {}
    
    try:
        if action_type == "find_delayed_orders":
            orders = engine.get_delayed_orders()
            return {
                "success": True,
                "count": len(orders),
                "orders": orders,
                "message": f"共 {len(orders)} 个延误订单" if orders else "当前无延误订单",
            }
        
        if action_type == "run_heuristic":
            # 解析资源名称
            resource_names = params.get("resource_names") or []
            resource_ids = _resolve_resource_names_to_ids(resource_names, db) if resource_names else None
            
            # 获取参数
            display_start = params.get("display_start_date")
            display_end = params.get("display_end_date")
            expected_date_value = params.get("expected_date_value")
            order_internal_relation = params.get("order_internal_relation") or "始终考虑"
            
            # 构建启发式配置
            optimizer_config = {
                "finite_capacity": True,
                "resolve_backlog": True,
                "resolve_overload": True,
                "preserve_scheduled": True,
                "sorting_rule": "订单优先级",
                "planning_mode": "查找槽位",
                "planning_direction": "向前",
                "expected_date": "指定日期" if expected_date_value else "当前日期",
                "order_internal_relation": order_internal_relation,
                "sub_planning_mode": "根据调度模式调度相关操作",
                "error_handling": "立即终止",
                "planning_horizon": 90,
                "schedule_selected_resources_only": True,
            }
            
            if expected_date_value:
                optimizer_config["expected_date_value"] = expected_date_value
            if display_start:
                optimizer_config["display_start_date"] = display_start
            if display_end:
                optimizer_config["display_end_date"] = display_end
            
            request = schemas.AutoPlanRequest(
                plan_type="heuristic",
                heuristic_id="stable_forward",
                optimizer_config=optimizer_config,
                resource_ids=resource_ids,
            )
            
            result = engine.auto_plan(request)
            result_dict = dict(result) if isinstance(result, dict) else {"result": result}
            result_dict["success"] = True
            return result_dict
        
        if action_type == "cancel_plan":
            resource_ids = params.get("resource_ids")
            product_ids = params.get("product_ids")
            result = engine.cancel_plan(resource_ids=resource_ids, product_ids=product_ids)
            if isinstance(result, dict):
                result["success"] = True
                return result
            return {"success": True, "message": "取消计划已执行", "result": result}
        
        if action_type == "save_plan":
            resource_ids = params.get("resource_ids")
            product_ids = params.get("product_ids")
            result = engine.save_plan(resource_ids=resource_ids, product_ids=product_ids)
            if isinstance(result, dict):
                result["success"] = True
                return result
            return {"success": True, "message": "计划已保存", "result": result}
        
        if action_type == "adjust_strategy":
            return {
                "success": True,
                "message": "策略调整请在前端排程页面的策略配置中修改",
                "action": "adjust_strategy",
            }
        
        return {
            "success": False,
            "error": "unknown_action",
            "message": f"未知动作类型: {action_type}"
        }
        
    except Exception as e:
        logger.exception(f"execute_action {action_type} failed")
        return {
            "success": False,
            "error": str(e),
            "message": f"执行动作失败: {str(e)}"
        }
