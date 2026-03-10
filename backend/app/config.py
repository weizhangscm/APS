"""
配置模块：管理环境变量和应用配置
"""
import os
from typing import Optional
from pathlib import Path


class Config:
    """应用配置类"""
    
    # OpenAI 配置
    # 首先尝试从环境变量读取，如果没有则使用默认值（开发环境）
    OPENAI_API_KEY: Optional[str] = (
        os.environ.get("OPENAI_API_KEY", "").strip() or 
        "sk-B3G5StfWpvvV2w4ScGlbmAI2hR6l0ypvUfA43RBMHBHqPJ7Z"  # 开发环境默认值
    )
    OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4o").strip()
    OPENAI_BASE_URL: Optional[str] = os.environ.get("OPENAI_BASE_URL", "").strip() or None
    
    # LLM 对话配置
    MAX_CONVERSATION_HISTORY: int = 20  # 最大保留消息数
    CONVERSATION_TIMEOUT_MINUTES: int = 30  # 会话超时时间（分钟）
    
    @classmethod
    def validate_openai_config(cls) -> bool:
        """验证 OpenAI 配置是否完整"""
        if cls.OPENAI_API_KEY and cls.OPENAI_API_KEY != "":
            return True
        return False
    
    @classmethod
    def get_openai_client_kwargs(cls) -> dict:
        """获取 OpenAI 客户端初始化参数"""
        kwargs = {"api_key": cls.OPENAI_API_KEY}
        if cls.OPENAI_BASE_URL:
            kwargs["base_url"] = cls.OPENAI_BASE_URL
        return kwargs


config = Config()
