param([ValidatePattern('^panel_v14_build(?:_retry[0-9]+)?$')][string]$RunName = 'panel_v14_build')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = 'C:\Users\Junejay_Huang\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$result = Join-Path $root 'tests\results'
$output = Join-Path $result $RunName
if (Test-Path -LiteralPath $output) { throw 'Existing v14 build evidence must not be overwritten.' }
$active = @(Get-Process -Name gw_sh,pnr -ErrorAction SilentlyContinue)
if ($active.Count -gt 0) { throw 'Another Gowin build is active; do not overlap physical builds.' }
New-Item -ItemType Directory -Path $result -Force | Out-Null
$stdout = Join-Path $result ($RunName + '_driver_stdout.log')
$stderr = Join-Path $result ($RunName + '_driver_stderr.log')
if ((Test-Path -LiteralPath $stdout) -or (Test-Path -LiteralPath $stderr)) { throw 'Existing driver logs must not be overwritten.' }
$env:PANEL_V14_RUN = $RunName
$process = Start-Process -FilePath $python -ArgumentList @('-B','-X','utf8','scripts/run_panel_v14.py') -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
$receipt = [ordered]@{ started = (Get-Date).ToString('o'); pid = $process.Id; root = $root; script = 'scripts/run_panel_v14.py'; stdout = $stdout; stderr = $stderr; FPGA_written = $false; S3_written = $false }
$receipt.run_name = $RunName
$receipt | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $result ($RunName + '_launcher.json')) -Encoding utf8
$receipt | ConvertTo-Json

