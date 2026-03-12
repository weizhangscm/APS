"""
测试 Gemini API 超时问题修复
"""
import sys
import io
import time
from openai import OpenAI

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# API 配置
API_KEY = "sk-kpTnRoj9FgVj5u0vEh0IYAGgjs1D1XZs7vi2ROAomLKwGhzv"
BASE_URL = "https://xiaoai.plus/v1"
MODEL = "gemini-3-pro-preview"


def test_timeout_fix():
    """测试超时问题修复"""
    print("=" * 60)
    print("测试 Gemini API 超时修复")
    print("=" * 60)
    
    # 创建客户端，设置120秒超时
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=120.0,  # 120秒超时
        max_retries=2
    )
    
    # 测试 1: 简单查询（应该快速返回）
    print("\n测试 1: 简单查询（预计响应快）")
    print("-" * 60)
    
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": "你好"}
            ],
            timeout=120.0
        )
        elapsed = time.time() - start_time
        print(f"[OK] 响应成功")
        print(f"[OK] 回复: {response.choices[0].message.content[:50]}...")
        print(f"[OK] 耗时: {elapsed:.2f} 秒")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] 失败: {str(e)}")
        print(f"[ERROR] 耗时: {elapsed:.2f} 秒")
        return False
    
    # 测试 2: 复杂查询（可能较慢）
    print("\n测试 2: 复杂查询（预计响应慢）")
    print("-" * 60)
    
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user", 
                    "content": "请详细解释 APS 系统的核心功能、应用场景和实施要点，并举例说明。"
                }
            ],
            max_tokens=500,
            timeout=120.0
        )
        elapsed = time.time() - start_time
        print(f"[OK] 响应成功")
        print(f"[OK] 回复长度: {len(response.choices[0].message.content)} 字符")
        print(f"[OK] 耗时: {elapsed:.2f} 秒")
        
        if elapsed > 30:
            print(f"[INFO] 注意：响应时间 {elapsed:.2f} 秒超过了旧的30秒限制")
            print(f"[INFO] 新的120秒超时设置成功避免了错误")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] 失败: {str(e)}")
        print(f"[ERROR] 耗时: {elapsed:.2f} 秒")
        return False
    
    # 测试 3: Function Calling（可能较慢）
    print("\n测试 3: Function Calling（预计较慢）")
    print("-" * 60)
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "find_delayed_orders",
                "description": "查询延误订单",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    ]
    
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": "请查询交期在 3.9-3.20 之间的延期订单"}
            ],
            tools=tools,
            tool_choice="auto",
            timeout=120.0
        )
        elapsed = time.time() - start_time
        
        message = response.choices[0].message
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"[OK] Function Calling 成功")
            print(f"[OK] 函数: {message.tool_calls[0].function.name}")
            print(f"[OK] 耗时: {elapsed:.2f} 秒")
        else:
            print(f"[OK] 响应成功（未触发函数）")
            print(f"[OK] 回复: {message.content[:100]}...")
            print(f"[OK] 耗时: {elapsed:.2f} 秒")
        
        if elapsed > 30:
            print(f"[INFO] 响应时间 {elapsed:.2f} 秒超过了旧的30秒限制")
            print(f"[INFO] 新的120秒超时设置成功避免了错误")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] 失败: {str(e)}")
        print(f"[ERROR] 耗时: {elapsed:.2f} 秒")
        return False
    
    print("\n" + "=" * 60)
    print("[SUCCESS] 所有测试通过！超时问题已解决。")
    print("=" * 60)
    print("\n建议:")
    print("  1. 如果响应时间仍然较慢，可以考虑:")
    print("     - 简化 System Prompt")
    print("     - 减少 Function Calling 工具数量")
    print("     - 使用流式响应（streaming）")
    print("  2. 如果仍然超时，可以继续增加超时时间")
    
    return True


if __name__ == "__main__":
    success = test_timeout_fix()
    sys.exit(0 if success else 1)
