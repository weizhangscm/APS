"""
LLM 服务模块：封装 OpenAI Chat Completion API 调用，实现 Function Calling
按《API交互约定》从 agent_config.yaml 动态生成 System Prompt 和 Tools。
"""
import logging
import time
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from openai import OpenAI
from ..config import config
from .. import schemas

logger = logging.getLogger(__name__)

# 会话存储：{conversation_id: {"messages": [...], "last_access": timestamp}}
_conversations: Dict[str, Dict[str, Any]] = {}

# 配置缓存
_agent_config: Optional[Dict[str, Any]] = None

# 默认 System Prompt（配置文件缺失时使用）
SYSTEM_PROMPT_FALLBACK = """你是 APS（高级计划排程系统）的 AI 助手。你可以帮助用户：
- 查询延误订单
- 运行启发式排程（需要参数：显示区间、资源、日期等）
- 取消或保存排程计划
- 回答关于排程系统的问题

请用简洁专业的语言与用户交流。当用户请求执行排程操作时，请使用可用的工具函数。"""


def _load_agent_config() -> Dict[str, Any]:
    """加载 agent_config.yaml"""
    global _agent_config
    if _agent_config is not None:
        return _agent_config
    config_path = Path(__file__).parent.parent / "agent_config.yaml"
    if not config_path.exists():
        logger.warning("agent_config.yaml not found, using fallback")
        return {"version": "1.0", "system_prompt": SYSTEM_PROMPT_FALLBACK, "actions": [], "special_values": {}}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            _agent_config = yaml.safe_load(f)
        return _agent_config
    except Exception as e:
        logger.exception("Failed to load agent_config.yaml: %s", e)
        return {"version": "1.0", "system_prompt": SYSTEM_PROMPT_FALLBACK, "actions": [], "special_values": {}}


def _generate_system_prompt() -> str:
    """从配置生成 System Prompt"""
    return _load_agent_config().get("system_prompt", SYSTEM_PROMPT_FALLBACK)


def _is_english_locale(context: Optional[dict]) -> bool:
    """根据前端 context.locale 判断是否为英文界面。"""
    if not context or not isinstance(context, dict):
        return False
    locale = (context.get("locale") or "").strip()
    return str(locale).lower().startswith("en")


def _get_language_instruction(context: Optional[dict]) -> str:
    """返回根据界面语言附加的回复语言要求（追加到 system prompt）。"""
    if _is_english_locale(context):
        return "\n\nYou must reply in English only. Do not use Chinese in your response."
    return "\n\n请仅使用中文回复，不要使用英文。"


def _generate_tools() -> List[Dict[str, Any]]:
    """从配置生成 TOOLS 列表"""
    actions = _load_agent_config().get("actions", [])
    tools = []
    for action in actions:
        tools.append({
            "type": "function",
            "function": {
                "name": action.get("name"),
                "description": action.get("description", ""),
                "parameters": action.get("parameters", {"type": "object", "properties": {}, "required": []}),
            },
        })
    return tools


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
        use_en = _is_english_locale(context)
        reply = "Configuration error: OPENAI_API_KEY is not set. Please contact the administrator." if use_en else "系统配置错误：未设置 OPENAI_API_KEY 环境变量。请联系管理员配置。"
        return schemas.ChatResponse(
            reply=reply,
            action_result=None,
            action_type=None,
            context_for_next=None
        )
    
    try:
        # 初始化 OpenAI 客户端
        client = OpenAI(**config.get_openai_client_kwargs())
        
        # 获取会话历史
        messages = _get_conversation(conversation_id)
        
        # 如果是新会话，添加 system prompt（从配置生成），并按界面语言附加回复语言要求
        if not messages:
            system_content = _generate_system_prompt() + _get_language_instruction(context)
            messages = [{"role": "system", "content": system_content}]
        
        # 添加用户消息
        messages.append({"role": "user", "content": message})
        
        # 调用 OpenAI API
        logger.info(f"Calling LLM API with model: {config.OPENAI_MODEL}")
        tools = _generate_tools()
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            timeout=120.0  # 设置单次请求超时时间为120秒
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
            logger.info("Calling LLM API again to generate final response")
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                timeout=120.0  # 设置单次请求超时时间为120秒
            )
            
            final_message = response.choices[0].message
            messages.append(final_message.model_dump(exclude_unset=True))
            reply = final_message.content or ("Done." if _is_english_locale(context) else "操作已完成。")
        else:
            # 没有 tool calls，直接使用 LLM 的回复
            reply = assistant_message.content or ("I didn't understand your request." if _is_english_locale(context) else "抱歉，我没有理解您的问题。")
        
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
        error_msg = str(e)
        use_en = _is_english_locale(context)
        # 提供更友好的错误提示（按界面语言）
        if "timeout" in error_msg.lower():
            user_msg = "Request timed out. Please try again or simplify your question." if use_en else "AI 响应超时，请稍后重试。如果问题持续，请尝试简化您的问题。"
        elif "api" in error_msg.lower() or "connection" in error_msg.lower():
            user_msg = "Unable to reach the AI service. Please check your network or try again later." if use_en else "无法连接到 AI 服务，请检查网络连接或稍后重试。"
        else:
            user_msg = f"An error occurred: {error_msg}" if use_en else f"处理消息时发生错误：{error_msg}"
        
        return schemas.ChatResponse(
            reply=user_msg,
            action_result=None,
            action_type=None,
            context_for_next=None
        )
