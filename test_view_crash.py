import os
import django
from django.test import RequestFactory
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.views import monthly_analytics_report

def test_view():
    factory = RequestFactory()
    # Mocking the request with parameters from user's URL
    url = '/finance/reports/monthly-analytics/?report_type=monthly&month=1&year=2026&goal_profit=200000&goal_months=3'
    request = factory.get(url)
    
    # Mocking a staff user
    from django.contrib.auth.models import User
    user = User.objects.filter(is_superuser=True).first()
    request.user = user

    try:
        print("Executing monthly_analytics_report...")
        response = monthly_analytics_report(request)
        print(f"Status Code: {response.status_code}")
    except Exception as e:
        import traceback
        print("EXCEPTION CAUGHT:")
        traceback.print_exc()

if __name__ == "__main__":
    test_view()
