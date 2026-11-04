param(
    [Parameter(Mandatory=$true)][ValidatePattern('^COM[0-9]+$')][string]$Port,
    [switch]$Write,
    [ValidateSet(-1,0,1,2,3,4,5,6,7)][int]$Chip = -1,
    [string]$Python = 'C:\Espressif\tools\python\v6.1\venv\Scripts\python.exe'
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Python)) {
    throw 'Pass -Python with an ESP-IDF Python interpreter that has pyserial installed.'
}
$arguments = @('-B','-X','utf8',(Join-Path $PSScriptRoot 'host/write_config.py'),'--port',$Port)
if ($Write) { $arguments += '--write' }
if ($Chip -ne -1) { $arguments += @('--chip',[string]$Chip) }
& $Python @arguments
exit $LASTEXITCODE
