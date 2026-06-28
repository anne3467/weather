$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
$AdapterRoot = Join-Path $ProjectRoot "adapter\OpenMeteoAdapter"
$Stage = Join-Path $ProjectRoot "_stage\adapter_zip"
$StageAdapter = Join-Path $Stage "OpenMeteoAdapter"
$OutZip = Join-Path $ProjectRoot "dist\OpenMeteo.BingWeather453LocalTile_Adapter.zip"

if (-not (Test-Path -LiteralPath $AdapterRoot)) {
    throw "Adapter folder not found: $AdapterRoot"
}

if (Test-Path -LiteralPath $Stage) {
    Remove-Item -LiteralPath $Stage -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $StageAdapter | Out-Null

Copy-Item -LiteralPath `
    (Join-Path $AdapterRoot "openmeteo_msn_adapter.py"), `
    (Join-Path $AdapterRoot "Start-Adapter.ps1"), `
    (Join-Path $AdapterRoot "Enable-WeatherLoopback.ps1"), `
    (Join-Path $AdapterRoot "README.txt") `
    -Destination $StageAdapter `
    -Force

Copy-Item -LiteralPath (Join-Path $AdapterRoot "WeatherIcons") -Destination $StageAdapter -Recurse -Force
Copy-Item -LiteralPath (Join-Path $AdapterRoot "WeatherImages") -Destination $StageAdapter -Recurse -Force

Compress-Archive -Path $StageAdapter -DestinationPath $OutZip -Force

Remove-Item -LiteralPath $Stage -Recurse -Force
$StageRoot = Split-Path -Parent $Stage
if ((Test-Path -LiteralPath $StageRoot) -and -not (Get-ChildItem -LiteralPath $StageRoot -Force)) {
    Remove-Item -LiteralPath $StageRoot -Force
}

Write-Host "Adapter zip rebuilt:"
Write-Host $OutZip
