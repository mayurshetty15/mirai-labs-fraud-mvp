$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Set-Location $projectRoot
$env:LOKY_MAX_CPU_COUNT = [Environment]::ProcessorCount

Write-Host ""
python -m app.print_model_metrics 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Model metrics could not be loaded; continuing with service startup."
}
Write-Host ""

foreach ($port in 8001, 8502) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction Stop
        foreach ($connection in $connections) {
            if ($connection.OwningProcess) {
                Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
            }
        }
    }
    catch {
        # No listener on this port; nothing to clean up.
    }
}

$apiProcess = Start-Process python -ArgumentList @(
    "-m", "uvicorn", "app.api:app", "--app-dir", $projectRoot,
    "--host", "127.0.0.1", "--port", "8001"
) -WorkingDirectory $projectRoot -NoNewWindow -PassThru
$frontendProcess = Start-Process python -ArgumentList @(
    "-m", "streamlit", "run", "frontend/app.py",
    "--server.address", "127.0.0.1", "--server.port", "8502"
) -WorkingDirectory $projectRoot -NoNewWindow -PassThru

Write-Host "FastAPI starting at http://127.0.0.1:8001"
Write-Host "Streamlit starting at http://127.0.0.1:8502"
Write-Host "API PID: $($apiProcess.Id) | Streamlit PID: $($frontendProcess.Id)"
