from django.core.management.base import BaseCommand
from manufacturing.models import ManufacturingOrder
from inventory.models import Item, Category
from core.models import Carat, Branch
from crm.models import Customer
from sales.models import Invoice, InvoiceItem
from django.utils import timezone
from django.contrib.auth.models import User
import random
from decimal import Decimal
import datetime

class Command(BaseCommand):
    help = 'Populate database with dummy data: Items, Customers, Sales, and Orders'

    def handle(self, *args, **kwargs):
        self.stdout.write("Generating dummy data...")

        # 0. Ensure Admin User exists for 'created_by'
        user = User.objects.first()
        if not user:
            user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write("Created superuser 'admin'")

        # 1. Ensure Categories exist
        cat_ring, _ = Category.objects.get_or_create(name="خواتم", defaults={"description": "خواتم ذهب متنوعة"})
        cat_brace, _ = Category.objects.get_or_create(name="أساور", defaults={"description": "أساور وغوايش"})
        cat_set, _ = Category.objects.get_or_create(name="أطقم", defaults={"description": "أطقم كاملة"})
        cat_earring, _ = Category.objects.get_or_create(name="أقراط", defaults={"description": "حلقان وتراجي"})

        # 2. Ensure Carats exist
        carat21, _ = Carat.objects.get_or_create(name="21K", defaults={"purity": 0.875})
        carat18, _ = Carat.objects.get_or_create(name="18K", defaults={"purity": 0.750})
        carat24, _ = Carat.objects.get_or_create(name="24K", defaults={"purity": 0.999})

        # 3. Ensure Branch exists
        branch, _ = Branch.objects.get_or_create(name="الفرع الرئيسي", defaults={"location": "الرياض - العليا"})

        # 4. Create Customers
        customer_names = [
            ("أحمد محمد", "0501234567"),
            ("سارة علي", "0509876543"),
            ("شركة الذهب المتطورة", "0555555555"),
            ("خالد عبدالله", "0543219876"),
            ("منال حسن", "0567891234")
        ]
        
        customers = []
        for name, phone in customer_names:
            cust, created = Customer.objects.get_or_create(phone=phone, defaults={"name": name})
            customers.append(cust)
        self.stdout.write(f"Ensured {len(customers)} customers exist.")

        # 5. Create Inventory Items (More Items)
        item_definitions = [
            ("خاتم لازوردي", cat_ring, carat21, 3.5, 5.0),
            ("دبلة سادة", cat_ring, carat21, 2.0, 6.0),
            ("غوايش صب", cat_brace, carat21, 10.0, 20.0),
            ("سلسلة كارتيه", cat_set, carat18, 5.0, 15.0),
            ("خاتم الماس", cat_ring, carat18, 2.5, 5.0),
            ("طقم بحريني", cat_set, carat21, 30.0, 60.0),
            ("انسيال خفيف", cat_brace, carat18, 3.0, 8.0),
            ("حلق طويل", cat_earring, carat21, 4.0, 7.0),
            ("سبيكة", cat_set, carat24, 10.0, 10.0), # 10g bar
        ]

        # Generate 50 items
        existing_items_count = Item.objects.count()
        if existing_items_count < 50:
            for i in range(50):
                def_name, def_cat, def_carat, min_w, max_w = random.choice(item_definitions)
                weight = round(random.uniform(min_w, max_w), 2)
                barcode = f"GOLD-{random.randint(10000, 99999)}"
                
                if not Item.objects.filter(barcode=barcode).exists():
                    Item.objects.create(
                        barcode=barcode,
                        name=f"{def_name} {''.join(random.choices('ABCDEF', k=2))}", # Unique-ish name
                        category=def_cat,
                        carat=def_carat,
                        gross_weight=Decimal(weight),
                        net_gold_weight=Decimal(weight),
                        status='available',
                        current_branch=branch,
                        labor_fee_per_gram=Decimal(random.randint(100, 300))
                    )
            self.stdout.write("Added inventory items to reach approx 50 items.")

        # 6. Create Sales (Invoices)
        # Create 10 invoices
        gold_price_21 = Decimal(250) # Approx price
        gold_price_18 = Decimal(215)
        
        for i in range(10):
            inv_num = f"INV-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            customer = random.choice(customers)
            
            # Pick 1-3 items to sell
            items_to_sell = Item.objects.filter(status='available').order_by('?')[:random.randint(1, 3)]
            if not items_to_sell:
                continue

            invoice = Invoice.objects.create(
                invoice_number=inv_num,
                customer=customer,
                branch=branch,
                created_by=user,
                payment_method=random.choice(['cash', 'card'])
            )

            total_gold = Decimal(0)
            total_labor = Decimal(0)

            for item in items_to_sell:
                price_per_gram = gold_price_21 if item.carat.name == '21K' else gold_price_18
                item_gold_price = item.net_gold_weight * price_per_gram
                item_labor = item.net_gold_weight * item.labor_fee_per_gram
                
                subtotal = item_gold_price + item_labor
                
                InvoiceItem.objects.create(
                    invoice=invoice,
                    item=item,
                    sold_weight=item.net_gold_weight,
                    sold_gold_price=price_per_gram,
                    sold_labor_fee=item.labor_fee_per_gram,
                    subtotal=subtotal
                )
                
                # Update item status
                item.status = 'sold'
                item.save()

                total_gold += item_gold_price
                total_labor += item_labor

            invoice.total_gold_value = total_gold
            invoice.total_labor_value = total_labor
            invoice.total_tax = (total_gold + total_labor) * Decimal('0.15')
            invoice.grand_total = total_gold + total_labor + invoice.total_tax
            invoice.save()

            # Update Customer Stats
            customer.total_purchases_value += invoice.grand_total
            customer.save()

        self.stdout.write("Created dummy invoices and updated item statuses.")

        # 7. Create Manufacturing Orders (All statuses)
        statuses = [
            ('draft', 'مسودة', 0, 0),
            ('casting', 'سبك', 1000, 992),
            ('crafting', 'صياغة', 500, 490),
            ('polishing', 'تلميع / واجهة', 250, 248),
            ('completed', 'مكتمل / جاهز', 1500, 1450),
            ('cancelled', 'ملغى', 0, 0)
        ]

        count_orders = 0
        for status, desc, inp, out in statuses:
            order_num = f"ORD-{random.randint(1000, 9999)}-{status[:3].upper()}"
            if not ManufacturingOrder.objects.filter(order_number=order_num).exists():
                scrap = Decimal(inp) - Decimal(out) if inp > 0 else 0
                
                ManufacturingOrder.objects.create(
                    order_number=order_num,
                    carat=carat21,
                    status=status,
                    assigned_technician="محمد الفني",
                    input_weight=Decimal(inp),
                    output_weight=Decimal(out),
                    scrap_weight=scrap
                )
                count_orders += 1
        
        self.stdout.write(f"Created {count_orders} manufacturing orders.")
        self.stdout.write(self.style.SUCCESS("Data generation complete! Dashboard should now show real numbers."))
