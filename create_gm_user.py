import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.contrib.auth.models import User
from core.user_management import UserProfile

print("=== Creating General Manager Account ===")

# Check if GM exists
gm_username = "gm"
gm_password = "admin123"

user, created = User.objects.get_or_create(
    username=gm_username,
    defaults={
        'first_name': 'General',
        'last_name': 'Manager',
        'email': 'gm@gold.com',
        'is_staff': True,
        'is_superuser': True,
    }
)

if created:
    user.set_password(gm_password)
    user.save()
    print(f"[OK] User created: {gm_username}")
else:
    print(f"[INFO] User already exists: {gm_username}")

# Create or update profile
profile, p_created = UserProfile.objects.get_or_create(
    user=user,
    defaults={'role': 'general_manager'}
)

if not p_created:
    profile.role = 'general_manager'
    profile.save()

print(f"[OK] Role set: General Manager")

print("\n" + "="*50)
print("GM Login Credentials:")
print("="*50)
print(f"Username: {gm_username}")
print(f"Password: {gm_password}")
print(f"Login URL: http://localhost:8000/admin/")
print(f"GM Dashboard: http://localhost:8000/admin/gm-dashboard/")
print("="*50)
