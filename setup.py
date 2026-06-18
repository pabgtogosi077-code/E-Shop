"""
E-Shop loyihasini avtomatik sozlash skripti.
Ishlatish: python setup.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import Category, Product

User = get_user_model()

print("=" * 50)
print("  E-Shop loyihasi sozlanmoqda...")
print("=" * 50)

# Superuser yaratish
if not User.objects.filter(username='ZAHON').exists():
    user = User.objects.create_superuser(
        username='ZAHON',
        email='admin@eshop.uz',
        password='ZAHON.COM',
        first_name='Admin',
        last_name='ZAHON',
    )
    print("✅ Superuser yaratildi: ZAHON / ZAHON.COM")
else:
    print("ℹ️  Superuser allaqachon mavjud: ZAHON")

# Namuna kategoriyalar
categories_data = [
    ('Elektronika', 'elektronika'),
    ('Kiyim-kechak', 'kiyim-kechak'),
    ('Maishiy texnika', 'maishiy-texnika'),
    ('Kitoblar', 'kitoblar'),
    ('Sport', 'sport'),
    ('Oziq-ovqat', 'oziq-ovqat'),
]

created_cats = {}
for name, slug in categories_data:
    cat, created = Category.objects.get_or_create(slug=slug, defaults={'name': name})
    created_cats[slug] = cat
    if created:
        print(f"✅ Kategoriya: {name}")

# Namuna mahsulotlar
products_data = [
    {
        'name': 'Samsung Galaxy A54',
        'slug': 'samsung-galaxy-a54',
        'category': 'elektronika',
        'price': 4500000,
        'old_price': 5200000,
        'stock': 15,
        'is_featured': True,
        'description': 'Samsung Galaxy A54 - 6.4 dyuymli ekran, 128GB xotira, 50MP kamera.'
    },
    {
        'name': 'iPhone 15',
        'slug': 'iphone-15',
        'category': 'elektronika',
        'price': 12000000,
        'old_price': 13500000,
        'stock': 8,
        'is_featured': True,
        'description': 'Apple iPhone 15 - A16 chip, 48MP kamera, USB-C.'
    },
    {
        'name': 'Nike Air Max',
        'slug': 'nike-air-max',
        'category': 'sport',
        'price': 890000,
        'old_price': 1100000,
        'stock': 25,
        'is_featured': True,
        'description': "Nike Air Max sport poyabzali - yuqori qulaylik va uzoq muddatli chidamlilik."
    },
    {
        'name': 'Adidas Ultraboost',
        'slug': 'adidas-ultraboost',
        'category': 'sport',
        'price': 1200000,
        'stock': 12,
        'is_featured': False,
        'description': "Adidas Ultraboost - eng qulay yugurish poyabzali."
    },
    {
        'name': 'Erkaklar ko\'ylagi',
        'slug': 'erkaklar-koylagi',
        'category': 'kiyim-kechak',
        'price': 150000,
        'old_price': 200000,
        'stock': 50,
        'is_featured': False,
        'description': "100% paxta, klassik uslub."
    },
    {
        'name': 'Samsung 55" Smart TV',
        'slug': 'samsung-55-smart-tv',
        'category': 'maishiy-texnika',
        'price': 8900000,
        'old_price': 10500000,
        'stock': 5,
        'is_featured': True,
        'description': '55 dyuymli 4K Smart TV, WiFi, Bluetooth.'
    },
    {
        'name': 'Python Dasturlash',
        'slug': 'python-dasturlash-kitobi',
        'category': 'kitoblar',
        'price': 89000,
        'stock': 100,
        'is_featured': False,
        'description': "Python dasturlash tili bo'yicha to'liq qo'llanma."
    },
    {
        'name': 'LG Muzlatgich',
        'slug': 'lg-muzlatgich',
        'category': 'maishiy-texnika',
        'price': 5600000,
        'old_price': 6200000,
        'stock': 7,
        'is_featured': True,
        'description': 'LG No-Frost muzlatgich, 320L, A++ energiya.'
    },
]

for pd in products_data:
    if not Product.objects.filter(slug=pd['slug']).exists():
        Product.objects.create(
            name=pd['name'],
            slug=pd['slug'],
            category=created_cats[pd['category']],
            price=pd['price'],
            old_price=pd.get('old_price'),
            stock=pd['stock'],
            is_featured=pd['is_featured'],
            is_active=True,
            description=pd['description'],
        )
        print(f"✅ Mahsulot: {pd['name']}")

print("\n" + "=" * 50)
print("  ✅ Sozlash muvaffaqiyatli tugadi!")
print("=" * 50)
print(f"\n🔐 Admin panel: http://127.0.0.1:8000/admin/")
print(f"   Login:    ZAHON")
print(f"   Password: ZAHON.COM")
print(f"\n🌐 Sayt: http://127.0.0.1:8000/")
print("=" * 50)
