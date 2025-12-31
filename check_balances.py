import os
import django
import sys
from django.db.models import Sum

# Force UTF-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import Workshop, ManufacturingOrder

def check_balances():
    print("=== WORKSHOP BALANCES ACCOUNTS ===")
    workshops = Workshop.objects.all()
    
    if not workshops.exists():
        print("No workshops found.")
        return

    for ws in workshops:
        print(f"\nWorkshop: {ws.name} (Type: {ws.get_workshop_type_display()})")
        print(f"  Gold 18: {ws.gold_balance_18}")
        print(f"  Gold 21: {ws.gold_balance_21}")
        print(f"  Gold 24: {ws.gold_balance_24}")
        print(f"  Filings 18: {ws.filings_balance_18}")
        print(f"  Scrap 18: {ws.scrap_balance_18}")
        print(f"  Labor Balance: {ws.labor_balance}")
        
        # Check active orders
        active_orders = ws.orders.filter(status__in=['in_progress', 'casting', 'crafting', 'polishing'])
        if active_orders.exists():
             print(f"  Active Orders: {list(active_orders.values_list('order_number', flat=True))}")

    print("\n=== ORDER 11 WALLET INSPECTION ===")
    order_11 = ManufacturingOrder.objects.filter(order_number='11').first() or ManufacturingOrder.objects.filter(order_number__icontains='11').first()
    
    if order_11:
        print(f"Order: {order_11.order_number}")
        print(f"Assigned Workshop: {order_11.workshop}")
        if order_11.workshop:
            ws = order_11.workshop
            print(f"  -> Linked Workshop Balances: 18k={ws.gold_balance_18}, Labor={ws.labor_balance}")
        else:
            print("  -> No Main Workshop Assigned")
            
        print("  -> Stages Workshops:")
        for stage in order_11.stages.all():
             print(f"    Stage {stage.stage_name}: {stage.workshop}")

if __name__ == "__main__":
    check_balances()
