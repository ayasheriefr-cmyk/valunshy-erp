import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import Workshop

def fix_workshop_names():
    renames = {
        "تركيب اربال": "تركيب اربان",
        "جلاية انور": "جلاه انور تحت التشغيل",
    }
    
    for old_name, new_name in renames.items():
        w = Workshop.objects.filter(name=old_name).first()
        if w:
            w.name = new_name
            w.save()
            print(f"Renamed workshop: {old_name} -> {new_name}")

if __name__ == "__main__":
    fix_workshop_names()
