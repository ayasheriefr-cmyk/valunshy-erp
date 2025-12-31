from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('dashboard/', views.finance_dashboard, name='finance_dashboard'),
    path('treasuries/', views.treasuries_dashboard, name='treasuries_dashboard'),
    path('reports/trial-balance/', views.trial_balance, name='trial_balance'),
    path('reports/balance-sheet/', views.balance_sheet, name='balance_sheet'),
    path('reports/income-statement/', views.income_statement, name='income_statement'),
    path('reports/gold-position/', views.gold_position, name='gold_position'),
    path('reports/treasury-handover/', views.treasury_handover_report, name='treasury_handover_report'),
    path('reports/treasury-comparison/', views.treasury_comparison_report, name='treasury_comparison_report'),
    path('reports/monthly-analytics/', views.monthly_analytics_report, name='monthly_analytics_report'),
    path('daily-close/', views.daily_close, name='daily_close'),

]
