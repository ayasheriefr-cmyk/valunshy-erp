import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.treasury_models import Treasury, TreasuryTool, ToolTransfer, Custody, CustodyTool, CustodyHolder
from manufacturing.models import InstallationTool
from django.contrib.auth.models import User

def verify():
    # 1. Check Initial Stock
    laser = Treasury.objects.get(code='LSR01')
    production = Treasury.objects.filter(treasury_type='production').first()
    if not production:
        production = Treasury.objects.get(code='TR002') # Fallback to a common code
    
    wire = InstallationTool.objects.filter(name__icontains='سلك').first()
    
    laser_stock = TreasuryTool.objects.get(treasury=laser, tool=wire)
    print(f"Initial Laser Stock: {laser_stock.weight}g")
    
    prod_stock, _ = TreasuryTool.objects.get_or_create(treasury=production, tool=wire)
    print(f"Initial Production Stock: {prod_stock.weight}g")

    # 2. Transfer 100g from Laser to Production
    admin_user = User.objects.filter(is_superuser=True).first()
    transfer = ToolTransfer.objects.create(
        from_treasury=laser,
        to_treasury=production,
        tool=wire,
        weight=Decimal('100.0'),
        quantity=Decimal('1.0'),
        status='completed', # This should trigger the signal
        initiated_by=admin_user
    )
    print(f"Transfer {transfer.transfer_number} completed.")

    # 3. Verify Stock after Transfer
    laser_stock.refresh_from_db()
    prod_stock.refresh_from_db()
    print(f"Laser Stock after Transfer: {laser_stock.weight}g")
    print(f"Production Stock after Transfer: {prod_stock.weight}g")

    # 4. Issue 50g to a Tech from Production
    holder = CustodyHolder.objects.first()
    custody = Custody.objects.create(
        custody_number='CUST-TEST-01',
        holder=holder,
        treasury=production,
        status='active',
        created_by=admin_user
    )
    
    # Adding tool custody
    CustodyTool.objects.create(
        custody=custody,
        tool=wire,
        weight=Decimal('50.0'),
        quantity=Decimal('1.0')
    )
    print(f"Issued 50g custody to {holder.user.username}")

    # 5. Verify Stock after Issuance
    prod_stock.refresh_from_db()
    print(f"Production Stock after Issuance: {prod_stock.weight}g")

if __name__ == "__main__":
    verify()
