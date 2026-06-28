@echo off
setlocal
pushd "%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-BingWeather453LocalTile.ps1"
set "ERR=%ERRORLEVEL%"
popd
if not "%ERR%"=="0" (
  echo.
  echo Install failed. Check the message above.
  pause
  exit /b %ERR%
)
echo.
echo Install finished.
pause
