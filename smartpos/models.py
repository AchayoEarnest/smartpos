from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from decimal import Decimal
import uuid

class CustomUser(AbstractUser):
    """Extended User model with roles and additional fields"""
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
        ('accountant', 'Accountant'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cashier')
    is_active_staff = models.BooleanField(default=True)
    phone = models.CharField(max_length=15, blank=True)
    activity_log = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Category(models.Model):
    """Product categories"""
    CATEGORY_TYPES = [
        ('drinks', 'Drinks'),
        ('food', 'Food'),
        ('groceries', 'Groceries'),
        ('household', 'Household Items'),
        ('alcohol', 'Alcohol'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100, unique=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Product inventory"""
    UNIT_CHOICES = [
        ('piece', 'Piece'),
        ('kg', 'Kilogram'),
        ('liter', 'Liter'),
        ('bottle', 'Bottle'),
        ('glass', 'Glass'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    barcode = models.CharField(max_length=100, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_of_measure = models.CharField(max_length=20, choices=UNIT_CHOICES)
    image = models.ImageField(upload_to='products/', blank=True)
    
    # Supermarket specific
    expiry_date = models.DateField(null=True, blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    
    # Bar specific
    bottle_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    glass_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_alcohol = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def margin(self):
        """Calculate profit margin"""
        if self.cost_price == 0:
            return 0
        return ((self.selling_price - self.cost_price) / self.selling_price * 100)


class Inventory(models.Model):
    """Stock tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')
    quantity_on_hand = models.DecimalField(max_digits=10, decimal_places=2)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2)
    last_restocked = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Inventories"
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity_on_hand} units"
    
    @property
    def stock_value(self):
        """Calculate total stock value"""
        return self.quantity_on_hand * self.product.cost_price
    
    @property
    def is_low_stock(self):
        return self.quantity_on_hand <= self.reorder_level


class Supplier(models.Model):
    """Supplier management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    outstanding_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    def __str__(self):
        return self.name


class Customer(models.Model):
    """Customer management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    loyalty_points = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Sale(models.Model):
    """Sales transactions"""
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('split', 'Split Payment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    cashier = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_refunded = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Sale #{self.id} - {self.final_amount}"
    
    @property
    def profit(self):
        """Calculate profit from sale"""
        return sum(item.profit for item in self.items.all())


class SaleItem(models.Model):
    """Individual items in a sale"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    @property
    def profit(self):
        """Calculate profit for this item"""
        cost = self.product.cost_price * self.quantity
        return self.subtotal - cost
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Expense(models.Model):
    """Expense tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.category} - {self.amount}"


class CashDrawer(models.Model):
    """Cash drawer management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    cashier = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    is_open = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Drawer - {self.cashier.username} ({self.opened_at.date()})"


class Purchase(models.Model):
    """Supplier purchases"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    received_by = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField()
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('received', 'Received')], default='pending')
    
    def __str__(self):
        return f"PO#{self.id} - {self.supplier.name}"


class PurchaseItem(models.Model):
    """Items in a purchase order"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

