# 清除可能阻止 pip 访问 PyPI 的环境变量
Remove-Item Env:PIP_NO_INDEX -ErrorAction SilentlyContinue
Remove-Item Env:PIP_DISABLE_PIP_VERSION_CHECK -ErrorAction SilentlyContinue
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

# 清理临时目录
Write-Host "清理临时目录..."
Start-Sleep -Seconds 2
Get-ChildItem "$env:TEMP\pip-*" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# 使用阿里云镜像源安装依赖（如果清华镜像无法访问）
Write-Host "开始安装依赖..."
$pythonPath = "C:\Users\Chun.Wang\AppData\Local\Programs\Python\Python313\python.exe"

# 尝试使用阿里云镜像源
Write-Host "尝试使用阿里云镜像源..." -ForegroundColor Yellow
& $pythonPath -m pip install --user --no-cache-dir --index-url https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt

# 如果失败，尝试清华镜像源
if ($LASTEXITCODE -ne 0) {
    Write-Host "阿里云镜像源失败，尝试清华镜像源..." -ForegroundColor Yellow
    & $pythonPath -m pip install --user --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn -r requirements.txt
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "依赖安装成功！" -ForegroundColor Green
} else {
    Write-Host "依赖安装失败。如果遇到权限问题，请尝试以管理员身份运行此脚本。" -ForegroundColor Red
    Write-Host "或者手动执行以下命令：" -ForegroundColor Yellow
    Write-Host '$env:PIP_NO_INDEX = ""; $env:NO_PROXY = "*"; [System.Net.WebRequest]::DefaultWebProxy = $null; python -m pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn -r requirements.txt' -ForegroundColor Cyan
}
