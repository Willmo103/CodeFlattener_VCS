@echo off
:: Install script for CodeFlattener (CMD)

set "installDir=%USERPROFILE%\CodeFlattener"
mkdir "%installDir%" 2>nul

:: Download files
powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/Willmo103/FlattenCodeBase/releases/download/v2.2.0/CodeFlattener.exe' -OutFile '%installDir%\CodeFlattener.exe'}"
powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/Willmo103/FlattenCodeBase/releases/download/v2.2.0/appsettings.json' -OutFile '%installDir%\appsettings.json'}"
powershell -Command "& {Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/Willmo103/CodeFlattener_VCS/main/setup_flattener_vcs.py' -OutFile '%installDir%\Setup_flattener_vcs.py'}"

:: Create a batch file to run the Python script
echo @echo off > "%installDir%\fltn.bat"
echo python "%installDir%\Setup_flattener_vcs.py" %%* >> "%installDir%\fltn.bat"

:: Add the installation directory to the user's PATH
setx PATH "%PATH%;%installDir%"

echo Installation completed. CodeFlattener is installed in: %installDir%
echo The 'fltn' command has been added to your PATH.
echo Please restart your command prompt to use the new command.
echo Usage: fltn [path_to_codebase]
