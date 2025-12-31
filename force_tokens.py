import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from sales.models import SalesRepresentative

def ensure_tokens_and_users():
    users_to_check = [
        ('admin', 'admin123'),
        ('mandoob', 'gold123')
    ]
    
    for username, password in users_to_check:
        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        user.save()
        
        # Ensure SalesRep object linked
        rep, _ = SalesRepresentative.objects.get_or_create(
            user=user,
            defaults={'name': f"User {username}"}
        )
        
        # Force generate token
        token, _ = Token.objects.get_or_create(user=user)
        print(f"User: {username} | Password: {password} | Token: {token.key}")

if __name__ == '__main__':
    ensure_tokens_and_users()
