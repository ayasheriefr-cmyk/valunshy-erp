
import os
import django
import sys

# Add project root to path if needed (though running from root usually works)
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder
from inventory.models import Category, Item
from core.models import Carat
from decimal import Decimal

def verify():
    print("Starting Verification...")
    
    # 1. Setup Test Data
    c21 = Carat.objects.filter(name__icontains='21').first()
    if not c21:
        print("Error: No Carat 21 found.")
        return

    # Ensure a category with prefix exists
    cat_name = 'Test Ring Category'
    cat, created = Category.objects.get_or_create(name=cat_name, defaults={'barcode_prefix': 'TST'})
    if cat.barcode_prefix != 'TST':
        cat.barcode_prefix = 'TST'
        cat.save()
    
    print(f"Using Category: {cat.name} with Prefix: {cat.barcode_prefix}")

    # 2. Create Order
    print("Creating Test Order...")
    order_num = 'TEST-BARCODE-GEN-01'
    # Cleanup previous run
    ManufacturingOrder.objects.filter(order_number=order_num).delete()
    
    order = ManufacturingOrder.objects.create(
        order_number=order_num,
        item_category=cat,
        carat=c21,
        input_weight=Decimal('10.000'),
        output_weight=Decimal('9.500'), # Some loss
        status='draft',
        auto_create_item=True
    )

    # 3. Complete Order
    print("Completing Order...")
    # Update status to completed to trigger signal
    # Note: Signal checks for status change. Since we just created it as draft, saving as completed is a change.
    order.status = 'completed'
    order.save()
    
    # Reload to get related item
    order.refresh_from_db()

    # 4. Check Result
    item = order.resulting_item
    if item:
        print(f"SUCCESS: Item created. ID: {item.id}")
        print(f"Barcode: {item.barcode}")
        
        if item.barcode.startswith('TST'):
            print("VERIFICATION PASSED: Barcode starts with expected prefix.")
        else:
            print(f"VERIFICATION FAILED: Barcode {item.barcode} does not start with 'TST'.")
        
        # Cleanup Item
        item.delete()
    else:
        print("VERIFICATION FAILED: No item created after order completion.")

    # Cleanup Order
    order.delete()
    # Cleanup Category if created
    if created:
        cat.delete()

if __name__ == '__main__':
    try:
        verify()
    except Exception as e:
        print(f"ERROR: {e}")
