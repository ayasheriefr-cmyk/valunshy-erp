from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('reports/accounts/', views.customer_accounts_report, name='customer_accounts'),
    path('reports/supplier-accounts/', views.supplier_accounts_report, name='supplier_accounts'),
]
