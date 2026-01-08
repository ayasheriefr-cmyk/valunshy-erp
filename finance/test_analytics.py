from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
import datetime
from finance.models import Account, LedgerEntry, JournalEntry, FiscalYear, FinanceSettings, Partner
from sales.models import Invoice, InvoiceItem
from inventory.models import Item, RawMaterial
from manufacturing.models import ManufacturingOrder, ProductionStage, Workshop
from core.models import Carat

class MonthlyAnalyticsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='staff', password='password', is_staff=True)
        self.client.login(username='staff', password='password')
        
        # Setup Accounts
        self.revenue_acc = Account.objects.create(code="401", name="Revenue", account_type="revenue")
        self.expense_acc = Account.objects.create(code="501", name="Expense", account_type="expense")
        self.asset_acc = Account.objects.create(code="101", name="Asset", account_type="asset")
        
        # Setup Partner
        self.partner = Partner.objects.create(name="Partner 1", percentage=50, is_active=True)
        
        # Setup Data for Analysis
        today = timezone.now().date()
        self.start_date = today.replace(day=1)
        
        # 1. Create Financial Data
        je = JournalEntry.objects.create(date=today, description="Test Sales", created_by=self.user)
        LedgerEntry.objects.create(journal_entry=je, account=self.asset_acc, debit=1000, credit=0)
        LedgerEntry.objects.create(journal_entry=je, account=self.revenue_acc, debit=0, credit=1000)
        
        je2 = JournalEntry.objects.create(date=today, description="Test Expense", created_by=self.user)
        LedgerEntry.objects.create(journal_entry=je2, account=self.expense_acc, debit=200, credit=0)
        LedgerEntry.objects.create(journal_entry=je2, account=self.asset_acc, debit=0, credit=200)

        # 2. Setup Manufacturing Data (for Efficiency)
        workshop = Workshop.objects.create(name="WS1")
        order = ManufacturingOrder.objects.create(order_number="ORD-001", status="completed", workshop=workshop)
        ProductionStage.objects.create(
            order=order, 
            stage_name="casting", 
            start_datetime=timezone.now() - datetime.timedelta(hours=2),
            end_datetime=timezone.now()
        )
        
    def test_monthly_analytics_loads(self):
        """Test that the analytics page loads without error and contains key data"""
        response = self.client.get(reverse('finance:monthly_analytics_report'))
        self.assertEqual(response.status_code, 200)
        
        # Check Financials
        # Revenue: 1000, Expense: 200, Net: 800
        self.assertContains(response, "800") 
        self.assertContains(response, "Partner 1")
        
    def test_performance_benchmark(self):
        """Simple benchmark - ensure it runs reasonably fast (under 2s for small data)"""
        import time
        start = time.time()
        response = self.client.get(reverse('finance:monthly_analytics_report'))
        end = time.time()
        duration = end - start
        
        self.assertEqual(response.status_code, 200)
        print(f"Analytics View took: {duration:.4f} seconds")
        self.assertLess(duration, 2.0, "View is too slow even with minimal data!")
