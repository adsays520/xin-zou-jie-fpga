$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = (Join-Path $projectRoot 'tools/python_deps') + ';' + $env:PYTHONPATH
$candidates = @()
if ($env:FPGA_HOST_PYTHON) { $candidates += @{ Exe=$env:FPGA_HOST_PYTHON; Prefix=@() } }
$candidates += @{ Exe=(Join-Path $projectRoot '.venv/Scripts/python.exe'); Prefix=@() }
if (Get-Command py -ErrorAction SilentlyContinue) { $candidates += @{ Exe='py'; Prefix=@('-3') } }
if (Get-Command python -ErrorAction SilentlyContinue) { $candidates += @{ Exe='python'; Prefix=@() } }
$candidates += @{ Exe='D:/conda/envs/py38/python.exe'; Prefix=@() }
$candidates += @{ Exe=(Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'); Prefix=@() }
foreach ($candidate in $candidates) {
    if (-not (Get-Command $candidate.Exe -ErrorAction SilentlyContinue)) { continue }
    $exe = $candidate.Exe
    $prefix = $candidate.Prefix
    try {
        & $exe @prefix -c 'import sys,tkinter,numpy,serial; assert sys.version_info >= (3,8)' 2>$null
    } catch { continue }
    if ($LASTEXITCODE -eq 0) {
        Push-Location $PSScriptRoot
        try { & $exe @prefix 'guitar_controller.py'; exit $LASTEXITCODE }
        finally { Pop-Location }
    }
}
Write-Host 'No Python 3.8+ with tkinter/numpy/pyserial found.'
Write-Host 'Install host/requirements.txt, or set FPGA_HOST_PYTHON to your Python executable.'
exit 1
