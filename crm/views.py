from django.shortcuts import render
from django.db.models import Sum
from .models import Customer, Supplier
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def customer_accounts_report(request):
    customers = Customer.objects.all().order_by('-money_balance')
    
    total_money = customers.aggregate(Sum('money_balance'))['money_balance__sum'] or 0
    total_gold_21 = customers.aggregate(Sum('gold_balance_21'))['gold_balance_21__sum'] or 0
    
    context = {
        'customers': customers,
        'total_money': total_money,
        'total_gold_21': total_gold_21,
        'title': 'كشف حسابات العملاء المجمع'
    }
    return render(request, 'crm/customer_accounts.html', context)

@staff_member_required
def supplier_accounts_report(request):
    suppliers = Supplier.objects.all().order_by('-money_balance')
    
    total_money = suppliers.aggregate(Sum('money_balance'))['money_balance__sum'] or 0
    total_gold_21 = suppliers.aggregate(Sum('gold_balance_21'))['gold_balance_21__sum'] or 0
    
    context = {
        'suppliers': suppliers,
        'total_money': total_money,
        'total_gold_21': total_gold_21,
        'title': 'كشف حسابات الموردين المجمع'
    }
    return render(request, 'crm/supplier_accounts.html', context)

@staff_member_required
def customer_dashboard(request):
    """
    Dashboard for CRM stats.
    """
    from django.db.models import Count, Sum
    
    # 1. KPI Cards
    total_customers = Customer.objects.count()
    total_receivables = Customer.objects.filter(money_balance__gt=0).aggregate(Sum('money_balance'))['money_balance__sum'] or 0
    total_debts = Customer.objects.filter(money_balance__lt=0).aggregate(Sum('money_balance'))['money_balance__sum'] or 0
    
    total_gold_21 = Customer.objects.aggregate(Sum('gold_balance_21'))['gold_balance_21__sum'] or 0
    total_gold_18 = Customer.objects.aggregate(Sum('gold_balance_18'))['gold_balance_18__sum'] or 0

    # 2. Charts Data
    # Top 5 Customers by Purchases
    top_customers = Customer.objects.order_by('-total_purchases_value')[:5]
    
    # Recent Customers
    recent_customers = Customer.objects.order_by('-created_at')[:5]

    context = {
        'total_customers': total_customers,
        'total_receivables': total_receivables,
        'total_debts': abs(total_debts),
        'total_gold_21': total_gold_21,
        'total_gold_18': total_gold_18,
        'top_customers': top_customers,
        'recent_customers': recent_customers,
        'title': 'لوحة تحكم العملاء',
    }
    return render(request, 'crm/dashboard.html', context)
