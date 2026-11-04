param([string]$IdfProfile = 'C:\Espressif\tools\Microsoft.v6.1.PowerShell_profile.ps1')

$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
if (-not $env:IDF_PATH -or -not (Get-Command idf.py -ErrorAction SilentlyContinue)) {
    . $IdfProfile
}
& idf.py -C $PSScriptRoot -B (Join-Path $PSScriptRoot 'build_config') -D IDF_TARGET=esp32s3 build
exit $LASTEXITCODE
