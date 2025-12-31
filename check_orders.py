import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from manufacturing.models import ManufacturingOrder

print(f"Total Orders: {ManufacturingOrder.objects.count()}")
print("By Status:")
for s in ['pending', 'in_progress', 'completed', 'cancelled']:
    count = ManufacturingOrder.objects.filter(status=s).count()
    print(f"  {s}: {count}")
