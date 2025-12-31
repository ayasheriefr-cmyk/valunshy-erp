import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder

order = ManufacturingOrder.objects.filter(id=11).first() or ManufacturingOrder.objects.filter(order_number__icontains='11').first()

if order:
    print(f"--- ORDER MAIN DATA ---")
    print(f"Order #: {order.order_number}")
    print(f"Input Gold: {order.input_weight}")
    print(f"Output Gross: {order.output_weight}")
    print(f"Prop Stones: {order.total_stone_weight}")
    print(f"Net Gold: {order.output_weight - order.total_stone_weight}")
    print(f"Order Loss: {order.scrap_weight}")
    
    print(f"\n--- PRODUCTION STAGES FLOW ---")
    stages = order.stages.all().order_by('id')
    for i, stage in enumerate(stages, 1):
        loss_type = "GAIN (Ziayda)" if stage.loss_weight < 0 else "LOSS (Halk)"
        print(f"Step {i}: [{stage.stage_name}]")
        print(f"   In: {stage.input_weight} -> Out: {stage.output_weight}")
        print(f"   Diff: {stage.loss_weight} ({loss_type})")
        
        # Check continuity
        if i < len(stages):
            next_stage = stages[i]
            if stage.output_weight != next_stage.input_weight:
                gap = stage.output_weight - next_stage.input_weight
                print(f"   [WARNING] Gap to next stage: {gap}g lost/gained in transit!")

else:
    print("Order 11 not found")
