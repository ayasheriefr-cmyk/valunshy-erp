
import os
import django
import sys

# Setup Django Environment
sys.path.append('c:\\Users\\COMPU LINE\\Desktop\\mm\\final\\gold')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import Workshop
from django.contrib.auth.models import User

def create_workshops():
    workshops_data = [
        {"name": "ورشة السبك", "type": "internal", "description": "ورشة صهر وسبك الذهب"},
        {"name": "ورشة الليزر", "type": "internal", "description": "ورشة الحفر والقطع بالليزر"},
        {"name": "ورشة الجلاء والتلميع", "type": "internal", "description": "ورشة تلميع وتنظيف المشغولات"},
        {"name": "ورشة التركيب", "type": "internal", "description": "ورشة تركيب الأحجار والأجزاء"},
        {"name": "ورشة النشار", "type": "internal", "description": "ورشة قص ونشر الذهب"},
    ]
    
    count = 0
    for data in workshops_data:
        # Check if exists
        try:
            ws, created = Workshop.objects.get_or_create(
                name=data["name"],
                defaults={
                    "workshop_type": data["type"],
                    "contact_person": "المدير المسؤول"
                }
            )
            if created:
                print(f"Created workshop type: {data['type']}")
                count += 1
            else:
                print(f"Workshop exists: {data['type']}")
        except Exception as e:
            print(f"Error processing workshop: {e}")

    print(f"Final Count: {count}")

if __name__ == "__main__":
    create_workshops()
