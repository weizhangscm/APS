"""
Agent 代理服务：处理用户消息，解析意图并调用排程引擎相应方法。

支持的动作类型：
- adjust_strategy: 调整策略参数（返回策略配置供前端应用）
- run_heuristic: 运行启发式排程 engine.auto_plan()
- cancel_plan: 取消计划 engine.cancel_plan()
- save_plan: 保存计划 engine.save_plan()
- find_delayed_orders: 查找延误订单 engine.get_delayed_orders()

未配置外部 Agent API 时，使用内置意图识别（关键词）并直接执行动作。
"""
import os
import re
import logging
from typing import Optional, Dict, Any

from .. import schemas
from ..scheduler.engine import SchedulingEngine

logger = logging.getLogger(__name__)

# 可选：外部 Agent API URL，若设置则优先调用
AGENT_API_URL = os.environ.get("APS_AGENT_API_URL", "").strip()


def _detect_intent(message: str) -> tuple:
    """
    根据用户消息检测意图与参数。
    返回 (action_type, params_dict) 或 (None, {})。
    """
    msg = (message or "").strip().lower()
    # 中文关键词
    if re.search(r"延误|延迟|逾期|交期.*超", msg) or re.search(r"delayed|delay|overdue", msg):
        return "find_delayed_orders", {}
    if re.search(r"运行.*启发|启发式|自动排程|执行.*排程", msg) or re.search(r"run.*heuristic|auto.?plan", msg):
        return "run_heuristic", {}
    if re.search(r"取消.*计划|取消计划", msg) or re.search(r"cancel.?plan", msg):
        return "cancel_plan", {}
    if re.search(r"保存.*计划|保存计划", msg) or re.search(r"save.?plan", msg):
        return "save_plan", {}
    if re.search(r"调整.*策略|策略.*调整", msg) or re.search(r"adjust.?strategy", msg):
        return "adjust_strategy", {}
    return None, {}


def _execute_action(
    action_type: str,
    params: Dict[str, Any],
    engine: SchedulingEngine,
) -> Dict[str, Any]:
    """执行动作并返回 action_result。"""
    try:
        if action_type == "find_delayed_orders":
            orders = engine.get_delayed_orders()
            return {
                "count": len(orders),
                "orders": orders,
                "message": f"共 {len(orders)} 个延误订单" if orders else "当前无延误订单",
            }
        if action_type == "run_heuristic":
            request = schemas.AutoPlanRequest(
                plan_type="heuristic",
                heuristic_id="stable_forward",
                optimizer_config={
                    "finite_capacity": True,
                    "sorting_rule": "订单优先级",
                    "planning_direction": "向前",
                    "order_internal_relation": "始终考虑",
                },
            )
            result = engine.auto_plan(request)
            return dict(result) if isinstance(result, dict) else {"result": result}
        if action_type == "cancel_plan":
            resource_ids = params.get("resource_ids")
            product_ids = params.get("product_ids")
            return engine.cancel_plan(resource_ids=resource_ids, product_ids=product_ids)
        if action_type == "save_plan":
            resource_ids = params.get("resource_ids")
            product_ids = params.get("product_ids")
            return engine.save_plan(resource_ids=resource_ids, product_ids=product_ids)
        if action_type == "adjust_strategy":
            return {
                "message": "策略调整请在前端排程页面的策略配置中修改",
                "action": "adjust_strategy",
            }
    except Exception as e:
        logger.exception("execute_action %s failed", action_type)
        return {"success": False, "error": str(e), "message": str(e)}
    return {"message": "未知动作", "action_type": action_type}


def chat(message: str, context: Optional[dict], db) -> schemas.ChatResponse:
    """
    处理聊天消息：检测意图、执行动作并返回回复。

    - 若配置了 AGENT_API_URL，可在此处调用外部 Agent API 并解析返回的动作。
    - 当前实现使用内置意图识别并调用 SchedulingEngine。
    """
    engine = SchedulingEngine(db)
    action_type, params = _detect_intent(message)

    if action_type:
        action_result = _execute_action(action_type, params, engine)
        # 生成简短回复文案
        if action_type == "find_delayed_orders":
            count = action_result.get("count", 0)
            reply = f"已查询延误订单，共 {count} 个。" if count else "当前没有延误订单。"
        elif action_type == "run_heuristic":
            reply = action_result.get("message", "启发式排程已执行。")
        elif action_type == "cancel_plan":
            reply = action_result.get("message", "取消计划已执行。")
        elif action_type == "save_plan":
            reply = action_result.get("message", "计划已保存。")
        elif action_type == "adjust_strategy":
            reply = action_result.get("message", "请在前端策略配置中调整。")
        else:
            reply = action_result.get("message", "操作已执行。")
        if action_result.get("success") is False:
            reply = "操作失败：" + (action_result.get("message") or action_result.get("error", ""))
        return schemas.ChatResponse(
            reply=reply,
            action_result=action_result,
            action_type=action_type,
        )

    # 无匹配意图时的默认回复
    return schemas.ChatResponse(
        reply="您好，我可以帮您：查找延误订单、运行启发式排程、取消计划、保存计划等。请直接说出您的需求。",
        action_result=None,
        action_type=None,
    )
