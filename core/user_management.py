from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

class UserProfile(models.Model):
    """Extended user profile with role and permissions"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    ROLE_CHOICES = [
        ('general_manager', 'مدير عام'),
        ('sales_manager', 'مدير المبيعات'),
        ('inventory_manager', 'مدير المخزون'),
        ('manufacturing_manager', 'مدير التصنيع'),
        ('accountant', 'محاسب'),
        ('sales_rep', 'مندوب مبيعات'),
        ('cashier', 'كاشير'),
        ('customer', 'عميل'),
    ]
    role = models.CharField("الدور", max_length=30, choices=ROLE_CHOICES, default='sales_rep')
    
    # Branch Access
    branch = models.ForeignKey('core.Branch', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="الفرع")
    
    # Module Access Flags (for quick checks)
    can_access_sales = models.BooleanField("صلاحية المبيعات", default=False)
    can_access_inventory = models.BooleanField("صلاحية المخزون", default=False)
    can_access_manufacturing = models.BooleanField("صلاحية التصنيع", default=False)
    can_access_finance = models.BooleanField("صلاحية المالية", default=False)
    can_access_crm = models.BooleanField("صلاحية العملاء", default=False)
    can_access_reports = models.BooleanField("صلاحية التقارير", default=False)
    can_access_settings = models.BooleanField("صلاحية الإعدادات", default=False)
    
    # Special Permissions
    can_confirm_invoices = models.BooleanField("صلاحية تأكيد الفواتير", default=False)
    can_void_invoices = models.BooleanField("صلاحية إلغاء الفواتير", default=False)
    can_edit_prices = models.BooleanField("صلاحية تعديل الأسعار", default=False)
    can_view_costs = models.BooleanField("صلاحية عرض التكاليف", default=False)
    can_export_data = models.BooleanField("صلاحية تصدير البيانات", default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Track if role was changed to auto-apply permissions
    _original_role = None
    
    class Meta:
        verbose_name = "ملف المستخدم"
        verbose_name_plural = "إدارة المستخدمين - الملفات الشخصية"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_role = self.role  # Store original role
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def save(self, *args, **kwargs):
        # Only auto-set permissions if this is a NEW profile OR role was CHANGED
        is_new = self.pk is None
        role_changed = self.role != self._original_role
        
        if is_new or role_changed:
            self.set_permissions_from_role()
        
        super().save(*args, **kwargs)
        self._original_role = self.role  # Update tracked role
    
    def set_permissions_from_role(self):
        """Set module access based on role"""
        role_permissions = {
            'general_manager': {
                'can_access_sales': True,
                'can_access_inventory': True,
                'can_access_manufacturing': True,
                'can_access_finance': True,
                'can_access_crm': True,
                'can_access_reports': True,
                'can_access_settings': True,
                'can_confirm_invoices': True,
                'can_void_invoices': True,
                'can_edit_prices': True,
                'can_view_costs': True,
                'can_export_data': True,
            },
            'sales_manager': {
                'can_access_sales': True,
                'can_access_crm': True,
                'can_access_reports': True,
                'can_confirm_invoices': True,
                'can_view_costs': False,
            },
            'inventory_manager': {
                'can_access_inventory': True,
                'can_access_reports': True,
            },
            'manufacturing_manager': {
                'can_access_manufacturing': True,
                'can_access_inventory': True,
                'can_access_reports': True,
            },
            'accountant': {
                'can_access_finance': True,
                'can_access_reports': True,
                'can_view_costs': True,
                'can_export_data': True,
            },
            'sales_rep': {
                'can_access_sales': True,
            },
            'cashier': {
                'can_access_sales': True,
                'can_access_finance': True,
            },
            'customer': {
                # No admin access
            },
        }
        
        perms = role_permissions.get(self.role, {})
        for perm, value in perms.items():
            setattr(self, perm, value)
    
    def is_general_manager(self):
        return self.role == 'general_manager'
    
    def has_module_access(self, module_name):
        """Check if user has access to a specific module"""
        if self.role == 'general_manager':
            return True
        return getattr(self, f'can_access_{module_name}', False)


class ActivityLog(models.Model):
    """Track user activities for audit"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="المستخدم")
    
    ACTION_CHOICES = [
        ('login', 'تسجيل دخول'),
        ('logout', 'تسجيل خروج'),
        ('create', 'إنشاء'),
        ('update', 'تعديل'),
        ('delete', 'حذف'),
        ('view', 'عرض'),
        ('export', 'تصدير'),
        ('confirm', 'تأكيد'),
        ('reject', 'رفض'),
    ]
    action = models.CharField("الإجراء", max_length=20, choices=ACTION_CHOICES)
    
    model_name = models.CharField("الجدول", max_length=100, blank=True)
    object_id = models.IntegerField("معرف السجل", null=True, blank=True)
    description = models.TextField("الوصف", blank=True)
    
    ip_address = models.GenericIPAddressField("عنوان IP", null=True, blank=True)
    user_agent = models.TextField("المتصفح", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "سجل نشاط"
        verbose_name_plural = "إدارة المستخدمين - سجل النشاطات"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.created_at}"


def create_default_groups():
    """Create default user groups with permissions"""
    groups_config = {
        'المدير العام': ['add', 'change', 'delete', 'view'],
        'مدير المبيعات': ['view', 'add', 'change'],
        'مدير المخزون': ['view', 'add', 'change'],
        'مدير التصنيع': ['view', 'add', 'change'],
        'محاسب': ['view', 'add'],
        'مندوب مبيعات': ['view', 'add'],
        'كاشير': ['view', 'add'],
    }
    
    for group_name, actions in groups_config.items():
        group, created = Group.objects.get_or_create(name=group_name)
        # Permissions would be added here based on models
