# PowerShell 脚本：设置 OpenAI API 环境变量
# 使用方法：在 PowerShell 中运行 .\set_env.ps1

$env:OPENAI_API_KEY="sk-B3G5StfWpvvV2w4ScGlbmAI2hR6l0ypvUfA43RBMHBHqPJ7Z"
$env:OPENAI_MODEL="gpt-4o"

Write-Host "✓ 环境变量已设置:" -ForegroundColor Green
Write-Host "  OPENAI_API_KEY = $env:OPENAI_API_KEY"
Write-Host "  OPENAI_MODEL   = $env:OPENAI_MODEL"
Write-Host ""
Write-Host "现在可以启动后端服务了:" -ForegroundColor Cyan
Write-Host "  uvicorn app.main:app --reload"
