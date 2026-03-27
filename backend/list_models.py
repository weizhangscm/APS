"""
列出 API 中可用的模型
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

def list_models():
    """列出所有可用的模型"""
    print("=" * 60)
    print("查询可用的模型列表")
    print("=" * 60)
    if not API_KEY:
        print("[ERROR] OPENAI_API_KEY 未设置")
        return False
    print(f"API Base URL: {BASE_URL}")
    print("-" * 60)
    
    try:
        client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL
        )
        
        # 尝试列出模型
        models = client.models.list()
        
        print("\n可用的模型:")
        print("-" * 60)
        
        claude_models = []
        for model in models.data:
            print(f"  - {model.id}")
            if 'claude' in model.id.lower():
                claude_models.append(model.id)
        
        if claude_models:
            print("\n" + "=" * 60)
            print("Claude 相关模型:")
            print("=" * 60)
            for model in claude_models:
                print(f"  - {model}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 无法列出模型")
        print(f"错误信息: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        
        # 尝试常见的模型名称
        print("\n尝试常见的模型命名格式...")
        print("-" * 60)
        
        test_models = [
            # Anthropic 官方格式
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            # 简化格式
            "claude-3.5-sonnet",
            "claude-3-opus",
            "claude-3-sonnet", 
            "claude-3-haiku",
            # 通用格式
            "claude",
            "claude-v1",
            "claude-v2",
            # OpenAI 兼容格式（某些代理会这样命名）
            "gpt-4",
            "gpt-3.5-turbo",
        ]
        
        client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL
        )
        
        for model_name in test_models:
            try:
                print(f"测试: {model_name:40s} ... ", end="", flush=True)
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": "hi"}],
                    max_tokens=5
                )
                print("[OK] 可用")
                print(f"    回复: {response.choices[0].message.content}")
            except Exception as err:
                error_msg = str(err)
                if "model_not_found" in error_msg:
                    print("[X] 不存在")
                elif "503" in error_msg:
                    print("[X] 服务不可用")
                else:
                    print(f"[?] {error_msg[:30]}")
        
        return False


if __name__ == "__main__":
    success = list_models()
    sys.exit(0 if success else 1)
