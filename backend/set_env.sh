#!/bin/bash
# Bash 脚本：设置 OpenAI API 环境变量
# 使用方法：source ./set_env.sh

export OPENAI_API_KEY="sk-B3G5StfWpvvV2w4ScGlbmAI2hR6l0ypvUfA43RBMHBHqPJ7Z"
export OPENAI_MODEL="gpt-4o"

echo "✓ 环境变量已设置:"
echo "  OPENAI_API_KEY = $OPENAI_API_KEY"
echo "  OPENAI_MODEL   = $OPENAI_MODEL"
echo ""
echo "现在可以启动后端服务了:"
echo "  uvicorn app.main:app --reload"
