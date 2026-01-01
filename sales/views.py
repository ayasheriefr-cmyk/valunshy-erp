from django.shortcuts import render
from django.http import HttpResponse

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

from django.contrib.auth.decorators import login_required
from inventory.models import Item
from .models import Invoice
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
