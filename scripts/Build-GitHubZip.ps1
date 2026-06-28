$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
$OutZip = Join-Path (Split-Path -Parent $ProjectRoot) "bing-weather-453-old-tile_github-ready.zip"
$Stage = Join-Path $ProjectRoot "_stage\github_zip"

if (Test-Path -LiteralPath $Stage) {
    Remove-Item -LiteralPath $Stage -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $Stage | Out-Null

$skip = @(".git", "_stage")
Get-ChildItem -LiteralPath $ProjectRoot -Force |
    Where-Object { $skip -notcontains $_.Name } |
    ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $Stage -Recurse -Force
    }

Compress-Archive -Path (Join-Path $Stage "*") -DestinationPath $OutZip -Force

Remove-Item -LiteralPath $Stage -Recurse -Force
$StageRoot = Split-Path -Parent $Stage
if ((Test-Path -LiteralPath $StageRoot) -and -not (Get-ChildItem -LiteralPath $StageRoot -Force)) {
    Remove-Item -LiteralPath $StageRoot -Force
}

Write-Host "GitHub-ready zip rebuilt:"
Write-Host $OutZip
