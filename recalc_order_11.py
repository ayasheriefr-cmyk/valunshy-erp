import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder

order = ManufacturingOrder.objects.filter(id=11).first() or ManufacturingOrder.objects.filter(order_number__icontains='11').first()

if order:
    print(f"--- RECALCULATING ORDER {order.order_number} ---")
    stages = order.stages.all()
    for stage in stages:
        # Trigger save to recalculate logic in signals
        stage.save()
        print(f"Stage: {stage.stage_name} | In: {stage.input_weight} | Out: {stage.output_weight} | Loss: {stage.loss_weight}")

print("Done.")
