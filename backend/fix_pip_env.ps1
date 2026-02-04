# 修复 pip 环境变量问题的脚本
# 此脚本会删除阻止 pip 从索引下载包的环境变量

Write-Host "正在修复 pip 环境变量..." -ForegroundColor Cyan

# 删除用户级别的 PIP_NO_INDEX 环境变量
try {
    [System.Environment]::SetEnvironmentVariable("PIP_NO_INDEX", $null, "User")
    Write-Host "✓ 已删除用户级别的 PIP_NO_INDEX 环境变量" -ForegroundColor Green
} catch {
    Write-Host "⚠ 无法删除用户级别的 PIP_NO_INDEX（可能需要管理员权限）" -ForegroundColor Yellow
}

# 删除进程级别的环境变量
$env:PIP_NO_INDEX = $null
Remove-Item Env:PIP_NO_INDEX -ErrorAction SilentlyContinue

Write-Host "`n环境变量已修复。请重新打开 PowerShell 窗口以使更改生效。" -ForegroundColor Yellow
Write-Host "或者运行以下命令安装依赖：" -ForegroundColor Cyan
Write-Host 'python -m pip install --index-url https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt' -ForegroundColor White
