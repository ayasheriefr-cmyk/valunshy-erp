
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from django.core.management import call_command

print("Backing up data to all_data.json with UTF-8 encoding...")
try:
    with open('all_data.json', 'w', encoding='utf-8') as f:
        call_command('dumpdata', exclude=['contenttypes', 'auth.Permission'], indent=2, stdout=f)
    print("Backup successful!")
except Exception as e:
    print(f"Backup failed: {e}")
