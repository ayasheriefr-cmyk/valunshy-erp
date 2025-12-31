import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ProductionStage

try:
    # Fix Stage 1 (First Qasem) to be LOSS
    stage1 = ProductionStage.objects.get(id=1)
    stage1.input_weight = 10.500
    stage1.output_weight = 10.000
    stage1.save()
    print(f"Stage 1 Updated: In {stage1.input_weight} -> Out {stage1.output_weight} | Loss: {stage1.loss_weight}")

    # Verify Stage 3 (Second Qasem) is GAIN
    stage3 = ProductionStage.objects.get(id=3)
    print(f"Stage 3 Check: In {stage3.input_weight} -> Out {stage3.output_weight} | Loss: {stage3.loss_weight}")

except Exception as e:
    print(e)
