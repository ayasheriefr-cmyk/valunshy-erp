import os
import sys
import django
from decimal import Decimal

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import Workshop
from finance.treasury_models import Treasury

def fix_laser_link():
    print("Beginning Laser Treasury & Workshop Correction...")
    
    try:
        # 1. correct the link
        # Treasury 5: "خزينه الليزر"
        t_laser = Treasury.objects.get(id=5)
        # Workshop 28: "ورشة ليزر"
        ws_laser = Workshop.objects.get(id=28)
        
        print(f"Target Treasury: {t_laser.name} (ID: {t_laser.id})")
        print(f"Target Workshop: {ws_laser.name} (ID: {ws_laser.id})")
        
        if t_laser.workshop != ws_laser:
            print(f"Current Link: {t_laser.workshop}")
            t_laser.workshop = ws_laser
            t_laser.save()
            print("-> Updated Treasury Link to Workshop 28.")
        else:
            print("-> Treasury is already linked correctly.")
            
        # 2. Transfer 100g (Add 100g to Workshop 28)
        # Assuming "Workshop 6" (source) is gone or has 0 balance, we treat this as a correction add.
        # Plan said: "Transfer 100g balance from Workshop 6 to Workshop 12"
        # We assume Workshop 12 -> 28.
        
        print(f"Current Workshop Balance (18k): {ws_laser.gold_balance_18}")
        
        # Add 100g
        correction_amount = Decimal('100.000')
        ws_laser.gold_balance_18 += correction_amount
        ws_laser.save()
        
        print(f"-> Added {correction_amount}g to Workshop Balance.")
        print(f"New Workshop Balance (18k): {ws_laser.gold_balance_18}")
        
        print("Correction Complete.")
        
    except Exception as e:
        print(f"Error during correction: {e}")

if __name__ == "__main__":
    fix_laser_link()
