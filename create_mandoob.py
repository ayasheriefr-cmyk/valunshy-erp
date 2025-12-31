"""
Script to create a Sales Representative account with test data
Run this with: python manage.py shell < create_mandoob.py
"""

from django.contrib.auth.models import User
from sales.models import SalesRepresentative
from inventory.models import Item, Branch, Carat
from crm.models import Customer

print("=" * 50)
print("إنشاء حساب مندوب مبيعات")
print("=" * 50)

# 1. Create or get user account
username = "mandoob"
password = "mandoob123"

user, created = User.objects.get_or_create(
    username=username,
    defaults={
        'first_name': 'أحمد',
        'last_name': 'المندوب',
        'is_staff': False,
        'is_active': True
    }
)

if created:
    user.set_password(password)
    user.save()
    print(f"✅ تم إنشاء مستخدم جديد: {username}")
else:
    print(f"ℹ️  المستخدم موجود بالفعل: {username}")

# 2. Create or get Sales Representative
sales_rep, created = SalesRepresentative.objects.get_or_create(
    user=user,
    defaults={
        'name': 'أحمد محمد - مندوب المبيعات',
        'phone': '0501234567',
        'email': 'mandoob@example.com',
        'commission_type': 'percentage',
        'commission_rate': 2.5,  # 2.5% commission
        'is_active': True,
        'total_sales': 0,
        'total_commission': 0
    }
)

# Try to assign a branch if exists
try:
    branch = Branch.objects.first()
    if branch:
        sales_rep.branch = branch
        sales_rep.save()
        print(f"✅ تم ربط المندوب بالفرع: {branch.name}")
except:
    print("⚠️  لم يتم العثور على فرع")

if created:
    print(f"✅ تم إنشاء مندوب مبيعات: {sales_rep.name}")
else:
    print(f"ℹ️  المندوب موجود بالفعل: {sales_rep.name}")

print("\n" + "=" * 50)
print("بيانات الدخول:")
print("=" * 50)
print(f"اسم المستخدم: {username}")
print(f"كلمة المرور: {password}")
print(f"رابط التطبيق: http://localhost:8000/sales/mobile/")
print("=" * 50)

# 3. Check available items
available_items = Item.objects.filter(status='available')
print(f"\n📦 عدد المنتجات المتاحة للبيع: {available_items.count()}")

if available_items.count() == 0:
    print("\n⚠️  تحذير: لا توجد منتجات متاحة!")
    print("💡 لإنشاء منتجات تجريبية، قم بتشغيل:")
    print("   python manage.py shell < create_test_items.py")
else:
    print("\n✅ المنتجات المتاحة:")
    for item in available_items[:5]:
        print(f"   - {item.barcode}: {item.name} ({item.net_gold_weight} جم)")
    if available_items.count() > 5:
        print(f"   ... و {available_items.count() - 5} منتج آخر")

# 4. Check customers
customers = Customer.objects.all()
print(f"\n👥 عدد العملاء: {customers.count()}")
if customers.count() == 0:
    print("⚠️  لا يوجد عملاء في النظام")
    print("💡 يمكنك إضافة عملاء من لوحة الإدارة")

print("\n" + "=" * 50)
print("✅ تم الإعداد بنجاح!")
print("=" * 50)
