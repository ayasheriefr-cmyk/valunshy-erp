"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from core.views import home_dashboard, ai_assistant_query, get_notifications, mark_notification_read
from django.views.generic import TemplateView
from rest_framework.authtoken.views import obtain_auth_token
from inventory.api_views import get_next_barcode

from core.gm_views import gm_dashboard


urlpatterns = [

    path('accounts/login/', admin.site.login), # Redirect standard login to Admin Login
    path('admin/gm-dashboard/', gm_dashboard, name='gm_dashboard'),
    path('admin/help/', TemplateView.as_view(template_name='admin/help.html'), name='admin_help'),
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('inventory/', include('inventory.urls')),
    path('finance/', include('finance.urls')),
    path('crm/', include('crm.urls')),
    path('manufacturing/', include('manufacturing.urls')),
    path('sales/', include('sales.urls')),
    path('api-token-auth/', obtain_auth_token), # For mobile login
    path('ai-assistant/', ai_assistant_query, name='ai_assistant'),
    path('api/notifications/', get_notifications, name='get_notifications'),
    path('api/notifications/read/<int:notif_id>/', mark_notification_read, name='mark_notification_read'),
    path('api/inventory/next-barcode/', get_next_barcode, name='api_next_barcode'),
    path('', home_dashboard, name='home'),
]

# Admin Site Customization
admin.site.site_header = "نظام فالينشى المتطور"
admin.site.site_title = "نظام فالينشى"
admin.site.index_title = "لوحة التحكم - نظام فالينشى المتطور"
