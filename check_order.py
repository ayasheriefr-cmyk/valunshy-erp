import os
import django
import sys

# Add project root to path
sys.path.append('c:\\Users\\COMPU LINE\\Desktop\\mm\\final\\gold')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder

order_number = "1252"
exists = ManufacturingOrder.objects.filter(order_number=order_number).exists()

print(f"Manufacturing Order number '{order_number}' exists: {exists}")
