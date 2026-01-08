import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from sales.models import Invoice, InvoiceItem
from inventory.models import Item, Category
from core.models import Carat, Branch
from django.contrib.auth.models import User

def verify_invoice_calculations():
    print("=== Testing Invoice Calculations ===")
    
    # 1. Setup minimal data
    user = User.objects.first()
    branch = Branch.objects.first()
    category = Category.objects.get_or_create(name="Test Category")[0]
    carat = Carat.objects.get_or_create(name="21K", purity=0.875)[0]
    
    # Create a test item
    item1 = Item.objects.create(
        barcode="TEST001",
        name="Test Ring",
        category=category,
        carat=carat,
        gross_weight=Decimal('10.500'),
        stone_weight=Decimal('0.500'),
        net_gold_weight=Decimal('10.000'),
        status='available'
    )
    
    # 2. Create Invoice
    invoice = Invoice.objects.create(
        invoice_number="INV-TEST-999",
        branch=branch,
        created_by=user,
        status='draft'
    )
    
    # 3. Add Item to Invoice
    # Sold weight 10.0, Price 3000, Labor 500, Stones 200
    inv_item = InvoiceItem.objects.create(
        invoice=invoice,
        item=item1,
        sold_weight=Decimal('10.000'),
        sold_gold_price=Decimal('3000'),
        sold_labor_fee=Decimal('500'),
        sold_stone_fee=Decimal('200')
    )
    
    # Recalculate
    invoice.calculate_totals()
    
    print(f"Invoice: {invoice.invoice_number}")
    print(f"Total Gold Weight: {invoice.total_gold_weight} (Expected: 10.000)")
    print(f"Total Labor Value: {invoice.total_labor_value} (Expected: 500.00)")
    print(f"Total Stones Value: {invoice.total_stones_value} (Expected: 200.00)")
    print(f"Combined Labor (Property): {invoice.total_combined_labor} (Expected: 700.00)")
    
    success = (
        invoice.total_gold_weight == Decimal('10.000') and
        invoice.total_combined_labor == Decimal('700.00')
    )
    
    if success:
        print("\n[SUCCESS] Invoice calculations are correct!")
    else:
        print("\n[FAILURE] Discrepancy detected in calculations.")
    
    # Cleanup
    inv_item.delete()
    invoice.delete()
    item1.delete()

if __name__ == "__main__":
    verify_invoice_calculations()
