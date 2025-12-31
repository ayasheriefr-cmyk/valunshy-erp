import os
import django
import random
import datetime
from django.utils import timezone

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from sales.models import Invoice
from inventory.models import Item, Category
from core.models import Branch, Carat
from crm.models import Customer
from django.contrib.auth.models import User

def run():
    print("Starting Dashboard Data Population...")

    # 1. Ensure Basic Data
    branch, _ = Branch.objects.get_or_create(name="الفرع الرئيسي", defaults={'code': 'HQ'})
    customer, _ = Customer.objects.get_or_create(name="عميل نقدي", defaults={'phone': '0000000000'})
    category, _ = Category.objects.get_or_create(name="مجوهرات متنوعة")
    
    # Get a user for created_by
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser('admin_temp', 'admin@example.com', 'admin123')
    
    carats = {}
    for k in [18, 21, 24]:
        c, _ = Carat.objects.get_or_create(name=f"عيار {k}", defaults={'purity': k/24.0})
        carats[k] = c

    # 2. Create Inventory Items (For Pie Chart)
    print("Creating Inventory Items...")
    item_types = ['Ring', 'Bracelet', 'Necklace', 'Earring', 'Coin']
    
    # 21K Items
    for i in range(10):
        barcode = f"AUTO21-{i}{random.randint(100,999)}"
        if not Item.objects.filter(barcode=barcode).exists():
            Item.objects.create(
                barcode=barcode,
                name=f"{random.choice(item_types)} 21K",
                category=category,
                carat=carats[21],
                gross_weight=random.uniform(5, 15),
                net_gold_weight=random.uniform(4.5, 14),
                current_branch=branch,
                status='available'
            )

    # 18K Items
    for i in range(5):
        barcode = f"AUTO18-{i}{random.randint(100,999)}"
        if not Item.objects.filter(barcode=barcode).exists():
            Item.objects.create(
                barcode=barcode,
                name=f"{random.choice(item_types)} 18K",
                category=category,
                carat=carats[18],
                gross_weight=random.uniform(3, 8),
                net_gold_weight=random.uniform(2.8, 7.5),
                current_branch=branch,
                status='available'
            )

    # 3. Create Sales (Invoices) for Last 7 Days (For Line Chart)
    print("Generating Sales History...")
    today = timezone.now().date()
    
    for i in range(7):
        day = today - datetime.timedelta(days=i)
        # Create 1-3 invoices per day
        daily_invoices_count = random.randint(1, 4)
        
        for j in range(daily_invoices_count):
            amount = random.randint(5000, 45000)
            inv_num = f"INV-{day.strftime('%Y%m%d')}-{j}{random.randint(10,99)}"
            
            if not Invoice.objects.filter(invoice_number=inv_num).exists():
                inv = Invoice.objects.create(
                    invoice_number=inv_num,
                    customer=customer,
                    branch=branch,
                    grand_total=amount,
                    total_gold_value=amount * 0.9,
                    total_labor_value=amount * 0.1,
                    payment_method='cash',
                    created_by=admin_user
                )
                # Set specific date
                dt = timezone.make_aware(datetime.datetime.combine(day, datetime.time(12, 0)))
                Invoice.objects.filter(pk=inv.pk).update(created_at=dt)
                print(f"   Created Invoice {inv_num} for {amount} EGP on {day}")

    print("Success! Data populated. Refresh the dashboard.")

if __name__ == '__main__':
    run()
