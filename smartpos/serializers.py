# smartpos/serializers.py

from rest_framework import serializers
from .models import (
    CustomUser,
    Category,
    Product,
    Inventory,
    Sale,
    SaleItem,
    Customer,
    Supplier,
    Expense,
    CashDrawer,
    Purchase,
    PurchaseItem
)


# ============================================
# USER SERIALIZERS
# ============================================

class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUser model"""
    
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'role',
            'phone',
            'is_active_staff',
            'first_name',
            'last_name'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=255, write_only=True)


# ============================================
# CATEGORY SERIALIZERS
# ============================================

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'category_type',
            'description',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# ============================================
# INVENTORY SERIALIZERS
# ============================================

class InventorySerializer(serializers.ModelSerializer):
    """Serializer for Inventory model"""
    stock_value = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = Inventory
        fields = [
            'id',
            'product',
            'product_name',
            'quantity_on_hand',
            'reorder_level',
            'stock_value',
            'is_low_stock',
            'last_restocked'
        ]
        read_only_fields = ['id', 'last_restocked']
    
    def get_stock_value(self, obj):
        """Calculate stock value (quantity * cost price)"""
        return float(obj.quantity_on_hand * obj.product.cost_price)
    
    def get_is_low_stock(self, obj):
        """Check if stock is low"""
        return obj.quantity_on_hand <= obj.reorder_level


# ============================================
# PRODUCT SERIALIZERS
# ============================================

class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    stock_quantity = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'barcode',
            'category',
            'category_name',
            'selling_price',
            'stock_quantity',
            'is_active'
        ]
        read_only_fields = ['id']
    
    def get_stock_quantity(self, obj):
        """Get current stock quantity"""
        try:
            return float(obj.inventory.quantity_on_hand)
        except:
            return 0


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for product"""
    inventory = InventorySerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    margin = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'barcode',
            'category',
            'category_name',
            'cost_price',
            'selling_price',
            'unit_of_measure',
            'image',
            'expiry_date',
            'batch_number',
            'bottle_price',
            'glass_price',
            'is_alcohol',
            'is_active',
            'margin',
            'inventory',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_margin(self, obj):
        """Calculate profit margin percentage"""
        if obj.selling_price == 0:
            return 0
        margin = ((obj.selling_price - obj.cost_price) / obj.selling_price) * 100
        return round(margin, 2)


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products"""
    
    class Meta:
        model = Product
        fields = [
            'name',
            'barcode',
            'category',
            'cost_price',
            'selling_price',
            'unit_of_measure',
            'image',
            'expiry_date',
            'batch_number',
            'bottle_price',
            'glass_price',
            'is_alcohol',
            'is_active'
        ]


# ============================================
# CUSTOMER SERIALIZERS
# ============================================

class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model"""
    
    class Meta:
        model = Customer
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'loyalty_points',
            'total_spent',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'loyalty_points', 'total_spent']


# ============================================
# SUPPLIER SERIALIZERS
# ============================================

class SupplierSerializer(serializers.ModelSerializer):
    """Serializer for Supplier model"""
    
    class Meta:
        model = Supplier
        fields = [
            'id',
            'name',
            'contact_person',
            'email',
            'phone',
            'address',
            'outstanding_balance'
        ]
        read_only_fields = ['id', 'outstanding_balance']


# ============================================
# SALE ITEM SERIALIZERS
# ============================================

class SaleItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating sale items"""
    
    class Meta:
        model = SaleItem
        fields = [
            'product',
            'quantity',
            'unit_price'
        ]


class SaleItemDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for sale items"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_barcode = serializers.CharField(source='product.barcode', read_only=True)
    profit = serializers.SerializerMethodField()
    cost_price = serializers.SerializerMethodField()
    
    class Meta:
        model = SaleItem
        fields = [
            'id',
            'product',
            'product_name',
            'product_barcode',
            'quantity',
            'unit_price',
            'subtotal',
            'cost_price',
            'profit'
        ]
        read_only_fields = ['id', 'subtotal']
    
    def get_profit(self, obj):
        """Calculate profit for this item"""
        cost = obj.product.cost_price * obj.quantity
        return float(obj.subtotal - cost)
    
    def get_cost_price(self, obj):
        """Get total cost price"""
        return float(obj.product.cost_price * obj.quantity)


# ============================================
# SALE SERIALIZERS
# ============================================

class SaleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for sale lists"""
    cashier_name = serializers.CharField(source='cashier.username', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True, allow_null=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Sale
        fields = [
            'id',
            'cashier_name',
            'customer_name',
            'final_amount',
            'payment_method',
            'items_count',
            'is_refunded',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_items_count(self, obj):
        """Get number of items in sale"""
        return obj.items.count()


class SaleDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for sales"""
    items = SaleItemDetailSerializer(many=True, read_only=True)
    cashier_name = serializers.CharField(source='cashier.username', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True, allow_null=True)
    profit = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()
    
    class Meta:
        model = Sale
        fields = [
            'id',
            'cashier',
            'cashier_name',
            'customer',
            'customer_name',
            'total_amount',
            'discount',
            'tax',
            'final_amount',
            'payment_method',
            'reference_number',
            'items',
            'profit',
            'total_cost',
            'is_refunded',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'cashier',
            'created_at',
            'profit',
            'total_cost'
        ]
    
    def get_profit(self, obj):
        """Calculate total profit from sale"""
        total_profit = 0
        for item in obj.items.all():
            cost = item.product.cost_price * item.quantity
            total_profit += item.subtotal - cost
        return float(total_profit)
    
    def get_total_cost(self, obj):
        """Calculate total cost price"""
        total_cost = 0
        for item in obj.items.all():
            total_cost += item.product.cost_price * item.quantity
        return float(total_cost)


class SaleCreateSerializer(serializers.Serializer):
    """Serializer for creating sales with items"""
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        required=False,
        allow_null=True
    )
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=[
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('split', 'Split Payment'),
    ])
    reference_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    items = SaleItemCreateSerializer(many=True)
    
    def validate_items(self, value):
        """Validate that items is not empty"""
        if not value:
            raise serializers.ValidationError("Sale must contain at least one item.")
        return value


# ============================================
# EXPENSE SERIALIZERS
# ============================================

class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for Expense model"""
    recorded_by_name = serializers.CharField(source='recorded_by.username', read_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id',
            'category',
            'amount',
            'description',
            'recorded_by',
            'recorded_by_name',
            'created_at'
        ]
        read_only_fields = ['id', 'recorded_by', 'created_at']


# ============================================
# CASH DRAWER SERIALIZERS
# ============================================

class CashDrawerSerializer(serializers.ModelSerializer):
    """Serializer for CashDrawer model"""
    cashier_name = serializers.CharField(source='cashier.username', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = CashDrawer
        fields = [
            'id',
            'cashier',
            'cashier_name',
            'opening_balance',
            'closing_balance',
            'opened_at',
            'closed_at',
            'is_open',
            'duration'
        ]
        read_only_fields = ['id', 'cashier', 'opened_at']
    
    def get_duration(self, obj):
        """Calculate duration the drawer was open"""
        if obj.closed_at:
            delta = obj.closed_at - obj.opened_at
            hours = delta.total_seconds() / 3600
            return round(hours, 2)
        return None


# ============================================
# PURCHASE ITEM SERIALIZERS
# ============================================

class PurchaseItemDetailSerializer(serializers.ModelSerializer):
    """Serializer for purchase items"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = PurchaseItem
        fields = [
            'id',
            'product',
            'product_name',
            'quantity',
            'unit_cost',
            'subtotal'
        ]
        read_only_fields = ['id', 'subtotal']


class PurchaseItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating purchase items"""
    
    class Meta:
        model = PurchaseItem
        fields = [
            'product',
            'quantity',
            'unit_cost'
        ]


# ============================================
# PURCHASE SERIALIZERS
# ============================================

class PurchaseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for purchase lists"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Purchase
        fields = [
            'id',
            'supplier_name',
            'total_amount',
            'status',
            'delivery_date',
            'items_count',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_items_count(self, obj):
        """Get number of items in purchase"""
        return obj.items.count()


class PurchaseDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for purchases"""
    items = PurchaseItemDetailSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    received_by_name = serializers.CharField(source='received_by.username', read_only=True)
    
    class Meta:
        model = Purchase
        fields = [
            'id',
            'supplier',
            'supplier_name',
            'total_amount',
            'received_by',
            'received_by_name',
            'items',
            'delivery_date',
            'status',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'received_by',
            'created_at'
        ]


class PurchaseCreateSerializer(serializers.Serializer):
    """Serializer for creating purchases"""
    supplier = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.all())
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    delivery_date = serializers.DateField()
    status = serializers.ChoiceField(choices=[('pending', 'Pending'), ('received', 'Received')])
    items = PurchaseItemCreateSerializer(many=True)
    
    def validate_items(self, value):
        """Validate that items is not empty"""
        if not value:
            raise serializers.ValidationError("Purchase must contain at least one item.")
        return value


# ============================================
# DASHBOARD/ANALYTICS SERIALIZERS
# ============================================

class DailySalesSerializer(serializers.Serializer):
    """Serializer for daily sales summary"""
    date = serializers.DateField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_profit = serializers.DecimalField(max_digits=15, decimal_places=2)
    transaction_count = serializers.IntegerField()
    average_transaction = serializers.DecimalField(max_digits=15, decimal_places=2)
    top_products = serializers.ListField()
    payment_distribution = serializers.ListField()


class InventorySummarySerializer(serializers.Serializer):
    """Serializer for inventory summary"""
    total_inventory_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    low_stock_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()
    total_products = serializers.IntegerField()


class SalesTrendSerializer(serializers.Serializer):
    """Serializer for sales trend data"""
    date = serializers.DateField()
    total = serializers.DecimalField(max_digits=15, decimal_places=2)