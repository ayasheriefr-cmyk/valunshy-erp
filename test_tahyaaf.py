import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from inventory.models import Item, Category, Carat
from core.models import Branch

def test_tahyaaf():
    # Setup
    carat_18, _ = Carat.objects.get_or_create(name="18k", defaults={'purity': 0.750})
    category, _ = Category.objects.get_or_create(name="Test")
    branch, _ = Branch.objects.get_or_create(name="HQ")
    
    # Test Data: 0.005 carats stone
    # Formula: 0.005 * 0.2 = 0.001g gold
    # Gross: 10.000g -> Net should be 9.999g
    
    print("\n--- Testing Tahyaaf Calculation (1 Carat = 0.2 Gram) ---")
    
    test_item = Item.objects.create(
        barcode="TAH-TEST-1",
        name="Tahyaaf Sample",
        category=category,
        carat=carat_18,
        gross_weight=Decimal('10.000'),
        stone_weight=Decimal('0.005'), # 0.005 Centi/Carat
        current_branch=branch
    )
    
    print(f"Item Created: {test_item.name}")
    print(f"Gross Weight: {test_item.gross_weight} g")
    print(f"Stone Weight: {test_item.stone_weight} carats")
    print(f"Stone Equivalent in Gold: {test_item.stone_weight_in_gold} g")
    print(f"Calculated Net Gold: {test_item.net_gold_weight} g")
    
    expected_net = Decimal('10.000') - (Decimal('0.005') * Decimal('0.2'))
    if test_item.net_gold_weight == expected_net:
        print("SUCCESS: Tahyaaf calculation is accurate.")
    else:
        print(f"FAILED: Expected {expected_net}, got {test_item.net_gold_weight}")

if __name__ == '__main__':
    test_item = Item.objects.filter(barcode="TAH-TEST-1").delete()
    test_tahyaaf()
