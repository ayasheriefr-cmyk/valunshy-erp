import os
import django
import sys

# Add project root to path
sys.path.append('c:\\Users\\COMPU LINE\\Desktop\\mm\\final\\gold')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import WorkshopTransfer

# Get the latest transfer
latest_transfer = WorkshopTransfer.objects.select_related('from_workshop', 'to_workshop', 'carat').order_by('-id').first()

if latest_transfer:
    print("=== LATEST TRANSFER DETAILS ===")
    print(f"Transfer No: {latest_transfer.transfer_number}")
    print(f"Date: {latest_transfer.date}")
    print(f"From: {latest_transfer.from_workshop.name.encode('utf-8', 'replace').decode('utf-8')}") # Attempt to handle name safely or just print
    print(f"To: {latest_transfer.to_workshop.name.encode('utf-8', 'replace').decode('utf-8')}")
    print(f"Weight: {latest_transfer.weight}")
    print(f"Carat: {latest_transfer.carat.name}")
    print(f"Status: {latest_transfer.status}")
    
    # Check Balances
    src = latest_transfer.from_workshop
    dst = latest_transfer.to_workshop
    
    print("\n=== CURRENT WORKSHOP BALANCES ===")
    print(f"FROM Workshop ({src.id}):")
    print(f"  - Gold 18: {src.gold_balance_18}")
    print(f"  - Gold 21: {src.gold_balance_21}")
    
    print(f"\nTO Workshop ({dst.id}):")
    print(f"  - Gold 18: {dst.gold_balance_18}")
    print(f"  - Gold 21: {dst.gold_balance_21}")

else:
    print("No transfers found.")
