import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from crm.models import Supplier

suppliers = Supplier.objects.all().order_by('id')
print(f"Total Suppliers in DB: {suppliers.count()}")
print("-" * 30)
for s in suppliers:
    print(f"ID: {s.id} | Name: {s.name} | Phone: {s.phone} | Carat: {s.primary_carat}")
