
import os
import django
import unicodedata
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from sales.models import SalesRepresentative

def slugify_arabic(text):
    # Very aggressive slugify to ensure ASCII only
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_') or "rep_user"

def fix_reps():
    reps = SalesRepresentative.objects.all()
    print(f"Checking {reps.count()} representatives...")
    
    for rep in reps:
        if not rep.user:
            username = slugify_arabic(rep.name)
            # Ensure uniqueness
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            password = "gold1234"
            user = User.objects.create_user(username=username, password=password)
            rep.user = user
            rep.save()
            print(f"Created user for rep ID {rep.id}:")
            print(f"  - Username: {username}")
            print(f"  - Password: {password}")
        else:
            print(f"Resetting password for Rep ID {rep.id}...")
            rep.user.set_password("gold1234")
            rep.user.save()

if __name__ == "__main__":
    fix_reps()
