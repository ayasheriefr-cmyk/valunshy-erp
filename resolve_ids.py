import os
import django
import sys

sys.path.append('c:\\Users\\COMPU LINE\\Desktop\\mm\\final\\gold')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from inventory.models import Carat
from manufacturing.models import Workshop

c = Carat.objects.get(id=12)
w1 = Workshop.objects.get(id=7)
w2 = Workshop.objects.get(id=8)

# Print safe rep
print(f"Carat: {c.pk}") # We can guess 18/21 or try to decode if safe
print(f"W1: {w1.pk}")
print(f"W2: {w2.pk}")

# Try to print name encoded
try:
    print(f"Carat Name: {c.name.encode('utf-8')}")
except:
    pass
