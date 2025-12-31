import os
import django
import sys
from decimal import Decimal

# Force UTF-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder

def inspect_order():
    # Try by order_number 11 specifically if possible, or search
    # The user said "Order 11", likely order_number="11"
    order = ManufacturingOrder.objects.filter(order_number='11').first()
    if not order:
        order = ManufacturingOrder.objects.filter(order_number__icontains='11').first()

    if not order:
        print("Order 11 not found.")
        return

    print(f"=== ORDER SUMMARY: {order.order_number} ===")
    print(f"ID: {order.id}")
    print(f"Status (Code): {order.status}")
    print(f"Status (Display): {order.get_status_display()}")
    try:
        print(f"Carat: {order.carat}")
    except:
        print(f"Carat ID: {order.carat_id}")

    print(f"Input Weight (Gold): {order.input_weight}")
    print(f"Output Weight: {order.output_weight}")
    print(f"Loss Weight: {order.loss_weight}")
    print(f"Scrap Weight: {order.scrap_weight}")
    print(f"Powder Weight: {order.powder_weight}")
    
    print("\n--- STAGES ---")
    stages = order.stages.all().order_by('id')
    for stage in stages:
        print(f"Stage: {stage.stage_name} (ID: {stage.id})")
        try:
             print(f"  Worker: {stage.workshop}")
        except:
             print(f"  Worker ID: {stage.workshop_id}")
             
        print(f"  Input: {stage.input_weight}")
        print(f"  Output: {stage.output_weight}")
        print(f"  Loss: {stage.loss_weight}")
        print(f"  Powder: {stage.powder_weight}")
        print("-" * 30)

if __name__ == "__main__":
    inspect_order()
