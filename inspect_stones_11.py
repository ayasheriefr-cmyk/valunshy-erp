import os
import django
import sys
from django.db.models import Sum

# Force UTF-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder, OrderStone

def inspect_stones():
    # Try by order_number 11 specifically if possible, or search
    order = ManufacturingOrder.objects.filter(order_number='11').first()
    if not order:
        order = ManufacturingOrder.objects.filter(order_number__icontains='11').first()

    if not order:
        print("Order 11 not found.")
        return

    print(f"=== ORDER {order.order_number} STONES ===")
    print(f"Total Stone Weight (Order Field): {order.total_stone_weight}")
    
    order_stones = OrderStone.objects.filter(order=order)
    
    if not order_stones.exists():
        print("No stones found for this order.")
        return

    print(f"\n--- Stone Details ({order_stones.count()} records) ---")
    total_calculated_weight = 0
    
    for os_item in order_stones:
        stone_name = os_item.stone.name
        stone_type = os_item.stone.stone_type
        unit = os_item.stone.unit
        
        qty_req = os_item.quantity_required
        qty_iss = os_item.quantity_issued
        qty_broken = os_item.quantity_broken
        
        # Calculate weight contribution if applicable (e.g. if unit is carat, convert to gold weight if logic exists, 
        # but usually total_stone_weight represents the weight of stones themselves added to the piece?)
        # Let's check the property `weight_in_gold` which implies conversion for accounting, 
        # but usually we want to know the actual stone weight too.
        
        print(f"Stone: {stone_name} ({stone_type})")
        print(f"  Unit: {unit}")
        print(f"  Required: {qty_req} | Issued: {qty_iss} | Broken: {qty_broken}")
        
        # Check standard weight field if exists or calculate
        # The model has `weight_in_gold` property
        print(f"  Weight in Gold (Approx): {os_item.weight_in_gold}")
        
        stage = os_item.production_stage
        if stage:
            print(f"  Stage: {stage.stage_name} (ID: {stage.id})")
        else:
            print(f"  Stage: None")
        print("-" * 20)

if __name__ == "__main__":
    inspect_stones()
