import os
import django
import json
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from crm.models import Supplier

def import_suppliers(json_file):
    if not os.path.exists(json_file):
        print(f"Error: {json_file} not found.")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    created_count = 0
    updated_count = 0

    for item in data:
        name = item.get('Name')
        phone = item.get('Mobile')
        address = item.get('Address')
        karat = item.get('Karat', '18')

        # Clean phone and address if they are placeholders
        if phone == '--' or phone == '00' or phone == '00000' or len(phone) < 5:
            phone = ""
        
        if address == '--':
            address = ""

        try:
            primary_carat = int(karat)
        except (ValueError, TypeError):
            primary_carat = 18

        # Try to find existing supplier by name
        supplier, created = Supplier.objects.get_or_create(
            name=name,
            defaults={
                'phone': phone,
                'address': address,
                'primary_carat': primary_carat,
                'supplier_type': 'factory'  # Default type
            }
        )

        if created:
            created_count += 1
            # print(f"Created: {name}") # Commented out to avoid encoding issues
        else:
            # Update existing supplier if fields are empty
            updated = False
            if not supplier.phone and phone:
                supplier.phone = phone
                updated = True
            if not supplier.address and address:
                supplier.address = address
                updated = True
            if updated:
                supplier.save()
                updated_count += 1
                # print(f"Updated: {name}")
            # else:
            #    print(f"Skipped (Already exists): {name}")

    print(f"\nImport finished!")
    print(f"Total processed: {len(data)}")
    print(f"Created: {created_count}")
    print(f"Updated: {updated_count}")

if __name__ == "__main__":
    import_suppliers('scraped_suppliers.json')
