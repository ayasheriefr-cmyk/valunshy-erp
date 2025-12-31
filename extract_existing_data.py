import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import Stone, Workshop

data = {
    'stones': [{'id': s.id, 'name': s.name, 'type': s.stone_type} for s in Stone.objects.all()],
    'workshops': [{'id': w.id, 'name': w.name} for w in Workshop.objects.all()]
}

with open('existing_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("Data exported to existing_data.json")
