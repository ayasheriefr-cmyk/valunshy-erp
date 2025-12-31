import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from sales.models import SalesRepresentative

try:
    # Get the admin user
    user = User.objects.get(username='admin')
    
    # Check if rep exists or create one
    rep, created = SalesRepresentative.objects.get_or_create(
        name='Admin Manager',
        defaults={
            'phone': '01000000000',
            'commission_rate': 0
        }
    )
    
    # Link them
    rep.user = user
    rep.save()
    
    print(f"Successfully linked User '{user.username}' to Sales Rep '{rep.name}'")

except User.DoesNotExist:
    print("Error: User 'admin' does not exist. Please create a superuser first.")
except Exception as e:
    print(f"Error: {e}")
