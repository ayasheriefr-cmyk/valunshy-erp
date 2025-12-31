from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta


@staff_member_required
def gm_dashboard(request):
    """General Manager Dashboard - Shows all KPIs and reports"""
    from sales.models import Invoice, SalesRepresentative
    from inventory.models import Item
    from finance.treasury_models import Treasury
    from manufacturing.models import ManufacturingOrder
    from core.user_management import ActivityLog
    from core.models import GoldPrice
    
    today = timezone.now().date()
    
    # Sales Stats
    today_invoices = Invoice.objects.filter(
        created_at__date=today,
        status='confirmed'
    )
    today_sales = today_invoices.aggregate(total=Sum('grand_total'))['total'] or 0
    today_invoices_count = today_invoices.count()
    
    # Inventory Stats
    available_items = Item.objects.filter(status='available')
    inventory_count = available_items.count()
    
    # Calculate inventory value (simplified)
    inventory_value = 0
    for item in available_items.select_related('carat'):
        price = GoldPrice.objects.filter(carat=item.carat).first()
        if price:
            inventory_value += float(item.net_gold_weight) * float(price.price_per_gram)
    
    # Treasury Balance
    treasury_balance = Treasury.objects.aggregate(total=Sum('cash_balance'))['total'] or 0
    
    # Pending Orders
    pending_orders = Invoice.objects.filter(status='pending').count()
    
    # Manufacturing Orders (Detailed)
    manufacturing_qs = ManufacturingOrder.objects.exclude(status__in=['completed', 'cancelled'])
    manufacturing_orders = manufacturing_qs.count()
    
    # Breakdown by stage
    mo_casting = manufacturing_qs.filter(status='casting').count()
    mo_crafting = manufacturing_qs.filter(status='crafting').count()
    mo_polishing = manufacturing_qs.filter(status='polishing').count()
    
    # Delayed
    mo_delayed = manufacturing_qs.filter(end_date__lt=today).count()
    
    # Total Gold in work
    mo_weight = manufacturing_qs.aggregate(total=Sum('input_weight'))['total'] or 0
    
    # Pending Commissions
    pending_commissions = 0
    for rep in SalesRepresentative.objects.all():
        paid = rep.transactions.filter(transaction_type='payment').aggregate(Sum('amount'))['amount__sum'] or 0
        pending_commissions += float(rep.total_commission or 0) - float(paid)
    
    # Recent Activity
    recent_activity = ActivityLog.objects.select_related('user').all()[:10]
    
    # Suppliers & Customers Stats
    from crm.models import Supplier, Customer
    suppliers = Supplier.objects.all()
    suppliers_count = suppliers.count()
    suppliers_balance = suppliers.aggregate(total=Sum('money_balance'))['total'] or 0
    
    customers = Customer.objects.all()
    customers_count = customers.count()
    customers_balance = customers.aggregate(total=Sum('money_balance'))['total'] or 0
    customers_purchases = customers.aggregate(total=Sum('total_purchases_value'))['total'] or 0

    # Custody Stats (Active Custody)
    from finance.treasury_models import Custody
    active_custody = Custody.objects.filter(status='active')
    active_custody_count = active_custody.count()
    active_custody_total = active_custody.aggregate(total=Sum('cash_amount'))['total'] or 0

    # Profit & Loss Logic (Simplified)
    from finance.models import Account, LedgerEntry
    
    # 1. Total Revenue (Credits - Debits for Revenue Accounts)
    revenue_accounts = Account.objects.filter(account_type='revenue')
    revenue_credits = LedgerEntry.objects.filter(account__in=revenue_accounts).aggregate(total=Sum('credit'))['total'] or 0
    revenue_debits = LedgerEntry.objects.filter(account__in=revenue_accounts).aggregate(total=Sum('debit'))['total'] or 0
    total_revenue = float(revenue_credits) - float(revenue_debits)

    # 2. Total Expenses (Debits - Credits for Expense Accounts)
    expense_accounts = Account.objects.filter(account_type='expense')
    expense_debits = LedgerEntry.objects.filter(account__in=expense_accounts).aggregate(total=Sum('debit'))['total'] or 0
    expense_credits = LedgerEntry.objects.filter(account__in=expense_accounts).aggregate(total=Sum('credit'))['total'] or 0
    total_expenses = float(expense_debits) - float(expense_credits)

    # 3. Net Profit
    net_profit = total_revenue - total_expenses

    # 4. Cost Center Breakdown
    from finance.models import CostCenter
    cost_centers_data = []
    for cc in CostCenter.objects.filter(is_active=True):
        cc_revenue = LedgerEntry.objects.filter(
            cost_center=cc, 
            account__account_type='revenue'
        ).aggregate(total=Sum('credit'))['total'] or 0
        
        cc_expenses = LedgerEntry.objects.filter(
            cost_center=cc, 
            account__account_type='expense'
        ).aggregate(total=Sum('debit'))['total'] or 0
        
        if cc_revenue > 0 or cc_expenses > 0:
            cost_centers_data.append({
                'name': cc.name,
                'code': cc.code,
                'revenue': cc_revenue,
                'expenses': cc_expenses,
                'profit': float(cc_revenue) - float(cc_expenses)
            })

    # Historical Sales for Chart (Last 7 days)
    sales_chart_labels = []
    sales_chart_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        day_total = Invoice.objects.filter(
            created_at__date=date,
            status='confirmed'
        ).aggregate(total=Sum('grand_total'))['total'] or 0
        sales_chart_labels.append(date.strftime('%Y-%m-%d'))
        sales_chart_data.append(float(day_total))

    # Top Selling Items
    from django.db.models import Count
    top_items = Item.objects.filter(invoiceitem__invoice__status='confirmed').annotate(
        sales_count=Count('invoiceitem')
    ).order_by('-sales_count')[:5]

    # Smart AI Message
    from core.ai_engine import ValunshyAI
    ai = ValunshyAI(request.user)
    business_status_msg = ai.get_smart_status()

    context = {
        'today': today,
        'today_sales': today_sales,
        'today_invoices_count': today_invoices_count,
        'inventory_value': inventory_value,
        'inventory_count': inventory_count,
        'treasury_balance': treasury_balance,
        'pending_orders': pending_orders,
        'manufacturing_orders': manufacturing_orders,
        'pending_commissions': pending_commissions,
        'recent_activity': recent_activity,
        'suppliers_balance': suppliers_balance,
        'suppliers_count': suppliers_count,
        'customers_balance': customers_balance,
        'customers_count': customers_count,
        'customers_purchases': customers_purchases,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'sales_chart_labels': sales_chart_labels,
        'sales_chart_data': sales_chart_data,
        'top_items': top_items,
        'business_status_msg': business_status_msg,
        'active_custody_count': active_custody_count,
        'active_custody_total': active_custody_total,
        'cost_centers_data': cost_centers_data,
        # Manufacturing Details
        'mo_casting': mo_casting,
        'mo_crafting': mo_crafting,
        'mo_polishing': mo_polishing,
        'mo_delayed': mo_delayed,
        'mo_weight': mo_weight,
    }
    
    return render(request, 'admin/gm_dashboard.html', context)
