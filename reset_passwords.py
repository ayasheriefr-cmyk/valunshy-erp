import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from sales.models import SalesRepresentative

def setup_test_users():
    # 1. Reset Admin Password
    try:
        admin_user = User.objects.get(username='admin')
        admin_user.set_password('admin123')
        admin_user.save()
        print("Admin password reset to: admin123")
        
        # Ensure linked
        rep, _ = SalesRepresentative.objects.get_or_create(name='Admin Manager')
        rep.user = admin_user
        rep.save()
    except User.DoesNotExist:
        print("Admin user not found, skipping reset.")

    # 2. Create dedicated Mandoob User
    mandoob_user, created = User.objects.get_or_create(username='mandoob')
    mandoob_user.set_password('gold123')
    mandoob_user.save()
    
    rep_mandoob, _ = SalesRepresentative.objects.get_or_create(
        name='مندوب تجريبي',
        defaults={'phone': '0123456789'}
    )
    rep_mandoob.user = mandoob_user
    rep_mandoob.save()
    
    print(f"Mandoob test user ready: \nUsername: mandoob \nPassword: gold123")

if __name__ == '__main__':
    setup_test_users()
