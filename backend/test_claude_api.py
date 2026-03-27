"""
测试 Claude API 连接和配置
"""
import sys
import io
import os
from openai import OpenAI

# 设置 UTF-8 编码（Windows 兼容）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# API 配置
API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.chataiapi.com/v1").strip()

# 常见的 Claude 模型名称
MODELS_TO_TRY = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet",
    "claude-3-sonnet",
    "claude-3-opus",
    "claude-3-haiku",
]

def find_available_model(client):
    """查找可用的 Claude 模型"""
    print("\n查找可用的模型...")
    print("-" * 60)
    
    for model in MODELS_TO_TRY:
        try:
            print(f"尝试模型: {model} ... ", end="")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10
            )
            print("✓ 可用")
            return model
        except Exception as e:
            print(f"✗ 不可用 ({str(e)[:50]})")
    
    return None


def test_claude_api():
    """测试 Claude API 基本功能"""
    print("=" * 60)
    print("测试 Claude API 连接")
    print("=" * 60)
    if not API_KEY:
        print("[ERROR] OPENAI_API_KEY 未设置")
        return False
    print(f"API Base URL: {BASE_URL}")
    print("-" * 60)
    
    try:
        # 初始化客户端
        client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL
        )
        
        # 查找可用模型
        MODEL = find_available_model(client)
        if not MODEL:
            print("\n错误: 没有找到可用的 Claude 模型")
            return False
        
        print(f"\n使用模型: {MODEL}")
        print("-" * 60)
        
        # 测试简单对话
        print("\n测试 1: 简单对话")
        print("-" * 60)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": "你好，请用一句话介绍你自己。"}
            ],
            max_tokens=100
        )
        
        reply = response.choices[0].message.content
        print(f"[OK] 回复: {reply}")
        print(f"[OK] 使用 tokens: {response.usage.total_tokens}")
        
        # 测试中文能力
        print("\n测试 2: 中文理解和回答")
        print("-" * 60)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": "什么是 APS 系统？请简短回答。"}
            ],
            max_tokens=150
        )
        
        reply = response.choices[0].message.content
        print(f"[OK] 回复: {reply}")
        
        # 测试 Function Calling
        print("\n测试 3: Function Calling 能力")
        print("-" * 60)
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
                                "description": "城市名称"
                            }
                        },
                        "required": ["city"]
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
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        if message.tool_calls:
            print(f"[OK] Function Calling 成功")
            print(f"[OK] 调用函数: {message.tool_calls[0].function.name}")
            print(f"[OK] 参数: {message.tool_calls[0].function.arguments}")
        else:
            print(f"[OK] 回复（未触发函数调用）: {message.content}")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] 所有测试通过！Claude API 配置正确。")
        print("推荐使用的模型: " + MODEL)
        print("=" * 60)
        
        return True
        
        return MODEL  # 返回可用的模型名称
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("[ERROR] 测试失败")
        print("=" * 60)
        print(f"错误信息: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        return None


if __name__ == "__main__":
    model = test_claude_api()
    sys.exit(0 if model else 1)
