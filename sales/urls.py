from django.urls import path
from . import views
from . import api_views

app_name = 'sales'

urlpatterns = [
    # Dashboard / Admin Views (If any exist or will exist)
    path('invoice/', views.invoice_list_view, name='invoice_list'), 
    path('mobile/', views.mobile_app_view, name='mobile_app'), # The Web App
    path('dashboard/', views.sales_dashboard_view, name='sales_dashboard'), # New Dashboard View
    path('reports/profitability/', views.profitability_report, name='profitability_report'),
    path('shop/', views.customer_catalog_view, name='customer_catalog'), # Customer Catalog
    
    # API Endpoints (For Mobile App)
    path('api/catalog/', api_views.ItemCatalogView.as_view(), name='api-catalog'),
    path('api/invoice/create/', api_views.CreateInvoiceView.as_view(), name='api-invoice-create'),
    path('api/me/', api_views.MyProfileView.as_view(), name='api-profile'),
    path('api/prices/', api_views.GoldPriceView.as_view(), name='api-prices'),
    path('api/customers/', api_views.CustomerListView.as_view(), name='api-customers'),
    
    # Client App
    path('api/order/create/', api_views.CustomerOrderView.as_view(), name='api-order-create'),
    path('api/quick-sell/', api_views.QuickSellView.as_view(), name='api-quick-sell'),
    
    # Reservation Feature
    path('reservation/', views.reservation_view, name='reservation_page'),
    path('api/item-by-barcode/<str:barcode>/', api_views.ItemDetailByBarcodeView.as_view(), name='api-item-barcode'),
    path('api/reserve/', api_views.CreateReservationView.as_view(), name='api-reserve'),
]
