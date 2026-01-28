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
from django.db import connection

print("=" * 70)
print("🔍 فحص شامل لمشكلة تسجيل الدخول")
print("=" * 70)

# 1. التحقق من الاتصال بقاعدة البيانات
print("\n1️⃣ التحقق من الاتصال بقاعدة البيانات...")
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("   ✅ الاتصال بقاعدة البيانات يعمل بشكل صحيح")
except Exception as e:
    print(f"   ❌ خطأ في الاتصال بقاعدة البيانات: {e}")
    sys.exit(1)

# 2. عرض جميع المستخدمين
print("\n2️⃣ قائمة جميع المستخدمين في النظام:")
users = User.objects.all()
print(f"   📊 عدد المستخدمين: {users.count()}")
for user in users:
    print(f"\n   👤 {user.username}")
    print(f"      - مدير: {'نعم ✅' if user.is_superuser else 'لا'}")
    print(f"      - نشط: {'نعم ✅' if user.is_active else 'لا ❌'}")
    print(f"      - الموظف: {'نعم' if user.is_staff else 'لا'}")

# 3. إعادة تعيين كلمة المرور للمستخدم admin
print("\n3️⃣ إعادة تعيين كلمة المرور للمستخدم admin...")
username = 'admin'
new_password = 'Radwa@01000'

try:
    user = User.objects.get(username=username)
    print(f"   ✅ تم العثور على المستخدم: {username}")
    
    # تعيين كلمة المرور الجديدة
    user.set_password(new_password)
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
    user.save()
    
    print(f"   ✅ تم تحديث كلمة المرور بنجاح")
    print(f"   ✅ تم تفعيل الحساب")
    print(f"   ✅ تم منح صلاحيات المدير")
    
except User.DoesNotExist:
    print(f"   ❌ المستخدم {username} غير موجود")
    print(f"   🔄 سيتم إنشاء مستخدم جديد...")
    
    user = User.objects.create_superuser(
        username=username,
        email='admin@gold.com',
        password=new_password
    )
    print(f"   ✅ تم إنشاء مستخدم مدير جديد بنجاح")

# 4. اختبار تسجيل الدخول
print("\n4️⃣ اختبار تسجيل الدخول...")
auth_user = authenticate(username=username, password=new_password)

if auth_user is not None:
    print(f"   ✅✅✅ نجح! كلمة المرور تعمل بشكل صحيح")
    print(f"   ✅ يمكنك الآن تسجيل الدخول باستخدام:")
    print(f"      👤 اسم المستخدم: {username}")
    print(f"      🔑 كلمة المرور: {new_password}")
else:
    print(f"   ❌ فشل تسجيل الدخول")
    print(f"   ⚠️ هناك مشكلة في المصادقة")

# 5. معلومات إضافية
print("\n5️⃣ معلومات مهمة:")
print(f"   📍 للدخول إلى لوحة التحكم: http://localhost:8000/admin/")
print(f"   📍 أو: http://127.0.0.1:8000/admin/")
print(f"   💡 تأكد من تشغيل السيرفر بالأمر: python manage.py runserver")

print("\n" + "=" * 70)
print("✅ انتهى الفحص")
print("=" * 70)
