from django.urls import path
from . import views

app_name = 'manufacturing'

urlpatterns = [
    path('dashboard/', views.manufacturing_dashboard, name='dashboard'),
    path('analytics/', views.manufacturing_analytics, name='analytics'), # NEW
    path('order/<int:order_id>/print/', views.print_job_card, name='print_job_card'),
]
