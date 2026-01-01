from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'role', 'is_active_staff', 'email')
    list_filter = ('role', 'is_active_staff')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'is_active_staff', 'phone')}),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'cost_price', 'selling_price', 'is_active')
    list_filter = ('category', 'is_active', 'is_alcohol')
    search_fields = ('name', 'barcode')

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity_on_hand', 'reorder_level', 'is_low_stock')
    list_filter = ('product__category',)
    search_fields = ('product__name',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'outstanding_balance')
    search_fields = ('name', 'email')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'loyalty_points', 'total_spent')
    search_fields = ('name', 'email', 'phone')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'cashier', 'final_amount', 'payment_method', 'created_at')
    list_filter = ('payment_method', 'created_at')
    search_fields = ('reference_number',)

@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'subtotal', 'profit')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'recorded_by', 'created_at')
    list_filter = ('category', 'created_at')

@admin.register(CashDrawer)
class CashDrawerAdmin(admin.ModelAdmin):
    list_display = ('cashier', 'opening_balance', 'closing_balance', 'is_open', 'opened_at')
    list_filter = ('is_open', 'opened_at')

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'total_amount', 'status', 'delivery_date')
    list_filter = ('status', 'delivery_date')

@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'unit_cost', 'subtotal')