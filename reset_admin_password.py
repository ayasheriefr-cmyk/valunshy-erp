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

# إعادة تعيين كلمة المرور للمستخدم admin
try:
    user = User.objects.get(username='admin')
    user.set_password('Radwa@01000')
    user.save()
    print(f"✅ تم تغيير كلمة المرور بنجاح للمستخدم: admin")
    print(f"   اسم المستخدم: admin")
    print(f"   كلمة المرور الجديدة: Radwa@01000")
except User.DoesNotExist:
    print(f"❌ المستخدم admin غير موجود")
    print("   سيتم إنشاء مستخدم مدير جديد...")
    user = User.objects.create_superuser(
        username='admin',
        email='admin@gold.com',
        password='Radwa@01000'
    )
    print(f"✅ تم إنشاء مستخدم مدير جديد")
    print(f"   اسم المستخدم: admin")
    print(f"   كلمة المرور: Radwa@01000")
