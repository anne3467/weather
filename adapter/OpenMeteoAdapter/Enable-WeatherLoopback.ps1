$ErrorActionPreference = "Stop"
$pkg = Get-AppxPackage -Name "OpenMeteo.BingWeather"
if (-not $pkg) {
    throw "OpenMeteo.BingWeather is not installed yet."
}
CheckNetIsolation LoopbackExempt -a -n=$pkg.PackageFamilyName
CheckNetIsolation LoopbackExempt -s
