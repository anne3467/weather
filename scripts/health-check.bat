@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8765/health' -TimeoutSec 5 | Select-Object -ExpandProperty Content"
echo.
pause
