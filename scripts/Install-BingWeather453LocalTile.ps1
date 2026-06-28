$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot

$CertPath = Join-Path $ProjectRoot "dist\OpenMeteo.BingWeather453Visual.Local.cer"
$AppxPath = Join-Path $ProjectRoot "dist\OpenMeteo.BingWeather453LocalTile_4.53.41681.0_x64.appx"
$PackageName = "OpenMeteo.BingWeather453LocalTile"
$AdapterScript = Join-Path $ProjectRoot "adapter\OpenMeteoAdapter\Start-Adapter.ps1"
$TaskName = "OpenMeteo BingWeather Local Tile Adapter"

if (-not (Test-Path -LiteralPath $CertPath)) {
    throw "Certificate not found: $CertPath"
}

if (-not (Test-Path -LiteralPath $AppxPath)) {
    throw "AppX not found: $AppxPath"
}

if (-not (Test-Path -LiteralPath $AdapterScript)) {
    throw "Adapter start script not found: $AdapterScript"
}

Import-Certificate `
    -FilePath $CertPath `
    -CertStoreLocation "Cert:\CurrentUser\TrustedPeople" | Out-Null

Get-AppxPackage -Name $PackageName | Remove-AppxPackage -ErrorAction SilentlyContinue

Add-AppxPackage -Path $AppxPath

$pkg = Get-AppxPackage -Name $PackageName
if (-not $pkg) {
    throw "Package install did not complete: $PackageName"
}

CheckNetIsolation LoopbackExempt -a -n=$pkg.PackageFamilyName | Out-Host

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$AdapterScript`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Force | Out-Null

Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -like "*openmeteo_msn_adapter.py*" -and
        $_.Name -like "python*"
    } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }

Start-ScheduledTask -TaskName $TaskName

& $AdapterScript

$healthy = $false
for ($i = 0; $i -lt 10; $i++) {
    try {
        $health = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8765/health" -TimeoutSec 2
        if ($health.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $healthy) {
    throw "Local tile adapter did not start. Run scripts\start-adapter.bat and check Python installation."
}

Write-Host "Installed $PackageName"
Write-Host "Local tile adapter task registered and started."
Write-Host "Tip: unpin and re-pin the Weather tile if Windows keeps showing an older tile."
