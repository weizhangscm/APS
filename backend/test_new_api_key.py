"""
快速测试新 API Key 支持的模型
"""
import sys
import io
from openai import OpenAI

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 新的 API 配置
API_KEY = "sk-VwCqIndGZuUtYBd1zmtcbetWFfomPO0thZAN5XeXU7BjghhG"
BASE_URL = "https://api.chataiapi.com/v1"

# 常见模型列表
TEST_MODELS = [
    # Claude 3.5 系列
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet",
    "claude-3-opus",
    "claude-3-sonnet",
    "claude-3-haiku",
    # GPT 系列
    "gpt-4",
    "gpt-4-turbo",
    "gpt-4o",
    "gpt-3.5-turbo",
    # 其他
    "claude",
]

def test_models():
    print("=" * 60)
    print("测试新 API Key 支持的模型")
    print("=" * 60)
    print(f"API Key: {API_KEY[:15]}...{API_KEY[-10:]}")
    print(f"Base URL: {BASE_URL}")
    print("-" * 60)
    
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    available_models = []
    
    for model in TEST_MODELS:
        try:
            print(f"测试: {model:40s} ... ", end="", flush=True)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10
            )
            print("[OK] 可用")
            available_models.append(model)
            print(f"    回复: {response.choices[0].message.content}")
        except Exception as e:
            error_msg = str(e)
            if "model_not_found" in error_msg or "无可用渠道" in error_msg:
                print("[X] 无可用渠道")
            elif "403" in error_msg and "额度不足" in error_msg:
                print("[X] 余额不足")
            elif "401" in error_msg or "Unauthorized" in error_msg:
                print("[X] 认证失败")
            else:
                print(f"[?] {error_msg[:40]}")
    
    print("\n" + "=" * 60)
    if available_models:
        print(f"发现 {len(available_models)} 个可用模型:")
        print("=" * 60)
        for model in available_models:
            print(f"  ✓ {model}")
        print("\n推荐使用: " + available_models[0])
    else:
        print("未找到可用模型")
        print("可能的原因:")
        print("  1. API Key 没有配置任何模型")
        print("  2. 账户余额不足")
        print("  3. API Key 无效")
    print("=" * 60)
    
    return available_models

if __name__ == "__main__":
    models = test_models()
    sys.exit(0 if models else 1)
