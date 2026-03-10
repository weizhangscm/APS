"""
LLM 服务模块：封装 OpenAI Chat Completion API 调用，实现 Function Calling
"""
import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from openai import OpenAI
from ..config import config
from .. import schemas

logger = logging.getLogger(__name__)

# 会话存储：{conversation_id: {"messages": [...], "last_access": timestamp}}
_conversations: Dict[str, Dict[str, Any]] = {}


# System Prompt
SYSTEM_PROMPT = """你是 APS（高级计划排程系统）的 AI 助手。你可以帮助用户：
- 查询延误订单
- 运行启发式排程（需要参数：显示区间、资源、日期等）
- 取消或保存排程计划
- 回答关于排程系统的问题

请用简洁专业的语言与用户交流。当用户请求执行排程操作时，请使用可用的工具函数。"""


# Tools 定义（Function Calling）
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_delayed_orders",
            "description": "查询当前延误/逾期的订单列表",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_heuristic",
            "description": "运行启发式排程。需要指定显示区间和资源。",
            "parameters": {
                "type": "object",
                "properties": {
                    "display_start_date": {
                        "type": "string",
                        "description": "显示区间开始日期，格式 YYYY-MM-DD"
                    },
                    "display_end_date": {
                        "type": "string",
                        "description": "显示区间结束日期，格式 YYYY-MM-DD"
                    },
                    "resource_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "资源名称列表，如 ['装配工位-1', 'CNC-01']"
                    },
                    "expected_date_value": {
                        "type": "string",
                        "description": "指定日期值，格式 YYYY-MM-DD，当 expected_date 为 '指定日期' 时使用"
                    },
                    "order_internal_relation": {
                        "type": "string",
                        "enum": ["始终考虑", "不考虑"],
                        "description": "订单内部关系，默认为 '始终考虑'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_plan",
            "description": "取消计划排程",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "要取消排程的资源ID列表"
                    },
                    "product_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "要取消排程的产品ID列表"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_plan",
            "description": "保存计划排程",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "要保存排程的资源ID列表"
                    },
                    "product_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "要保存排程的产品ID列表"
                    }
                },
                "required": []
            }
        }
    }
]


def _cleanup_expired_conversations():
    """清理过期的会话"""
    now = time.time()
    timeout_seconds = config.CONVERSATION_TIMEOUT_MINUTES * 60
    expired_ids = [
        conv_id for conv_id, data in _conversations.items()
        if now - data.get("last_access", 0) > timeout_seconds
    ]
    for conv_id in expired_ids:
        del _conversations[conv_id]
    if expired_ids:
        logger.info(f"Cleaned up {len(expired_ids)} expired conversations")


def _get_conversation(conversation_id: Optional[str]) -> List[Dict[str, Any]]:
    """获取会话历史"""
    if not conversation_id:
        return []
    _cleanup_expired_conversations()
    conv_data = _conversations.get(conversation_id)
    if not conv_data:
        return []
    conv_data["last_access"] = time.time()
    return conv_data.get("messages", [])


def _save_conversation(conversation_id: str, messages: List[Dict[str, Any]]):
    """保存会话历史"""
    # 限制消息数量
    if len(messages) > config.MAX_CONVERSATION_HISTORY:
        # 保留 system message + 最近的消息
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]
        messages = system_msgs + other_msgs[-(config.MAX_CONVERSATION_HISTORY - len(system_msgs)):]
    
    _conversations[conversation_id] = {
        "messages": messages,
        "last_access": time.time()
    }


def chat_with_llm(
    message: str,
    conversation_id: Optional[str],
    context: Optional[dict],
    action_executor,
) -> schemas.ChatResponse:
    """
    使用 LLM 处理聊天消息，支持 Function Calling
    
    Args:
        message: 用户消息
        conversation_id: 会话ID，用于多轮对话
        context: 上下文信息（locale等）
        action_executor: 动作执行器，用于执行 tool calls
    
    Returns:
        ChatResponse
    """
    # 验证配置
    if not config.validate_openai_config():
        logger.error("OpenAI API key not configured")
        return schemas.ChatResponse(
            reply="系统配置错误：未设置 OPENAI_API_KEY 环境变量。请联系管理员配置。",
            action_result=None,
            action_type=None,
            context_for_next=None
        )
    
    try:
        # 初始化 OpenAI 客户端
        client = OpenAI(**config.get_openai_client_kwargs())
        
        # 获取会话历史
        messages = _get_conversation(conversation_id)
        
        # 如果是新会话，添加 system prompt
        if not messages:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # 添加用户消息
        messages.append({"role": "user", "content": message})
        
        # 调用 OpenAI API
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        messages.append(assistant_message.model_dump(exclude_unset=True))
        
        # 处理 tool calls
        action_result = None
        action_type = None
        
        if assistant_message.tool_calls:
            # 执行所有 tool calls
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = tool_call.function.arguments
                
                logger.info(f"Executing tool: {function_name} with args: {function_args}")
                
                # 导入 json 以解析参数
                import json
                try:
                    args = json.loads(function_args)
                except json.JSONDecodeError:
                    args = {}
                
                # 执行动作
                result = action_executor(function_name, args, context)
                action_result = result
                action_type = function_name
                
                # 将 tool 执行结果添加到消息历史
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                }
                messages.append(tool_message)
            
            # 再次调用 LLM 以生成最终回复
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto"
            )
            
            final_message = response.choices[0].message
            messages.append(final_message.model_dump(exclude_unset=True))
            reply = final_message.content or "操作已完成。"
        else:
            # 没有 tool calls，直接使用 LLM 的回复
            reply = assistant_message.content or "抱歉，我没有理解您的问题。"
        
        # 保存会话历史
        if conversation_id:
            _save_conversation(conversation_id, messages)
        
        return schemas.ChatResponse(
            reply=reply,
            action_result=action_result,
            action_type=action_type,
            context_for_next=None
        )
        
    except Exception as e:
        logger.exception("LLM chat failed")
        return schemas.ChatResponse(
            reply=f"处理消息时发生错误：{str(e)}",
            action_result=None,
            action_type=None,
            context_for_next=None
        )
