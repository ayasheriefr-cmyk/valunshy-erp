@echo off
title Valunshy ERP - PostgreSQL Edition
echo ===============================================
echo     Valunshy Jewelry ERP System
echo     Running on PostgreSQL Database
echo ===============================================
echo.

cd /d "%~dp0"

echo Starting the server...
echo.

:: Open browser after 3 seconds delay (gives server time to start)
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:8000"

echo ===============================================
echo   Server is running!
echo   Opening browser automatically...
echo   
echo   To access from other devices on the network:
echo   Use your IP address instead of 127.0.0.1
echo   Example: http://192.168.1.xxx:8000
echo ===============================================
echo.
echo To stop the server, press Ctrl+C or close this window.
echo.

python manage.py runserver 0.0.0.0:8000

pause
