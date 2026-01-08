from django.urls import path
from .views import inventory_dashboard
from .api_views import get_next_barcode

app_name = 'inventory'

from . import views

urlpatterns = [
    path('dashboard/', views.inventory_dashboard, name='dashboard'),
    path('print-tags/', views.print_tags, name='print_tags'),
]

