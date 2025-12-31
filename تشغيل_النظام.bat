@echo off
title Gold ERP System - [Daysum Inspired]
color 0E

echo ======================================================
echo           SYSTEM STARTING - GOLD ERP
echo          Inspired by Daysum (Diesem)
echo ======================================================

:: Check if migrations are pending
echo [1/3] Checking for database updates...
python manage.py migrate --noinput

:: Run initial data if needed
echo [2/3] Verifying system defaults (Carats, Accounts)...
python manage.py init_gold

:: Launch Browser with a slight delay in the background
echo [3/3] Launching System Interface...
start /b cmd /c "timeout /t 3 /nobreak > nul && start "" http://127.0.0.1:8000"

echo.
echo ------------------------------------------------------
echo SYSTEM IS ACTIVE AT: http://127.0.0.1:8000
echo Control + C to stop the server
echo ------------------------------------------------------
echo.

:: Run server in foreground to show logs
python manage.py runserver 0.0.0.0:8000
pause
