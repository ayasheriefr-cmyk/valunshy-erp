from django.conf import settings
import django
import os
import sys
from decimal import Decimal

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from inventory.models import Item, Category
from core.models import Carat, Branch, GoldPrice

def create_test_data():
    print("Starting Test Data Creation...")

    # 1. Ensure Branch exists
    # Branch has name, location, is_main
    branch, created = Branch.objects.get_or_create(
        name="Main Showroom",
        defaults={'location': 'Downtown, Cairo', 'is_main': True}
    )
    print(f"Branch: {branch.name} (Created: {created})")

    # 2. Ensure Carats exist
    carat_21, _ = Carat.objects.get_or_create(name="21K", defaults={'purity': 0.875})
    carat_18, _ = Carat.objects.get_or_create(name="18K", defaults={'purity': 0.750})
    carat_24, _ = Carat.objects.get_or_create(name="24K", defaults={'purity': 0.999})
    print("Carats Verified")

    # 2.5 Ensure Gold Prices exist (for logical checkout)
    # Set dummy prices if not exists: 21K=4000, 18K=3428, 24K=4571
    GoldPrice.objects.update_or_create(carat=carat_21, defaults={'price_per_gram': Decimal('4000.00')})
    GoldPrice.objects.update_or_create(carat=carat_18, defaults={'price_per_gram': Decimal('3428.00')})
    GoldPrice.objects.update_or_create(carat=carat_24, defaults={'price_per_gram': Decimal('4571.00')})
    print("Gold Prices Verified")

    # 3. Ensure Categories exist
    cat_ring, _ = Category.objects.get_or_create(name="Khawatim (Rings)")
    cat_bracelet, _ = Category.objects.get_or_create(name="Ghawyesh (Bracelets)")
    cat_necklace, _ = Category.objects.get_or_create(name="Salasel (Necklaces)")
    print("Categories Verified")

    # 4. Create Items
    items_data = [
        {
            'barcode': 'TEST-RING-001',
            'name': 'Lazurde Gold Ring 21K',
            'category': cat_ring,
            'carat': carat_21,
            'gross_weight': Decimal('5.500'),
            'stone_weight': Decimal('0.000'),
            'labor_fee_per_gram': Decimal('150.00'),
            'fixed_labor_fee': Decimal('0.00'),
            'status': 'available',
            'image_path': 'items/ring_test.jpg' # Placeholder
        },
        {
            'barcode': 'TEST-BRACELET-002',
            'name': 'Classic 18K Bracelet',
            'category': cat_bracelet,
            'carat': carat_18,
            'gross_weight': Decimal('12.750'),
            'stone_weight': Decimal('0.250'), # Has stones
            'labor_fee_per_gram': Decimal('200.00'),
            'fixed_labor_fee': Decimal('500.00'), # Premium design
            'status': 'available',
            'image_path': 'items/bracelet_test.jpg'
        },
        {
            'barcode': 'TEST-NECKLACE-003',
            'name': 'Royal 21K Necklace Set',
            'category': cat_necklace,
            'carat': carat_21,
            'gross_weight': Decimal('45.000'),
            'stone_weight': Decimal('0.000'),
            'labor_fee_per_gram': Decimal('120.00'),
            'fixed_labor_fee': Decimal('0.00'),
            'status': 'available',
            'image_path': 'items/necklace_test.jpg'
        }
    ]

    for data in items_data:
        # Calculate net weight automatically via save() logic or set explicitly
        # Model save() has: net_gold = gross - (stone * 0.2)
        
        item, created = Item.objects.update_or_create(
            barcode=data['barcode'],
            defaults={
                'name': data['name'],
                'category': data['category'],
                'carat': data['carat'],
                'gross_weight': data['gross_weight'],
                'stone_weight': data['stone_weight'],
                'labor_fee_per_gram': data['labor_fee_per_gram'],
                'fixed_labor_fee': data['fixed_labor_fee'],
                'status': data['status'],
                'current_branch': branch,
                'retail_margin': Decimal('1.05') # 5% default margin
            }
        )
        if created:
            print(f"Created Item: {item.name}")
        else:
            print(f"Updated Item: {item.name}")

    print("All 3 Test Items Created Successfully!")

if __name__ == "__main__":
    create_test_data()
