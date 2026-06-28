$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$logPath = Join-Path $scriptDir "adapter.log"
try {
    $health = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8765/health" -TimeoutSec 2
    if ($health.StatusCode -eq 200) {
        Write-Host "Open-Meteo adapter is already running."
        exit 0
    }
} catch {
}
$adapter = Join-Path $scriptDir "openmeteo_msn_adapter.py"
$command = @"
Set-Location -LiteralPath '$scriptDir'
python -u '$adapter' *> '$logPath'
"@

Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $command) `
    -WorkingDirectory $scriptDir `
    -WindowStyle Hidden

for ($i = 0; $i -lt 15; $i++) {
    try {
        $health = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8765/health" -TimeoutSec 2
        if ($health.StatusCode -eq 200) {
            Write-Host "Open-Meteo adapter started."
            exit 0
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

throw "Open-Meteo adapter did not start. Check $logPath"
