import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from core.models import Carat

with open('carats_list.txt', 'w', encoding='utf-8') as f:
    for c in Carat.objects.all():
        f.write(f"{c.id}: {c.name}\n")
