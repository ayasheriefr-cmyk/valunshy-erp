import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.treasury_models import Treasury, TreasuryTool
from manufacturing.models import InstallationTool
from core.models import Branch

def setup():
    # 1. Ensure Laser Treasury exists
    branch = Branch.objects.first()
    laser_treasury, created = Treasury.objects.get_or_create(
        code='LSR01',
        defaults={
            'name': 'خزينه الليزر',
            'treasury_type': 'gold_tools',
            'branch': branch,
            'is_active': True
        }
    )
    if created:
        print(f"Created Laser Treasury: {laser_treasury.code}")
    else:
        print(f"Laser Treasury already exists: {laser_treasury.code}")

    # 2. Find Welding Wire tool
    wire_tool = InstallationTool.objects.filter(name__icontains='سلك ليزر').first()
    if not wire_tool:
        wire_tool = InstallationTool.objects.create(
            name='سلك ليزر ذهب 18',
            tool_type='gold_wire',
            unit='gram',
            weight=100.0,
            min_weight=10.0
        )
        print(f"Created new Tool: {wire_tool.id}")
    else:
        print(f"Found existing Tool: {wire_tool.id}")

    # 3. Initialize stock in Laser Treasury
    stock, created = TreasuryTool.objects.get_or_create(
        treasury=laser_treasury,
        tool=wire_tool,
        defaults={
            'weight': 500.0,
            'quantity': 1.0
        }
    )
    if created:
        print(f"Initialized stock: 500g")
    else:
        stock.weight += 500.0
        stock.save()
        print(f"Updated stock: Now {stock.weight}g")

if __name__ == "__main__":
    setup()
