import os
import django
import sys

# Add project root to path
sys.path.append('c:\\Users\\COMPU LINE\\Desktop\\mm\\final\\gold')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import Workshop
from finance.treasury_models import Treasury
from crm.models import Customer
from inventory.models import Item

print("=== WORKSHOPS ===")
for w in Workshop.objects.all()[:5]:
    print(w.name)

print("\n=== TREASURIES ===")
for t in Treasury.objects.all()[:5]:
    print(t.name)

print("\n=== CUSTOMERS ===")
for c in Customer.objects.all()[:3]:
    print(c.name)
