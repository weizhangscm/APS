# PowerShell 脚本：检查 OpenAI API 环境变量（不写入密钥）
# 使用方法：在 PowerShell 中运行 .\set_env.ps1

if (-not $env:OPENAI_API_KEY) {
    Write-Host "[ERROR] OPENAI_API_KEY 未设置" -ForegroundColor Red
    Write-Host "请先在系统环境变量中配置 OPENAI_API_KEY，再重新打开终端。" -ForegroundColor Yellow
    exit 1
}

# 如果系统未设置，给出默认建议值（不覆盖系统环境变量）
if (-not $env:OPENAI_BASE_URL) { $env:OPENAI_BASE_URL = "https://api.chataiapi.com/v1" }
if (-not $env:OPENAI_MODEL) { $env:OPENAI_MODEL = "gemini-3-flash-preview" }

Write-Host "✓ 已读取环境变量（API Key 已隐藏）:" -ForegroundColor Green
Write-Host "  OPENAI_API_KEY = configured"
Write-Host "  OPENAI_BASE_URL = $env:OPENAI_BASE_URL"
Write-Host "  OPENAI_MODEL   = $env:OPENAI_MODEL"
Write-Host ""
Write-Host "现在可以启动后端服务了:" -ForegroundColor Cyan
Write-Host "  uvicorn app.main:app --reload"
