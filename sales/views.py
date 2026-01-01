from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from inventory.models import Item
from .models import Invoice, Reservation
from crm.models import Customer
from core.models import GoldPrice

def invoice_list_view(request):
    return HttpResponse("Sales Invoice List - Coming Soon")

def mobile_app_view(request):
    """
    Renders the PWA/Mobile App Interface.
    The logic is handled via JS calling the API.
    """
    return render(request, 'sales/mobile_app.html')

def customer_catalog_view(request):
    """
    Customer-facing catalog page for browsing and ordering products.
    """
    return render(request, 'sales/customer_catalog.html')

@login_required
def reservation_view(request):
    """View to handle product reservation for customers"""
    # Fetch all customers for the dropdown
    customers = Customer.objects.all().order_by('name')
    context = {
        'customers': customers
    }
    return render(request, 'sales/reservation.html', context)

from crm.models import Customer
from core.models import GoldPrice

@login_required
def sales_dashboard_view(request):
    """
    Simpler Dashboard for Sales Reps.
    """
    # 1. Get Inventory
    items = Item.objects.filter(status='available').select_related('carat')
    
    # 2. Get Recent Invoices
    recent_invoices = Invoice.objects.filter(created_by=request.user).order_by('-created_at')[:10]
    
    # 3. Get Customers
    customers = Customer.objects.all().order_by('name')
    
    # 4. Get Prices for context
    prices = {gp.carat.name: gp.price_per_gram for gp in GoldPrice.objects.all()}

    return render(request, 'sales/dashboard.html', {
        'items': items,
        'recent_invoices': recent_invoices,
        'customers': customers,
        'prices': prices
    })
@login_required
def profitability_report(request):
    """
    Detailed Profitability Report with Ranking.
    """
    from .models import InvoiceItem, Invoice
    from inventory.models import Category
    from django.db.models import Sum, F, ExpressionWrapper, DecimalField
    from django.utils import timezone
    import datetime

    # 1. Advanced Filtering
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    branch_id = request.GET.get('branch')
    sales_rep_id = request.GET.get('sales_rep')
    category_id = request.GET.get('category')
    
    today = timezone.localtime(timezone.now()).date()
    start_date = today - datetime.timedelta(days=30)
    end_date = today

    if start_date_str:
        try: start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except: pass
    if end_date_str:
        try: end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except: pass

    # Base Query
    invoices = Invoice.objects.filter(
        created_at__date__gte=start_date, 
        created_at__date__lte=end_date, 
        status='confirmed'
    )
    
    # Apply Invoice Filters
    if branch_id:
        invoices = invoices.filter(branch_id=branch_id)
    if sales_rep_id:
        invoices = invoices.filter(sales_rep_id=sales_rep_id)
        
    invoice_items = InvoiceItem.objects.filter(invoice__in=invoices).select_related('item', 'item__category')
    
    # Apply Item Filters
    if category_id:
        invoice_items = invoice_items.filter(item__category_id=category_id)

    # Re-evaluate invoices based on filtered items if category is selected
    if category_id:
        invoices = invoices.filter(items__item__category_id=category_id).distinct()

    # 2. Key Metrics
    total_sales = sum(item.subtotal for item in invoice_items)
    total_profit = sum(item.profit for item in invoice_items)
    total_cost = float(total_sales) - float(total_profit)
    margin_pct = (float(total_profit) / float(total_sales) * 100) if total_sales > 0 else 0

    # 3. Item Ranking
    item_stats = {}
    for item in invoice_items:
        key = f"{item.item.name} ({item.item.barcode})"
        if key not in item_stats:
            item_stats[key] = {'sales': 0, 'profit': 0, 'qty': 0}
        item_stats[key]['sales'] += float(item.subtotal)
        item_stats[key]['profit'] += float(item.profit)
        item_stats[key]['qty'] += 1

    ranked_items = sorted(item_stats.items(), key=lambda x: x[1]['profit'], reverse=True)

    # 4. Category Ranking
    category_stats = {}
    for item in invoice_items:
        cat_name = item.item.category.name if item.item.category else "Other"
        if cat_name not in category_stats:
            category_stats[cat_name] = {'sales': 0, 'profit': 0}
        category_stats[cat_name]['sales'] += float(item.subtotal)
        category_stats[cat_name]['profit'] += float(item.profit)

    ranked_categories = sorted(category_stats.items(), key=lambda x: x[1]['profit'], reverse=True)

    # 5. Metadata for Filter Dropdowns
    from inventory.models import Branch as InvBranch
    from .models import SalesRepresentative
    
    context = {
        'total_sales': total_sales,
        'total_profit': total_profit,
        'total_cost': total_cost,
        'margin_pct': margin_pct,
        'ranked_items': ranked_items[:20],
        'ranked_categories': ranked_categories,
        'start_date': start_date,
        'end_date': end_date,
        # Filters
        'branches': InvBranch.objects.all(),
        'sales_reps': SalesRepresentative.objects.all(),
        'categories': Category.objects.all(),
        'selected_branch': branch_id,
        'selected_rep': sales_rep_id,
        'selected_cat': category_id,
    }


    return render(request, 'sales/profitability_report.html', context)
