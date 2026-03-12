"""
测试 Gemini API 连接和配置
"""
import sys
import io
from openai import OpenAI

# 设置 UTF-8 编码（Windows 兼容）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Gemini API 配置
API_KEY = "sk-kpTnRoj9FgVj5u0vEh0IYAGgjs1D1XZs7vi2ROAomLKwGhzv"
BASE_URL = "https://xiaoai.plus/v1"

# 常见的 Gemini 模型名称
MODELS_TO_TRY = [
    "gemini-3-pro-preview",
    "gemini-3-pro",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-pro",
    "gemini-3.1-pro",
    "gemini-3.1-flash",
]


def find_available_model(client):
    """查找可用的 Gemini 模型"""
    print("\n查找可用的模型...")
    print("-" * 60)
    
    for model in MODELS_TO_TRY:
        try:
            print(f"尝试模型: {model:40s} ... ", end="", flush=True)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10
            )
            print("[OK] 可用")
            print(f"    回复: {response.choices[0].message.content}")
            return model
        except Exception as e:
            error_msg = str(e)
            if "model_not_found" in error_msg or "not found" in error_msg.lower():
                print("[X] 不存在")
            elif "403" in error_msg or "401" in error_msg:
                print(f"[X] {error_msg[:50]}")
            else:
                print(f"[?] {error_msg[:50]}")
    
    return None


def test_gemini_api():
    """测试 Gemini API 基本功能"""
    print("=" * 60)
    print("测试 Gemini API 连接")
    print("=" * 60)
    print(f"API Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:20]}...{API_KEY[-10:]}")
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
            print("\n错误: 没有找到可用的 Gemini 模型")
            return None
        
        print(f"\n使用模型: {MODEL}")
        print("-" * 60)
        
        # 测试 1: 简单对话
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
        if hasattr(response, 'usage') and response.usage:
            print(f"[OK] 使用 tokens: {response.usage.total_tokens}")
        
        # 测试 2: 中文理解
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
        
        # 测试 3: Function Calling
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
        
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "user", "content": "北京今天天气怎么样？"}
                ],
                tools=tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            if hasattr(message, 'tool_calls') and message.tool_calls:
                print(f"[OK] Function Calling 成功")
                print(f"[OK] 调用函数: {message.tool_calls[0].function.name}")
                print(f"[OK] 参数: {message.tool_calls[0].function.arguments}")
            else:
                print(f"[OK] 回复（未触发函数调用）: {message.content}")
        except Exception as e:
            print(f"[WARN] Function Calling 测试跳过: {str(e)[:60]}")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] 测试通过！Gemini API 配置正确。")
        print("推荐使用的模型: " + MODEL)
        print("=" * 60)
        
        return MODEL
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("[ERROR] 测试失败")
        print("=" * 60)
        print(f"错误信息: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        return None


if __name__ == "__main__":
    model = test_gemini_api()
    sys.exit(0 if model else 1)
