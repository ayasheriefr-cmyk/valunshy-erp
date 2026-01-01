from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Invoice, SalesRepresentative
from inventory.models import Item
from .serializers import ItemSerializer, InvoiceSerializer, SalesRepSerializer
from decimal import Decimal

# 1. Catalog API (ReadOnly)
class ItemCatalogView(generics.ListAPIView):
    """
    Returns a list of AVAILABLE items for sale.
    Support filtering by barcode or carat.
    """
    queryset = Item.objects.filter(status='available')
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['barcode', 'name', 'carat__name']

# 2. Create Invoice API
class CreateInvoiceView(generics.CreateAPIView):
    """
    Allows the mobile app to post a new sales invoice.
    """
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

# 3. Mandoob Profile API
class MyProfileView(APIView):
    """
    Returns the logged-in delegate's profile, sales stats, and commission.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            sales_rep = request.user.salesrepresentative
            serializer = SalesRepSerializer(sales_rep)
            return Response(serializer.data)
        except SalesRepresentative.DoesNotExist:
            return Response({"error": "User is not linked to a Sales Representative account."}, status=400)

from core.models import GoldPrice
from .serializers import GoldPriceSerializer

# 4. Gold Prices API
class GoldPriceView(APIView):
    """
    Returns current gold prices for all carats.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        prices = GoldPrice.objects.all()
        serializer = GoldPriceSerializer(prices, many=True)
        return Response(serializer.data)

from crm.models import Customer
from crm.serializers import CustomerSerializer # Assuming this exists or creates a simple one

# 5. Customer List API
class CustomerListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        customers = Customer.objects.all().values('id', 'name', 'phone') # Optimized
        return Response(list(customers))

# 6. Customer Order API (For Client App)
class CustomerOrderView(APIView):
    """
    Allow a CUSTOMER to book/order an item.
    Creates a pending invoice.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # 1. Get Customer Profile
        try:
            customer = request.user.customer_profile
        except:
             return Response({"error": "User is not a registered customer"}, status=400)

        # 2. Get Item
        item_id = request.data.get('item_id')
        if not item_id:
             return Response({"error": "Item ID is required"}, status=400)
        
        try:
             item = Item.objects.get(id=item_id, status='available')
        except Item.DoesNotExist:
             return Response({"error": "Item not found or unavailable"}, status=404)

        # 3. Calculate Price Snapshot (Server Side Security)
        # We don't trust client price. calculate now.
        from core.models import GoldPrice
        latest_price = GoldPrice.objects.filter(carat=item.carat).order_by('-updated_at').first()
        if not latest_price:
             return Response({"error": "Gold price not set for this carat"}, status=400)

        price_per_gram = latest_price.price_per_gram
        gold_val = item.net_gold_weight * price_per_gram
        labor_val = (item.gross_weight * item.labor_fee_per_gram) + item.fixed_labor_fee + item.retail_margin
        subtotal = gold_val + labor_val

        # 4. Create Invoice (Pending)
        import random
        # Create Invoice
        invoice = Invoice.objects.create(
            invoice_number=f"ORD-APP-{random.randint(100000, 999999)}",
            customer=customer,
            branch=item.current_branch, # Link to item's branch
            status='pending', # PENDING APPROVAL
            created_by=request.user,
            payment_method='cash', # Default, can be changed later
            
            # Initial Totals
            total_gold_value=gold_val,
            total_labor_value=labor_val,
            grand_total=subtotal * Decimal('1.15'), # + VAT approx
            total_tax=subtotal * Decimal('0.15')
        )

        # Link Item
        from .models import InvoiceItem
        InvoiceItem.objects.create(
            invoice=invoice,
            item=item,
            sold_weight=item.net_gold_weight,
            sold_gold_price=price_per_gram,
            sold_labor_fee=labor_val,
            subtotal=subtotal
        )

        # Mark item as 'reserved' or 'sold'? 
        # Better to mark 'held' or keep available until confirmed?
        # Let's set to 'pending' if we had that status, or keep available but risky.
        # For now, let's NOT change status until Admin confirms, OR use a 'reserved' status.
        # Ideally: item.status = 'reserved'
        
        return Response({"message": "Order placed successfully", "order_number": invoice.invoice_number}, status=201)
