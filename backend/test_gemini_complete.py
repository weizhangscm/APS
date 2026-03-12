"""
Gemini API 完整功能测试
"""
import sys
import io
from openai import OpenAI

# 设置 UTF-8 编码（Windows 兼容）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Gemini API 配置
API_KEY = "sk-kpTnRoj9FgVj5u0vEh0IYAGgjs1D1XZs7vi2ROAomLKwGhzv"
BASE_URL = "https://xiaoai.plus/v1"
MODEL = "gemini-3-pro-preview"


def test_basic_chat():
    """测试基本对话功能"""
    print("\n测试 1: 基本对话")
    print("-" * 60)
    
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "你好，请用一句话介绍你自己。"}
        ],
        max_tokens=100
    )
    
    reply = response.choices[0].message.content
    print(f"[OK] 回复: {reply}")
    if hasattr(response, 'usage') and response.usage:
        print(f"[OK] Tokens: {response.usage.total_tokens}")
    return True


def test_chinese_understanding():
    """测试中文理解能力"""
    print("\n测试 2: 中文理解和专业知识")
    print("-" * 60)
    
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "什么是 APS（高级计划排程）系统？请详细说明其主要功能。"}
        ],
        max_tokens=300
    )
    
    reply = response.choices[0].message.content
    print(f"[OK] 回复: {reply}")
    return True


def test_function_calling():
    """测试 Function Calling 功能"""
    print("\n测试 3: Function Calling（工具调用）")
    print("-" * 60)
    
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
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
                            "description": "资源名称列表"
                        }
                    },
                    "required": []
                }
            }
        }
    ]
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "帮我查询一下延误的订单"}
        ],
        tools=tools,
        tool_choice="auto"
    )
    
    message = response.choices[0].message
    
    if hasattr(message, 'tool_calls') and message.tool_calls:
        print(f"[OK] Function Calling 成功触发")
        for tool_call in message.tool_calls:
            print(f"  - 函数名: {tool_call.function.name}")
            print(f"  - 参数: {tool_call.function.arguments}")
    else:
        print(f"[WARN] 未触发 Function Calling")
        print(f"  回复: {message.content}")
    
    return True


def test_multi_turn_conversation():
    """测试多轮对话"""
    print("\n测试 4: 多轮对话")
    print("-" * 60)
    
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    messages = [
        {"role": "user", "content": "我叫张三，我在管理一个工厂的生产排程。"}
    ]
    
    # 第一轮
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=100
    )
    
    reply1 = response.choices[0].message.content
    print(f"用户: {messages[0]['content']}")
    print(f"助手: {reply1}")
    
    # 第二轮
    messages.append({"role": "assistant", "content": reply1})
    messages.append({"role": "user", "content": "你还记得我叫什么名字吗？"})
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=100
    )
    
    reply2 = response.choices[0].message.content
    print(f"用户: {messages[2]['content']}")
    print(f"助手: {reply2}")
    
    if "张三" in reply2:
        print("[OK] 多轮对话上下文保持成功")
    else:
        print("[WARN] 可能没有正确记住上下文")
    
    return True


def test_system_prompt():
    """测试系统提示词"""
    print("\n测试 5: 系统提示词")
    print("-" * 60)
    
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    system_prompt = """你是 APS（高级计划排程系统）的 AI 助手。你可以帮助用户：
- 查询延误订单
- 运行启发式排程
- 取消或保存排程计划
- 回答关于排程系统的问题

请用简洁专业的语言与用户交流。"""
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "什么是瓶颈资源？"}
        ],
        max_tokens=200
    )
    
    reply = response.choices[0].message.content
    print(f"系统角色: APS AI 助手")
    print(f"用户问题: 什么是瓶颈资源？")
    print(f"[OK] 回复: {reply}")
    
    return True


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Gemini API 完整功能测试")
    print("=" * 60)
    print(f"API Base URL: {BASE_URL}")
    print(f"Model: {MODEL}")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-10:]}")
    print("=" * 60)
    
    tests = [
        ("基本对话", test_basic_chat),
        ("中文理解", test_chinese_understanding),
        ("Function Calling", test_function_calling),
        ("多轮对话", test_multi_turn_conversation),
        ("系统提示词", test_system_prompt),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"[ERROR] {test_name} 失败")
            print(f"  错误: {str(e)}")
            failed += 1
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"通过: {passed}/{len(tests)}")
    print(f"失败: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n[SUCCESS] 所有测试通过！Gemini API 已成功集成。")
        print("\n推荐配置:")
        print(f"  OPENAI_API_KEY: {API_KEY}")
        print(f"  OPENAI_BASE_URL: {BASE_URL}")
        print(f"  OPENAI_MODEL: {MODEL}")
    else:
        print("\n[WARNING] 部分测试失败，请检查配置。")
    
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
