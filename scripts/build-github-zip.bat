@echo off
setlocal
pushd "%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-GitHubZip.ps1"
set "ERR=%ERRORLEVEL%"
popd
if not "%ERR%"=="0" (
  echo.
  echo Build zip failed.
  pause
  exit /b %ERR%
)
echo.
pause
