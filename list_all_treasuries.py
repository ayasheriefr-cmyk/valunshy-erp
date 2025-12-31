import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.treasury_models import Treasury

with open('treasuries_full_list.txt', 'w', encoding='utf-8') as f:
    for t in Treasury.objects.all().order_by('code'):
        f.write(f"Code: {t.code} | Name: {t.name}\n")
