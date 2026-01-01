from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from .models import (
    Product, Category, Sale, SaleItem, Customer, Supplier,
    Inventory, Expense, CashDrawer, Purchase
)
from .serializers import (
    ProductSerializer, CategorySerializer, SaleSerializer,
    CustomerSerializer, SupplierSerializer, InventorySerializer
)
from .utils import SalesAnalytics, InventoryManager, ReportGenerator


class CategoryViewSet(viewsets.ModelViewSet):
    """Product categories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name']


class ProductViewSet(viewsets.ModelViewSet):
    """Product management"""
    queryset = Product.objects.filter(is_active=True).select_related('category', 'inventory')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_alcohol', 'is_active']
    search_fields = ['name', 'barcode']
    ordering_fields = ['selling_price', 'created_at', 'name']
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get all low stock products"""
        low_stock_items = InventoryManager.get_low_stock_items()
        products = [item.product for item in low_stock_items]
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Get out of stock products"""
        out_of_stock_items = InventoryManager.get_out_of_stock_items()
        products = [item.product for item in out_of_stock_items]
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get products expiring within 30 days"""
        days = request.query_params.get('days', 30)
        expiring = InventoryManager.get_expiring_items(int(days))
        serializer = self.get_serializer(expiring, many=True)
        return Response(serializer.data)


class InventoryViewSet(viewsets.ViewSet):
    """Inventory management"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get inventory summary"""
        inventory_value = InventoryManager.calculate_inventory_value()
        low_stock_count = Inventory.objects.filter(quantity_on_hand__lte=F('reorder_level')).count()
        out_of_stock_count = Inventory.objects.filter(quantity_on_hand=0).count()
        
        return Response({
            'total_inventory_value': inventory_value,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'total_products': Inventory.objects.count(),
        })


class CustomerViewSet(viewsets.ModelViewSet):
    """Customer management"""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email', 'phone']


class SaleViewSet(viewsets.ModelViewSet):
    """Sales transactions"""
    queryset = Sale.objects.select_related('cashier', 'customer').prefetch_related('items')
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['payment_method', 'created_at']
    ordering = ['-created_at']
    
    def create(self, request, *args, **kwargs):
        """Create new sale with items"""
        data = request.data
        
        # Create sale
        sale = Sale.objects.create(
            cashier=request.user,
            customer=data.get('customer'),
            total_amount=data.get('total_amount'),
            discount=data.get('discount', 0),
            tax=data.get('tax', 0),
            final_amount=data.get('final_amount'),
            payment_method=data.get('payment_method'),
            reference_number=data.get('reference_number', '')
        )
        
        # Create sale items and update inventory
        for item_data in data.get('items', []):
            product = Product.objects.get(id=item_data['product_id'])
            quantity = item_data['quantity']
            
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                unit_price=item_data.get('unit_price', product.selling_price)
            )
            
            # Update inventory
            InventoryManager.update_stock(product, quantity, 'out')
        
        serializer = self.get_serializer(sale)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """Get daily sales summary"""
        date = request.query_params.get('date')
        if date:
            from datetime import datetime
            date = datetime.strptime(date, '%Y-%m-%d').date()
        
        sales = SalesAnalytics.get_daily_sales(date)
        
        return Response({
            'date': date or timezone.now().date(),
            'total_sales': SalesAnalytics.calculate_total_sales(sales),
            'total_profit': SalesAnalytics.calculate_total_profit(sales),
            'transaction_count': sales.count(),
            'top_products': list(SalesAnalytics.get_top_products(sales, 5)),
            'payment_distribution': list(SalesAnalytics.get_sales_by_method(sales)),
        })
    
    @action(detail=False, methods=['get'])
    def period_summary(self, request):
        """Get sales summary for period"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        from datetime import datetime
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        report = ReportGenerator.generate_period_report(start_date, end_date)
        return Response(report)
    
    @action(detail=False, methods=['get'])
    def sales_trend(self, request):
        """Get sales trend for last N days"""
        days = int(request.query_params.get('days', 7))
        trend = SalesAnalytics.get_daily_trend(days)
        return Response(list(trend))
    
    @action(detail='', methods=['post'])
    def refund_sale(self, request, pk=None):
        """Process refund for a sale"""
        sale = self.get_object()
        
        if sale.is_refunded:
            return Response(
                {'error': 'Sale already refunded'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Restore inventory
        for item in sale.items.all():
            InventoryManager.update_stock(item.product, item.quantity, 'in')
        
        sale.is_refunded = True
        sale.save()
        
        serializer = self.get_serializer(sale)
        return Response(serializer.data)


class SupplierViewSet(viewsets.ModelViewSet):
    """Supplier management"""
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name', 'email', 'contact_person']


class CashDrawerViewSet(viewsets.ModelViewSet):
    """Cash drawer management"""
    queryset = CashDrawer.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_open', 'cashier']
    
    @action(detail=False, methods=['get'])
    def open_drawer(self, request):
        """Get or create open cash drawer for current user"""
        drawer = CashDrawer.objects.filter(cashier=request.user, is_open=True).first()
        
        if not drawer:
            opening_balance = request.query_params.get('opening_balance', 0)
            drawer = CashDrawer.objects.create(
                cashier=request.user,
                opening_balance=opening_balance
            )
        
        return Response({
            'id': drawer.id,
            'opening_balance': drawer.opening_balance,
            'opened_at': drawer.opened_at
        })
    
    @action(detail='', methods=['post'])
    def close_drawer(self, request, pk=None):
        """Close cash drawer"""
        drawer = self.get_object()
        drawer.closing_balance = request.data.get('closing_balance')
        drawer.closed_at = timezone.now()
        drawer.is_open = False
        drawer.save()
        
        return Response({
            'message': 'Drawer closed',
            'opening': drawer.opening_balance,
            'closing': drawer.closing_balance,
            'difference': drawer.closing_balance - drawer.opening_balance
        })
