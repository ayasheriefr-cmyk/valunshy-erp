
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()
from django.contrib.auth.models import User
user = User.objects.filter(is_superuser=True).first()
if user:
    print(f"Superuser found: {user.username}")
else:
    print("No superuser found.")
    all_users = User.objects.all()
    for u in all_users:
        print(f"User: {u.username}")
