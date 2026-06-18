import csv
from decimal import Decimal
from io import StringIO

from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
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
    ProductImage,
    ProductReview,
    SupportMessage,
    calculate_shipping_fee,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Mahsulotlar soni"


class ProductImageInline(admin.StackedInline):
    model = ProductImage
    extra = 0
    max_num = 5
    fields = ['image', 'order']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ['product', 'quantity', 'price', 'total_price']
    readonly_fields = ['total_price']

    def total_price(self, obj):
        return f"{obj.total_price():,.0f} so'm"
    total_price.short_description = "Jami"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['image_tag', 'sku', 'name', 'category', 'brand', 'price', 'stock', 'rating_display', 'review_count_display', 'sold_count_display', 'is_active', 'is_featured', 'created_at']
    list_filter = ['is_active', 'is_featured', 'category', 'brand', 'color']
    search_fields = ['name', 'description', 'brand', 'color', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'is_featured', 'stock']
    list_per_page = 20
    ordering = ['-created_at']
    inlines = [ProductImageInline]
    actions = ['export_products_csv']

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover; border-radius:5px;"/>', obj.image.url)
        return "Rasm yo'q"
    image_tag.short_description = "Rasm"

    def rating_display(self, obj):
        return f"{obj.average_rating():.1f}"
    rating_display.short_description = "Baho"

    def review_count_display(self, obj):
        return obj.review_count()
    review_count_display.short_description = "Izohlar"

    def sold_count_display(self, obj):
        return obj.sold_count()
    sold_count_display.short_description = "Sotilgan"

    def export_products_csv(self, request, queryset):
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(['SKU', 'Nomi', 'Kategoriya', 'Brend', 'Rang', 'Narx', 'Ombor', 'Baho', 'Sotilgan'])
        for obj in queryset:
            writer.writerow([obj.sku, obj.name, obj.category.name, obj.brand, obj.color, obj.price, obj.stock, obj.average_rating(), obj.sold_count()])
        response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'
        return response
    export_products_csv.short_description = "CSV eksport"

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('category', 'name', 'slug', 'sku', 'description', 'specifications')
        }),
        ('Narx va Ombor', {
            'fields': ('price', 'old_price', 'brand', 'color', 'warranty', 'stock')
        }),
        ('Asosiy rasm va Ko\'rinish', {
            'fields': ('image', 'is_active', 'is_featured')
        }),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['image_tag', 'product', 'order', 'created_at']
    list_filter = ['product__category']
    search_fields = ['product__name']

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover; border-radius:5px;"/>', obj.image.url)
        return "Rasm yo'q"
    image_tag.short_description = "Rasm"


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'has_image', 'created_at']
    list_filter = ['rating', 'product__category', 'created_at']
    search_fields = ['user__username', 'product__name', 'comment']
    readonly_fields = ['user', 'product', 'rating', 'comment', 'image', 'created_at', 'updated_at']
    actions = ['delete_selected']

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = "Rasm"


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'image_tag', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['title', 'subtitle']

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="70" height="40" style="object-fit:cover; border-radius:5px;"/>', obj.image.url)
        return "Rasm yo'q"
    image_tag.short_description = "Rasm"


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'min_order_amount', 'is_active', 'is_valid_now', 'expires_at', 'created_at']
    list_filter = ['discount_type', 'is_active', 'expires_at', 'created_at']
    search_fields = ['code']
    list_editable = ['is_active']
    list_per_page = 30
    ordering = ['-created_at']
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('code', 'discount_type', 'discount_value', 'min_order_amount')
        }),
        ('Amal qilish va faollik', {
            'fields': ('is_active', 'expires_at')
        }),
    )

    def is_valid_now(self, obj):
        if not obj.is_active:
            return format_html('<span style="color:#ef4444;font-weight:700;">Faol emas</span>')
        if obj.expires_at and obj.expires_at < timezone.now():
            return format_html('<span style="color:#f97316;font-weight:700;">Muddati tugagan</span>')
        return format_html('<span style="color:#16a34a;font-weight:700;">Yaroqli</span>')
    is_valid_now.short_description = "Hozirgi holat"
    is_valid_now.allow_tags = True


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'payment_method_display', 'region', 'district', 'coupon_display', 'total_price_display', 'discount_display', 'shipping_fee_display', 'grand_total_display', 'phone', 'created_at']
    list_filter = ['status', 'payment_method', 'region', 'district', 'created_at']
    search_fields = ['user__username', 'full_name', 'phone', 'shipping_address']
    readonly_fields = ['total_price', 'discount_amount', 'shipping_fee', 'grand_total_display', 'status_buttons', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    list_per_page = 20
    actions = ['tasdiqlash', 'yuborishga_olish', 'yetkazildi_belgilash', 'bekor_qilish', 'export_orders_csv']

    fieldsets = (
        ('Mijoz ma\'lumotlari', {
            'fields': ('user', 'full_name', 'phone', 'region', 'district', 'shipping_address', 'status', 'payment_method')
        }),
        ('Narx, kupon va yetkazib berish', {
            'fields': ('coupon', 'total_price', 'discount_amount', 'shipping_fee', 'grand_total_display', 'note')
        }),
        ('Tizim', {
            'fields': ('status_buttons', 'created_at', 'updated_at')
        }),
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        subtotal = sum(item.total_price() for item in obj.items.all())
        coupon = obj.coupon
        discount = coupon.discount_amount(subtotal) if coupon else Decimal('0.00')
        obj.total_price = subtotal
        obj.discount_amount = discount
        obj.shipping_fee = calculate_shipping_fee(max(subtotal - discount, 0), obj.region, obj.district)
        obj.save(update_fields=['total_price', 'discount_amount', 'shipping_fee', 'updated_at'])

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/status/<str:status>/',
                self.admin_site.admin_view(self.status_update),
                name='products_order_status_update',
            ),
        ]
        return custom_urls + urls

    def status_update(self, request, object_id, status):
        order = get_object_or_404(Order, id=object_id)
        if status not in dict(Order.STATUS_CHOICES):
            messages.error(request, "Noto'g'ri holat tanlandi.")
        else:
            order.status = status
            order.save(update_fields=['status', 'updated_at'])
            messages.success(request, f"Buyurtma #{order.id} holati '{order.get_status_display()}' ga o'zgartirildi.")
        return redirect(reverse('admin:products_order_change', args=[order.id]))

    def status_buttons(self, obj):
        if not obj or not obj.pk:
            return ''
        buttons = [
            ('processing', 'Tasdiqlash', '#198754'),
            ('shipped', 'Yuborildi', '#0d6efd'),
            ('delivered', 'Yetkazildi', '#212529'),
            ('cancelled', 'Bekor qilish', '#dc3545'),
        ]
        html = '<div class="order-status-buttons" style="display:flex;gap:8px;flex-wrap:wrap;">'
        for status_key, label, color in buttons:
            url = reverse('admin:products_order_status_update', args=[obj.pk, status_key])
            html += format_html(
                '<a class="button" href="{}" style="background:{};border-color:{};color:#fff;text-decoration:none;padding:8px 12px;border-radius:8px;font-weight:700;">{}</a>',
                url,
                color,
                color,
                label,
            )
        html += '</div>'
        return format_html('{}', html)
    status_buttons.short_description = "Holatni o'zgartirish"

    def payment_method_display(self, obj):
        return obj.get_payment_method_display()
    payment_method_display.short_description = "To'lov usuli"

    def coupon_display(self, obj):
        return obj.coupon.code if obj.coupon else "—"
    coupon_display.short_description = "Kupon"

    def total_price_display(self, obj):
        return f"{obj.total_price:,.0f} so'm"
    total_price_display.short_description = "Mahsulotlar"

    def discount_display(self, obj):
        return f"-{obj.discount_amount:,.0f} so'm"
    discount_display.short_description = "Chegirma"

    def shipping_fee_display(self, obj):
        return f"{obj.shipping_fee:,.0f} so'm"
    shipping_fee_display.short_description = "Yetkazib berish"

    def grand_total_display(self, obj):
        return f"{obj.grand_total_price():,.0f} so'm"
    grand_total_display.short_description = "Jami"

    def tasdiqlash(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f"{updated} ta buyurtma tasdiqlandi.")
    tasdiqlash.short_description = "Tanlangan buyurtmalarni tasdiqlash"

    def yuborishga_olish(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f"{updated} ta buyurtma yuborishga olingan.")
    yuborishga_olish.short_description = "Yuborishga olish"

    def yetkazildi_belgilash(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f"{updated} ta buyurtma yetkazildi deb belgilandi.")
    yetkazildi_belgilash.short_description = "Yetkazildi deb belgilash"

    def bekor_qilish(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"{updated} ta buyurtma bekor qilindi.")
    bekor_qilish.short_description = "Bekor qilish"

    def export_orders_csv(self, request, queryset):
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(['ID', 'Foydalanuvchi', 'Telefon', 'Holat', 'To\'lov', 'Viloyat', 'Tuman', 'Jami'])
        for obj in queryset:
            writer.writerow([obj.id, obj.user.username, obj.phone, obj.get_status_display(), obj.get_payment_method_display(), obj.region, obj.district, obj.grand_total_price()])
        response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="orders.csv"'
        return response
    export_orders_csv.short_description = "CSV eksport"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'added_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items_display', 'total_price_display', 'shipping_fee_display', 'grand_total_display', 'created_at']
    inlines = [CartItemInline]
    readonly_fields = ['user', 'created_at']

    def total_items_display(self, obj):
        return obj.total_items()
    total_items_display.short_description = "Mahsulotlar soni"

    def total_price_display(self, obj):
        return f"{obj.total_price():,.0f} so'm"
    total_price_display.short_description = "Mahsulotlar"

    def shipping_fee_display(self, obj):
        return f"{obj.shipping_fee():,.0f} so'm"
    shipping_fee_display.short_description = "Yetkazib berish"

    def grand_total_display(self, obj):
        return f"{obj.grand_total_price():,.0f} so'm"
    grand_total_display.short_description = "Jami"


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'phone', 'message']
    actions = ['mark_read']

    def mark_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} ta xabar o'qilgan deb belgilandi.")
    mark_read.short_description = "O'qilgan deb belgilash"


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'is_answered', 'created_at']
    list_filter = ['is_answered', 'created_at']
    search_fields = ['name', 'email', 'message']
    actions = ['mark_answered']

    def mark_answered(self, request, queryset):
        updated = queryset.update(is_answered=True)
        self.message_user(request, f"{updated} ta chat xabariga javob berilgan deb belgilandi.")
    mark_answered.short_description = "Javob berilgan deb belgilash"
