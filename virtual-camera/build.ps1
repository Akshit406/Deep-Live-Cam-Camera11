$ErrorActionPreference = 'Stop'
$cameraRoot = $PSScriptRoot
$vswhere = 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
$buildTools = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $buildTools) { throw 'Microsoft C++ Build Tools are required.' }
$cameraCmake = Join-Path $buildTools 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
foreach ($target in @(@('x64','x64'),@('x86','Win32'))) {
    $output = Join-Path $cameraRoot ('build-' + $target[0])
    & $cameraCmake -S $cameraRoot -B $output -G 'Visual Studio 17 2022' -A $target[1]
    if ($LASTEXITCODE -ne 0) { throw 'Camera configuration failed.' }
    & $cameraCmake --build $output --config Release
    if ($LASTEXITCODE -ne 0) { throw 'Camera build failed.' }
    $binary = Join-Path $output ('Release\deeplive-camera11-' + $target[0] + '.dll')
    $destination = Join-Path $cameraRoot 'bin'
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    Copy-Item -LiteralPath $binary -Destination $destination -Force
}
Write-Host 'Both camera DLLs built. Run Install Camera11.bat to install.'
