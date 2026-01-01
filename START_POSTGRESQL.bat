@echo off
echo Starting Valunshy ERP with PostgreSQL...
echo.
echo Make sure PostgreSQL service is running!
echo.
timeout /t 3
start http://127.0.0.1:8000
python manage.py runserver 0.0.0.0:8000
pause
