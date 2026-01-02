# smartpos/api_views.py

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Q, Avg, F

from .models import (
    Product,
    Category,
    Sale,
    SaleItem,
    Customer,
    Supplier,
    Inventory,
    Expense,
    CashDrawer,
    Purchase,
    PurchaseItem,
    CustomUser
)

from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    CategorySerializer,
    SaleListSerializer,
    SaleDetailSerializer,
    SaleCreateSerializer,
    SaleItemDetailSerializer,
    CustomerSerializer,
    SupplierSerializer,
    InventorySerializer,
    ExpenseSerializer,
    CashDrawerSerializer,
    PurchaseListSerializer,
    PurchaseDetailSerializer,
    PurchaseCreateSerializer,
    DailySalesSerializer,
    InventorySummarySerializer,
    SalesTrendSerializer
)


# ============================================
# CATEGORY VIEWSET
# ============================================

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product Categories
    
    list: Get all categories
    create: Create new category
    retrieve: Get category details
    update: Update category
    destroy: Delete category
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name', 'category_type']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


# ============================================
# PRODUCT VIEWSET
# ============================================

class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Products
    
    list: Get all active products
    create: Create new product
    retrieve: Get product details
    update: Update product
    destroy: Delete/deactivate product
    low_stock: Get low stock items
    out_of_stock: Get out of stock items
    expiring_soon: Get expiring products
    """
    queryset = Product.objects.filter(is_active=True).select_related(
        'category',
        'inventory'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_alcohol', 'is_active']
    search_fields = ['name', 'barcode']
    ordering_fields = ['selling_price', 'created_at', 'name']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Use appropriate serializer based on action"""
        if self.action == 'retrieve':
            return ProductDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        else:
            return ProductListSerializer
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get all low stock products"""
        low_stock_items = Inventory.objects.filter(
            quantity_on_hand__lte=F('reorder_level')
        ).select_related('product')
        
        products = [item.product for item in low_stock_items]
        serializer = ProductDetailSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Get out of stock products"""
        out_of_stock_items = Inventory.objects.filter(
            quantity_on_hand=0
        ).select_related('product')
        
        products = [item.product for item in out_of_stock_items]
        serializer = ProductDetailSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get products expiring within specified days"""
        days = int(request.query_params.get('days', 30))
        expiry_date = timezone.now().date() + timedelta(days=days)
        
        expiring = Product.objects.filter(
            expiry_date__lte=expiry_date,
            expiry_date__gte=timezone.now().date(),
            is_active=True
        )
        
        serializer = ProductDetailSerializer(expiring, many=True)
        return Response(serializer.data)


# ============================================
# INVENTORY VIEWSET
# ============================================

class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Inventory Management (Read-only)
    
    list: Get all inventory
    retrieve: Get inventory for product
    summary: Get inventory summary statistics
    """
    queryset = Inventory.objects.select_related('product')
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['product__name', 'product__barcode']
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get inventory summary statistics"""
        total_value = Inventory.objects.aggregate(
            total=Sum(F('quantity_on_hand') * F('product__cost_price'))
        )['total'] or Decimal('0')
        
        low_stock_count = Inventory.objects.filter(
            quantity_on_hand__lte=F('reorder_level')
        ).count()
        
        out_of_stock_count = Inventory.objects.filter(
            quantity_on_hand=0
        ).count()
        
        return Response({
            'total_inventory_value': float(total_value),
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'total_products': Inventory.objects.count(),
        })


# ============================================
# CUSTOMER VIEWSET
# ============================================

class CustomerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Customer Management
    
    list: Get all customers
    create: Create new customer
    retrieve: Get customer details
    update: Update customer
    destroy: Delete customer
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['total_spent', 'loyalty_points', 'created_at']
    ordering = ['-total_spent']


# ============================================
# SALE VIEWSET
# ============================================

class SaleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Sales Transactions
    
    list: Get all sales
    create: Create new sale
    retrieve: Get sale details
    daily_summary: Get daily sales summary
    period_summary: Get sales for date range
    sales_trend: Get sales trend
    refund_sale: Refund a sale
    """
    queryset = Sale.objects.select_related(
        'cashier',
        'customer'
    ).prefetch_related('items')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['payment_method', 'is_refunded']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use appropriate serializer based on action"""
        if self.action == 'retrieve':
            return SaleDetailSerializer
        elif self.action == 'create':
            return SaleCreateSerializer
        else:
            return SaleListSerializer
    
    def create(self, request, *args, **kwargs):
        """Create new sale with items"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Create sale
        sale = Sale.objects.create(
            cashier=request.user,
            customer=data.get('customer'),
            total_amount=data['total_amount'],
            discount=data.get('discount', 0),
            tax=data.get('tax', 0),
            final_amount=data['final_amount'],
            payment_method=data['payment_method'],
            reference_number=data.get('reference_number', '')
        )
        
        # Create sale items and update inventory
        for item_data in data['items']:
            product = item_data['product']
            quantity = item_data['quantity']
            unit_price = item_data.get('unit_price', product.selling_price)
            
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                unit_price=unit_price
            )
            
            # Update inventory - decrease stock
            inventory = product.inventory
            inventory.quantity_on_hand -= Decimal(str(quantity))
            inventory.save()
        
        # Return created sale with details
        sale_serializer = SaleDetailSerializer(sale)
        return Response(sale_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """Get daily sales summary"""
        date_str = request.query_params.get('date')
        
        if date_str:
            from datetime import datetime
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()
        
        sales = Sale.objects.filter(created_at__date=date)
        
        total_sales = sales.aggregate(Sum('final_amount'))['final_amount__sum'] or Decimal('0')
        transaction_count = sales.count()
        avg_transaction = sales.aggregate(Avg('final_amount'))['final_amount__avg'] or Decimal('0')
        
        # Calculate total profit
        total_profit = Decimal('0')
        for sale in sales:
            for item in sale.items.all():
                cost = item.product.cost_price * item.quantity
                total_profit += item.subtotal - cost
        
        # Top products
        top_products = SaleItem.objects.filter(
            sale__created_at__date=date
        ).values('product__name').annotate(
            qty=Sum('quantity'),
            revenue=Sum('subtotal')
        ).order_by('-revenue')[:5]
        
        # Payment distribution
        payment_dist = sales.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('final_amount')
        )
        
        return Response({
            'date': date,
            'total_sales': float(total_sales),
            'total_profit': float(total_profit),
            'transaction_count': transaction_count,
            'average_transaction': float(avg_transaction),
            'top_products': list(top_products),
            'payment_distribution': list(payment_dist),
        })
    
    @action(detail=False, methods=['get'])
    def period_summary(self, request):
        """Get sales summary for date range"""
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'start_date and end_date query parameters required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from datetime import datetime
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        sales = Sale.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        total_sales = sales.aggregate(Sum('final_amount'))['final_amount__sum'] or Decimal('0')
        transaction_count = sales.count()
        avg_transaction = sales.aggregate(Avg('final_amount'))['final_amount__avg'] or Decimal('0')
        
        # Calculate total profit
        total_profit = Decimal('0')
        for sale in sales:
            for item in sale.items.all():
                cost = item.product.cost_price * item.quantity
                total_profit += item.subtotal - cost
        
        # Top products
        top_products = SaleItem.objects.filter(
            sale__created_at__date__gte=start_date,
            sale__created_at__date__lte=end_date
        ).values('product__name').annotate(
            qty=Sum('quantity'),
            revenue=Sum('subtotal')
        ).order_by('-revenue')[:10]
        
        # Payment distribution
        payment_dist = sales.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('final_amount')
        )
        
        return Response({
            'start_date': start_date,
            'end_date': end_date,
            'total_sales': float(total_sales),
            'total_profit': float(total_profit),
            'transaction_count': transaction_count,
            'average_transaction': float(avg_transaction),
            'top_products': list(top_products),
            'payment_distribution': list(payment_dist),
        })
    
    @action(detail=False, methods=['get'])
    def sales_trend(self, request):
        """Get sales trend for last N days"""
        days = int(request.query_params.get('days', 7))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        sales = Sale.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            total=Sum('final_amount'),
            count=Count('id')
        ).order_by('date')
        
        return Response(list(sales))
    
    @action(detail='', methods=['post'])
    def refund_sale(self, request, pk=None):
        """Process refund for a sale and restore inventory"""
        sale = self.get_object()
        
        if sale.is_refunded:
            return Response(
                {'error': 'Sale already refunded'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Restore inventory
        for item in sale.items.all():
            inventory = item.product.inventory
            inventory.quantity_on_hand += Decimal(str(item.quantity))
            inventory.save()
        
        sale.is_refunded = True
        sale.save()
        
        serializer = SaleDetailSerializer(sale)
        return Response(serializer.data)


# ============================================
# SUPPLIER VIEWSET
# ============================================

class SupplierViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Supplier Management
    
    list: Get all suppliers
    create: Create new supplier
    retrieve: Get supplier details
    update: Update supplier
    destroy: Delete supplier
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'contact_person', 'phone']
    ordering_fields = ['name', 'outstanding_balance']
    ordering = ['name']


# ============================================
# EXPENSE VIEWSET
# ============================================

class ExpenseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Expense Tracking
    
    list: Get all expenses
    create: Create new expense
    retrieve: Get expense details
    update: Update expense
    destroy: Delete expense
    """
    queryset = Expense.objects.select_related('recorded_by')
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['category', 'description']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Automatically set recorded_by to current user"""
        serializer.save(recorded_by=self.request.user)


# ============================================
# CASH DRAWER VIEWSET
# ============================================

class CashDrawerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Cash Drawer Management
    
    list: Get all cash drawers
    retrieve: Get drawer details
    open_drawer: Open new drawer
    close_drawer: Close drawer
    """
    queryset = CashDrawer.objects.select_related('cashier')
    serializer_class = CashDrawerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_open', 'cashier']
    ordering = ['-opened_at']
    
    @action(detail=False, methods=['get'])
    def open_drawer(self, request):
        """Get or create open cash drawer for current user"""
        drawer = CashDrawer.objects.filter(
            cashier=request.user,
            is_open=True
        ).first()
        
        if not drawer:
            opening_balance = request.query_params.get('opening_balance', 0)
            drawer = CashDrawer.objects.create(
                cashier=request.user,
                opening_balance=opening_balance
            )
        
        serializer = self.get_serializer(drawer)
        return Response(serializer.data)
    
    @action(detail='', methods=['post'])
    def close_drawer(self, request, pk=None):
        """Close cash drawer"""
        drawer = self.get_object()
        
        if not drawer.is_open:
            return Response(
                {'error': 'Drawer is already closed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        closing_balance = request.data.get('closing_balance')
        
        if closing_balance is None:
            return Response(
                {'error': 'closing_balance is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        drawer.closing_balance = closing_balance
        drawer.closed_at = timezone.now()
        drawer.is_open = False
        drawer.save()
        
        difference = drawer.closing_balance - drawer.opening_balance
        
        return Response({
            'message': 'Drawer closed successfully',
            'opening_balance': float(drawer.opening_balance),
            'closing_balance': float(drawer.closing_balance),
            'difference': float(difference),
            'expected_cash': float(sum(
                Sale.objects.filter(
                    cashier=drawer.cashier,
                    created_at__gte=drawer.opened_at,
                    payment_method='cash'
                ).values_list('final_amount', flat=True)
            ))
        })


# ============================================
# PURCHASE VIEWSET
# ============================================

class PurchaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Purchase Orders
    
    list: Get all purchase orders
    create: Create new purchase order
    retrieve: Get purchase order details
    update: Update purchase order
    """
    queryset = Purchase.objects.select_related(
        'supplier',
        'received_by'
    ).prefetch_related('items')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'supplier']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use appropriate serializer based on action"""
        if self.action == 'retrieve':
            return PurchaseDetailSerializer
        elif self.action == 'create':
            return PurchaseCreateSerializer
        else:
            return PurchaseListSerializer
    
    def create(self, request, *args, **kwargs):
        """Create new purchase order with items"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Create purchase
        purchase = Purchase.objects.create(
            supplier=data['supplier'],
            total_amount=data['total_amount'],
            received_by=request.user,
            delivery_date=data['delivery_date'],
            status=data.get('status', 'pending')
        )
        
        # Create purchase items
        for item_data in data['items']:
            product = item_data['product']
            quantity = item_data['quantity']
            unit_cost = item_data['unit_cost']
            
            subtotal = quantity * unit_cost
            
            PurchaseItem.objects.create(
                purchase=purchase,
                product=product,
                quantity=quantity,
                unit_cost=unit_cost,
                subtotal=subtotal
            )
        
        # Return created purchase with details
        purchase_serializer = PurchaseDetailSerializer(purchase)
        return Response(purchase_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail='', methods=['post'])
    def mark_received(self, request, pk=None):
        """Mark purchase as received and update inventory"""
        purchase = self.get_object()
        
        if purchase.status == 'received':
            return Response(
                {'error': 'Purchase already marked as received'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update inventory for each item
        for item in purchase.items.all():
            inventory = item.product.inventory
            inventory.quantity_on_hand += item.quantity
            inventory.save()
        
        purchase.status = 'received'
        purchase.save()
        
        serializer = PurchaseDetailSerializer(purchase)
        return Response(serializer.data)