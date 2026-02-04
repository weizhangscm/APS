# 使用虚拟环境安装后端依赖的 PowerShell 脚本
# 这可以避免权限问题

Write-Host "正在创建虚拟环境并安装依赖..." -ForegroundColor Cyan

# 清除可能阻止 pip 访问 PyPI 的环境变量
Remove-Item Env:PIP_NO_INDEX -ErrorAction SilentlyContinue
Remove-Item Env:HTTP_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:HTTPS_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:http_proxy -ErrorAction SilentlyContinue
Remove-Item Env:https_proxy -ErrorAction SilentlyContinue

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

# 创建虚拟环境
Write-Host "创建虚拟环境..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "虚拟环境已存在，跳过创建" -ForegroundColor Green
} else {
    & $pythonPath -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "虚拟环境创建失败！" -ForegroundColor Red
        exit 1
    }
    Write-Host "虚拟环境创建成功！" -ForegroundColor Green
}

# 激活虚拟环境并安装依赖
Write-Host "激活虚拟环境并安装依赖..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# 升级 pip
Write-Host "升级 pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --index-url https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 安装依赖
Write-Host "安装依赖包..." -ForegroundColor Yellow
python -m pip install --index-url https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n依赖安装成功！" -ForegroundColor Green
    Write-Host "已安装的包：" -ForegroundColor Cyan
    python -m pip list | Select-String -Pattern "fastapi|uvicorn|sqlalchemy|pydantic|dateutil|aiosqlite"
    Write-Host "`n要使用虚拟环境，请运行：.\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
} else {
    Write-Host "`n依赖安装失败。" -ForegroundColor Red
    Write-Host "如果仍然遇到问题，请尝试以管理员身份运行此脚本。" -ForegroundColor Yellow
}

Write-Host "`n按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
