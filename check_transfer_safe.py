import os
import django
import sys

sys.path.append('c:\\Users\\COMPU LINE\\Desktop\\mm\\final\\gold')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import WorkshopTransfer

latest_transfer = WorkshopTransfer.objects.order_by('-id').first()

if latest_transfer:
    print("=== DETAILS ===")
    print(f"ID: {latest_transfer.id}")
    print(f"Number: {latest_transfer.transfer_number}")
    print(f"Weight: {latest_transfer.weight}")
    try:
        print(f"Carat: {latest_transfer.carat.name_en if hasattr(latest_transfer.carat, 'name_en') else latest_transfer.carat.id}")
    except:
        print(f"Carat ID: {latest_transfer.carat_id}")
    print(f"From Workshop ID: {latest_transfer.from_workshop_id}")
    print(f"To Workshop ID: {latest_transfer.to_workshop_id}")
else:
    print("Zero transfers.")
