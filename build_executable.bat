@echo off
chcp 65001 >nul
title بناء التطبيق التنفيذي - Build Executable
color 0E

echo ═══════════════════════════════════════════════════════════
echo       🔨 بناء تطبيق تنفيذي مستقل 🔨
echo          Valunshy ERP - Standalone Build
echo ═══════════════════════════════════════════════════════════
echo.
echo ⚠️  تنبيه: هذه العملية قد تستغرق 5-10 دقائق
echo.

:: التحقق من PyInstaller
echo [1/6] التحقق من أدوات البناء...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  PyInstaller غير مثبت. جاري التثبيت...
    pip install pyinstaller waitress
    if errorlevel 1 (
        echo ❌ فشل تثبيت PyInstaller
        pause
        exit /b 1
    )
)
echo ✅ أدوات البناء جاهزة

:: تنظيف البناءات السابقة
echo.
echo [2/6] تنظيف البناءات السابقة...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec" (
    echo      حذف ملفات spec القديمة...
)
echo ✅ تم التنظيف

:: إنشاء entry_point محدّث
echo.
echo [3/6] تحديث ملف التشغيل...
(
echo import os
echo import sys
echo import webbrowser
echo from threading import Timer
echo from waitress import serve
echo.
echo # Set base path for bundled app
echo if getattr^(sys, 'frozen', False^):
echo     base_path = sys._MEIPASS
echo else:
echo     base_path = os.path.dirname^(os.path.abspath^(__file__^)^)
echo.
echo os.environ.setdefault^('DJANGO_SETTINGS_MODULE', 'backend.settings'^)
echo.
echo def open_browser^(^):
echo     webbrowser.open_new^('http://127.0.0.1:8000/'^)
echo.
echo if __name__ == '__main__':
echo     from backend.wsgi import application
echo     
echo     print^("═══════════════════════════════════════════════════"^)
echo     print^("    🏆 نظام إدارة ورش الصياغة 🏆"^)
echo     print^("       Valunshy Jewelry ERP"^)
echo     print^("═══════════════════════════════════════════════════"^)
echo     print^(^)
echo     print^("⏳ جاري تشغيل النظام..."^)
echo     print^("🌐 سيتم فتح المتصفح خلال 2 ثانية..."^)
echo     print^(^)
echo     print^("═══════════════════════════════════════════════════"^)
echo     print^("   النظام يعمل على: http://127.0.0.1:8000"^)
echo     print^("   اضغط Ctrl + C للإيقاف"^)
echo     print^("═══════════════════════════════════════════════════"^)
echo     
echo     Timer^(2.0, open_browser^).start^(^)
echo     serve^(application, host='127.0.0.1', port=8000^)
) > entry_point_updated.py
echo ✅ تم تحديث ملف التشغيل

:: إنشاء spec file محسّن
echo.
echo [4/6] إنشاء ملف البناء...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo.
echo block_cipher = None
echo.
echo a = Analysis^(
echo     ['entry_point_updated.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[
echo         ^('templates', 'templates'^),
echo         ^('static', 'static'^),
echo         ^('db.sqlite3', '.'^),
echo         ^('backend', 'backend'^),
echo         ^('core', 'core'^),
echo         ^('crm', 'crm'^),
echo         ^('finance', 'finance'^),
echo         ^('inventory', 'inventory'^),
echo         ^('manufacturing', 'manufacturing'^),
echo         ^('sales', 'sales'^),
echo     ],
echo     hiddenimports=[
echo         'django',
echo         'django.contrib.admin',
echo         'django.contrib.auth',
echo         'django.contrib.contenttypes',
echo         'django.contrib.sessions',
echo         'django.contrib.messages',
echo         'django.contrib.staticfiles',
echo         'waitress',
echo         'backend',
echo         'backend.settings',
echo         'backend.wsgi',
echo     ],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=[],
echo     win_no_prefer_redirects=False,
echo     win_private_assemblies=False,
echo     cipher=block_cipher,
echo     noarchive=False,
echo ^)
echo.
echo pyz = PYZ^(a.pure, a.zipped_data, cipher=block_cipher^)
echo.
echo exe = EXE^(
echo     pyz,
echo     a.scripts,
echo     [],
echo     exclude_binaries=True,
echo     name='ValunshyERP',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     console=True,
echo     disable_windowed_traceback=False,
echo     argv_emulation=False,
echo     target_arch=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo ^)
echo.
echo coll = COLLECT^(
echo     exe,
echo     a.binaries,
echo     a.zipfiles,
echo     a.datas,
echo     strip=False,
echo     upx=True,
echo     upx_exclude=[],
echo     name='ValunshyERP',
echo ^)
) > valunshy_build.spec
echo ✅ تم إنشاء ملف البناء

:: بناء التطبيق
echo.
echo [5/6] بناء التطبيق التنفيذي...
echo      هذا قد يستغرق عدة دقائق، يرجى الانتظار...
echo.
pyinstaller --clean valunshy_build.spec
if errorlevel 1 (
    echo.
    echo ❌ فشل البناء! يرجى مراجعة الأخطاء أعلاه
    pause
    exit /b 1
)

:: نسخ قاعدة البيانات وإنشاء ملف تشغيل
echo.
echo [6/6] إنهاء الحزمة...
if exist "dist\ValunshyERP" (
    copy /Y db.sqlite3 "dist\ValunshyERP\" >nul
    
    echo @echo off > "dist\ValunshyERP\شغّل_النظام.bat"
    echo chcp 65001 ^>nul >> "dist\ValunshyERP\شغّل_النظام.bat"
    echo title Valunshy ERP >> "dist\ValunshyERP\شغّل_النظام.bat"
    echo cls >> "dist\ValunshyERP\شغّل_النظام.bat"
    echo ValunshyERP.exe >> "dist\ValunshyERP\شغّل_النظام.bat"
    
    echo ✅ تم البناء بنجاح!
) else (
    echo ❌ لم يتم إنشاء المجلد
    pause
    exit /b 1
)

echo.
echo ═══════════════════════════════════════════════════════════
echo    ✅ اكتمل البناء بنجاح! ✅
echo ═══════════════════════════════════════════════════════════
echo.
echo 📁 الموقع: dist\ValunshyERP
echo 📋 المحتويات:
echo    • ValunshyERP.exe - الملف التنفيذي الرئيسي
echo    • شغّل_النظام.bat - ملف التشغيل السريع
echo    • ملفات النظام الأخرى
echo.
echo 💡 يمكنك الآن:
echo    1. نسخ مجلد "dist\ValunshyERP" كاملاً لأي جهاز
echo    2. تشغيل "شغّل_النظام.bat" للبدء
echo    3. لا يحتاج الجهاز الهدف لتثبيت Python!
echo.
pause
explorer "dist\ValunshyERP"
