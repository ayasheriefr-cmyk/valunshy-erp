from django.db import models
from django.utils.translation import gettext_lazy as _

class Carat(models.Model):
    name = models.CharField("اسم العيار", max_length=50)  # e.g., 24K, 21K, 18K
    purity = models.DecimalField("نسبة النقاء", max_digits=5, decimal_places=4)  # e.g., 0.875 for 21K
    base_weight = models.PositiveSmallIntegerField("وزن العيار الأساسي", default=21, help_text="مثال: 18، 21، 24")
    is_active = models.BooleanField("نشط", default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "عيار"
        verbose_name_plural = "إعدادات - العيارات"

class GoldPrice(models.Model):
    carat = models.ForeignKey(Carat, on_delete=models.CASCADE, related_name='prices', verbose_name="العيار")
    price_per_gram = models.DecimalField("السعر للجرام", max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    def __str__(self):
        return f"{self.carat.name}: {self.price_per_gram} ج.م"

    class Meta:
        verbose_name = "سعر الذهب"
        verbose_name_plural = "إعدادات - أسعار الذهب اليومية"

class Branch(models.Model):
    name = models.CharField("اسم الفرع", max_length=100)
    location = models.CharField("الموقع", max_length=255, blank=True)
    is_main = models.BooleanField("الفرع الرئيسي", default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "فرع"
        verbose_name_plural = "إعدادات - الفروع"

class SystemSettings(models.Model):
    """إعدادات النظام العامة"""
    system_name = models.CharField("اسم النظام", max_length=100, default="Valunshy Gold ERP")
    base_url = models.URLField("رابط النظام (Base URL)", help_text="مثال: https://valunshy.pythonanywhere.com", blank=True)
    
    class Meta:
        verbose_name = "إعدادات النظام"
        verbose_name_plural = "إعدادات - إعدادات النظام"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.system_name

class Notification(models.Model):
    """نظام التنبيهات والاخطارات"""
    title = models.CharField("العنوان", max_length=100)
    message = models.TextField("الرسالة")
    
    TYPE_CHOICES = [
        ('info', 'معلومة'),
        ('success', 'نجاح'),
        ('warning', 'تحذير'),
        ('danger', 'خطر'),
    ]
    level = models.CharField("الأهمية", max_length=10, choices=TYPE_CHOICES, default='info')
    
    is_read = models.BooleanField("تمت القراءة", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Target (Optional: simple system wide for now, can be per user)
    # user = models.ForeignKey(...)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "إشعار"
        verbose_name_plural = "الإشعارات"

    def __str__(self):
        return self.title
