"""
聊天机器人 API：接收前端消息，通过 LLM 服务处理并执行动作。
"""
from fastapi import APIRouter, Depends

from ..database import get_db
from .. import schemas
from ..services.llm_service import chat_with_llm
from ..services.agent_proxy import execute_action
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/chat", response_model=schemas.ChatResponse)
def post_chat(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    """
    处理聊天消息，通过 LLM 进行智能对话并执行排程动作。

    支持的功能：
    - 智能对话（OpenAI GPT）
    - 查找延误订单
    - 运行启发式排程
    - 取消/保存计划
    - 调整策略参数
    """
    # 定义动作执行器
    def action_executor(action_type: str, params: dict, context: dict):
        return execute_action(action_type, params, db, context)
    
    # 通过 LLM 服务处理消息
    return chat_with_llm(
        message=request.message,
        conversation_id=request.conversation_id,
        context=request.context,
        action_executor=action_executor
    )


@router.get("/history")
def get_history():
    """获取聊天历史（可选实现，当前返回空列表）。"""
    return {"messages": []}
