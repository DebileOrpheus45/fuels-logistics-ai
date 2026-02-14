# Fuels Logistics AI - Start All Services
# Usage: powershell -File start_all.ps1

Write-Host "Starting Fuels Logistics AI..." -ForegroundColor Cyan

# 1. Backend (FastAPI)
Write-Host "`n[1/3] Starting Backend (port 8000)..." -ForegroundColor Yellow
$backend = Start-Process -FilePath "python" `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" `
    -WorkingDirectory "$PSScriptRoot\backend" `
    -PassThru -NoNewWindow
Write-Host "  Backend PID: $($backend.Id)" -ForegroundColor Green

# Wait for backend to be ready
Write-Host "  Waiting for backend..." -ForegroundColor Gray
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "  Backend ready!" -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}

# 2. Email Poller
Write-Host "`n[2/3] Starting Email Poller..." -ForegroundColor Yellow
$poller = Start-Process -FilePath "python" `
    -ArgumentList "start_email_poller.py" `
    -WorkingDirectory "$PSScriptRoot\backend" `
    -PassThru -NoNewWindow
Write-Host "  Poller PID: $($poller.Id)" -ForegroundColor Green

# 3. Frontend (Vite)
Write-Host "`n[3/3] Starting Frontend (port 5173)..." -ForegroundColor Yellow
$frontend = Start-Process -FilePath "npx" `
    -ArgumentList "vite" `
    -WorkingDirectory "$PSScriptRoot\frontend" `
    -PassThru -NoNewWindow
Write-Host "  Frontend PID: $($frontend.Id)" -ForegroundColor Green

Write-Host "`n--- All services started ---" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  Poller:   Running (30s interval)" -ForegroundColor White
Write-Host "`nPress Ctrl+C to stop all services." -ForegroundColor Gray

# Wait and cleanup on exit
try {
    while ($true) { Start-Sleep -Seconds 5 }
} finally {
    Write-Host "`nStopping services..." -ForegroundColor Yellow
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $poller.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
    Write-Host "All services stopped." -ForegroundColor Green
}
