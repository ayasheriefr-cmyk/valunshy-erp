import os
import sys
import django

# Fix encoding for Windows console to support Arabic and emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

# التحقق من المستخدمين الموجودين
print("=" * 60)
print("قائمة المستخدمين في النظام:")
print("=" * 60)

users = User.objects.all()
for user in users:
    print(f"\n👤 اسم المستخدم: {user.username}")
    print(f"   البريد الإلكتروني: {user.email}")
    print(f"   مدير؟: {'نعم ✅' if user.is_superuser else 'لا'}")
    print(f"   نشط؟: {'نعم ✅' if user.is_active else 'لا ❌'}")
    print(f"   تاريخ آخر تسجيل دخول: {user.last_login}")

print("\n" + "=" * 60)
print("اختبار تسجيل الدخول بكلمة المرور الجديدة:")
print("=" * 60)

# محاولة تسجيل الدخول
username = 'admin'
password = 'Radwa@01000'

user = authenticate(username=username, password=password)
if user is not None:
    print(f"✅ نجح تسجيل الدخول للمستخدم: {username}")
    print(f"   كلمة المرور '{password}' تعمل بشكل صحيح!")
else:
    print(f"❌ فشل تسجيل الدخول للمستخدم: {username}")
    print(f"   كلمة المرور '{password}' غير صحيحة!")
    print("\n🔄 سيتم إعادة تعيين كلمة المرور مرة أخرى...")
    
    try:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.is_active = True  # التأكد من أن الحساب نشط
        user.save()
        print(f"✅ تم إعادة تعيين كلمة المرور بنجاح")
        
        # اختبار مرة أخرى
        user = authenticate(username=username, password=password)
        if user is not None:
            print(f"✅ الآن تسجيل الدخول يعمل بشكل صحيح!")
        else:
            print(f"❌ لا يزال هناك مشكلة في تسجيل الدخول")
    except Exception as e:
        print(f"❌ خطأ: {e}")

print("\n" + "=" * 60)
