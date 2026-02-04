from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django import forms
from django.db.models import Sum, F
from django.core.mail import send_mail
from django.conf import settings
from .models import Product, Category, Sale, Order, OrderItem, Wishlist

# 1. LANDING PAGE (Trending + Categories + Skin Types)
def landing_page(request):
    # Stock wale top 4 products
    trending = Product.objects.filter(stock__gt=0)[:4]
    categories = Category.objects.all()
    
    skin_types = [
        {'name': 'Oily', 'img': 'https://i.pinimg.com/1200x/e4/40/f9/e440f959f5531dde9c1cf9adb96ef02f.jpg'},
        {'name': 'Dry', 'img': 'https://i.pinimg.com/1200x/86/8d/a4/868da4e3d4009701d1fd301bfb515ae1.jpg'},
        {'name': 'Sensitive', 'img': 'https://i.pinimg.com/1200x/4c/7c/27/4c7c273c75675abb884ab50bc28ea0d4.jpg'},
        {'name': 'Combination', 'img': 'https://i.pinimg.com/736x/4b/fd/e5/4bfde508132a7e68c121a556c270880a.jpg'},
    ]
    
    context = {
        'trending': trending,
        'categories': categories,
        'skin_types': skin_types,
        'is_logged_in': request.user.is_authenticated
    }
    return render(request, 'main/landing.html', context)

def product_list(request):
    query = request.GET.get('q')
    skin_filter = request.GET.get('skin_type')
    category_filter = request.GET.get('category')
    
    products = Product.objects.all().select_related('category')

    if query:
        products = products.filter(name__icontains=query) | products.filter(brand__icontains=query)
    
    if skin_filter:
        products = products.filter(skin_type__iexact=skin_filter)

    if category_filter:
        try:
            category_obj = Category.objects.get(id=category_filter)
        except Category.DoesNotExist:
            category_obj = None
        else:
            products = products.filter(category=category_obj)
    
    categories = Category.objects.all()

    context = {
        'products': products,
        'query': query or '',
        'current_skin': skin_filter or '',
        'current_category': category_obj if category_filter and category_obj else None,
        'categories': categories,
    }
    return render(request, 'main/product_list.html', context)

def product_detail(request, pk):
    product = get_object_or_404(Product, id=pk)
    return render(request, 'main/detail.html', {'product': product})

# Admin product form
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'brand', 'category', 'price', 'cost_price', 'stock', 'ingredients', 'is_vegan', 'image', 'skin_type']

@staff_member_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product created successfully.')
            return redirect('admin_dashboard')
    else:
        form = ProductForm()
    return render(request, 'main/product_form.html', {'form': form})

@staff_member_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('admin_dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'main/product_form.html', {'form': form, 'product': product})

@staff_member_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully.')
        return redirect('admin_dashboard')
    return render(request, 'main/product_delete_confirm.html', {'product': product})

@staff_member_required
def admin_dashboard(request):
    # Render the dashboard page; the charts will be populated via AJAX
    # Provide an initial default last-7-days dataset on first load
    from django.utils import timezone
    today = timezone.now().date()
    week_ago = today - timezone.timedelta(days=6)

    recent_orders = Order.objects.all().order_by('-created_at')[:12]

    context = {
        'default_start': week_ago.strftime('%Y-%m-%d'),
        'default_end': today.strftime('%Y-%m-%d'),
        'inventory_value': Product.objects.aggregate(total=Sum(F('price') * F('stock')))['total'] or 0,
        'products': Product.objects.all()[:50],
        'recent_orders': recent_orders,
    }
    return render(request, 'main/admin_dashboard.html', context)


@staff_member_required
def admin_sales_data(request):
    """Return sales aggregates and timeseries JSON for a date range (GET params: start=YYYY-MM-DD, end=YYYY-MM-DD)."""
    from django.db.models.functions import TruncDate
    from django.utils import timezone
    import datetime

    start = request.GET.get('start')
    end = request.GET.get('end')

    today = timezone.now().date()
    if not end:
        end = today
    else:
        end = datetime.date.fromisoformat(end)
    if not start:
        start = end - timezone.timedelta(days=6)
    else:
        start = datetime.date.fromisoformat(start)

    sales = Sale.objects.filter(sold_at__date__gte=start, sold_at__date__lte=end)

    # Totals
    total_rev = sales.aggregate(total=Sum(F('sale_price') * F('quantity')))['total'] or 0
    total_units = sales.aggregate(total=Sum('quantity'))['total'] or 0

    profit = 0
    for s in sales:
        profit += (s.sale_price - s.product.cost_price) * s.quantity

    # Daily series
    daily_qs = (sales.annotate(day=TruncDate('sold_at'))
                .values('day')
                .annotate(total_qty=Sum('quantity'), revenue=Sum(F('sale_price') * F('quantity')))
                .order_by('day'))

    labels = [entry['day'].strftime('%Y-%m-%d') for entry in daily_qs]
    quantities = [int(entry['total_qty']) for entry in daily_qs]
    revenues = [float(entry['revenue'] or 0) for entry in daily_qs]

    # Product breakdown (top 10 by revenue)
    prod_qs = (sales.values('product__id', 'product__brand', 'product__name')
               .annotate(total_rev=Sum(F('sale_price') * F('quantity')))
               .order_by('-total_rev')[:10])

    prod_labels = [f"{p['product__brand']} - {p['product__name']}" for p in prod_qs]
    prod_revs = [float(p['total_rev'] or 0) for p in prod_qs]

    from django.http import JsonResponse
    return JsonResponse({
        'labels': labels,
        'quantities': quantities,
        'revenues': revenues,
        'total_revenue': float(total_rev),
        'total_units': int(total_units or 0),
        'profit': float(profit),
        'product_labels': prod_labels,
        'product_revenues': prod_revs,
    })


@staff_member_required
def admin_export_sales_csv(request):
    """Export sales in CSV for a date range (start, end)."""
    import datetime, csv
    from django.http import HttpResponse
    from django.utils import timezone

    start = request.GET.get('start')
    end = request.GET.get('end')
    today = timezone.now().date()
    if not end:
        end = today
    else:
        end = datetime.date.fromisoformat(end)
    if not start:
        start = end - timezone.timedelta(days=6)
    else:
        start = datetime.date.fromisoformat(start)

    sales = Sale.objects.filter(sold_at__date__gte=start, sold_at__date__lte=end).order_by('sold_at')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_{start}_{end}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Sale ID', 'Product ID', 'Brand', 'Name', 'Quantity', 'Sale Price', 'Total', 'Sold At'])

    for s in sales:
        writer.writerow([s.id, s.product.id, s.product.brand, s.product.name, s.quantity, float(s.sale_price), float(s.sale_price * s.quantity), s.sold_at.isoformat()])

    return response


def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    
    cart[product_id_str] = cart.get(product_id_str, 0) + 1
    request.session['cart'] = cart
    return redirect('cart_detail')

def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    grand_total = 0
    
    for p_id, quantity in cart.items():
        product = get_object_or_404(Product, id=p_id)
        total_price = product.price * quantity
        grand_total += total_price
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total_price': total_price,
        })
        
    return render(request, 'main/cart.html', {
        'cart_items': cart_items,
        'grand_total': grand_total
    })

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    if product_id_str in cart:
        del cart[product_id_str]
        request.session['cart'] = cart
    return redirect('cart_detail')

from decimal import Decimal

def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.info(request, 'Your cart is empty.')
        return redirect('cart_detail')

    cart_items = []
    grand_total = Decimal('0')
    for p_id, quantity in cart.items():
        product = get_object_or_404(Product, id=p_id)
        total_price = product.price * quantity
        grand_total += total_price
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total_price': total_price,
        })

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        if not payment_method:
            messages.error(request, 'Please select a payment method.')
            return redirect('checkout')

        # Check stock availability
        for it in cart_items:
            if it['quantity'] > it['product'].stock:
                messages.error(request, f"Not enough stock for {it['product'].name}.")
                return redirect('cart_detail')

        # Create order
        total = Decimal('0')
        for it in cart_items:
            # it['total_price'] is already a Decimal from the model field; aggregate safely
            total += it['total_price']

        order = Order.objects.create(user=(request.user if request.user.is_authenticated else None), payment_method=payment_method, total=total)

        # Create OrderItems, Sale records and decrement stock
        for it in cart_items:
            OrderItem.objects.create(order=order, product=it['product'], quantity=it['quantity'], price=it['product'].price)
            Sale.objects.create(product=it['product'], quantity=it['quantity'], sale_price=it['product'].price, order=order)
            prod = it['product']
            prod.stock = prod.stock - it['quantity']
            prod.save()

        # Clear cart
        request.session['cart'] = {}
        messages.success(request, 'Your order has been placed successfully!')
        return redirect('checkout_success')

    return render(request, 'main/checkout.html', {
        'cart_items': cart_items,
        'grand_total': grand_total
    })


def checkout_success(request):
    return render(request, 'main/checkout_success.html')


import logging
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

def subscribe_newsletter(request):
    """Newsletter subscribe endpoint: validates email, stores subscriber, sends welcome mail and logs failures."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            messages.error(request, 'Please provide a valid email address to subscribe.')
            return redirect('home')

        # validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return redirect('home')

        try:
            from user_auth.models import NewsletterSubscriber
            sub, created = NewsletterSubscriber.objects.get_or_create(email=email)
        except Exception as exc:
            # Likely DB error (migration missing or DB down). Log details and show friendly message.
            logger.exception('Failed to create NewsletterSubscriber for %s', email)
            if settings.DEBUG:
                messages.error(request, f'Unable to subscribe: {exc}')
            else:
                messages.error(request, 'Unable to subscribe at the moment. Please try again later.')
            return redirect('home')

        if created:
            subject = 'Welcome to Glow & Beauty'
            message = 'Thanks for joining the Glow Club! Use code GLOW10 for 10% off your first order.\n\n— Glow & Beauty Team'
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
                messages.success(request, 'Thanks for subscribing! Check your email for a welcome message.')
            except Exception as exc:
                logger.exception('Failed to send welcome email to %s', email)
                # We still show success because subscription succeeded; email will be retried manually.
                messages.success(request, 'Thanks for subscribing! We will send a welcome email shortly.')
        else:
            messages.info(request, 'This email is already subscribed.')
    return redirect('home')


@login_required
def account_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'main/account_orders.html', {'orders': orders})


@login_required
def reorder(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.user != request.user:
        messages.error(request, 'You cannot reorder someone else\'s order.')
        return redirect('account_orders')

    if request.method == 'POST':
        cart = request.session.get('cart', {})
        for item in order.items.all():
            pid = str(item.product.id)
            cart[pid] = cart.get(pid, 0) + item.quantity
        request.session['cart'] = cart
        messages.success(request, 'Items added to your cart. You can proceed to checkout.')
        return redirect('cart_detail')

    return render(request, 'main/account_reorder_confirm.html', {'order': order})


@login_required
def account_wishlist(request):
    wlist = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'main/account_wishlist.html', {'wishlist': wlist})


def about_us(request):
    return render(request, 'main/about.html')