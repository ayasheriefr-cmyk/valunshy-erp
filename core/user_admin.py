from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .user_management import UserProfile, ActivityLog


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = "الصلاحيات والدور"
    verbose_name_plural = "الصلاحيات والدور"
    
    fieldsets = (
        ('الدور الوظيفي', {
            'fields': ('role', 'branch'),
            'description': '⚡ عند تغيير الدور، يتم تعيين الصلاحيات الافتراضية تلقائياً. يمكنك تعديلها أدناه.'
        }),
        ('صلاحيات الأقسام (يمكن تعديلها يدوياً)', {
            'fields': (
                ('can_access_sales', 'can_access_inventory'),
                ('can_access_manufacturing', 'can_access_finance'),
                ('can_access_crm', 'can_access_reports'),
                'can_access_settings',
            ),
            'description': '✏️ يمكنك تفعيل/إلغاء أي صلاحية يدوياً لهذا المستخدم بغض النظر عن دوره'
        }),
        ('صلاحيات خاصة', {
            'fields': (
                ('can_confirm_invoices', 'can_void_invoices'),
                ('can_edit_prices', 'can_view_costs'),
                'can_export_data',
            ),
        }),
    )


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'get_branch', 'is_active', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__role', 'profile__branch')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    def get_role(self, obj):
        try:
            role = obj.profile.get_role_display()
            colors = {
                'مدير عام': '#D4AF37',
                'مدير المبيعات': '#4CAF50',
                'مدير المخزون': '#2196F3',
                'مدير التصنيع': '#9C27B0',
                'محاسب': '#FF9800',
                'مندوب مبيعات': '#00BCD4',
                'كاشير': '#795548',
                'عميل': '#607D8B',
            }
            color = colors.get(role, '#666')
            return format_html(
                '<span style="background: {}; color: #fff; padding: 4px 12px; border-radius: 12px; font-size: 11px;">{}</span>',
                color, role
            )
        except UserProfile.DoesNotExist:
            return mark_safe('<span style="color: #999;">غير محدد</span>')
    get_role.short_description = "الدور"
    
    def get_branch(self, obj):
        try:
            return obj.profile.branch.name if obj.profile.branch else "-"
        except UserProfile.DoesNotExist:
            return "-"
    get_branch.short_description = "الفرع"


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_badge', 'model_name', 'description_short', 'ip_address', 'created_at')
    list_filter = ('action', 'model_name', 'created_at')
    search_fields = ('user__username', 'model_name', 'description')
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'description', 'ip_address', 'user_agent', 'created_at')
    
    def action_badge(self, obj):
        colors = {
            'login': '#4CAF50',
            'logout': '#607D8B',
            'create': '#2196F3',
            'update': '#FF9800',
            'delete': '#f44336',
            'view': '#9E9E9E',
            'export': '#9C27B0',
            'confirm': '#4CAF50',
            'reject': '#f44336',
        }
        color = colors.get(obj.action, '#666')
        return format_html(
            '<span style="background: {}; color: #fff; padding: 3px 10px; border-radius: 10px; font-size: 10px;">{}</span>',
            color, obj.get_action_display()
        )
    action_badge.short_description = "الإجراء"
    
    def description_short(self, obj):
        if len(obj.description) > 50:
            return obj.description[:50] + "..."
        return obj.description
    description_short.short_description = "الوصف"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
