import os
import sys
import django

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.treasury_models import Treasury

t5 = Treasury.objects.get(id=5)
print(f"Treasury 5 ({t5.name}):")
print(f"  18k: {t5.gold_balance_18}")
print(f"  21k: {t5.gold_balance_21}")
print(f"  Linked Workshop: {t5.workshop}")
