from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta

# Dashboard View
@login_required
def dashboard(request):
    """Main dashboard with KPI cards and analytics"""
    today = timezone.now().date()
    
    # KPI Calculations
    today_sales = Sale.objects.filter(created_at__date=today).aggregate(
        total=Sum('final_amount'),
        count=Count('id')
    )
    
    today_profit = 0
    for sale in Sale.objects.filter(created_at__date=today):
        today_profit += sale.profit
    
    low_stock = Inventory.objects.filter(is_low_stock=True).count()
    out_of_stock = Inventory.objects.filter(quantity_on_hand=0).count()
    
    # Sales trend (last 7 days)
    last_7_days = timezone.now() - timedelta(days=7)
    sales_trend = Sale.objects.filter(created_at__gte=last_7_days).extra(
        select={'date': 'DATE(created_at)'}
    ).values('date').annotate(total=Sum('final_amount')).order_by('date')
    
    # Top selling products
    top_products = SaleItem.objects.values('product__name').annotate(
        qty=Sum('quantity'),
        revenue=Sum('subtotal')
    ).order_by('-revenue')[:5]
    
    # Payment method distribution
    payment_dist = Sale.objects.filter(created_at__date=today).values(
        'payment_method'
    ).annotate(count=Count('id'))
    
    context = {
        'today_sales': today_sales['total'] or 0,
        'today_transactions': today_sales['count'] or 0,
        'today_profit': today_profit,
        'low_stock_count': low_stock,
        'out_of_stock_count': out_of_stock,
        'sales_trend': list(sales_trend),
        'top_products': list(top_products),
        'payment_distribution': list(payment_dist),
    }
    
    return render(request, 'smartpos/dashboard.html', context)


# POS View
@login_required
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


# Create Sale API
@csrf_exempt
@require_POST
@login_required
def create_sale(request):
    """API to create a new sale"""
    import json
    
    data = json.loads(request.body)
    
    total_amount = Decimal(str(data.get('total_amount', 0)))
    discount = Decimal(str(data.get('discount', 0)))
    tax = Decimal(str(data.get('tax', 0)))
    final_amount = total_amount - discount + tax
    payment_method = data.get('payment_method')
    
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
        product = get_object_or_404(Product, id=item['product_id'])
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
    
    return JsonResponse({'success': True, 'sale_id': str(sale.id)})


# Product Management
@login_required
def product_list(request):
    """List all products"""
    products = Product.objects.all()
    
    return render(request, 'smartpos/product_list.html', {'products': products})


@login_required
def add_product(request):
    """Add new product"""
    if request.user.role not in ['manager', 'admin']:
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Handle form submission
        pass
    
    categories = Category.objects.all()
    return render(request, 'smartpos/add_product.html', {'categories': categories})


# Reports View
@login_required
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
    
    sales = Sale.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lt=end_date
    )
    
    report_data = {
        'total_sales': sales.aggregate(Sum('final_amount'))['final_amount__sum'] or 0,
        'total_transactions': sales.count(),
        'average_transaction': sales.aggregate(Avg('final_amount'))['final_amount__avg'] or 0,
        'sales': sales,
    }
    
    return render(request, 'smartpos/sales_report.html', report_data)


# Authentication Views
def login_view(request):
    """User login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            context = {'error': 'Invalid credentials'}
            return render(request, 'smartpos/login.html', context)
    
    return render(request, 'smartpos/login.html')


def logout_view(request):
    """User logout"""
    logout(request)
    return redirect('login')