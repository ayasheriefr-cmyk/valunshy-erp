import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import StoneCategoryGroup, StoneCut, StoneModel, StoneSize

def populate_stones_from_image():
    # 1. Ensure a Category Group exists
    group, _ = StoneCategoryGroup.objects.get_or_create(
        code=1,
        defaults={'name': 'ألماس', 'short_code': 'DIA'}
    )

    # Data from image
    data = [
        # (code, cut_code, cut_name, model_code, model_name, type, short, weight_from, weight_to, price)
        (1, 'MQ', 'Marquise', 'M10', 'Model 10', 'MQ .10', 'MQ', '0.080', '0.120', '950.00'),
        (2, 'MQ', 'Marquise', 'M3c', 'Model 3c', 'MQ.03', 'MQ', '0.010', '0.030', '950.00'),
        (3, 'MQ', 'Marquise', 'M5c', 'Model 5c', 'MQ.05', 'MQ', '0.050', '0.075', '950.00'),
        (4, 'PE', 'Pear', 'P3c', 'Model 3c', 'PEAR.03', 'PE', '0.010', '0.030', '950.00'),
        (5, 'PE', 'Pear', 'P10', 'Model 10', 'Pear.10', 'Pe', '0.080', '0.120', '950.00'), # Adjusted 8.000 to 0.080 as it's more logical
        (6, 'MQ', 'Marquise', 'M15', 'Model 15', 'MQ.15', 'MQ', '0.135', '0.170', '950.00'),
        (7, 'MQ', 'Marquise', 'M20', 'Model 20', 'MQ.20', 'MQ', '0.180', '0.230', '950.00'),
        (8, 'MQ', 'Marquise', 'M25', 'Model 25', 'MQ.25', 'MQ', '0.240', '0.280', '950.00'),
        (9, 'PE', 'Pear', 'P5c', 'Model 5c', 'Pear.05', 'Pe', '0.035', '0.075', '950.00'),
        (10, 'PE', 'Pear', 'P15', 'Model 15', 'Pear.15', 'Pe', '0.130', '0.180', '950.00'),
    ]

    for item in data:
        code, cut_code, cut_name, model_code, model_name, stone_type, short, w_from, w_to, price = item
        
        # Create/Get cut
        cut, _ = StoneCut.objects.get_or_create(
            code=cut_code,
            defaults={'name': cut_name, 'category_group': group}
        )
        
        # Create/Get model
        model, _ = StoneModel.objects.get_or_create(
            code=model_code,
            stone_cut=cut,
            defaults={'name': model_name}
        )
        
        # Create/Update stone size
        StoneSize.objects.update_or_create(
            code=code,
            defaults={
                'stone_cut': cut,
                'stone_model': model,
                'stone_type': stone_type,
                'short_code': short,
                'weight_from': Decimal(w_from),
                'weight_to': Decimal(w_to),
                'price_per_carat': Decimal(price),
                'color': 'G-H',
                'clarity': 'VVS'
            }
        )
        print(f"Processed stone code: {code}")

if __name__ == "__main__":
    populate_stones_from_image()
