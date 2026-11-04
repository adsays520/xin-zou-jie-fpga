$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path "$PSScriptRoot/..").Path
$receiptPath = Join-Path $taskRoot 'impl/drum_gate_v5_space_r1_debug/gate_receipt.json'
if (!(Test-Path -LiteralPath $receiptPath)) { throw 'Run experiments/drums/run_gate_compare.ps1 before routing' }
$receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
# Gowin's child-process environment can omit PowerShell script modules.
# Use the built-in .NET implementation instead of the Get-FileHash function.
function Get-DrumSha256([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { [BitConverter]::ToString($hasher.ComputeHash($stream)).Replace('-', '') }
    finally { $stream.Dispose(); $hasher.Dispose() }
}
$checks = @{
    netlist_sha256 = 'impl/gwsynthesis/guitar_audio_drums_v5_space_r1.vg'
    synth_sha256 = 'src/drums/drum_synth.v'
    machine_sha256 = 'src/drums/drum_machine.v'
    audio_test_sha256 = 'experiments/drums/tb_drum_gate_compare.sv'
    pattern_test_sha256 = 'experiments/drums/tb_drum_gate_pattern.sv'
    cycle_monitor_sha256 = 'experiments/drums/tb_drum_gate_cycles.sv'
    audio_log_sha256 = 'impl/drum_gate_v5_space_r1_debug/gate_compare.log'
    pattern_log_sha256 = 'impl/drum_gate_v5_space_r1_debug/gate_pattern.log'
}
foreach ($key in $checks.Keys) {
    $actual = Get-DrumSha256 (Join-Path $taskRoot $checks[$key])
    if (!$receipt.$key -or $receipt.$key -ne $actual) {
        throw "Stale or missing gate comparison: $($checks[$key]). Run experiments/drums/run_gate_compare.ps1 again."
    }
}
if ($receipt.compared_kits -ne 3 -or $receipt.compared_voices -ne 12 -or
    $receipt.compared_stereo_frames -lt 288 -or $receipt.pattern_beats -ne 16 -or
    $receipt.every_cycle_compared -ne $true) {
    throw 'Incomplete drum gate comparison'
}
if (!(Select-String -LiteralPath (Join-Path $taskRoot $checks.audio_log_sha256) -Pattern 'PASS tb_drum_gate_compare' -Quiet) -or
    !(Select-String -LiteralPath (Join-Path $taskRoot $checks.pattern_log_sha256) -Pattern 'PASS tb_drum_gate_pattern' -Quiet)) {
    throw 'Drum gate comparison did not pass'
}
$fxReceiptPath = Join-Path $taskRoot 'impl/master_fx_gate_v5_r1/gate_receipt.json'
if (!(Test-Path -LiteralPath $fxReceiptPath)) { throw 'Run master FX gate comparison before routing' }
$fxReceipt = Get-Content -LiteralPath $fxReceiptPath -Raw | ConvertFrom-Json
$fxChecks = @{
    netlist_sha256 = 'impl/gwsynthesis/guitar_audio_drums_v5_space_r1.vg'
    control_sha256 = 'src/effects/master_space_fx_control.v'
    fx_sha256 = 'src/effects/master_space_fx.v'
    test_sha256 = 'experiments/poly32_tdm/tb_master_space_fx_gate.sv'
    log_sha256 = 'impl/master_fx_gate_v5_r1/gate_compare.log'
}
foreach ($key in $fxChecks.Keys) {
    $actual = Get-DrumSha256 (Join-Path $taskRoot $fxChecks[$key])
    if (!$fxReceipt.$key -or $fxReceipt.$key -ne $actual) {
        throw "Stale master FX gate comparison: $($fxChecks[$key])."
    }
}
if (!(Select-String -LiteralPath (Join-Path $taskRoot $fxChecks.log_sha256) -Pattern 'PASS tb_master_space_fx_gate' -Quiet)) {
    throw 'Master FX gate comparison did not pass'
}
Write-Output 'PASS drum and master FX gate guards: netlist, source, cycle timing, audio and pattern tests match'
