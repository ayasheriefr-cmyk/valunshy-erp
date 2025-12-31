
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from sales.models import SalesRepresentative

def update_admin():
    try:
        user = User.objects.get(username='admin')
        user.set_password('radwa01000')
        user.save()
        print("Password updated for 'admin' to 'radwa01000'")
        
        # Ensure linked to a rep
        rep, created = SalesRepresentative.objects.get_or_create(
            user=user,
            defaults={'name': 'Admin Rep', 'phone': '01000000000'}
        )
        if not created:
            rep.user = user
            rep.save()
        print(f"User 'admin' successfully linked to Sales Rep ID {rep.id}")

    except User.DoesNotExist:
        print("Error: User 'admin' not found.")

if __name__ == "__main__":
    update_admin()
