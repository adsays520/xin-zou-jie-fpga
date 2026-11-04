param([switch]$CheckOnly, [switch]$Arrangement)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$controllerPath = Join-Path $PSScriptRoot 'host_controller.py'
$env:PYTHONPATH = (Join-Path $projectRoot 'tools/python_deps') + ';' + $env:PYTHONPATH
$env:PYTHONDONTWRITEBYTECODE = '1'
$candidates = @()
if ($env:FPGA_HOST_PYTHON) { $candidates += @{ Exe=$env:FPGA_HOST_PYTHON; Prefix=@() } }
$candidates += @{ Exe=(Join-Path $projectRoot '.venv/Scripts/python.exe'); Prefix=@() }
if (Get-Command py -ErrorAction SilentlyContinue) { $candidates += @{ Exe='py'; Prefix=@('-3') } }
if (Get-Command python -ErrorAction SilentlyContinue) { $candidates += @{ Exe='python'; Prefix=@() } }
$candidates += @{ Exe=(Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'); Prefix=@() }
$candidates += @{ Exe='D:/conda/envs/py38/python.exe'; Prefix=@() }

Push-Location $PSScriptRoot
try {
    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Exe -ErrorAction SilentlyContinue)) { continue }
        $exe = $candidate.Exe
        $prefix = $candidate.Prefix
        try {
            & $exe @prefix -B -X utf8 -c 'import sys; assert sys.version_info >= (3,8); import tkinter,numpy,serial,host_controller; assert host_controller.legacy.serial is not None' 2>$null
            $usable = $LASTEXITCODE -eq 0
        } catch { $usable = $false }
        if (-not $usable) { continue }
        if ($CheckOnly) {
            Write-Host "R15 host imports OK: $exe"
            exit 0
        }
        $launchArguments = @()
        if ($Arrangement) { $launchArguments += '--arrangement' }
        & $exe @prefix -B -X utf8 $controllerPath @launchArguments
        exit $LASTEXITCODE
    }
    Write-Host 'No compatible Python with tkinter/numpy/pyserial found.'
    Write-Host 'Install host/requirements.txt, or set FPGA_HOST_PYTHON to your Python executable.'
    exit 1
} finally {
    Pop-Location
}
