from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Case, Count, FloatField, F, IntegerField, OuterRef, Q, Subquery, Sum, When, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    Banner,
    Cart,
    CartItem,
    Category,
    ContactMessage,
    Coupon,
    Order,
    OrderItem,
    Product,
    ProductReview,
    SupportMessage,
    calculate_shipping_fee,
)

BOUGHT_STATUSES = ['processing', 'shipped', 'delivered']
REGION_CHOICES = [
    'Toshkent', 'Samarqand', 'Buxoro', 'Xorazm', 'Navoiy', 'Jizzax',
    'Sirdaryo', 'Farg\'ona', 'Namangan', 'Andijon', 'Qashqadaryo',
    'Surxondaryo', 'Qoraqalpog\'iston', 'Nukus'
]
DISTRICT_CHOICES = [
    'Buxoro', 'Vobkent', 'Gijduvon', 'Kogon', 'Romitan', 'Shofirkon',
    'Olot', 'Peshku', 'Qorako\'l', 'Jondor'
]


def clean_price(value):
    if not value:
        return None
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def product_stats_queryset():
    sold_subquery = OrderItem.objects.filter(
        product=OuterRef('pk'),
        order__status__in=BOUGHT_STATUSES,
    ).values('product').annotate(total=Sum('quantity')).values('total')

    rating_subquery = ProductReview.objects.filter(
        product=OuterRef('pk')
    ).values('product').annotate(avg=Avg('rating')).values('avg')

    review_count_subquery = ProductReview.objects.filter(
        product=OuterRef('pk')
    ).values('product').annotate(count=Count('id')).values('count')

    return Product.objects.annotate(
        sold_count=Coalesce(Subquery(sold_subquery), 0, output_field=IntegerField()),
        rating_avg=Coalesce(Subquery(rating_subquery), 0.0, output_field=FloatField()),
        rating_count=Coalesce(Subquery(review_count_subquery), 0, output_field=IntegerField()),
    )


def get_active_coupon(code, subtotal):
    coupon = Coupon.objects.filter(code__iexact=code.strip(), is_active=True).first()
    if not coupon:
        return None, Decimal('0.00'), 'Kupon topilmadi.'
    if coupon.expires_at and coupon.expires_at < timezone.now():
        return None, Decimal('0.00'), 'Kupon muddati tugagan.'
    discount = coupon.discount_amount(subtotal)
    if discount <= 0:
        return None, Decimal('0.00'), 'Kupon ushbu buyurtmaga mos kelmadi.'
    return coupon, discount, ''


def home_view(request):
    banner = Banner.objects.filter(is_active=True).first()
    featured_products = product_stats_queryset().filter(is_active=True, is_featured=True).order_by('-rating_avg', '-sold_count')[:8]
    new_products = product_stats_queryset().filter(is_active=True).order_by('-created_at')[:8]
    discount_products = product_stats_queryset().filter(is_active=True, old_price__gt=F('price'))[:4]
    categories = Category.objects.all()[:6]
    return render(request, 'products/home.html', {
        'banner': banner,
        'featured_products': featured_products,
        'new_products': new_products,
        'discount_products': discount_products,
        'categories': categories,
    })


def product_list_view(request):
    products = product_stats_queryset().filter(is_active=True)
    categories = Category.objects.all()

    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query) | Q(brand__icontains=query) | Q(color__icontains=query) | Q(sku__icontains=query)
        )

    category_slug = request.GET.get('category', '').strip()
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    else:
        category = None

    min_price = clean_price(request.GET.get('min_price', ''))
    max_price = clean_price(request.GET.get('max_price', ''))
    if min_price is not None:
        products = products.filter(price__gte=min_price)
    if max_price is not None:
        products = products.filter(price__lte=max_price)

    brand = request.GET.get('brand', '').strip()
    if brand:
        products = products.filter(brand__icontains=brand)

    color = request.GET.get('color', '').strip()
    if color:
        products = products.filter(color__icontains=color)

    sort = request.GET.get('sort', '-created_at')
    if sort == 'popular':
        products = products.order_by('-sold_count', '-rating_avg', '-created_at')
    elif sort == 'rating':
        products = products.order_by('-rating_avg', '-rating_count', '-created_at')
    elif sort in ['price', '-price', '-created_at', 'name']:
        products = products.order_by(sort)
    else:
        sort = '-created_at'
        products = products.order_by(sort)

    return render(request, 'products/product_list.html', {
        'products': products,
        'categories': categories,
        'selected_category': category,
        'query': query,
        'sort': sort,
        'min_price': min_price,
        'max_price': max_price,
        'brand': brand,
        'color': color,
        'regions': REGION_CHOICES,
        'districts': DISTRICT_CHOICES,
    })


def product_detail_view(request, slug):
    product_qs = product_stats_queryset().filter(slug=slug, is_active=True)
    product = get_object_or_404(product_qs)
    reviews = product.reviews.select_related('user').order_by('-created_at')[:8]
    user_review = None
    can_review = False
    if request.user.is_authenticated:
        user_review = ProductReview.objects.filter(user=request.user, product=product).first()
        can_review = OrderItem.objects.filter(order__user=request.user, product=product, order__status__in=BOUGHT_STATUSES).exists()

    related_products = product_stats_queryset().filter(
        category=product.category, is_active=True
    ).exclude(id=product.id).order_by('-sold_count', '-rating_avg')[:6]

    return render(request, 'products/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'user_review': user_review,
        'can_review': can_review,
        'related_products': related_products,
    })


@login_required
def add_review_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    if not OrderItem.objects.filter(order__user=request.user, product=product, order__status__in=BOUGHT_STATUSES).exists():
        messages.error(request, "Faqat ushbu mahsulotni sotib olgan foydalanuvchilar baho berishi mumkin.")
        return redirect('product_detail', slug=product.slug)

    if request.method == 'POST':
        try:
            rating = int(request.POST.get('rating', 0))
        except (TypeError, ValueError):
            rating = 0

        comment = request.POST.get('comment', '').strip()
        image = request.FILES.get('review_image')

        if rating < 1 or rating > 5:
            messages.error(request, "Baho 1 dan 5 gacha bo'lishi kerak.")
            return redirect('product_detail', slug=product.slug)

        if not comment and not image:
            messages.error(request, "Izoh yoki rasm qoldiring.")
            return redirect('product_detail', slug=product.slug)

        review, created = ProductReview.objects.update_or_create(
            user=request.user,
            product=product,
            defaults={'rating': rating, 'comment': comment},
        )
        if image:
            review.image = image
            review.save()

        if created:
            messages.success(request, "Baho va izoh qo'shildi.")
        else:
            messages.success(request, "Baho va izoh yangilandi.")
        return redirect('product_detail', slug=product.slug)

    return redirect('product_detail', slug=product.slug)


@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    subtotal = cart.total_price()
    coupon = None
    discount = Decimal('0.00')
    coupon_message = ''

    # Handle coupon application/removal
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code', '').strip()
        if coupon_code:
            coupon, discount, coupon_message = get_active_coupon(coupon_code, subtotal)
            if coupon:
                request.session['applied_coupon_code'] = coupon.code
                messages.success(request, f"Kupon '{coupon.code}' qo'llanildi. Chegirma: {discount:,.0f} so'm.")
            else:
                if coupon_message:
                    messages.error(request, coupon_message)
                else:
                    messages.error(request, "Noto'g'ri kupon kodi.")
                if 'applied_coupon_code' in request.session:
                    del request.session['applied_coupon_code']
        else: # If coupon code is empty, assume user wants to remove it
            if 'applied_coupon_code' in request.session:
                del request.session['applied_coupon_code']
                messages.info(request, "Kupon olib tashlandi.")
        return redirect('cart') # Redirect to GET request to avoid re-submission

    # Re-evaluate coupon if present in session (for GET requests or after POST)
    if 'applied_coupon_code' in request.session:
        session_coupon_code = request.session['applied_coupon_code']
        coupon, discount, coupon_message = get_active_coupon(session_coupon_code, subtotal)
        if not coupon: # If coupon in session is no longer valid
            del request.session['applied_coupon_code']
            messages.warning(request, f"Sizning '{session_coupon_code}' kuponingiz endi amal qilmaydi.")
            discount = Decimal('0.00') # Reset discount

    shipping_fee = calculate_shipping_fee(max(subtotal - discount, Decimal('0.00')))
    grand_total = subtotal - discount + shipping_fee

    context = {
        'cart': cart,
        'subtotal': subtotal,
        'coupon': coupon,
        'discount': discount,
        'shipping_fee': shipping_fee,
        'grand_total': grand_total,
        'coupon_message': coupon_message, # Pass message for display if needed
    }
    return render(request, 'products/cart.html', context)


@login_required
def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user)

    if product.stock <= 0:
        messages.error(request, "Mahsulot omborda yo'q.")
        return redirect(request.META.get('HTTP_REFERER', 'product_list'))

    quantity = 1
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            quantity = 1
        quantity = max(1, min(quantity, product.stock))

    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    if cart_item.quantity + quantity > product.stock:
        messages.error(request, f"Savatda {product.name} uchun maksimal {product.stock} dona bo'lishi mumkin.")
        return redirect(request.META.get('HTTP_REFERER', 'cart'))

    if not item_created:
        cart_item.quantity += quantity
        cart_item.save()
        messages.success(request, f"'{product.name}' savatga {quantity} dona qo'shildi.")
    else:
        messages.success(request, f"'{product.name}' savatga qo'shildi.")

    return redirect(request.META.get('HTTP_REFERER', 'cart'))


@login_required
def remove_from_cart_view(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Mahsulot savatdan olib tashlandi.")
    return redirect('cart')


@login_required
def update_cart_view(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > cart_item.product.stock:
        messages.error(request, f"Maksimal mavjud miqdor: {cart_item.product.stock} dona")
    elif quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')


def wishlist_view(request):
    wishlist_ids = [int(item) for item in request.session.get('wishlist', []) if str(item).isdigit()]
    products = list(product_stats_queryset().filter(id__in=wishlist_ids, is_active=True))
    ordered_products = [product for product_id in wishlist_ids for product in products if product.id == product_id]
    return render(request, 'products/wishlist.html', {'products': ordered_products})


@login_required
def toggle_wishlist_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    wishlist = []
    for item in request.session.get('wishlist', []):
        try:
            wishlist.append(int(item))
        except (TypeError, ValueError):
            continue

    if product_id in wishlist:
        wishlist.remove(product_id)
        messages.info(request, f"'{product.name}' sevimlilardan olindi.")
    else:
        wishlist.append(product_id)
        messages.success(request, f"'{product.name}' sevimlilarga qo'shildi.")

    request.session['wishlist'] = wishlist
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))


@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'products/orders.html', {'orders': orders})


@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'products/order_detail.html', {'order': order})


@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        messages.error(request, "Savatcha bo'sh!")
        return redirect('cart')

    REGION_CHOICES = [
        'Toshkent', 'Samarqand', 'Buxoro', 'Xorazm', 'Navoiy', 'Jizzax',
        'Sirdaryo', 'Farg\'ona', 'Namangan', 'Andijon', 'Qashqadaryo',
        'Surxondaryo', 'Qoraqalpog\'iston', 'Nukus'
    ]
    DISTRICT_CHOICES = [
        'Buxoro', 'Vobkent', 'Gijduvon', 'Kogon', 'Romitan', 'Shofirkon',
        'Olot', 'Peshku', 'Qorako\'l', 'Jondor'
    ]

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address', '').strip()
        phone = request.POST.get('phone', '').strip()
        full_name = request.POST.get('full_name', '').strip() or request.user.get_full_name() or request.user.username
        note = request.POST.get('note', '').strip()
        payment_method = request.POST.get('payment_method', 'cash')
        region = request.POST.get('region', '').strip()
        district = request.POST.get('district', '').strip()
        coupon_code = request.POST.get('coupon_code', '').strip()
        payment_choices = dict(Order.PAYMENT_CHOICES)

        for item in cart.items.all():
            if item.quantity > item.product.stock:
                messages.error(request, f"{item.product.name} omborda yetarli emas.")
                return redirect('cart')

        if not shipping_address or not phone:
            messages.error(request, "Manzil va telefon raqami majburiy!")
        if payment_method not in payment_choices:
            messages.error(request, "To'lov usuli noto'g'ri tanlandi.")
        subtotal = cart.total_price()
        
        if 'applied_coupon_code' in request.session and not coupon_code:
            coupon_code = request.session['applied_coupon_code']

        coupon, discount, coupon_message = get_active_coupon(coupon_code, subtotal)
        if coupon_code and coupon_message:
            messages.warning(request, coupon_message)

        shipping_fee = calculate_shipping_fee(max(subtotal - discount, 0), region, district)
        grand_total = subtotal - discount + shipping_fee

        errors = [m for m in messages.get_messages(request) if m.tags == 'error']
        if errors:
            return render(request, 'products/checkout.html', {
                'cart': cart,
                'subtotal': subtotal,
                'coupon': coupon,
                'discount': discount,
                'shipping_fee': shipping_fee,
                'grand_total': grand_total,
                'coupon_message': coupon_message,
                'regions': REGION_CHOICES,
                'districts': DISTRICT_CHOICES,
                'shipping_address': shipping_address,
                'phone': phone,
                'full_name': full_name,
                'note': note,
                'payment_method': payment_method,
                'region': region,
                'district': district,
            })

        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            total_price=subtotal,
            discount_amount=discount,
            shipping_fee=shipping_fee,
            payment_method=payment_method,
            region=region,
            district=district,
            coupon=coupon,
            shipping_address=shipping_address,
            phone=phone,
            note=note,
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )
            item.product.stock -= item.quantity
            item.product.save()

        cart.items.all().delete()
        if 'applied_coupon_code' in request.session:
            del request.session['applied_coupon_code']

        messages.success(request, f"Buyurtmangiz #{order.id} muvaffaqiyatli qabul qilindi!")
        return redirect('order_detail', order_id=order.id)

    subtotal = cart.total_price()
    coupon = None
    discount = Decimal('0.00')
    coupon_message = ''

    if 'applied_coupon_code' in request.session:
        session_coupon_code = request.session['applied_coupon_code']
        coupon, discount, coupon_message = get_active_coupon(session_coupon_code, subtotal)
        if not coupon:
            del request.session['applied_coupon_code']
            messages.warning(request, f"Sizning '{session_coupon_code}' kuponingiz endi amal qilmaydi.")
            discount = Decimal('0.00')

    shipping_fee = calculate_shipping_fee(max(subtotal - discount, Decimal('0.00')))
    grand_total = subtotal - discount + shipping_fee
    context = {
        'cart': cart,
        'subtotal': subtotal,
        'coupon': coupon,
        'discount': discount,
        'coupon_message': coupon_message,
        'shipping_fee': shipping_fee,
        'grand_total': grand_total,
        'regions': REGION_CHOICES,
        'districts': DISTRICT_CHOICES,
    }
    return render(request, 'products/checkout.html', context)


def contact_view(request):
    if request.method == 'POST':
        ContactMessage.objects.create(
            name=request.POST.get('name', '').strip(),
            email=request.POST.get('email', '').strip(),
            phone=request.POST.get('phone', '').strip(),
            message=request.POST.get('message', '').strip(),
        )
        messages.success(request, "Xabaringiz yuborildi. Tez orada aloqaga chiqamiz.")
        return redirect('contact')
    return render(request, 'products/contact.html')


def faq_view(request):
    return render(request, 'products/faq.html')


@login_required
def dashboard_view(request):
    if not request.user.is_staff:
        messages.error(request, "Dashboardga faqat admin kirishi mumkin.")
        return redirect('home')
    total_orders = Order.objects.count()
    total_revenue = sum(order.grand_total_price() for order in Order.objects.filter(status__in=BOUGHT_STATUSES))
    total_products = Product.objects.filter(is_active=True).count()
    total_users = Order.objects.values('user').distinct().count()
    return render(request, 'products/dashboard.html', {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_products': total_products,
        'total_users': total_users,
    })


def support_message_view(request):
    if request.method == 'POST':
        SupportMessage.objects.create(
            name=request.POST.get('name', '').strip() or 'Mehmon',
            email=request.POST.get('email', '').strip(),
            message=request.POST.get('message', '').strip(),
        )
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)


def api_products_view(request):
    products = product_stats_queryset().filter(is_active=True)
    query = request.GET.get('q', '')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(brand__icontains=query) | Q(sku__icontains=query))
    data = [{
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'sku': product.sku,
        'price': str(product.price),
        'rating': product.rating_avg,
        'sold_count': product.sold_count,
    } for product in products[:50]]
    return JsonResponse({'count': len(data), 'results': data})


def api_product_detail_view(request, slug):
    product = get_object_or_404(product_stats_queryset(), slug=slug, is_active=True)
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'sku': product.sku,
        'price': str(product.price),
        'rating': product.rating_avg,
        'rating_count': product.rating_count,
        'sold_count': product.sold_count,
    })


@login_required
def api_orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:20]
    return JsonResponse({
        'results': [{
            'id': order.id,
            'status': order.get_status_display(),
            'total': str(order.grand_total_price()),
            'created_at': order.created_at.isoformat(),
        } for order in orders]
    })
