import os
import django
import datetime
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.models import Account, LedgerEntry
from sales.models import InvoiceItem, Invoice
from django.db.models import Sum

today = datetime.date(2026, 1, 4)
year = 2026
month = 1
report_type = 'quarterly'
year = 2026
month = 1

if report_type == 'quarterly':
    quarter = (month - 1) // 3 + 1
    start_month = (quarter - 1) * 3 + 1
    start_date = datetime.date(year, start_month, 1)
    if quarter == 4:
        end_date = datetime.date(year, 12, 31)
    else:
        end_date = datetime.date(year, start_month + 3, 1) - datetime.timedelta(days=1)
else:
    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

print(f"Checking data for {report_type} range: {start_date} to {end_date}")

invoices = InvoiceItem.objects.filter(invoice__created_at__date__range=[start_date, end_date])
print(f"InvoiceItem count: {invoices.count()}")

for inv_item in invoices:
    profit = Decimal('0')
    source_order = getattr(inv_item.item, 'source_order', None)
    if source_order:
         profit = source_order.factory_margin
    print(f"Item: {inv_item.item}, Profit: {profit}")

revenue_accounts = Account.objects.filter(account_type='revenue')
total_revenue = Decimal('0')
for acc in revenue_accounts:
    entries = LedgerEntry.objects.filter(account=acc, journal_entry__date__range=[start_date, end_date])
    credit = entries.aggregate(Sum('credit'))['credit__sum'] or Decimal('0')
    debit = entries.aggregate(Sum('debit'))['debit__sum'] or Decimal('0')
    total_revenue += (credit - debit)
print(f"Total Revenue: {total_revenue}")

expense_accounts = Account.objects.filter(account_type='expense')
total_expenses = Decimal('0')
for acc in expense_accounts:
    entries = LedgerEntry.objects.filter(account=acc, journal_entry__date__range=[start_date, end_date])
    debit = entries.aggregate(Sum('debit'))['debit__sum'] or Decimal('0')
    credit = entries.aggregate(Sum('credit'))['credit__sum'] or Decimal('0')
    total_expenses += (debit - credit)
print(f"Total Expenses: {total_expenses}")

net_profit = total_revenue - total_expenses
print(f"Net Profit: {net_profit}")
