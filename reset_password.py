import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User

# عرض جميع المستخدمين
print("\n=== المستخدمون المتاحون ===")
users = User.objects.all()
for u in users:
    print(f"ID: {u.id} | اسم المستخدم: {u.username} | البريد: {u.email} | مدير: {u.is_superuser}")

# إعادة تعيين كلمة المرور
print("\n=== إعادة تعيين كلمة المرور ===")
username = input("أدخل اسم المستخدم: ")
new_password = input("أدخل كلمة المرور الجديدة: ")

try:
    user = User.objects.get(username=username)
    user.set_password(new_password)
    user.save()
    print(f"\n✅ تم تغيير كلمة المرور بنجاح للمستخدم: {username}")
except User.DoesNotExist:
    print(f"\n❌ المستخدم {username} غير موجود")
