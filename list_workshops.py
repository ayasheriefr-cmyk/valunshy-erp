import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import Workshop

with open('workshops_list.txt', 'w', encoding='utf-8') as f:
    for w in Workshop.objects.all():
        f.write(f"{w.id}: {w.name}\n")
