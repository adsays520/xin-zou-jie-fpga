param([string]$Song = '', [switch]$Short, [switch]$CheckOnly)

$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$projectRoot = Join-Path $workspace 'drum_bass_pitch_20261013'
$appRoot = Join-Path $projectRoot 'violin_r15'
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
        if ($CheckOnly) {
            & $exe @prefix -B -X utf8 -c "import sys; sys.path.insert(0, r'$PSScriptRoot'); import demo_library; print('Demo library OK:', len(demo_library.read_catalog()), 'songs')"
            exit $LASTEXITCODE
        }
        $arguments = @()
        if ($Song) { $arguments += @('--song', $Song) }
        if ($Short) { $arguments += '--short' }
        & $exe @prefix -B -X utf8 (Join-Path $PSScriptRoot 'demo_library.py') @arguments
        exit $LASTEXITCODE
    }
    Write-Host 'No compatible Python with tkinter/numpy/pyserial found. Set FPGA_HOST_PYTHON.'
    exit 1
} finally {
    Pop-Location
}
