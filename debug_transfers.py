import os
import django
from django.db.models import Sum

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.treasury_models import Treasury, TreasuryTransfer

print("--- TREASURY DEBUG ---")
all_treasuries = Treasury.objects.all()
for t in all_treasuries:
    try:
        print(f"Treasury: {t.name} | Type: {t.treasury_type} | 18k: {t.gold_balance_18} | 21k: {t.gold_balance_21}")
    except UnicodeEncodeError:
        print(f"Treasury: {t.name.encode('utf-8', 'ignore')} | Type: {t.treasury_type} | 18k: {t.gold_balance_18} | 21k: {t.gold_balance_21}")

print("\n--- RECENT TRANSFERS ---")
transfers = TreasuryTransfer.objects.all().order_by('-created_at')[:5]
for tr in transfers:
    src = tr.from_treasury.name.encode('ascii', 'replace').decode('ascii')
    dst = tr.to_treasury.name.encode('ascii', 'replace').decode('ascii')
    carat = str(tr.gold_carat).encode('ascii', 'replace').decode('ascii') if tr.gold_carat else "None"
    print(f"From: {src} -> To: {dst} | Status: {tr.status} | Weight: {tr.gold_weight} | Carat: {carat}")
