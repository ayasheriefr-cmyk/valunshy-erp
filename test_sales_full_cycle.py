import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory
from rest_framework.request import Request
from core.models import Branch, Carat, GoldPrice
from inventory.models import Item, Category
from sales.models import Invoice, SalesRepresentative
from sales.serializers import InvoiceSerializer
from finance.models import Account, FinanceSettings, JournalEntry
from finance.treasury_models import Treasury

print("=== Starting Sales Cycle Test ===")

# 1. Cleanup Old Test Data
print("Cleaning up old test data...")
Invoice.objects.filter(invoice_number__startswith="INV-MOB-").delete()
Item.objects.filter(barcode="TEST-ITEM-999").delete()
from finance.treasury_models import TreasuryTransaction
TreasuryTransaction.objects.all().delete()
User.objects.filter(username="test_sales_rep").delete()
Account.objects.filter(code__startswith="TEST-ACC").delete()

# 2. Setup Basic Data
print("Setting up basic data...")
user = User.objects.create_user(username="test_sales_rep", password="password")
branch, _ = Branch.objects.get_or_create(name="Main Branch", defaults={"is_main": True})
carat21, _ = Carat.objects.get_or_create(name="21K", purity=0.875)
GoldPrice.objects.create(carat=carat21, price_per_gram=3500)

item = Item.objects.create(
    barcode="TEST-ITEM-999",
    name="Test Gold Ring",
    carat=carat21,
    gross_weight=10.0,
    net_gold_weight=10.0,
    labor_fee_per_gram=50,
    status='available',
    current_branch=branch
)

# 3. Setup Finance Accounts
print("Setting up accounts...")
# Helper to create/get account
def get_acc(code, name, type):
    acc, _ = Account.objects.get_or_create(code=code, defaults={'name': name, 'account_type': type})
    return acc

acc_cash = get_acc("TEST-ACC-101", "Test Cash", "asset")
acc_sales = get_acc("TEST-ACC-401", "Test Sales Revenue", "revenue")
acc_vat = get_acc("TEST-ACC-201", "Test VAT Payable", "liability")
acc_inv = get_acc("TEST-ACC-102", "Test Gold Inventory", "asset")
acc_cog = get_acc("TEST-ACC-501", "Test Cost of Gold", "expense")

FinanceSettings.objects.update_or_create(id=1, defaults={
    'cash_account': acc_cash,
    'sales_revenue_account': acc_sales,
    'vat_account': acc_vat,
    'inventory_gold_account': acc_inv,
    'cost_of_gold_account': acc_cog
})

# 4. Setup Sales Rep
sales_rep = SalesRepresentative.objects.create(
    name="Ahmed Tester",
    user=user,
    commission_type='percentage',
    commission_rate=Decimal("1.0") # 1%
)

# 5. Prepare Serializer Data
print("Preparing Invoice Data...")
# Create a dummy API request context
class MockRequest:
    def __init__(self, user):
        self.user = user

context = {'request': MockRequest(user)}

data = {
    'branch': branch.id,
    'payment_method': 'cash',
    'items': [
        {
            'item': item.id,
            'sold_weight': 10.0,
            'sold_gold_price': 3500.0,
            'sold_labor_fee': 500.0 # Total labor
        }
    ],
    'returned_gold': [
        {
            'carat': carat21.id, # Using ID in real POST
            'weight': 2.0,
            'value': 7000.0 # 2g * 3500
        }
    ]
}

# 6. Run Serializer
print("Executing Serializer...")
serializer = InvoiceSerializer(data=data, context=context)
if serializer.is_valid():
    invoice = serializer.save()
    print(f"[OK] Invoice Created: {invoice.invoice_number}")
    print(f"   Grand Total: {invoice.grand_total}")
    print(f"   Exchange Value: {invoice.exchange_value_deducted}")
    print(f"   Status: {invoice.status}")
    
    # 7. Verifications
    print("\n--- Verifying Financials ---")
    
    # A. Check Totals
    # Gross = (10 * 3500) + 500 = 35500
    # VAT = 35500 * 0.15 = 5325
    # Grand Total = 35500 + 5325 = 40825
    expected_total = Decimal('40825.00')
    if abs(invoice.grand_total - expected_total) < 0.1:
        print("[OK] Grand Total Calculation: OK")
    else:
        print(f"[ERROR] Grand Total Mismatch! Expected {expected_total}, Got {invoice.grand_total}")

    # B. Check Journal Entry
    je = JournalEntry.objects.filter(reference=invoice.invoice_number).first()
    if je:
        print(f"[OK] Journal Entry Found: {str(je).encode('ascii', 'replace').decode()}")
        print("   Entries:")
        for entry in je.ledger_entries.all():
            print(f"   - {entry.account.name}: Debit={entry.debit}, Credit={entry.credit}")
        
        # Verify Cash Debit = 40825 - 7000 = 33825
        cash_entry = je.ledger_entries.filter(account=acc_cash, debit__gt=0).first()
        if cash_entry and abs(cash_entry.debit - Decimal('33825.00')) < 0.1:
             print("[OK] Cash Debit Split: OK")
        else:
             print(f"[ERROR] Cash Debit Error. Expected ~33825. Got {cash_entry.debit if cash_entry else 'None'}")
             
        # Verify Old Gold Debit = 7000
        gold_entry = je.ledger_entries.filter(account=acc_inv, debit__gt=0).first()
        if gold_entry and abs(gold_entry.debit - Decimal('7000.00')) < 0.1:
             print("[OK] Old Gold Debit: OK")
        else:
             print("[ERROR] Old Gold Debit Error.")

    else:
        print("[ERROR] NO Journal Entry Created!")

    # C. Check Commission
    sales_rep.refresh_from_db()
    # Commission = 1% of 40825 = 408.25
    print(f"   Sales Rep Commission: {sales_rep.total_commission}")
    if abs(sales_rep.total_commission - Decimal('408.25')) < 1: # approximate
        print("[OK] Commission Calculation: OK")
    else:
        print("[ERROR] Commission Mismatch")

else:
    print("[ERROR] Serializer Validation Failed!")
    for field, errors in serializer.errors.items():
        print(f"Field: {field}")
        for error in errors:
            print(f"  Error: {str(error).encode('ascii', 'replace').decode()}")

print("\n=== Test Finished ===")
