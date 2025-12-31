import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.treasury_models import Treasury

print("Checking Treasuries...")
for t in Treasury.objects.all():
    # Avoid unicode issues in print
    name_clean = "".join([c if ord(c) < 128 else "?" for c in t.name])
    print(f"ID: {t.id} | Name: {name_clean} | Code: {t.code} | Type: {t.treasury_type}")
