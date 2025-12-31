import os
import django
import sys
from django.db.models import Sum

# Force UTF-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder, ProductionStage

try:
    # Try ID 11 first, or look for order_number containing 11 if not found
    order = ManufacturingOrder.objects.filter(id=11).first()
    if not order:
        order = ManufacturingOrder.objects.filter(order_number__icontains='11').first()

    if order:
        print(f"--- ORDER {order.order_number} (ID: {order.id}) ---")
        print(f"Status: {order.status}")
        print(f"Input: {order.input_weight}")
        print(f"Output: {order.output_weight}")
        print(f"Powder: {order.powder_weight}")
        print(f"Scrap: {order.scrap_weight}")
        
        stages = order.stages.all()
        print(f"\n--- STAGES ({stages.count()}) ---")
        for stage in stages:
            print(f"Stage: {stage.stage_name} | Workshop: {stage.workshop}")
            print(f"  In: {stage.input_weight} | Out: {stage.output_weight}")
            print(f"  Powder: {stage.powder_weight} | Loss: {stage.loss_weight}")
            
    else:
        print("Order #11 not found.")

except Exception as e:
    print(f"Error: {e}")
