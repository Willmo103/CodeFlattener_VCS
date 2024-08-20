# Install script for CodeFlattener (PowerShell)

$ErrorActionPreference = "Stop"

# Create installation directory
$installDir = Join-Path $env:USERPROFILE "CodeFlattener"
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

# Download files
$exeUrl = "https://github.com/Willmo103/FlattenCodeBase/releases/download/v2.2.0/CodeFlattener.exe"
$jsonUrl = "https://github.com/Willmo103/FlattenCodeBase/releases/download/v2.2.0/appsettings.json"
$pythonUrl = "https://raw.githubusercontent.com/Willmo103/CodeFlattener_SourceControl/main/setup_flattener_vcs.py"

$exePath = Join-Path $installDir "CodeFlattener.exe"
$jsonPath = Join-Path $installDir "appsettings.json"
$pythonPath = Join-Path $installDir "Setup_flattener_vcs.py"

Invoke-WebRequest -Uri $exeUrl -OutFile $exePath
Invoke-WebRequest -Uri $jsonUrl -OutFile $jsonPath
Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonPath

# Create a function to run the Python script
$functionContent = @"
function fltn {
    param(
        [string]`$path = "."
    )
    python "$pythonPath" `$path
}
"@

# Add the function to the PowerShell profile
$profilePath = $PROFILE.CurrentUserAllHosts
if (!(Test-Path $profilePath)) {
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
}
Add-Content -Path $profilePath -Value "`n$functionContent"

Write-Host "Installation completed. CodeFlattener is installed in: $installDir"
Write-Host "The 'fltn' command has been added to your PowerShell profile."
Write-Host "Please restart your PowerShell session or run '. $profilePath' to use the new command."
Write-Host "Usage: fltn [path_to_codebase]"
