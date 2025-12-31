import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory, force_authenticate
from core.models import Branch, Carat, GoldPrice
from inventory.models import Item
from crm.models import Customer
from sales.api_views import CustomerOrderView
from sales.models import Invoice

print("=== Starting Customer Order App Test ===")

# 1. Cleanup
print("Cleaning up old test data...")
User.objects.filter(username="test_client_user").delete()
Item.objects.filter(barcode="CLIENT-ITEM-001").delete()
Invoice.objects.filter(invoice_number__startswith="ORD-APP-").delete()

# 2. Setup Data
print("Setting up User & Customer...")
user = User.objects.create_user(username="test_client_user", password="password")
customer = Customer.objects.create(
    name="Client One",
    phone="050000000",
    user=user # Link User to Customer
)

print("Setting up Product...")
branch, _ = Branch.objects.get_or_create(name="Main Branch", defaults={"is_main": True})
carat18, _ = Carat.objects.get_or_create(name="18K", purity=0.750)
GoldPrice.objects.create(carat=carat18, price_per_gram=3000)

item = Item.objects.create(
    barcode="CLIENT-ITEM-001",
    name="Diamond Ring 18K",
    carat=carat18,
    gross_weight=5.0,
    net_gold_weight=4.0, # 1g stones
    stone_weight=1.0, 
    labor_fee_per_gram=100,
    fixed_labor_fee=200,
    status='available',
    current_branch=branch
)

# 3. Test View
print("Simulating App Request...")
factory = APIRequestFactory()
view = CustomerOrderView.as_view()

# Make POST request with item_id
request = factory.post('/api/sales/api/order/create/', {'item_id': item.id}, format='json')
force_authenticate(request, user=user)

# 4. Execute
response = view(request)
print(f"Response Status: {response.status_code}")
print(f"Response Data: {response.data}")

if response.status_code == 201:
    order_num = response.data['order_number']
    print(f"[OK] Order Created: {order_num}")
    
    # 5. Verify Invoice
    inv = Invoice.objects.get(invoice_number=order_num)
    print(f"   Status: {inv.status}")
    print(f"   Customer: {inv.customer.name}")
    print(f"   Grand Total: {inv.grand_total}")
    
    # Calculate Expected Price
    # Gold: 4g * 3000 = 12000
    # Labor: (5g * 100) + 200 = 700
    # Subtotal: 12700
    # VAT (15%): 1905
    # Total: 14605
    expected = Decimal('14605.00')
    
    if abs(inv.grand_total - expected) < 1.0:
        print("[OK] Price Calculation matches expected (14605)")
    else:
        print(f"[ERROR] Price mismatch. Expected {expected}, Got {inv.grand_total}")
        
else:
    print("[ERROR] Failed to create order")

print("=== Test Finished ===")
