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

# بيانات المستخدم
username = 'admin'
password = 'Radwa@01000'
email = 'admin@gold.com'

# حذف المستخدم admin إذا كان موجوداً وإعادة إنشائه
try:
    old_user = User.objects.get(username=username)
    old_user.delete()
    print(f"🗑️ تم حذف المستخدم القديم: {username}")
except User.DoesNotExist:
    print(f"ℹ️ المستخدم {username} غير موجود، سيتم إنشاؤه")

# إنشاء مستخدم جديد
user = User.objects.create_superuser(
    username=username,
    email=email,
    password=password
)
print(f"\n{'='*60}")
print(f"✅ تم إنشاء مستخدم المدير بنجاح!")
print(f"{'='*60}")
print(f"🔑 اسم المستخدم: {username}")
print(f"🔑 كلمة المرور: {password}")
print(f"📧 البريد الإلكتروني: {email}")
print(f"{'='*60}")
