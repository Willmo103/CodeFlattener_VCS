# Install script for CodeFlattener (PowerShell)

$ErrorActionPreference = "Stop"
$REPO_URL = "https://github.com/Willmo103/CodeFlattener_VCS"

# Create installation directory
$installDir = Join-Path $env:USERPROFILE "CodeFlattener"
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

# Download the releases.json file first to determine what to download
$releasesJsonUrl = "$REPO_URL/raw/main/releases.json"
$releasesJsonPath = Join-Path $installDir "releases.json"

Write-Host "Downloading releases information..."
Invoke-WebRequest -Uri $releasesJsonUrl -OutFile $releasesJsonPath

# Read the releases file to get the current version and download URLs
$releasesData = Get-Content -Path $releasesJsonPath -Raw | ConvertFrom-Json
$currentVersion = $releasesData.current_version
$currentRelease = $releasesData.releases | Where-Object { $_.version -eq $currentVersion }

Write-Host "Installing CodeFlattener version $currentVersion"

# Download the necessary files
$filesToDownload = @{
    "executable" = "CodeFlattener.exe"
    "config"     = "appsettings.json"
    "setup"      = "setup_flattener_vcs.py"
    "updater"    = "updater.py"
}

foreach ($key in $filesToDownload.Keys) {
    $url = $currentRelease.downloads.$key
    $destination = Join-Path $installDir $filesToDownload[$key]

    Write-Host "Downloading $($filesToDownload[$key])..."
    Invoke-WebRequest -Uri $url -OutFile $destination
}

# Create templates directory
$templatesDir = Join-Path $installDir "templates"
New-Item -ItemType Directory -Force -Path $templatesDir | Out-Null

# Download template files
$templateFiles = @(
    "powershell_script.ps1.j2",
    "shell_script.sh.j2",
    "add_doc.ps1.j2"
)

foreach ($templateFile in $templateFiles) {
    $url = "$REPO_URL/raw/main/templates/$templateFile"
    $destination = Join-Path $templatesDir $templateFile

    Write-Host "Downloading template $templateFile..."
    try {
        Invoke-WebRequest -Uri $url -OutFile $destination
    }
    catch {
        Write-Warning "Could not download template $templateFile. It will be generated automatically when needed."
    }
}

# Add the function to the PowerShell profile
$functionContent = @"
function fltn {
    param(
        [string]`$path = "."
    )
    python "$installDir\setup_flattener_vcs.py" `$path
}
"@

$profilePath = $PROFILE.CurrentUserAllHosts
if (!(Test-Path $profilePath)) {
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
}
Add-Content -Path $profilePath -Value "`n$functionContent"

Write-Host "Installation completed. CodeFlattener v$currentVersion is installed in: $installDir"
Write-Host "The 'fltn' command has been added to your PowerShell profile."
Write-Host "Please restart your PowerShell session or run '. $profilePath' to use the new command."
Write-Host "Usage: fltn [path_to_codebase]"
