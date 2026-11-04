param([switch]$Short, [switch]$CheckOnly)

$ErrorActionPreference = 'Stop'
$appRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$projectRoot = Split-Path -Parent $appRoot
$env:PYTHONPATH = "$appRoot;$(Join-Path $projectRoot 'host');$(Join-Path $projectRoot 'tools/python_deps');$env:PYTHONPATH"
$env:PYTHONDONTWRITEBYTECODE = '1'
$candidates = @()
if ($env:FPGA_HOST_PYTHON) { $candidates += @{ Exe=$env:FPGA_HOST_PYTHON; Prefix=@() } }
$candidates += @{ Exe=(Join-Path $projectRoot '.venv/Scripts/python.exe'); Prefix=@() }
$candidates += @{ Exe=(Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'); Prefix=@() }
$candidates += @{ Exe='py'; Prefix=@('-3') }
$candidates += @{ Exe='python'; Prefix=@() }
Push-Location $appRoot
try {
    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Exe -ErrorAction SilentlyContinue)) { continue }
        $exe = $candidate.Exe
        $prefix = $candidate.Prefix
        try {
            & $exe @prefix -B -X utf8 -c 'import tkinter,numpy,serial,host_controller; assert host_controller.legacy.serial is not None' 2>$null
            $usable = $LASTEXITCODE -eq 0
        } catch { $usable = $false }
        if (-not $usable) { continue }
        if ($CheckOnly) { Write-Host "Demo imports OK: $exe"; exit 0 }
        $arguments = @()
        if ($Short) { $arguments += '--short' }
        & $exe @prefix -B -X utf8 (Join-Path $PSScriptRoot 'open_demo.py') @arguments
        exit $LASTEXITCODE
    }
    Write-Host 'No compatible Python with tkinter/numpy/pyserial found. Set FPGA_HOST_PYTHON.'
    exit 1
} finally {
    Pop-Location
}
