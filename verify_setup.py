import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.treasury_models import Treasury
from manufacturing.models import Workshop

def verify():
    main = Treasury.objects.filter(code='1').first()
    if main:
        print(f"Main Treasury found.")
        subs = main.sub_treasuries.all()
        print(f"Sub-treasuries count: {subs.count()}")
        for s in subs:
            linked = "YES" if s.workshop else "NO"
            print(f"Sub: {s.code} | Linked to workshop: {linked}")
    else:
        print("Main Treasury NOT found.")

if __name__ == "__main__":
    verify()
