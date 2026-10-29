#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$InstallDir = '',
    [ValidateSet('Auto', 'Cpu', 'Cuda')][string]$Acceleration = 'Auto',
    [switch]$SkipCamera,
    [switch]$SkipModels,
    [switch]$SkipLaunch,
    [switch]$SkipShortcut,
    [switch]$Plan
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$release = 'v1.0.1'
$repository = 'Akshit406/Deep-Live-Cam-Camera11'

function Get-VerifiedFile([string]$Url, [string]$Destination, [string]$Sha256) {
    if ((Test-Path -LiteralPath $Destination) -and ((Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash -eq $Sha256)) { return }
    Write-Host "Downloading $Url"
    Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile ($Destination + '.part')
    if ((Get-FileHash -LiteralPath ($Destination + '.part') -Algorithm SHA256).Hash -ne $Sha256) {
        throw "Checksum mismatch for $Url. The file will not be used."
    }
    Move-Item -LiteralPath ($Destination + '.part') -Destination $Destination -Force
}

if (-not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') {
    throw 'This installer supports Windows 10/11 on Intel/AMD x64 computers.'
}
if ($Plan) {
    Write-Host "Camera11 ${release}: private Python 3.12.13; pinned packages; FFmpeg; face models; Camera11 registration (UAC); desktop shortcut."
    Write-Host 'Run the installer in Windows PowerShell. -Acceleration Cpu selects CPU; -SkipModels defers models; -SkipCamera skips registration; -SkipLaunch skips opening the app.'
    return
}
$sourceRoot = $PSScriptRoot
$localSource = $sourceRoot -and (Test-Path -LiteralPath (Join-Path $sourceRoot 'installer\assets.json'))
if (-not $InstallDir) {
    if ($localSource) { $InstallDir = $sourceRoot }
    else { $InstallDir = Join-Path $env:LOCALAPPDATA 'DeepLiveCamCamera11' }
}
$targetRoot = [IO.Path]::GetFullPath($InstallDir)
if (-not $localSource -or $targetRoot.TrimEnd('\') -ne $sourceRoot.TrimEnd('\')) {
    $marker = Join-Path $targetRoot 'installer\assets.json'
    if (Test-Path -LiteralPath $targetRoot) {
        if (-not (Test-Path -LiteralPath $marker)) {
            throw "Destination exists and is not a Camera11 installation: $targetRoot. Choose a new -InstallDir."
        }
        $existing = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
        if ($existing.release -ne $release) { throw 'Use a new directory for a different release; updates do not overwrite existing installs.' }
        Write-Host "Resuming installation in $targetRoot"
    } else {
        $downloadRoot = Join-Path ([IO.Path]::GetTempPath()) ('Camera11-' + [guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $downloadRoot | Out-Null
        $archive = Join-Path $downloadRoot 'source.zip'
        Write-Host "Downloading $repository $release"
        Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/$repository/archive/refs/tags/$release.zip" -OutFile $archive
        $extractRoot = Join-Path $downloadRoot 'source'
        Expand-Archive -LiteralPath $archive -DestinationPath $extractRoot
        $folders = @(Get-ChildItem -LiteralPath $extractRoot -Directory)
        if ($folders.Count -ne 1) { throw 'Unexpected source archive layout.' }
        $candidate = [IO.Path]::GetFullPath($folders[0].FullName)
        $expectedParent = [IO.Path]::GetFullPath($extractRoot).TrimEnd('\') + '\'
        if (-not $candidate.StartsWith($expectedParent, [StringComparison]::OrdinalIgnoreCase)) { throw 'Source directory validation failed.' }
        if (-not (Test-Path -LiteralPath (Join-Path $candidate 'installer\assets.json'))) { throw 'The source archive is incomplete.' }
        $parent = Split-Path -Parent $targetRoot
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
        Move-Item -LiteralPath $candidate -Destination $targetRoot
    }
}
$assets = Get-Content -LiteralPath (Join-Path $targetRoot 'installer\assets.json') -Raw | ConvertFrom-Json
$toolsRoot = Join-Path $targetRoot '.installer'
New-Item -ItemType Directory -Path $toolsRoot -Force | Out-Null
$uvZip = Join-Path $toolsRoot 'uv.zip'
Get-VerifiedFile $assets.uv.url $uvZip $assets.uv.sha256
Expand-Archive -LiteralPath $uvZip -DestinationPath (Join-Path $toolsRoot 'uv') -Force
$uvCandidates = @(Get-ChildItem -LiteralPath (Join-Path $toolsRoot 'uv') -Recurse -Filter 'uv.exe')
if ($uvCandidates.Count -ne 1) { throw 'Could not find the private uv executable.' }
$uv = $uvCandidates[0].FullName
# Keep the private Python installation with this app; do not edit the user's PATH.
$env:UV_PYTHON_INSTALL_DIR = Join-Path $targetRoot '.runtime'
$env:UV_PYTHON_BIN_DIR = Join-Path $toolsRoot 'python-bin'
& $uv python install $assets.python --no-bin --no-registry
if ($LASTEXITCODE -ne 0) { throw 'Private Python installation failed.' }
$python = Join-Path $targetRoot 'venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    & $uv venv (Join-Path $targetRoot 'venv') --python $assets.python --managed-python
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}
$setupArguments = @((Join-Path $targetRoot 'installer\setup_windows.py'), '--uv', $uv, '--acceleration', $Acceleration.ToLower())
if ($SkipCamera) { $setupArguments += '--skip-camera' }
if ($SkipModels) { $setupArguments += '--skip-models' }
if ($SkipLaunch) { $setupArguments += '--skip-launch' }
if ($SkipShortcut) { $setupArguments += '--skip-shortcut' }
& $python @setupArguments
if ($LASTEXITCODE -ne 0) { throw 'Camera11 setup failed. See the error above; rerun the same command to resume.' }
