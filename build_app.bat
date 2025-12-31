@echo off
echo Starting Build Process for Valunshy ERP...
echo Installing requirements...
pip install pyinstaller waitress

echo Cleaning previous builds...
rmdir /s /q build
rmdir /s /q dist

echo Building Application...
pyinstaller valunshy.spec

echo Build Complete!
echo You can find your app in dist/ValunshyERP
pause
