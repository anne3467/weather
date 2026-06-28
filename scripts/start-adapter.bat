@echo off
setlocal
pushd "%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%CD%\adapter\OpenMeteoAdapter\Start-Adapter.ps1"
set "ERR=%ERRORLEVEL%"
popd
if not "%ERR%"=="0" (
  echo.
  echo Adapter failed to start. Check adapter\OpenMeteoAdapter\adapter.log.
  pause
  exit /b %ERR%
)
echo.
echo Adapter is running.
pause
