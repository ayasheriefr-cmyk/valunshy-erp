@echo off
chcp 65001 >nul
title تحديث بيانات النظام - Sync ^& Migrate
color 0E

echo ═══════════════════════════════════════════════════════════
echo          🔄 تحديث بيانات النظام 🔄
echo ═══════════════════════════════════════════════════════════
echo.

echo [1/2] جاري فحص تحديثات قاعدة البيانات...
python manage.py migrate --noinput

echo.
echo [2/2] جاري تحديث الملفات الثابتة...
python manage.py collectstatic --noinput

echo.
echo ✅ تم تحديث النظام بنجاح!
echo.
pause
