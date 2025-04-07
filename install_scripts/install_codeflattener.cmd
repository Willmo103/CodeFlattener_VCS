@echo off
:: Install script for CodeFlattener (CMD)

set "REPO_URL=https://github.com/Willmo103/CodeFlattener_VCS"
set "installDir=%USERPROFILE%\CodeFlattener"
mkdir "%installDir%" 2>nul

:: Download the releases.json file first to determine what to download
echo Downloading releases information...
powershell -Command "& {Invoke-WebRequest -Uri '%REPO_URL%/raw/main/releases.json' -OutFile '%installDir%\releases.json'}"

:: Parse the releases file to get the current version
for /f "tokens=2 delims=:, " %%a in ('findstr /C:"current_version" "%installDir%\releases.json"') do (
    set "currentVersion=%%~a"
    set "currentVersion=!currentVersion:"=!"
)

echo Installing CodeFlattener version %currentVersion%

:: Download necessary files using PowerShell
powershell -Command "& {$releasesData = Get-Content -Path '%installDir%\releases.json' | ConvertFrom-Json; $currentRelease = $releasesData.releases | Where-Object { $_.version -eq $releasesData.current_version }; Invoke-WebRequest -Uri $currentRelease.downloads.executable -OutFile '%installDir%\CodeFlattener.exe'}"
powershell -Command "& {$releasesData = Get-Content -Path '%installDir%\releases.json' | ConvertFrom-Json; $currentRelease = $releasesData.releases | Where-Object { $_.version -eq $releasesData.current_version }; Invoke-WebRequest -Uri $currentRelease.downloads.config -OutFile '%installDir%\appsettings.json'}"
powershell -Command "& {$releasesData = Get-Content -Path '%installDir%\releases.json' | ConvertFrom-Json; $currentRelease = $releasesData.releases | Where-Object { $_.version -eq $releasesData.current_version }; Invoke-WebRequest -Uri $currentRelease.downloads.setup -OutFile '%installDir%\setup_flattener_vcs.py'}"
powershell -Command "& {$releasesData = Get-Content -Path '%installDir%\releases.json' | ConvertFrom-Json; $currentRelease = $releasesData.releases | Where-Object { $_.version -eq $releasesData.current_version }; Invoke-WebRequest -Uri $currentRelease.downloads.updater -OutFile '%installDir%\updater.py'}"

:: Create templates directory
mkdir "%installDir%\templates" 2>nul

:: Download template files
echo Downloading template files...
powershell -Command "& {try { Invoke-WebRequest -Uri '%REPO_URL%/raw/main/templates/powershell_script.ps1.j2' -OutFile '%installDir%\templates\powershell_script.ps1.j2' } catch { Write-Warning 'Could not download template. It will be generated automatically when needed.' }}"
powershell -Command "& {try { Invoke-WebRequest -Uri '%REPO_URL%/raw/main/templates/shell_script.sh.j2' -OutFile '%installDir%\templates\shell_script.sh.j2' } catch { Write-Warning 'Could not download template. It will be generated automatically when needed.' }}"
powershell -Command "& {try { Invoke-WebRequest -Uri '%REPO_URL%/raw/main/templates/add_doc.ps1.j2' -OutFile '%installDir%\templates\add_doc.ps1.j2' } catch { Write-Warning 'Could not download template. It will be generated automatically when needed.' }}"

:: Create a batch file to run the Python script
echo @echo off > "%installDir%\fltn.bat"
echo python "%installDir%\setup_flattener_vcs.py" %%* >> "%installDir%\fltn.bat"

:: Add the installation directory to the user's PATH
setx PATH "%PATH%;%installDir%"

echo Installation completed. CodeFlattener v%currentVersion% is installed in: %installDir%
echo The 'fltn' command has been added to your PATH.
echo Please restart your command prompt to use the new command.
echo Usage: fltn [path_to_codebase]
