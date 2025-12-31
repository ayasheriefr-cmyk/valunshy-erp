import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder, Workshop
from django.db import transaction

def fix_balances():
    # Find all active orders (not draft, not completed, not cancelled)
    active_orders = ManufacturingOrder.objects.filter(status='in_progress', input_weight__gt=0)
    print(f"Found {active_orders.count()} active orders to check.")
    
    for order in active_orders:
        if not order.workshop:
            continue
            
        workshop = order.workshop
        weight = order.input_weight
        carat_name = order.carat.name
        
        print(f"Processing Order {order.order_number}: {weight}g")
        
        with transaction.atomic():
            if '18' in carat_name:
                workshop.gold_balance_18 += weight
                field = 'gold_balance_18'
            elif '21' in carat_name:
                workshop.gold_balance_21 += weight
                field = 'gold_balance_21'
            elif '24' in carat_name:
                workshop.gold_balance_24 += weight
                field = 'gold_balance_24'
            else:
                print(f"  Skipping: Unsupported carat {carat_name}")
                continue
                
            workshop.save()
            print(f"  Done. Workshop ID {workshop.id} balance increased.")

if __name__ == "__main__":
    fix_balances()
