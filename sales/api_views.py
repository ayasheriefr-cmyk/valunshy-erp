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

from rest_framework.authentication import SessionAuthentication, BasicAuthentication

# 7. Quick Sell API (For Dashboard)
class QuickSellView(APIView):
    """
    Simplified Invoice Creation for Dashboard.
    Accepts item_id and customer_id.
    Calculates price automatically based on current date.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            item_id = request.data.get('item_id')
            customer_id = request.data.get('customer_id') # Can be None/Empty for Cash

            if not item_id:
                 return Response({"error": "Item ID is required"}, status=400)
            
            # 1. Get Item
            try:
                 item = Item.objects.get(id=item_id, status='available')
            except Item.DoesNotExist:
                 return Response({"error": "Item not found or unavailable"}, status=404)

            # 2. Get Customer
            customer = None
            if customer_id:
                try:
                    customer = Customer.objects.get(id=customer_id)
                except Customer.DoesNotExist:
                    pass # Treat as Cash if invalid ID? Or error? Let's treat as Cash/None.
            
            # 3. Calculate Price
            from core.models import GoldPrice
            latest_price = GoldPrice.objects.filter(carat=item.carat).order_by('-updated_at').first()
            if not latest_price:
                 return Response({"error": f"Gold price not set for {item.carat.name}"}, status=400)

            price_per_gram = latest_price.price_per_gram
            gold_val = item.net_gold_weight * price_per_gram
            
            # Labor: If estimated price > gold val, diff is labor. Else custom logic (100 minimal).
            # Robust logic:
            labor_val = (item.gross_weight * item.labor_fee_per_gram) + item.fixed_labor_fee + item.retail_margin
            
            subtotal = gold_val + labor_val
            total_with_tax = subtotal * Decimal('1.15') # VAT
            
            # Determine Branch (Critical for Invoice)
            invoice_branch = item.current_branch
            if not invoice_branch:
                # Fallback: Try obtaining from SalesRep profile
                if hasattr(request.user, 'salesrepresentative'):
                    invoice_branch = request.user.salesrepresentative.branch
                
                # Fallback: Default to first branch if Admin
                if not invoice_branch and request.user.is_superuser:
                    from core.models import Branch
                    invoice_branch = Branch.objects.first()
            
            if not invoice_branch:
                return Response({"error": "Cannot create invoice: Item has no branch and user has no assigned branch."}, status=400)
            
            # 4. Create Invoice
            import random
            # Invoice Number: "INV-YYYY-XXXX"
            inv_num = f"INV-{random.randint(100000, 999999)}"
            
            invoice = Invoice.objects.create(
                invoice_number=inv_num,
                customer=customer, # Can be Null
                branch=invoice_branch, 
                status='paid', # Direct Sale = Paid/Completed immediately? Or 'pending'? 
                               # Dashboard sales usually implied immediate handover. Let's say 'paid' or 'approved'.
                created_by=request.user,
                payment_method='cash',
                
                total_gold_value=gold_val,
                total_labor_value=labor_val,
                grand_total=total_with_tax,
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
            
            # Mark Item Sold
            item.status = 'sold'
            item.save()
            
            return Response({"message": "Sale recorded", "invoice_number": inv_num}, status=201)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"detail": f"Server Error: {str(e)}"}, status=500)

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from .models import Reservation
from django.db import transaction

class ItemDetailByBarcodeView(APIView):
    """API to fetch item details by barcode (Scanner)"""
    permission_classes = [IsAuthenticated]

    def get(self, request, barcode):
        try:
            item = Item.objects.select_related('carat').get(barcode=barcode)
            
            # Simple estimation logic
            estimated_price = 0
            if item.carat.prices.exists():
                estimated_price = float(item.net_gold_weight * item.carat.prices.latest('updated_at').price_per_gram)

            data = {
                'id': item.id,
                'name': item.name,
                'barcode': item.barcode,
                'carat': item.carat.name,
                'net_gold_weight': float(item.net_gold_weight),
                'status': item.status,
                'status_display': item.get_status_display(),
                'image_url': item.image.url if item.image else None,
                'estimated_price': estimated_price
            }
            return Response(data, status=status.HTTP_200_OK)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

class CreateReservationView(APIView):
    """API to reserve an item"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        item_id = request.data.get('item_id')
        customer_id = request.data.get('customer_id')
        notes = request.data.get('notes', '')

        if not item_id or not customer_id:
            return Response({'error': 'Missing item or customer'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = Item.objects.get(id=item_id)
            if item.status != 'available' and item.status != 'mandoob':
                return Response({'error': f'Item is not available (Status: {item.get_status_display()})'}, status=status.HTTP_400_BAD_REQUEST)

            customer = Customer.objects.get(id=customer_id)

            with transaction.atomic():
                # 1. Create Reservation
                Reservation.objects.create(
                    item=item,
                    customer=customer,
                    sales_rep=request.user,
                    notes=notes
                )

                # 2. Update Item Status
                item.status = 'reserved'
                item.save()

            return Response({'message': 'Reservation successful'}, status=status.HTTP_201_CREATED)

        except Item.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
