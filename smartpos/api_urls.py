from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'categories', api_views.CategoryViewSet)
router.register(r'products', api_views.ProductViewSet)
router.register(r'customers', api_views.CustomerViewSet)
router.register(r'sales', api_views.SaleViewSet)
router.register(r'suppliers', api_views.SupplierViewSet)
router.register(r'cash-drawers', api_views.CashDrawerViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('inventory/summary/', api_views.InventoryViewSet.as_action_view({'get': 'summary'})),
]
