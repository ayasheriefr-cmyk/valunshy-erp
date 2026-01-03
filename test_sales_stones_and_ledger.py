import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.contrib.auth.models import User
from core.models import Branch, Carat, GoldPrice
from inventory.models import Item, Category
from sales.models import Invoice, InvoiceItem, OldGoldReturn
from crm.models import Customer, CustomerTransaction
from django.utils import timezone

print("=== Starting Advanced Sales & Ledger Test ===")

# 1. Cleanup
print("Cleaning up...")
Invoice.objects.filter(invoice_number__startswith="TEST-INV-").delete()
Item.objects.filter(barcode__startswith="TEST-").delete()
Customer.objects.filter(phone="000000").delete()

# 2. Setup Data
print("Setting up data...")
branch, _ = Branch.objects.get_or_create(name="Main Test Branch")
carat21, _ = Carat.objects.get_or_create(name="21K", purity=0.875, defaults={'base_weight': 21})
if carat21.base_weight != 21:
    carat21.base_weight = 21
    carat21.save()

carat18, _ = Carat.objects.get_or_create(name="18K", purity=0.750, defaults={'base_weight': 18})
if carat18.base_weight != 18:
    carat18.base_weight = 18
    carat18.save()

GoldPrice.objects.get_or_create(carat=carat21, defaults={'price_per_gram': 3500})
GoldPrice.objects.get_or_create(carat=carat18, defaults={'price_per_gram': 3000})

customer = Customer.objects.create(name="Test Customer Ledger", phone="000000")

item_with_stones = Item.objects.create(
    barcode="TEST-STONE-001",
    name="Ring with Stones",
    carat=carat21,
    gross_weight=Decimal('5.0'),
    net_gold_weight=Decimal('4.8'),
    labor_fee_per_gram=50,
    fixed_labor_fee=100,
    default_stone_fee=250, # 250 fee
    status='available',
    current_branch=branch
)

# 3. Create Invoice
print("Creating Invoice with Stone Fees & Gold Barter...")
admin_user = User.objects.filter(is_superuser=True).first() or User.objects.create_superuser('admin_test', 'a@b.com', 'pass')

invoice = Invoice.objects.create(
    invoice_number="TEST-INV-001",
    customer=customer,
    branch=branch,
    payment_method='cash',
    created_by=admin_user,
    status='draft'
)

# Add item
inv_item = InvoiceItem.objects.create(
    invoice=invoice,
    item=item_with_stones,
    sold_weight=4.8,
    sold_gold_price=3500,
    sold_labor_fee=(5.0 * 50) + 100 # 350
    # sold_stone_fee should be auto-populated from item
)

# Verification of stone fee auto-population
inv_item.refresh_from_db()
print(f"Auto-populated Stone Fee: {inv_item.sold_stone_fee}")
if inv_item.sold_stone_fee == 250:
    print("[OK] Stone Fee auto-populated correctly.")
else:
    print(f"[ERROR] Stone Fee mismatch. Expected 250, got {inv_item.sold_stone_fee}")

# Add Gold Barter (Exchange)
# Exchange 2g of 18K gold worth 6000
OldGoldReturn.objects.create(
    invoice=invoice,
    carat=carat18,
    weight=2.0,
    value=6000
)

# 4. Trigger Totals Calculation
invoice.is_exchange = True
invoice.save() # Should trigger recalculation
invoice.refresh_from_db()

# Calculate Expected:
# Gold: 4.8 * 3500 = 16800
# Labor: 350
# Stones: 250
# Total Net: 17400
# Tax (15%): 2610
# Grand Total: 20010
print(f"Grand Total: {invoice.grand_total}")
if abs(invoice.grand_total - Decimal('20010.00')) < 0.1:
    print("[OK] Invoice Totals Calculation: OK")
else:
    print(f"[ERROR] Totals Mismatch. Got {invoice.grand_total}")

# 5. Confirm Invoice and check Ledger
print("Confirming Invoice...")
invoice.status = 'confirmed'
invoice.save() # Triggers ledger signal

customer.refresh_from_db()
print(f"Customer Balance: {customer.money_balance}")

# Expected Ledger:
# 1. Sale: Debit 20010
# 2. Barter: Credit 6000 (Cash) + Credit 2.0 (Gold 18)
# 3. Payment: Credit (20010 - 6000) = 14010
# Net Money Balance should be ~0 (if paid)
# Net Gold 18 Balance should be 2.0

if abs(customer.money_balance - Decimal('0')) < 0.1:
    print("[OK] Customer Cash Balance: OK")
else:
    print(f"[ERROR] Customer Cash Balance Mismatch: {customer.money_balance}")

if abs(customer.gold_balance_18 - Decimal('2.0')) < 0.001:
    print("[OK] Customer Gold 18 Balance: OK")
else:
    print(f"[ERROR] Customer Gold 18 Balance Mismatch: {customer.gold_balance_18}")

# Check ledger entries count
tc_count = CustomerTransaction.objects.filter(invoice=invoice).count()
print(f"Ledger Transactions for invoice: {tc_count}")
for tc in CustomerTransaction.objects.filter(invoice=invoice):
    print(f" - {tc.transaction_type}: Debit={tc.cash_debit}, Credit={tc.cash_credit}, GoldCredit={tc.gold_credit} ({tc.carat})")

if tc_count == 3: # Sale, Barter, Payment
    print("[OK] Ledger Transactions count: OK")

print("\n=== Test Finished ===")
