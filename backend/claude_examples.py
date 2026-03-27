"""
Claude API 使用示例
演示如何在 Python 代码中使用 Claude API
"""
import os
from openai import OpenAI

# API 配置
API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.chataiapi.com/v1").strip()
MODEL = os.environ.get("OPENAI_MODEL", "claude-sonnet-4-6").strip()


def example_1_simple_chat():
    """示例 1: 简单对话"""
    print("\n" + "="*60)
    print("示例 1: 简单对话")
    print("="*60)
    
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "你好，请用一句话介绍你自己。"}
        ],
        max_tokens=100
    )
    
    print(f"用户: 你好，请用一句话介绍你自己。")
    print(f"Claude: {response.choices[0].message.content}")
    print(f"Tokens 使用: {response.usage.total_tokens}")


def example_2_system_prompt():
    """示例 2: 使用系统提示词"""
    print("\n" + "="*60)
    print("示例 2: 使用系统提示词")
    print("="*60)
    
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system", 
                "content": "你是一个 APS（高级计划排程）系统的专家助手，专门帮助用户解决生产排程问题。"
            },
            {
                "role": "user", 
                "content": "什么是瓶颈资源？"
            }
        ],
        max_tokens=200
    )
    
    print(f"系统角色: APS 系统专家助手")
    print(f"用户: 什么是瓶颈资源？")
    print(f"Claude: {response.choices[0].message.content}")


def example_3_multi_turn():
    """示例 3: 多轮对话"""
    print("\n" + "="*60)
    print("示例 3: 多轮对话")
    print("="*60)
    
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    # 保存对话历史
    messages = [
        {"role": "system", "content": "你是一个友好的助手。"},
        {"role": "user", "content": "我的名字是张三。"}
    ]
    
    # 第一轮
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=100
    )
    
    assistant_reply = response.choices[0].message.content
    print(f"用户: 我的名字是张三。")
    print(f"Claude: {assistant_reply}")
    
    # 添加助手回复到历史
    messages.append({"role": "assistant", "content": assistant_reply})
    
    # 第二轮
    messages.append({"role": "user", "content": "你还记得我叫什么名字吗？"})
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=100
    )
    
    print(f"用户: 你还记得我叫什么名字吗？")
    print(f"Claude: {response.choices[0].message.content}")


def example_4_function_calling():
    """示例 4: Function Calling（工具调用）"""
    print("\n" + "="*60)
    print("示例 4: Function Calling（工具调用）")
    print("="*60)
    
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    # 定义可用的工具
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "获取指定城市的天气信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称，例如：北京、上海"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "温度单位"
                        }
                    },
                    "required": ["city"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_product",
                "description": "搜索产品信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "产品名称"
                        }
                    },
                    "required": ["product_name"]
                }
            }
        }
    ]
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "北京今天天气怎么样？"}
        ],
        tools=tools,
        tool_choice="auto"  # 让模型自动决定是否调用工具
    )
    
    message = response.choices[0].message
    
    print(f"用户: 北京今天天气怎么样？")
    
    if message.tool_calls:
        # 模型决定调用工具
        for tool_call in message.tool_calls:
            print(f"\nClaude 决定调用工具:")
            print(f"  工具名称: {tool_call.function.name}")
            print(f"  工具参数: {tool_call.function.arguments}")
            
            # 在实际应用中，这里会执行真实的函数调用
            # 例如: result = get_weather(**json.loads(tool_call.function.arguments))
            print(f"\n模拟函数执行结果: {{\"temperature\": 15, \"condition\": \"晴天\"}}")
    else:
        # 模型直接回复
        print(f"Claude: {message.content}")


def example_5_aps_scenario():
    """示例 5: APS 系统场景"""
    print("\n" + "="*60)
    print("示例 5: APS 系统实际场景")
    print("="*60)
    
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    # 定义 APS 系统的工具
    tools = [
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
                "description": "运行启发式排程算法",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resource_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "要排程的资源列表，例如 ['CNC-01', '装配工位-1']"
                        }
                    }
                }
            }
        }
    ]
    
    # 系统提示词
    system_prompt = """你是 APS（高级计划排程系统）的 AI 助手。你可以帮助用户：
- 查询延误订单
- 运行排程算法
- 回答排程相关问题

请用简洁专业的语言与用户交流。"""
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "帮我查一下有哪些订单延误了"}
        ],
        tools=tools,
        tool_choice="auto"
    )
    
    message = response.choices[0].message
    
    print(f"系统角色: APS AI 助手")
    print(f"用户: 帮我查一下有哪些订单延误了")
    
    if message.tool_calls:
        print(f"\nClaude 识别意图并调用工具:")
        for tool_call in message.tool_calls:
            print(f"  → 调用函数: {tool_call.function.name}")
            print(f"  → 参数: {tool_call.function.arguments}")
    else:
        print(f"\nClaude: {message.content}")


def example_6_streaming():
    """示例 6: 流式输出"""
    print("\n" + "="*60)
    print("示例 6: 流式输出（实时显示）")
    print("="*60)
    
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    print("用户: 请详细解释什么是 APS 系统")
    print("Claude: ", end="", flush=True)
    
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "请用 3 句话解释什么是 APS 系统"}
        ],
        max_tokens=200,
        stream=True  # 启用流式输出
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    
    print()  # 换行


def main():
    """运行所有示例"""
    if not API_KEY:
        print("[ERROR] OPENAI_API_KEY 未设置")
        return

    print("="*60)
    print("Claude API 使用示例集合")
    print("="*60)
    print(f"API: {BASE_URL}")
    print(f"Model: {MODEL}")
    print("="*60)
    
    examples = [
        ("简单对话", example_1_simple_chat),
        ("系统提示词", example_2_system_prompt),
        ("多轮对话", example_3_multi_turn),
        ("Function Calling", example_4_function_calling),
        ("APS 场景", example_5_aps_scenario),
        ("流式输出", example_6_streaming),
    ]
    
    print("\n可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\n" + "="*60)
    print("注意: 当前 API Key 余额不足，示例仅供参考")
    print("充值后即可运行所有示例")
    print("="*60)
    
    # 如果要运行示例，取消下面的注释
    # for name, func in examples:
    #     try:
    #         func()
    #         input("\n按回车继续下一个示例...")
    #     except Exception as e:
    #         print(f"\n错误: {e}")
    #         break


if __name__ == "__main__":
    main()
