"""
Script to create test items for the mobile sales app
Run this with: python manage.py shell < create_test_items.py
"""

from inventory.models import Item, Branch, Carat
from decimal import Decimal
import random



print("=" * 50)
print("Creating Test Items")
print("=" * 50)

# Get or create Carats
carat_21, _ = Carat.objects.get_or_create(
    name="عيار 21",
    defaults={'purity': Decimal('0.8750')}
)

carat_18, _ = Carat.objects.get_or_create(
    name="عيار 18",
    defaults={'purity': Decimal('0.7500')}
)

carat_24, _ = Carat.objects.get_or_create(
    name="عيار 24",
    defaults={'purity': Decimal('0.9999')}
)

print("Carats checked")

# Get first branch
branch = Branch.objects.first()
if not branch:
    branch = Branch.objects.create(
        name="الفرع الرئيسي",
        address="الرياض",
        phone="0112345678"
    )
    print(f"Created Branch")
else:
    print(f"Using Branch")

# Sample item data (Keep Arabic Names for Data)
items_data = [
    # عيار 21
    {"name": "سلسلة ذهب", "carat": carat_21, "weight": "15.500"},
    {"name": "خاتم نسائي", "carat": carat_21, "weight": "3.250"},
    {"name": "أسورة", "carat": carat_21, "weight": "8.750"},
    {"name": "حلق ذهب", "carat": carat_21, "weight": "2.100"},
    {"name": "دبلة زواج", "carat": carat_21, "weight": "4.500"},
    
    # عيار 18
    {"name": "سلسلة رفيعة", "carat": carat_18, "weight": "5.250"},
    {"name": "خاتم رجالي", "carat": carat_18, "weight": "6.800"},
    {"name": "حلق صغير", "carat": carat_18, "weight": "1.500"},
    {"name": "أسورة أطفال", "carat": carat_18, "weight": "3.200"},
    {"name": "دلاية قلب", "carat": carat_18, "weight": "2.750"},
    
    # عيار 24
    {"name": "جنيه ذهب", "carat": carat_24, "weight": "8.000"},
    {"name": "نصف جنيه", "carat": carat_24, "weight": "4.000"},
]

created_count = 0
existing_count = 0

for idx, item_data in enumerate(items_data, start=1):
    barcode = f"GOLD-{random.randint(10000, 99999)}"
    
    # Check if item with similar name exists and is available
    existing = Item.objects.filter(
        name=item_data['name'],
        carat=item_data['carat'],
        status='available'
    ).first()
    
    if existing:
        existing_count += 1
        continue
    
    gross_weight = Decimal(item_data['weight'])
    net_gold_weight = gross_weight * item_data['carat'].purity
    
    item = Item.objects.create(
        barcode=barcode,
        name=item_data['name'],
        carat=item_data['carat'],
        gross_weight=gross_weight,
        stone_weight=Decimal('0.000'),
        net_gold_weight=net_gold_weight,
        labor_fee_per_gram=Decimal('10.00'),  # رسوم صياغة للجرام
        fixed_labor_fee=Decimal('50.00'),  # رسوم صياغة ثابتة
        status='available',
        current_branch=branch
    )
    
    created_count += 1
    # print(f"Created: {item.barcode}")

print("\n" + "=" * 50)
print(f"Created {created_count} new items")
if existing_count > 0:
    print(f"{existing_count} items already existed")
print("=" * 50)

# Summary
available_items = Item.objects.filter(status='available')
print(f"\nTotal Available Items: {available_items.count()}")


print("\n" + "=" * 50)
print("✅ جاهز للاستخدام!")
print("=" * 50)
