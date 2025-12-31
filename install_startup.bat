@echo off
set "SHORTCUT_NAME=GoldERP.lnk"
set "TARGET_PATH=%~dp0تشغيل_النظام.bat"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\%SHORTCUT_NAME%"

echo Creating startup shortcut...
echo Target: %TARGET_PATH%
echo Destination: %SHORTCUT_PATH%

powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT_PATH%');$s.TargetPath='%TARGET_PATH%';$s.WorkingDirectory='%~dp0';$s.Save()"

if exist "%SHORTCUT_PATH%" (
    echo Shortcut created successfully!
) else (
    echo Failed to create shortcut.
)
pause
