import os
import django
import random
from decimal import Decimal
from django.utils import timezone
import datetime

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder, ProductionStage, Workshop, ManufacturingCylinder, Stone, StoneCut, StoneSize, StoneModel, StoneCategoryGroup
from inventory.models import Item, Carat, Branch, MaterialTransfer
from sales.models import Invoice, InvoiceItem, SalesRepresentative
from crm.models import Customer
from finance.models import JournalEntry, LedgerEntry, Account, FinanceSettings
from django.contrib.auth.models import User

def simulate_data():
    print("START: 2025 Data Simulation (Arabic)...")
    
    # 1. Setup Basics
    user = User.objects.filter(is_superuser=True).first()
    branch = Branch.objects.first() or Branch.objects.create(name="الفرع الرئيسي")
    workshop = Workshop.objects.first() or Workshop.objects.create(name="ورشة الذهب العمومية", workshop_type='internal')
    carat_18 = Carat.objects.filter(name__contains='18').first()
    carat_21 = Carat.objects.filter(name__contains='21').first()
    
    if not (carat_18 and carat_21):
        print("❌ Carats 18/21 missing. Please run initial setup first.")
        return

    # Sales accounts for Ledger
    sales_acc = Account.objects.filter(name__contains='مبيعات').first() or Account.objects.create(name="حساب المبيعات", code="4101", account_type='revenue')
    cash_acc = Account.objects.filter(name__contains='خزينة').first() or Account.objects.create(name="الخزينة الرئيسية", code="1101", account_type='asset')

    customer_names = ["أحمد محمد", "سارة علي", "شركة الهدى", "محل جوهرة", "عميل نقدي", "إبراهيم محمود"]
    customers = []
    for i, name in enumerate(customer_names):
        cust, _ = Customer.objects.get_or_create(name=name, defaults={'phone': f'010{i:08d}'})
        customers.append(cust)

    item_names = ["خاتم لازوردى", "سلسلة كويتي", "انسيال فرزاتشي", "حلق ايطالي", "تراسي ليزر", "كوليه ملكي"]
    
    # 2. Loop through 2025 months
    global_counter = 1
    for month in range(1, 13):
        days_in_month = (datetime.date(2025, month % 12 + 1, 1) - datetime.timedelta(days=1)).day if month < 12 else 31
        
        # Num of sales per month: 15 to 25
        num_sales = random.randint(15, 25)
        print(f"MONTH: Simulating Month {month}/2025: {num_sales} Invoices")
        
        for _ in range(num_sales):
            day = random.randint(1, days_in_month)
            date_val = datetime.datetime(2025, month, day, 12, 0, tzinfo=datetime.timezone.utc)
            
            # Create Invoice
            invoice_num = f"INV-25-{month:02d}-{day:02d}-{global_counter:04d}"
            global_counter += 1
            cust = random.choice(customers)
            invoice = Invoice.objects.create(
                invoice_number=invoice_num,
                customer=cust,
                branch=branch,
                status='confirmed',
                payment_method='cash',
                created_by=user,
                confirmed_by=user
            )
            # Override created_at/confirmed_at because of auto_now_add
            Invoice.objects.filter(id=invoice.id).update(created_at=date_val, confirmed_at=date_val)
            
            # Create Items and associated MFG Orders
            num_items = random.randint(1, 4)
            total_gold = 0
            total_labor = 0
            
            for i in range(num_items):
                item_name = random.choice(item_names)
                weight = Decimal(str(round(random.uniform(4.0, 18.0), 3)))
                carat = random.choice([carat_18, carat_21])
                labor_price = Decimal(str(random.randint(200, 500)))
                gold_price = Decimal('3250') if '21' in carat.name else Decimal('2800')
                
                # Create Item in Inventory
                final_item = Item.objects.create(
                    name=f"{item_name} - {random.randint(100, 999)}",
                    barcode=f"B-{random.randint(100000, 999999)}",
                    carat=carat,
                    gross_weight=weight,
                    net_gold_weight=weight * Decimal('0.98'),
                    status='sold',
                    current_branch=branch
                )
                
                # Create Invoice Item
                item_gold_val = weight * gold_price
                item_labor_val = weight * labor_price
                item_total = item_gold_val + item_labor_val
                
                InvoiceItem.objects.create(
                    invoice=invoice,
                    item=final_item,
                    sold_weight=weight,
                    sold_gold_price=gold_price,
                    sold_labor_fee=labor_price,
                    subtotal=item_total
                )
                total_gold += item_gold_val
                total_labor += item_labor_val
                
                # Create MFG Order for this item (to show in analytics efficiency/production)
                mfg_order = ManufacturingOrder.objects.create(
                    order_number=f"MFG-25-{month:02d}-{global_counter:05d}-{i}",
                    item_name_pattern=item_name,
                    carat=carat,
                    input_weight=weight * Decimal('1.02'),
                    output_weight=weight,
                    status='completed',
                    workshop=workshop,
                    target_branch=branch,
                    manufacturing_pay=weight * (labor_price * Decimal('0.7')), # Workshop pay
                    factory_margin=weight * (labor_price * Decimal('0.3')), # Our profit
                    resulting_item=final_item
                )
                mfg_order.created_at = date_val - datetime.timedelta(days=random.randint(2, 5))
                mfg_order.save()
                
                # Add Stages
                stages = [("صب", 1), ("برد", 1), ("تلميع", 1), ("تركيب", 2)]
                current_time = mfg_order.created_at
                for s_name, dur in stages:
                    ProductionStage.objects.create(
                        order=mfg_order,
                        stage_name=s_name,
                        input_weight=weight * Decimal('1.01'),
                        output_weight=weight,
                        timestamp=current_time + datetime.timedelta(hours=dur)
                    )
                    current_time += datetime.timedelta(hours=dur)

            grand_total = total_gold + total_labor
            tax = grand_total * Decimal('0.15')
            invoice.total_gold_value = total_gold
            invoice.total_labor_value = total_labor
            invoice.total_tax = tax
            invoice.grand_total = grand_total + tax
            invoice.save()
            
            # Create Ledger Entry for Finance
            inv_final = invoice.grand_total
            journal = JournalEntry.objects.create(
                reference=invoice.invoice_number,
                description=f"مبيعات فاتورة رقم {invoice.invoice_number} - 2025",
                date=date_val.date()
            )
            LedgerEntry.objects.create(journal_entry=journal, account=cash_acc, debit=inv_final, credit=0)
            LedgerEntry.objects.create(journal_entry=journal, account=sales_acc, debit=0, credit=inv_final)

    print("DONE: Simulation Completed. 2025 is now full of gold transactions!")

if __name__ == "__main__":
    simulate_data()
