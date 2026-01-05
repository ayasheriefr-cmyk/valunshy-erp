@echo off
title Valunshy ERP - Smart Manufacturing
color 0B

echo ======================================================
echo    STARTING VALUNSHY GOLD ERP SYSTEM
echo ======================================================

:: Launch regular dashboard and the new Smart Manufacturing Wizard
echo [1/2] Opening browser links...
start "" "http://127.0.0.1:8000/manufacturing/dashboard/"
start "" "http://127.0.0.1:8000/manufacturing/order/add/fast/"

:: Run the server
echo [2/2] Starting local server...
echo.
echo ------------------------------------------------------
echo SYSTEM IS ACTIVE AT: http://127.0.0.1:8000
echo PRESS CTRL+C TO STOP AT ANY TIME
echo ------------------------------------------------------
echo.

python manage.py runserver
pause
