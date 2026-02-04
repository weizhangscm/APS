# 以管理员身份安装后端依赖的 PowerShell 脚本
# 使用方法：右键点击此文件，选择"使用 PowerShell 运行"

Write-Host "正在安装后端依赖..." -ForegroundColor Cyan

# 设置环境变量来绕过代理
$env:PIP_NO_INDEX = ""
$env:NO_PROXY = "*"
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""

# 禁用系统代理
[System.Net.WebRequest]::DefaultWebProxy = $null

# 切换到脚本所在目录
Set-Location $PSScriptRoot

# Python 路径
$pythonPath = "C:\Users\Chun.Wang\AppData\Local\Programs\Python\Python313\python.exe"

# 清理临时目录
Write-Host "清理临时目录..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
Get-ChildItem "$env:TEMP\pip-*" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# 安装依赖
Write-Host "开始安装依赖包..." -ForegroundColor Yellow
& $pythonPath -m pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn --user -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n依赖安装成功！" -ForegroundColor Green
    Write-Host "已安装的包：" -ForegroundColor Cyan
    & $pythonPath -m pip list | Select-String -Pattern "fastapi|uvicorn|sqlalchemy|pydantic|dateutil|aiosqlite"
} else {
    Write-Host "`n依赖安装失败。" -ForegroundColor Red
    Write-Host "如果仍然遇到权限问题，请尝试：" -ForegroundColor Yellow
    Write-Host "1. 临时禁用防病毒软件" -ForegroundColor Yellow
    Write-Host "2. 使用虚拟环境安装" -ForegroundColor Yellow
}

Write-Host "`n按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
