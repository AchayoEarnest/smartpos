# smartpos/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, F, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
import json
from decimal import Decimal

from .models import (
    Product, Category, Sale, SaleItem, Customer, Supplier,
    Inventory, Expense, CashDrawer, Purchase, PurchaseItem, CustomUser
)


# ============================================
# AUTHENTICATION VIEWS
# ============================================

def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            context = {'error': 'Invalid username or password'}
            return render(request, 'smartpos/login.html', context)
    
    return render(request, 'smartpos/login.html')


def logout_view(request):
    """User logout view"""
    logout(request)
    return redirect('login')


# ============================================
# DASHBOARD VIEW
# ============================================

@login_required(login_url='login')
def dashboard(request):
    """Main dashboard with KPI cards and analytics"""
    today = timezone.now().date()
    
    # Get today's sales
    today_sales = Sale.objects.filter(created_at__date=today)
    today_sales_amount = today_sales.aggregate(Sum('final_amount'))['final_amount__sum'] or Decimal('0')
    today_transactions = today_sales.count()
    
    # Calculate today's profit
    today_profit = Decimal('0')
    for sale in today_sales:
        for item in sale.items.all():
            cost = item.product.cost_price * item.quantity
            today_profit += item.subtotal - cost
    
    # Low stock and out of stock items
    low_stock_count = Inventory.objects.filter(quantity_on_hand__lte=F('reorder_level')).count()
    out_of_stock_count = Inventory.objects.filter(quantity_on_hand=0).count()
    
    # Sales trend (last 7 days)
    last_7_days = timezone.now() - timedelta(days=7)
    sales_trend = Sale.objects.filter(created_at__gte=last_7_days).extra(
        select={'date': 'DATE(created_at)'}
    ).values('date').annotate(total=Sum('final_amount')).order_by('date')
    
    # Top selling products
    top_products = SaleItem.objects.filter(
        sale__created_at__date=today
    ).values('product__name').annotate(
        qty=Sum('quantity'),
        revenue=Sum('subtotal')
    ).order_by('-revenue')[:5]
    
    # Payment method distribution
    payment_dist = today_sales.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('final_amount')
    )
    
    context = {
        'today_sales': float(today_sales_amount),
        'today_transactions': today_transactions,
        'today_profit': float(today_profit),
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'sales_trend': list(sales_trend),
        'top_products': list(top_products),
        'payment_distribution': list(payment_dist),
    }
    
    return render(request, 'smartpos/dashboard.html', context)


# ============================================
# POS VIEWS
# ============================================

@login_required(login_url='login')
def pos_screen(request):
    """Fast checkout interface for cashiers"""
    if request.user.role not in ['cashier', 'manager', 'admin']:
        return redirect('dashboard')
    
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
    }
    
    return render(request, 'smartpos/pos_screen.html', context)


@csrf_exempt
@require_POST
@login_required(login_url='login')
def create_sale(request):
    """API endpoint to create a new sale"""
    try:
        data = json.loads(request.body)
        
        total_amount = Decimal(str(data.get('total_amount', 0)))
        discount = Decimal(str(data.get('discount', 0)))
        tax = Decimal(str(data.get('tax', 0)))
        final_amount = Decimal(str(data.get('final_amount', 0)))
        payment_method = data.get('payment_method', 'cash')
        
        # Create sale
        sale = Sale.objects.create(
            cashier=request.user,
            total_amount=total_amount,
            discount=discount,
            tax=tax,
            final_amount=final_amount,
            payment_method=payment_method,
            reference_number=data.get('reference_number', '')
        )
        
        # Create sale items and update inventory
        for item in data.get('items', []):
            try:
                product = Product.objects.get(id=item['product_id'])
                quantity = Decimal(str(item['quantity']))
                
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=product.selling_price
                )
                
                # Update inventory
                inventory = product.inventory
                inventory.quantity_on_hand -= quantity
                inventory.save()
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'error': f"Product {item['product_id']} not found"})
        
        return JsonResponse({'success': True, 'sale_id': str(sale.id)})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============================================
# PRODUCT MANAGEMENT VIEWS
# ============================================

@login_required(login_url='login')
def product_list(request):
    """List all products with filtering"""
    products = Product.objects.select_related('category', 'inventory').all()
    categories = Category.objects.all()
    
    # Search filter
    search = request.GET.get('search', '')
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(barcode__icontains=search)
        )
    
    # Category filter
    category = request.GET.get('category', '')
    if category:
        products = products.filter(category_id=category)
    
    context = {
        'products': products,
        'categories': categories,
        'search': search,
        'selected_category': category,
    }
    
    return render(request, 'smartpos/product_list.html', context)


@login_required(login_url='login')
def add_product(request):
    """Add new product view"""
    if request.user.role not in ['manager', 'admin']:
        return redirect('dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        barcode = request.POST.get('barcode')
        category_id = request.POST.get('category')
        cost_price = request.POST.get('cost_price')
        selling_price = request.POST.get('selling_price')
        unit_of_measure = request.POST.get('unit_of_measure')
        expiry_date = request.POST.get('expiry_date')
        batch_number = request.POST.get('batch_number')
        is_alcohol = request.POST.get('is_alcohol') == 'on'
        bottle_price = request.POST.get('bottle_price') or None
        glass_price = request.POST.get('glass_price') or None
        
        try:
            category = Category.objects.get(id=category_id)
            
            product = Product.objects.create(
                name=name,
                barcode=barcode,
                category=category,
                cost_price=cost_price,
                selling_price=selling_price,
                unit_of_measure=unit_of_measure,
                expiry_date=expiry_date if expiry_date else None,
                batch_number=batch_number,
                is_alcohol=is_alcohol,
                bottle_price=bottle_price,
                glass_price=glass_price,
                is_active=True
            )
            
            # Create inventory record
            Inventory.objects.create(
                product=product,
                quantity_on_hand=0,
                reorder_level=10
            )
            
            return redirect('product_list')
        except Exception as e:
            context = {
                'categories': Category.objects.all(),
                'error': str(e)
            }
            return render(request, 'smartpos/add_product.html', context)
    
    categories = Category.objects.all()
    return render(request, 'smartpos/add_product.html', {'categories': categories})


# ============================================
# REPORTS VIEW
# ============================================

@login_required(login_url='login')
def sales_report(request):
    """Generate sales reports"""
    period = request.GET.get('period', 'today')
    
    if period == 'today':
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=1)
    elif period == 'week':
        today = timezone.now().date()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
    elif period == 'month':
        today = timezone.now().date()
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = start_date.replace(year=today.year + 1, month=1)
        else:
            end_date = start_date.replace(month=today.month + 1)
    else:
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=1)
    
    sales = Sale.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lt=end_date
    ).select_related('cashier', 'customer').prefetch_related('items')
    
    total_sales = sales.aggregate(Sum('final_amount'))['final_amount__sum'] or Decimal('0')
    total_profit = Decimal('0')
    for sale in sales:
        for item in sale.items.all():
            cost = item.product.cost_price * item.quantity
            total_profit += item.subtotal - cost
    
    avg_transaction = sales.aggregate(Avg('final_amount'))['final_amount__avg'] or Decimal('0')
    
    report_data = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': float(total_sales),
        'total_profit': float(total_profit),
        'total_transactions': sales.count(),
        'average_transaction': float(avg_transaction),
        'sales': sales,
    }
    
    return render(request, 'smartpos/sales_report.html', report_data)