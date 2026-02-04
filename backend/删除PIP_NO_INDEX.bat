@echo off
echo 正在删除 PIP_NO_INDEX 环境变量...
echo.

REM 需要管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 错误：此脚本需要管理员权限！
    echo 请右键点击此文件，选择"以管理员身份运行"
    pause
    exit /b 1
)

REM 删除用户级别的 PIP_NO_INDEX 环境变量
reg delete "HKCU\Environment" /v PIP_NO_INDEX /f >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ 已成功删除用户级别的 PIP_NO_INDEX 环境变量
) else (
    echo ⚠ PIP_NO_INDEX 环境变量可能不存在或已被删除
)

echo.
echo 请重新打开 PowerShell 或命令提示符窗口以使更改生效。
echo 然后运行：python -m pip install --index-url https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt
echo.
pause
