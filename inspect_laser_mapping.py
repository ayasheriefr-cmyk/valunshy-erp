import os
import sys
import django
from django.db.models import Sum

# Force UTF-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import Workshop
from finance.treasury_models import Treasury

print("=== WORKSHOPS WITH BALANCE > 0 ===")
for w in Workshop.objects.all():
    if w.gold_balance_18 > 0 or w.gold_balance_21 > 0:
        print(f"ID: {w.id} | Name: {w.name} | 18k: {w.gold_balance_18}")

print("\n=== LASER TREASURIES INSPECTION ===")
lasers = Treasury.objects.filter(name__icontains="ليزر")
for t in lasers:
    print(f"ID: {t.id} | Name: {t.name} | Linked Workshop: {t.workshop_id} ({t.workshop})")
