# 方案 B：在 8000 端口启动新后端（先释放端口再启动）
# 用法：在 backend 目录下执行 .\start_on_8000.ps1

$port = 8000
Write-Host "Checking port $port..."
$conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    $pids = $conn.OwningProcess | Sort-Object -Unique
    foreach ($pid in $pids) {
        Write-Host "Stopping process $pid on port $port..."
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
}
Write-Host "Starting uvicorn on 127.0.0.1:$port..."
python -m uvicorn app.main:app --host 127.0.0.1 --port $port
