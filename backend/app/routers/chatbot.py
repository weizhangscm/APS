"""
聊天机器人 API：接收前端消息，转发给 Agent 代理并执行返回的动作。
"""
from fastapi import APIRouter, Depends

from ..database import get_db
from .. import schemas
from ..services.agent_proxy import chat
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/chat", response_model=schemas.ChatResponse)
def post_chat(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    """
    处理聊天消息，转发给 Agent 并执行返回的动作。

    Agent 可返回的动作类型：
    - adjust_strategy: 调整策略参数
    - run_heuristic: 运行启发式排程
    - cancel_plan: 取消计划
    - save_plan: 保存计划
    - find_delayed_orders: 查找延误订单
    """
    return chat(message=request.message, context=request.context, db=db)


@router.get("/history")
def get_history():
    """获取聊天历史（可选实现，当前返回空列表）。"""
    return {"messages": []}
