@echo off
REM 方案 B：在 8000 端口启动新后端
REM 若 8000 被占用，请先在任务管理器中结束占用 8000 的 python/uvicorn 进程，再运行此脚本。

cd /d "%~dp0"
echo Starting backend on http://127.0.0.1:8000 ...
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
