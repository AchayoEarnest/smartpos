from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # POS
    path('pos/', views.pos_screen, name='pos'),
    path('api/create-sale/', views.create_sale, name='create_sale'),
    
    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    
    # Reports
    path('reports/sales/', views.sales_report, name='sales_report'),
]