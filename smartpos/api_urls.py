from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'categories', api_views.CategoryViewSet, basename='category')
router.register(r'products', api_views.ProductViewSet, basename='product')
router.register(r'inventory', api_views.InventoryViewSet, basename='inventory')
router.register(r'customers', api_views.CustomerViewSet, basename='customer')
router.register(r'sales', api_views.SaleViewSet, basename='sale')
router.register(r'suppliers', api_views.SupplierViewSet, basename='supplier')
router.register(r'expenses', api_views.ExpenseViewSet, basename='expense')
router.register(r'cash-drawers', api_views.CashDrawerViewSet, basename='cashdrawer')
router.register(r'purchases', api_views.PurchaseViewSet, basename='purchase')

urlpatterns = [
    path('', include(router.urls)),
]
