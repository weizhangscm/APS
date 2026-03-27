#!/bin/bash
# Bash 脚本：检查 OpenAI API 环境变量（不写入密钥）
# 使用方法：source ./set_env.sh

if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "[ERROR] OPENAI_API_KEY 未设置"
  echo "请先在系统环境变量中配置 OPENAI_API_KEY，再重新打开终端。"
  return 1 2>/dev/null || exit 1
fi

# 如果系统未设置，给出默认建议值（不覆盖系统环境变量）
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://api.chataiapi.com/v1}"
export OPENAI_MODEL="${OPENAI_MODEL:-gemini-3-flash-preview}"

echo "✓ 已读取环境变量（API Key 已隐藏）:"
echo "  OPENAI_API_KEY = configured"
echo "  OPENAI_BASE_URL = $OPENAI_BASE_URL"
echo "  OPENAI_MODEL   = $OPENAI_MODEL"
echo ""
echo "现在可以启动后端服务了:"
echo "  uvicorn app.main:app --reload"
