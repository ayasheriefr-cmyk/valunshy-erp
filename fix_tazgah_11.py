import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder

order = ManufacturingOrder.objects.filter(id=11).first() or ManufacturingOrder.objects.filter(order_number__icontains='11').first()

if order:
    print(f"--- ORDER {order.order_number} STAGES ---")
    stages = order.stages.all().order_by('id')
    for stage in stages:
        print(f"ID: {stage.id} | Name: {stage.stage_name} | In: {stage.input_weight} | Out: {stage.output_weight} | Loss: {stage.loss_weight}")
        
    # Find the one with ~ 0.5 loss
    target = None
    for stage in stages:
        if stage.stage_name == 'tazgah_qasem' and stage.loss_weight > 0.4:
            target = stage
            break
            
    if target:
        print(f"\nTarget Found: ID {target.id}")
        # Swap values to achieve -0.5
        # Current: In 10.5, Out 10.0 -> Loss 0.5
        # Target: Loss -0.5 -> Gain 0.5.
        # So In should be X, Out should be X + 0.5.
        # Assuming the weights were swapped? In=10.0, Out=10.5.
        
        target.input_weight = 10.000
        target.output_weight = 10.500
        target.save()
        print(f"UPDATED: In: {target.input_weight} | Out: {target.output_weight} | New Loss: {target.loss_weight}")
    else:
        print("\nTarget stage (with gain expected) not found.")
