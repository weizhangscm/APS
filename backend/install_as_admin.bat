@echo off
echo 正在以管理员身份安装后端依赖...
echo.

REM 设置环境变量
set PIP_NO_INDEX=
set NO_PROXY=*
set HTTP_PROXY=
set HTTPS_PROXY=

REM 切换到后端目录
cd /d "%~dp0"

REM 使用 Python 安装依赖
"C:\Users\Chun.Wang\AppData\Local\Programs\Python\Python313\python.exe" -m pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn --user -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo 依赖安装成功！
    pause
) else (
    echo.
    echo 依赖安装失败，请检查错误信息。
    pause
)
