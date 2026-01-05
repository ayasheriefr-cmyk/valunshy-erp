import os
import django
import datetime
import random
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from sales.models import Invoice, InvoiceItem, SalesRepresentative
from inventory.models import Item, Branch
from crm.models import Customer
from core.models import Carat

def generate_example_data():
    print("Starting example data generation for January 2026...")
    
    # 1. Get or create dependencies
    branch = Branch.objects.first()
    if not branch:
        print("Error: No branch found. Please create a branch first.")
        return

    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser('admin_temp', 'admin@example.com', 'admin123')

    customer, _ = Customer.objects.get_or_create(
        name="عميل تجريبي (مخطط الأهداف)",
        phone="0123456789",
        defaults={'email': 'test@example.com'}
    )

    sales_rep, _ = SalesRepresentative.objects.get_or_create(
        name="مندوب تجريبي",
        defaults={'commission_rate': Decimal('2.0')}
    )

    # 2. Get some items to sell
    items = list(Item.objects.filter(status='available')[:5])
    if not items:
        print("Warning: No available items found. Creating temporary items...")
        carat_18, _ = Carat.objects.get_or_create(name="18", defaults={'purity': 750})
        carat_21, _ = Carat.objects.get_or_create(name="21", defaults={'purity': 875})
        
        for i in range(5):
             item = Item.objects.create(
                 barcode=f"TEST-GOAL-{i}",
                 name=f"صنف تجريبي {i}",
                 carat=carat_18 if i % 2 == 0 else carat_21,
                 gross_weight=Decimal(random.uniform(2.0, 15.0)),
                 labor_fee_per_gram=Decimal('150'),
                 fixed_labor_fee=Decimal('500'),
                 status='available',
                 current_branch=branch
             )
             items.append(item)

    # 3. Create Invoices for January 2026
    start_date = datetime.datetime(2026, 1, 1, 10, 0)
    
    for i in range(10):
        # Stagger dates through January
        invoice_date = start_date + datetime.timedelta(days=i * 2, hours=random.randint(0, 8))
        
        invoice = Invoice.objects.create(
            invoice_number=f"INV-2026-EX-{i:03d}",
            customer=customer,
            branch=branch,
            created_by=admin_user,
            sales_rep=sales_rep,
            status='confirmed',
            payment_method='cash'
        )
        # Override auto_now_add for created_at if possible, or just use it in queries
        # Note: created_at has auto_now_add=True, so we might need to update it after creation
        Invoice.objects.filter(pk=invoice.pk).update(created_at=invoice_date)
        
        # Add 1-3 items per invoice
        selected_items = random.sample(items, random.randint(1, min(3, len(items))))
        for item in selected_items:
            gold_price = Decimal(random.randint(3000, 3500))
            labor_fee = item.gross_weight * Decimal(random.randint(100, 250)) + item.fixed_labor_fee
            
            InvoiceItem.objects.create(
                invoice=invoice,
                item=item,
                sold_weight=item.gross_weight,
                sold_gold_price=gold_price,
                sold_labor_fee=labor_fee,
                sold_stone_fee=item.default_stone_fee,
                sold_factory_cost=item.total_manufacturing_cost
            )
        
        invoice.calculate_totals()
        print(f"Created Invoice {invoice.invoice_number} dated {invoice_date.date()}")

    print("Success: 10 example invoices created for January 2026.")

if __name__ == "__main__":
    generate_example_data()
