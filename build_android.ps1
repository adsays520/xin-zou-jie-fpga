param([string]$Sdk, [string]$Gradle = 'gradle', [string]$Jdk, [string]$GradleHome)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
if ($Jdk) {
    $env:JAVA_HOME = (Resolve-Path -LiteralPath $Jdk).Path
    $env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
}
if (!$Sdk) { $Sdk = $env:ANDROID_HOME }
if (!$Sdk) { $Sdk = $env:ANDROID_SDK_ROOT }
if (!$Sdk -or !(Test-Path -LiteralPath $Sdk -PathType Container)) {
    throw 'Pass -Sdk with an installed Android SDK (platform 35 and build tools).'
}
$Sdk = (Resolve-Path -LiteralPath $Sdk).Path
$env:ANDROID_HOME = $Sdk
$env:ANDROID_SDK_ROOT = $Sdk
if (!$GradleHome) { $GradleHome = Join-Path $root '.cache/gradle' }
$env:GRADLE_USER_HOME = $GradleHome
$env:ANDROID_USER_HOME = Join-Path $root '.cache/android'
$env:TEMP = Join-Path $root '.cache/temp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
# On affected Windows JDKs, an absent Unix-domain socket directory makes the
# JDK selector use TCP loopback instead. This avoids the packaged JDK's pipe error.
$env:JAVA_TOOL_OPTIONS = "-Djava.net.preferIPv4Stack=true -Djdk.net.unixdomain.tmpdir=$root/.cache/no_afunix"
$sdkProperty = $Sdk.Replace('\', '/').Replace(':', '\:')
[IO.File]::WriteAllText((Join-Path $root 'android/local.properties'), "sdk.dir=$sdkProperty`n", (New-Object Text.UTF8Encoding($false)))
& $Gradle -p (Join-Path $root 'android') --no-daemon assembleDebug
if ($LASTEXITCODE) { throw "Android build failed: $LASTEXITCODE" }
Write-Host "New APK: $root/android/app/build/outputs/apk/debug/app-debug.apk"
Write-Host 'The build does not overwrite delivered files in bin/.'
