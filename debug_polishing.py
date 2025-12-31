import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder

order = ManufacturingOrder.objects.filter(id=11).first() or ManufacturingOrder.objects.filter(order_number__icontains='11').first()

if order:
    print(f"--- ORDER {order.order_number} POLISHING STAGE ---")
    stages = order.stages.filter(stage_name='polishing')
    for stage in stages:
        print(f"ID: {stage.id} | Name: {stage.stage_name}")
        print(f"In: {stage.input_weight} | Out: {stage.output_weight}")
        print(f"Powder: {stage.powder_weight} | Loss: {stage.loss_weight}")
        print(f"Calculated (In - Out - P): {stage.input_weight - stage.output_weight - stage.powder_weight}")
