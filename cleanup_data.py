import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder, ProductionStage
from finance.treasury_models import TreasuryTransfer, TreasuryTransaction

def cleanup():
    print("Cleaning up old demo data...")
    today = timezone.now().date()
    
    # Delete non-REAL demo orders
    ManufacturingOrder.objects.filter(start_date=today).exclude(order_number__icontains="REAL").delete()
    
    # Delete old transfers for today that might be confusing
    TreasuryTransfer.objects.filter(date=today, notes__icontains="DEMO").exclude(notes__icontains="REAL").delete()
    
    print("Cleanup complete.")

if __name__ == '__main__':
    cleanup()
