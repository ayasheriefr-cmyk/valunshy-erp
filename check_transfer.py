import os
import django
import sys

# Add project root to path
sys.path.append('c:\\Users\\COMPU LINE\\Desktop\\mm\\final\\gold')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import WorkshopTransfer

transfer_number = "1252"
exists = WorkshopTransfer.objects.filter(transfer_number=transfer_number).exists()

print(f"Transfer number '{transfer_number}' exists: {exists}")
