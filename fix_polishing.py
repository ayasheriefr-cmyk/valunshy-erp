import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ProductionStage

try:
    stage = ProductionStage.objects.get(id=4)
    print(f"Before: In {stage.input_weight}, Out {stage.output_weight}, Loss {stage.loss_weight}")
    
    # Flip to make loss -0.4
    stage.input_weight = 10.000
    stage.output_weight = 10.400
    stage.save()
    
    print(f"After: In {stage.input_weight}, Out {stage.output_weight}, Loss {stage.loss_weight}")
except Exception as e:
    print(e)
