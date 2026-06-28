@echo off
setlocal
pushd "%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$u='http://127.0.0.1:8765/zh-cn/livetile/back/22.5,113.9?locationName=%%E5%%8D%%97%%E5%%B1%%B1%%E5%%8C%%BA&units=C'; $r=Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 25; $r.Content | Out-File -Encoding utf8 'tile-preview.xml'; Write-Host 'Saved to tile-preview.xml'; Write-Host ''; $r.Content"
set "ERR=%ERRORLEVEL%"
popd
if not "%ERR%"=="0" (
  echo.
  echo Preview failed. Start the adapter first with scripts\start-adapter.bat.
  pause
  exit /b %ERR%
)
echo.
pause
