param([Parameter(Mandatory=$true)][string]$Port, [string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$directory = Join-Path $PSScriptRoot 'bin/s3'
$manifest = Get-Content -LiteralPath (Join-Path $directory 'images.json') -Raw | ConvertFrom-Json
foreach ($image in $manifest.images) {
    $file = Join-Path $directory $image.file
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $image.sha256) {
        throw "Firmware hash mismatch: $file"
    }
}
& $Python -m esptool --chip esp32s3 --port $Port --baud 460800 --before default-reset --after hard-reset write-flash --flash-mode dio --flash-size 16MB --flash-freq 80m 0x0 (Join-Path $directory 'bootloader.bin') 0x8000 (Join-Path $directory 'partition-table.bin') 0x10000 (Join-Path $directory 's3_ble_led.bin')
if ($LASTEXITCODE) { throw "S3 flash failed: $LASTEXITCODE" }
