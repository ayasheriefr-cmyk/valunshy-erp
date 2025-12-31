import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import StoneCategoryGroup, StoneCut, StoneModel, StoneSize

def populate_stones_v2():
    group, _ = StoneCategoryGroup.objects.get_or_create(
        code=1,
        defaults={'name': 'ألماس', 'short_code': 'DIA'}
    )

    # Data extracted from images
    # Tuple: (code, cut_code, cut_name, model_code, model_name, stone_type, short_code, weight_from, weight_to, size_mm, price)
    data = [
        # Page 2
        (11, 'PE', 'Pear', 'P20', 'Model 20', 'Pear0.20', 'Pe', '0.180', '0.220', '0.000', '950.00'),
        (12, 'PE', 'Pear', 'P25', 'Model 25', 'Pear0.25', 'Pe', '0.230', '0.270', '0.000', '950.00'),
        (13, 'EM', 'Emerald', 'E3', 'Model E3', 'Em.03', 'Em', '0.010', '0.030', '0.000', '950.00'),
        (14, 'EM', 'Emerald', 'E5c', 'Model E5c', 'Em.05', 'Em', '0.040', '0.075', '0.000', '950.00'),
        (15, 'EM', 'Emerald', 'E10', 'Model E10', 'Em.10', 'Em', '0.080', '0.125', '0.000', '950.00'),
        (16, 'EM', 'Emerald', 'E15', 'Model E15', 'Em.15', 'Em', '0.130', '0.175', '0.000', '950.00'),
        (17, 'EM', 'Emerald', 'E20', 'Model E20', 'Em.20', 'Em', '0.180', '0.225', '0.000', '950.00'),
        (18, 'EM', 'Emerald', 'E25', 'Model E25', 'Em.25', 'Em', '0.230', '0.275', '0.000', '950.00'),
        (20, 'OV', 'Oval', 'O25', 'Model O25', 'Oval.25', 'Ov', '0.230', '0.275', '0.000', '950.00'),
        (21, 'BG', 'Baguette', 'BG', 'Model BG', 'BG-2', 'BG', '0.010', '0.030', '0.000', '950.00'),
        
        # Page 3
        (22, 'BG', 'Baguette', 'BG', 'Model BG', 'BG+2', 'BG', '0.040', '0.080', '0.000', '950.00'),
        (23, 'BG', 'Baguette', 'BG', 'Model BG', 'BG+3', 'BG', '0.085', '0.100', '0.000', '950.00'),
        (24, 'BG', 'Baguette', 'BG', 'Model BG', 'BG+4', 'BG', '0.120', '0.150', '0.000', '950.00'),
        (25, 'PR', 'Princess', 'PR', 'Model PR', 'PRINCESS', 'PR', '0.010', '0.200', '0.000', '950.00'),
        (26, 'CU', 'Cushion', 'CU', 'Model CU', 'CUSHION', 'CU', '0.010', '0.200', '0.000', '950.00'),
        (27, 'BC', 'Bicut', 'BC', 'Model BC', 'BICUT', 'BC', '0.100', '1.000', '0.000', '950.00'),
        (28, 'RD', 'Round', 'R10', 'R10', 'R10', 'RD', '0.080', '0.120', '3.000', '950.00'),
        (29, 'RD', 'Round', '2-', '2-', '0.80', '2-', '0.003', '0.003', '0.800', '950.00'),
        (30, 'RD', 'Round', '2-', '2-', '0.90', 'RD', '0.003', '0.004', '0.900', '950.00'),
        (33, 'RD', 'Round', '2-', '2-', '1.00', 'RD', '0.005', '0.006', '1.000', '950.00'),

        # Page 4
        (34, 'RD', 'Round', '2-', '2-', '1.10', '2-', '0.006', '0.007', '1.100', '950.00'),
        (35, 'RD', 'Round', '2-', '2-', '1.15', 'RD', '0.007', '0.008', '1.150', '950.00'),
        (36, 'RD', 'Round', '2-', '2-', '1.20', 'RD', '0.008', '0.008', '1.200', '950.00'),
        (37, 'RD', 'Round', '2-', '2-', '1.25', 'RD', '0.009', '0.009', '1.250', '950.00'),
        (38, 'RD', 'Round', '2+', '2+', '1.30', 'RD', '0.009', '1.000', '1.300', '950.00'),
        (39, 'RD', 'Round', '2+', '2+', '1.40', 'RD', '0.010', '0.012', '1.400', '950.00'),
        (40, 'RD', 'Round', '2+', '2+', '1.50', 'RD', '0.013', '0.015', '1.500', '950.00'),
        (41, 'RD', 'Round', '2+', '2+', '1.60', 'RD', '0.016', '0.018', '1.600', '950.00'),
        (42, 'RD', 'Round', '2+', '2+', '1.70', 'RD', '0.018', '0.020', '1.700', '950.00'),
        (43, 'RD', 'Round', '6+', '6+', '1.80', 'RD', '0.022', '0.025', '1.800', '950.00'),

        # Page 5
        (44, 'RD', 'Round', '6+', '6+', '1.90', 'RD', '0.026', '0.028', '1.900', '950.00'),
        (45, 'RD', 'Round', '6+', '6+', '2.00', 'RD', '0.029', '0.032', '2.000', '950.00'),
        (46, 'RD', 'Round', '6+', '6+', '2.10', 'RD', '0.033', '0.036', '2.100', '950.00'),
        (47, 'RD', 'Round', '6+', '6+', '2.20', 'RD', '0.037', '0.040', '2.200', '950.00'),
        (48, 'RD', 'Round', '6+', '6+', '2.30', 'RD', '0.042', '0.046', '2.300', '950.00'),
        (49, 'RD', 'Round', '6+', '6+', '2.40', 'RD', '0.047', '0.052', '2.400', '950.00'),
        (50, 'RD', 'Round', '6+', '6+', '2.50', 'RD', '0.053', '0.060', '2.500', '950.00'),
        (51, 'RD', 'Round', '6+', '6+', '2.60', 'RD', '0.062', '0.067', '2.600', '950.00'),
        (52, 'RD', 'Round', '6+', '6+', '2.70', 'RD', '0.068', '0.075', '2.700', '950.00'),
        (53, 'RD', 'Round', 'R15', 'R15', '0.15', 'RD', '0.130', '0.170', '0.150', '950.00'),

        # Page 6
        (54, 'RD', 'Round', 'R20', 'R20', '0.20', 'RD', '0.180', '0.220', '0.200', '950.00'),
        (55, 'CR', 'Crescent', 'CR1', 'CR1', '0.30', 'RD', '0.300', '0.300', '5.000', '950.00'),
        (56, 'RD', 'Round', '2-', '2-', '0.60', 'RD', '0.001', '0.002', '0.600', '950.00'),
        (57, 'MQ', 'Marquise', 'M30', 'M30', 'MQ30', 'MQ', '0.280', '0.320', '0.300', '950.00'),
        (58, 'OV', 'Oval', 'O15', 'O15', 'OV15', 'OV', '0.130', '0.170', '0.150', '950.00'),
        (59, 'OV', 'Oval', 'O20', 'O20', 'OV20', 'OV', '0.175', '0.220', '0.200', '950.00'),
        (60, 'OV', 'Oval', 'O25', 'O25', 'OV25', 'OV', '0.225', '0.270', '0.250', '950.00'),
        (61, 'TR', 'Trillion', 'TR', 'TR', 'TR', 'TR', '0.010', '0.070', '0.010', '950.00'),
        (62, 'BR', 'Briolette', 'BR', 'BR', 'BR', 'BRO', '0.002', '0.100', '0.100', '950.00'),
        (63, 'RD', 'Round', 'R25', 'R25', '0.25', 'R25', '0.230', '0.270', '0.250', '1250.00'),
    ]

    for item in data:
        code, cut_code, cut_name, model_code, model_name, stone_type, s_code, w_from, w_to, s_mm, price = item
        
        shortcut, created = StoneCut.objects.get_or_create(
            code=cut_code,
            defaults={'name': cut_name, 'category_group': group}
        )
        
        model, m_created = StoneModel.objects.get_or_create(
            code=model_code,
            stone_cut=shortcut,
            defaults={'name': model_name}
        )
        
        StoneSize.objects.update_or_create(
            code=code,
            defaults={
                'stone_cut': shortcut,
                'stone_model': model,
                'stone_type': stone_type,
                'short_code': s_code,
                'weight_from': Decimal(w_from),
                'weight_to': Decimal(w_to),
                'size_mm': Decimal(s_mm),
                'price_per_carat': Decimal(price),
                'color': 'G-H',
                'clarity': 'VVS'
            }
        )
        print(f"Processed stone code: {code}")

if __name__ == "__main__":
    populate_stones_v2()
