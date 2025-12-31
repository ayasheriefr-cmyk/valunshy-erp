from django.db import models
from django.utils.translation import gettext_lazy as _

class Customer(models.Model):
    name = models.CharField(_("Customer Name"), max_length=255)
    phone = models.CharField(_("Phone Number"), max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    vat_number = models.CharField(_("VAT Number"), max_length=50, blank=True, null=True)
    
    # App Login
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, null=True, blank=True, related_name='customer_profile', verbose_name='حساب التطبيق')
    
    # Preferences & Special Occasions
    birth_date = models.DateField(blank=True, null=True)
    wedding_anniversary = models.DateField(blank=True, null=True)
    
    # Financial Balances
    money_balance = models.DecimalField("الرصيد النقدي", max_digits=15, decimal_places=2, default=0, help_text="الرصيد المدين/الدائن للعميل")
    
    # Gold Balances (Custody or savings)
    gold_balance_18 = models.DecimalField("رصيد ذهب 18 (جم)", max_digits=12, decimal_places=3, default=0)
    gold_balance_21 = models.DecimalField("رصيد ذهب 21 (جم)", max_digits=12, decimal_places=3, default=0)
    gold_balance_24 = models.DecimalField("رصيد ذهب 24 (جم)", max_digits=12, decimal_places=3, default=0)
    
    total_purchases_value = models.DecimalField("إجمالي المشتريات", max_digits=15, decimal_places=2, default=0)
    loyalty_points = models.IntegerField("نقاط الولاء", default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.phone}"

    class Meta:
        verbose_name = "عميل"
        verbose_name_plural = "بيانات العملاء"

class Supplier(models.Model):
    name = models.CharField("اسم المورد", max_length=255)
    phone = models.CharField("رقم الجوال", max_length=20, blank=True)
    contact_person = models.CharField("الشخص المسؤول", max_length=100, blank=True)
    email = models.EmailField("البريد الإلكتروني", blank=True, null=True)
    vat_number = models.CharField("الرقم الضريبي", max_length=50, blank=True, null=True)
    address = models.CharField("العنوان", max_length=500, blank=True)
    primary_carat = models.IntegerField("العيار الأساسي", default=18, help_text="العيار الذي يتم التعامل به غالباً")
    
    SUPPLIER_TYPE_CHOICES = [
        ('gold_office', 'مكتب ذهب'),
        ('factory', 'مصنع'),
        ('trader', 'تاجر كسر'),
        ('other', 'آخر'),
    ]
    supplier_type = models.CharField("نوع المورد", max_length=20, choices=SUPPLIER_TYPE_CHOICES, default='factory')

    # Financial Balances
    money_balance = models.DecimalField("الرصيد النقدي", max_digits=15, decimal_places=2, default=0, help_text="الرصيد المدين/الدائن للمورد")
    
    # Gold Balances (Custody or debts)
    gold_balance_18 = models.DecimalField("رصيد ذهب 18 (جم)", max_digits=12, decimal_places=3, default=0)
    gold_balance_21 = models.DecimalField("رصيد ذهب 21 (جم)", max_digits=12, decimal_places=3, default=0)
    gold_balance_24 = models.DecimalField("رصيد ذهب 24 (جم)", max_digits=12, decimal_places=3, default=0)
    
    notes = models.TextField("ملاحظات", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_supplier_type_display()})"

    class Meta:
        verbose_name = "مورد"
        verbose_name_plural = "الموردين"
