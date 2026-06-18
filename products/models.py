from decimal import Decimal

from django.db import models
from django.db.models import Avg, Sum
from users.models import User


def calculate_shipping_fee(subtotal, region=None, district=None):
    amount = Decimal(str(subtotal or 0))
    if amount >= Decimal('1000000'):
        return Decimal('0.00')
    if amount >= Decimal('200000'):
        return Decimal('5000.00')
    if region or district:
        return Decimal('12000.00')
    return Decimal('10000.00')


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name="Kategoriya nomi")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, null=True, verbose_name="Tavsif")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Rasm")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Kategoriya")
    name = models.CharField(max_length=300, verbose_name="Mahsulot nomi")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    sku = models.CharField(max_length=80, blank=True, null=True, unique=True, verbose_name="SKU kodi")
    description = models.TextField(blank=True, null=True, verbose_name="Tavsif")
    specifications = models.TextField(blank=True, null=True, verbose_name="Xususiyatlar")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Narx (so'm)")
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Eski narx")
    brand = models.CharField(max_length=150, blank=True, null=True, verbose_name="Brend")
    color = models.CharField(max_length=80, blank=True, null=True, verbose_name="Rangi")
    warranty = models.CharField(max_length=100, blank=True, null=True, verbose_name="Kafolat muddati")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Asosiy rasm")
    stock = models.PositiveIntegerField(default=0, verbose_name="Ombordagi miqdor")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")
    is_featured = models.BooleanField(default=False, verbose_name="Tavsiya etilgan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int(((self.old_price - self.price) / self.old_price) * 100)
        return 0

    def is_in_stock(self):
        return self.stock > 0

    def average_rating(self):
        result = self.reviews.aggregate(avg=Avg('rating'))['avg']
        return round(float(result or 0), 1)

    def review_count(self):
        return self.reviews.count()

    def sold_count(self):
        result = OrderItem.objects.filter(
            product=self,
            order__status__in=['processing', 'shipped', 'delivered']
        ).aggregate(total=Sum('quantity'))['total']
        return int(result or 0)

    def gallery_items(self):
        return list(self.images.all())


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Mahsulot")
    image = models.ImageField(upload_to='products/gallery/', verbose_name="Qo'shimcha rasm")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Tartib raqami")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mahsulot rasmi"
        verbose_name_plural = "Mahsulot rasmlari"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.product.name} rasm #{self.order + 1}"


class ProductReview(models.Model):
    RATING_CHOICES = [
        (1, '1 yulduz'),
        (2, '2 yulduz'),
        (3, '3 yulduz'),
        (4, '4 yulduz'),
        (5, '5 yulduz'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_reviews', verbose_name="Foydalanuvchi")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Mahsulot")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, verbose_name="Baho")
    comment = models.TextField(blank=True, null=True, verbose_name="Izoh")
    image = models.ImageField(upload_to='reviews/', blank=True, null=True, verbose_name="Izoh rasmi")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mahsulot izohi"
        verbose_name_plural = "Mahsulot izohlari"
        ordering = ['-created_at']
        unique_together = ['user', 'product']

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating} yulduz"


class Banner(models.Model):
    title = models.CharField(max_length=200, verbose_name="Sarlavha")
    subtitle = models.CharField(max_length=300, blank=True, null=True, verbose_name="Qisqa matn")
    button_text = models.CharField(max_length=80, blank=True, null=True, verbose_name="Tugma matni")
    button_url = models.CharField(max_length=300, blank=True, null=True, verbose_name="Havola")
    image = models.ImageField(upload_to='banners/', blank=True, null=True, verbose_name="Banner rasmi")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Banner"
        verbose_name_plural = "Bannerlar"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Coupon(models.Model):
    code = models.CharField(max_length=40, unique=True, verbose_name="Kupon kodi")
    discount_type = models.CharField(
        max_length=20,
        choices=[('percent', 'Foiz'), ('amount', "So'm")],
        default='percent',
        verbose_name="Chegirma turi"
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Chegirma qiymati")
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Minimal buyurtma")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")
    expires_at = models.DateTimeField(blank=True, null=True, verbose_name="Muddati")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kupon"
        verbose_name_plural = "Kuponlar"
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def discount_amount(self, subtotal):
        if not self.is_active:
            return Decimal('0.00')
        if subtotal < self.min_order_amount:
            return Decimal('0.00')
        if self.discount_type == 'percent':
            return min(subtotal * (self.discount_value / Decimal('100')), subtotal)
        return min(self.discount_value, subtotal)


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', verbose_name="Foydalanuvchi")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Savat"
        verbose_name_plural = "Savatlar"

    def __str__(self):
        return f"{self.user.username} savati"

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())

    def shipping_fee(self):
        return calculate_shipping_fee(self.total_price())

    def grand_total_price(self):
        return self.total_price() + self.shipping_fee()

    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="Savat")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Mahsulot")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Miqdori")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Savat elementi"
        verbose_name_plural = "Savat elementlari"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def total_price(self):
        if self.product is None or self.product.price is None or not self.quantity:
            return Decimal('0.00')
        return self.product.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'To\'lov kutilmoqda'),
        ('processing', 'Tasdiqlandi'),
        ('shipped', 'Yuborildi'),
        ('delivered', 'Yetkazildi'),
        ('cancelled', 'Bekor qilindi'),
    ]

    PAYMENT_CHOICES = [
        ('cash', 'Naqd pul'),
        ('uzcard', 'Uzcard'),
        ('humo', 'Humo'),
        ('card', 'Karta'),
        ('click', 'Click'),
        ('payme', 'Payme'),
        ('uzumbank', 'Uzum Bank'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="Foydalanuvchi")
    full_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="To'liq ism")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Holati")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash', verbose_name="To'lov usuli")
    region = models.CharField(max_length=120, blank=True, null=True, verbose_name="Viloyat")
    district = models.CharField(max_length=120, blank=True, null=True, verbose_name="Tuman/Shahar")
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, blank=True, null=True, related_name='orders', verbose_name="Kupon")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Chegirma")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Mahsulotlar summasi")
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Yetkazib berish")
    shipping_address = models.TextField(verbose_name="Yetkazib berish manzili")
    phone = models.CharField(max_length=15, verbose_name="Telefon")
    note = models.TextField(blank=True, null=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ['-created_at']

    def __str__(self):
        if self.id:
            return f"Buyurtma #{self.id} - {self.user.username}"
        return f"Yangi buyurtma - {self.user.username}"

    def grand_total_price(self):
        return (self.total_price or 0) + (self.shipping_fee or 0) - (self.discount_amount or 0)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Buyurtma")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Mahsulot")
    quantity = models.PositiveIntegerField(verbose_name="Miqdori")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Narx")

    class Meta:
        verbose_name = "Buyurtma elementi"
        verbose_name_plural = "Buyurtma elementlari"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def total_price(self):
        if self.price is None or not self.quantity:
            return Decimal('0.00')
        return self.price * self.quantity


class ContactMessage(models.Model):
    name = models.CharField(max_length=150, verbose_name="Ism")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=30, blank=True, null=True, verbose_name="Telefon")
    message = models.TextField(verbose_name="Xabar")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, verbose_name="O'qilganmi")

    class Meta:
        verbose_name = "Kontakt xabari"
        verbose_name_plural = "Kontakt xabarlar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"


class SupportMessage(models.Model):
    name = models.CharField(max_length=150, verbose_name="Ism")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    message = models.TextField(verbose_name="Xabar")
    created_at = models.DateTimeField(auto_now_add=True)
    is_answered = models.BooleanField(default=False, verbose_name="Javob berilganmi")

    class Meta:
        verbose_name = "Chat support xabari"
        verbose_name_plural = "Chat support xabarlari"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - chat"
