from rest_framework import serializers
from .models import Invoice, InvoiceItem, SalesRepresentative
from inventory.models import Item
from crm.models import Customer
from django.db import transaction
from core.models import GoldPrice

class GoldPriceSerializer(serializers.ModelSerializer):
    carat_name = serializers.CharField(source='carat.name', read_only=True)
    
    class Meta:
        model = GoldPrice
        fields = ['carat', 'carat_name', 'price_per_gram', 'updated_at']

from .models import Invoice, InvoiceItem, SalesRepresentative, OldGoldReturn

class OldGoldReturnSerializer(serializers.ModelSerializer):
    carat_name = serializers.CharField(source='carat.name', read_only=True)
    
    class Meta:
        model = OldGoldReturn
        fields = ['carat', 'carat_name', 'weight', 'value']


# 1. Item Serializer (For Catalog)
class ItemSerializer(serializers.ModelSerializer):
    carat_name = serializers.CharField(source='carat.name', read_only=True)
    purity = serializers.DecimalField(source='carat.purity', max_digits=5, decimal_places=4, read_only=True)
    image_url = serializers.SerializerMethodField()
    estimated_price = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = ['id', 'barcode', 'name', 'carat', 'carat_name', 'gross_weight', 'net_gold_weight', 'purity', 'status', 'image_url', 'estimated_price']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_estimated_price(self, obj):
        # Fetch latest price for this carat
        from core.models import GoldPrice
        latest_price = GoldPrice.objects.filter(carat=obj.carat).order_by('-updated_at').first()
        if latest_price:
            price_per_gram = latest_price.price_per_gram
            # Value = (Gold Weight * Price) + (Total Labor)
            gold_val = obj.net_gold_weight * price_per_gram
            labor_val = (obj.gross_weight * obj.labor_fee_per_gram) + obj.fixed_labor_fee + obj.retail_margin
            total = gold_val + labor_val
            return total
        return 0

# 2. Invoice Item Serializer (Nested in Invoice)
class InvoiceItemSerializer(serializers.ModelSerializer):
    item_barcode = serializers.CharField(source='item.barcode', read_only=True)
    
    class Meta:
        model = InvoiceItem
        fields = ['item', 'item_barcode', 'sold_weight', 'sold_gold_price', 'sold_labor_fee', 'sold_stone_fee', 'subtotal']
        read_only_fields = ['subtotal']

# 3. Invoice Serializer (Main Transaction)
class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)
    returned_gold = OldGoldReturnSerializer(many=True, required=False) # Helper for input
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'status', 'customer', 'customer_name', 'branch', 
            'total_gold_value', 'total_labor_value', 'total_tax', 'grand_total',
            'is_exchange', 'exchange_gold_weight', 'exchange_value_deducted', 'returned_gold',
            'payment_method', 'zatca_uuid', 'created_at', 'items'
        ]
        read_only_fields = ['invoice_number', 'created_at', 'status', 'zatca_uuid', 
                          'total_gold_value', 'total_labor_value', 'total_tax', 'grand_total']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        returned_gold_data = validated_data.pop('returned_gold', [])
        
        # Auto-generate Invoice Number & ZATCA UUID
        import random
        import uuid
        validated_data['invoice_number'] = f"INV-MOB-{random.randint(10000, 99999)}"
        validated_data['zatca_uuid'] = uuid.uuid4()
        
        # Auto-confirm mobile sales
        validated_data['status'] = 'confirmed'
        
        # Set user from request
        user = self.context['request'].user
        validated_data['created_by'] = user
        
        # Link Sales Rep
        sales_rep = None
        try:
            sales_rep = user.salesrepresentative
            validated_data['sales_rep'] = sales_rep
        except:
            pass 
            
        with transaction.atomic():
            invoice = Invoice.objects.create(**validated_data)
            
            # 1. Process Invoice Items
            for item_data in items_data:
                item = item_data['item']
                if item.status != 'available':
                    raise serializers.ValidationError(f"Item {item.barcode} is not available!")
                
                # Mark as sold
                item.status = 'sold'
                item.save()
                
                # Default values if missing
                if 'sold_weight' not in item_data:
                    item_data['sold_weight'] = item.net_gold_weight
                if 'sold_gold_price' not in item_data:
                    item_data['sold_gold_price'] = 3500 # Fallback or get latest
                if 'sold_labor_fee' not in item_data:
                    item_data['sold_labor_fee'] = (item.gross_weight * item.labor_fee_per_gram) + item.fixed_labor_fee + item.retail_margin
                
                InvoiceItem.objects.create(invoice=invoice, **item_data)
            
            # 2. Process Old Gold Return (Exchange)
            if returned_gold_data:
                from .models import OldGoldReturn
                invoice.is_exchange = True
                
                for gold_data in returned_gold_data:
                    OldGoldReturn.objects.create(invoice=invoice, **gold_data)
            
            # 3. Calculate Totals (Centralized in Model)
            invoice.calculate_totals()
            
            # Note: exchange values are handled by the model's calculation or by 
            # updating fields manually if they aren't computed from items.
            # However, calculate_totals handles the Sale part. 
            # We must ensure exchange fields are updated if passed.
            if returned_gold_data:
                from django.db.models import Sum
                totals = invoice.returned_gold.aggregate(
                    weight=Sum('weight'),
                    value=Sum('value')
                )
                invoice.exchange_gold_weight = totals['weight'] or 0
                invoice.exchange_value_deducted = totals['value'] or 0
                invoice.save(update_fields=['is_exchange', 'exchange_gold_weight', 'exchange_value_deducted'])
            
            # We REMOVED the duplicate Commission Calculation here.
            # It is now handled EXCLUSIVELY by signals.py to avoid double counting.
                
            # 4. FINANCIAL IMPACT: Update Treasury (Cash In)
            # Cash to Collect = Grand Total - Exchange Value
            cash_to_collect = invoice.grand_total - Decimal(exchange_value_deducted)
            
            if invoice.payment_method == 'cash' and cash_to_collect > 0:
                from finance.treasury_models import Treasury, TreasuryTransaction
                
                treasury = Treasury.objects.filter(branch=invoice.branch).first() or \
                           Treasury.objects.filter(treasury_type='main').first()
                
                if not treasury:
                    # Create Fallback Treasury if missing
                    treasury = Treasury.objects.create(
                        name="الخزينة الرئيسية", 
                        code="MAIN-01", 
                        treasury_type='main',
                        branch=invoice.branch
                    )

                if treasury:
                    TreasuryTransaction.objects.create(
                        treasury=treasury,
                        transaction_type='cash_in',
                        cash_amount=cash_to_collect,
                        reference_type='invoice',
                        reference_id=invoice.id,
                        description=f"مبيعات تطبيق موبايل - فاتورة {invoice.invoice_number} (الصافي نقداً)",
                        created_by=user
                    )
                    treasury.cash_balance += cash_to_collect
                    treasury.save()
            
            # Create Notification
            from core.models import Notification
            Notification.objects.create(
                title="فاتورة مبيعات جديدة 💰",
                message=f"تم تسجيل فاتورة مبيعات رقم {invoice.invoice_number} بقيمة {invoice.grand_total} ج.م",
                level='success'
            )
                
        return invoice

# 4. Sales Rep Profile
class SalesRepSerializer(serializers.ModelSerializer):
    transactions_count = serializers.IntegerField(source='transactions.count', read_only=True)
    recent_invoices = serializers.SerializerMethodField()
    
    class Meta:
        model = SalesRepresentative
        fields = ['id', 'name', 'total_sales', 'total_commission', 'transactions_count', 'recent_invoices', 'branch']

    def get_recent_invoices(self, obj):
        # Limit to last 10 invoices
        invoices = obj.invoices.all().order_by('-created_at')[:10]
        return InvoiceSerializer(invoices, many=True).data
