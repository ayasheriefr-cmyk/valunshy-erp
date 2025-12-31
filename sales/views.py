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
