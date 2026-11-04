param([string]$IdfPath, [string]$ToolsPath, [string]$PythonEnvironment)
$ErrorActionPreference = 'Stop'
if (!$IdfPath) { $IdfPath = $env:IDF_PATH }
if (!$IdfPath -and (Test-Path 'C:/esp/v6.1/esp-idf')) { $IdfPath = 'C:/esp/v6.1/esp-idf' }
if (!$IdfPath -or !(Test-Path (Join-Path $IdfPath 'tools/idf.py'))) { throw 'Pass -IdfPath with a complete ESP-IDF 6.1 installation.' }
if (!$ToolsPath) { $ToolsPath = $env:IDF_TOOLS_PATH }
if (!$ToolsPath -and (Test-Path 'C:/Espressif/tools/espidf.constraints.v6.1.txt')) { $ToolsPath = 'C:/Espressif/tools' }
if (!$PythonEnvironment) { $PythonEnvironment = $env:IDF_PYTHON_ENV_PATH }
if (!$PythonEnvironment -and $ToolsPath -and (Test-Path (Join-Path $ToolsPath 'python/v6.1/venv'))) { $PythonEnvironment = Join-Path $ToolsPath 'python/v6.1/venv' }
if (!$PythonEnvironment) { throw 'Activate ESP-IDF 6.1 or pass -PythonEnvironment with its virtual environment.' }
$env:IDF_PATH = (Resolve-Path -LiteralPath $IdfPath).Path
if ($ToolsPath) { $env:IDF_TOOLS_PATH = (Resolve-Path -LiteralPath $ToolsPath).Path }
$env:IDF_PYTHON_ENV_PATH = (Resolve-Path -LiteralPath $PythonEnvironment).Path
$env:ESP_IDF_VERSION = '6.1.0'
$env:PYTHONUTF8 = '1'
$env:PATH = "$env:IDF_PYTHON_ENV_PATH/Scripts;$env:PATH"
if ($ToolsPath) {
    foreach ($tool in @('cmake', 'ninja', 'xtensa-esp-elf', 'esp32ulp-elf')) {
        foreach ($base in @($ToolsPath, (Join-Path $ToolsPath 'tools'))) {
            $toolDir = Join-Path $base $tool
            if (!(Test-Path -LiteralPath $toolDir)) { continue }
            $executables = Get-ChildItem -LiteralPath $toolDir -Recurse -File -Filter '*.exe' |
                Where-Object Name -In @('cmake.exe','ninja.exe','xtensa-esp32s3-elf-gcc.exe','esp32ulp-elf-as.exe')
            foreach ($executable in $executables) { $env:PATH = "$($executable.DirectoryName);$env:PATH" }
        }
    }
    $romBase = Join-Path $ToolsPath 'esp-rom-elfs'
    if (Test-Path -LiteralPath $romBase) { $env:ESP_ROM_ELF_DIR = (Get-ChildItem -LiteralPath $romBase -Directory | Select-Object -First 1).FullName }
}
$project = Join-Path $PSScriptRoot 'fpga/esp32S3/Guitar_Controller_R15'
$build = Join-Path $project 'build_ble'
& (Join-Path $env:IDF_PYTHON_ENV_PATH 'Scripts/python.exe') (Join-Path $env:IDF_PATH 'tools/idf.py') -C $project -B $build build
if ($LASTEXITCODE) { throw "S3 BLE build failed: $LASTEXITCODE" }
Write-Host "Build output: $build; flash addresses are recorded in flasher_args.json."
