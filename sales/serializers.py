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

class OldGoldReturnSerializer(serializers.ModelSerializer):
    carat_name = serializers.CharField(source='carat.name', read_only=True)
    
    class Meta:
        model = Invoice.returned_gold.rel.related_model  # Dynamic reference to OldGoldReturn
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
        fields = ['item', 'item_barcode', 'sold_weight', 'sold_gold_price', 'sold_labor_fee', 'subtotal']
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
            
            total_gold_value = 0
            total_labor_value = 0
            
            # 1. Process Invoice Items
            for item_data in items_data:
                item = item_data['item']
                if item.status != 'available':
                    raise serializers.ValidationError(f"Item {item.barcode} is not available!")
                
                item.status = 'sold'
                item.save()
                
                sold_weight = item_data.get('sold_weight', item.net_gold_weight)
                gold_price = item_data.get('sold_gold_price', 3500)
                # Default labor fee = Item's fixed fee (Factory Price) + Retail Margin
                default_labor = (item.gross_weight * item.labor_fee_per_gram) + item.fixed_labor_fee + item.retail_margin
                labor_fee = item_data.get('sold_labor_fee', default_labor)
                subtotal = (sold_weight * gold_price) + labor_fee
                
                item_data['subtotal'] = subtotal
                total_gold_value += sold_weight * gold_price
                total_labor_value += labor_fee
                
                InvoiceItem.objects.create(invoice=invoice, **item_data)
            
            # 2. Process Old Gold Return (Exchange)
            exchange_gold_weight = 0
            exchange_value_deducted = 0
            
            if returned_gold_data:
                from .models import OldGoldReturn
                invoice.is_exchange = True
                
                for gold_data in returned_gold_data:
                    OldGoldReturn.objects.create(invoice=invoice, **gold_data)
                    exchange_gold_weight += gold_data['weight']
                    exchange_value_deducted += gold_data['value']
            
            # 3. Calculate Totals
            from decimal import Decimal
            invoice.total_gold_value = total_gold_value
            invoice.total_labor_value = total_labor_value
            invoice.exchange_gold_weight = exchange_gold_weight
            invoice.exchange_value_deducted = exchange_value_deducted
            
            # Calculate Tax (Assuming 15% VAT on Total Value)
            # CHECK: Is VAT applied before or after exchange? strict VAT is usually on total sales value.
            gross_total = Decimal(total_gold_value) + Decimal(total_labor_value)
            total_tax = gross_total * Decimal('0.15')
            invoice.total_tax = total_tax
            
            # Grand Total = Gross + Tax
            invoice.grand_total = gross_total + total_tax
            invoice.save()
            
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
