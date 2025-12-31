from django.contrib import admin
from .models import Carat, GoldPrice, Branch, SystemSettings
from core.admin_mixins import ExportImportMixin

@admin.register(Carat)
class CaratAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('name', 'purity', 'is_active')
    search_fields = ('name',)

@admin.register(GoldPrice)
class GoldPriceAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('carat', 'price_per_gram', 'updated_at')
    list_filter = ('carat',)
    ordering = ('-updated_at',)

@admin.register(Branch)
class BranchAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('name', 'location', 'is_main')

from .models import SystemSettings
@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('system_name', 'base_url')

    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()

# Import user management admin
from . import user_admin
