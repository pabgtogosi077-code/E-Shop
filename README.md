# 🛒 E-Shop — To'liq Django E-Commerce Loyihasi

Django 4+ bilan qurilgan to'liq funksional internet do'kon.

---

## 📁 Loyiha tuzilmasi

```
ecommerce_project/
├── core/                      # Asosiy Django sozlamalari
│   ├── settings.py            # Sozlamalar
│   ├── urls.py                # Bosh URL marshrutlash
│   └── wsgi.py
│
├── users/                     # Foydalanuvchilar ilovasi
│   ├── models.py              # User, Profile modellari
│   ├── views.py               # Register, Login, Profile
│   ├── forms.py               # Forma classlari
│   ├── urls.py                # /users/ URL'lari
│   ├── admin.py               # Admin panel sozlamalari
│   └── signals.py             # Profile avtomatik yaratish
│
├── products/                  # Mahsulotlar ilovasi
│   ├── models.py              # Category, Product, Cart, Order
│   ├── views.py               # Barcha mahsulot ko'rinishlari
│   ├── urls.py                # Mahsulot URL'lari
│   └── admin.py               # Mahsulot admin paneli
│
├── templates/                 # HTML shablonlar
│   ├── base.html              # Asosiy shablon
│   ├── users/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── profile.html
│   │   └── edit_profile.html
│   └── products/
│       ├── home.html          # Bosh sahifa
│       ├── product_list.html  # Mahsulotlar ro'yxati
│       ├── product_detail.html# Mahsulot sahifasi
│       ├── cart.html          # Savat
│       ├── checkout.html      # Buyurtma berish
│       ├── orders.html        # Buyurtmalar ro'yxati
│       └── order_detail.html  # Buyurtma tafsilotlari
│
├── static/
│   └── css/style.css          # Umumiy uslublar
│
├── media/                     # Foydalanuvchi yuklagan fayllar
├── manage.py
├── setup.py                   # Avtomatik sozlash skripti
└── README.md
```

---

## 🚀 Ishga tushirish

### 1. Virtual muhit yarating
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Kerakli kutubxonalarni o'rnating
```bash
pip install django pillow
```

### 3. Ma'lumotlar bazasini yarating
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Avtomatik sozlash (superuser + namuna ma'lumotlar)
```bash
python setup.py
```

### 5. Serverni ishga tushiring
```bash
python manage.py runserver
```

---

## 🔐 Admin Panel

| URL | Login | Parol |
|-----|-------|-------|
| http://127.0.0.1:8000/admin/ | `ZAHON` | `ZAHON.COM` |

---

## 🌐 Sahifalar

| Sahifa | URL |
|--------|-----|
| Bosh sahifa | http://127.0.0.1:8000/ |
| Mahsulotlar | http://127.0.0.1:8000/products/ |
| Savat | http://127.0.0.1:8000/cart/ |
| Buyurtmalar | http://127.0.0.1:8000/orders/ |
| Profil | http://127.0.0.1:8000/users/profile/ |
| Kirish | http://127.0.0.1:8000/users/login/ |
| Ro'yxat | http://127.0.0.1:8000/users/register/ |
| Admin | http://127.0.0.1:8000/admin/ |

---

## ✅ Funksiyalar

### 👤 Foydalanuvchilar
- Ro'yxatdan o'tish / Kirish / Chiqish
- Profil ko'rish va tahrirlash
- Profil rasmi yuklash
- Telefon, manzil, bio, website

### 🛍️ Mahsulotlar
- Kategoriyalar bo'yicha filtrlash
- Qidiruv (ism va tavsif bo'yicha)
- Narx oralig'i filtri
- Saralash (narx, sana)
- Chegirmalar ko'rsatish
- Ombor holati

### 🛒 Savat
- Savatga qo'shish
- Miqdorni o'zgartirish
- Olib tashlash
- Jami summa hisoblash

### 📦 Buyurtmalar
- Buyurtma berish
- Yetkazib berish manzili
- Buyurtma holati kuzatuvi
- Buyurtma tarixi

### ⚙️ Admin Panel
- Mahsulot qo'shish/tahrirlash (rasm bilan)
- Kategoriya boshqaruvi
- Buyurtmalar boshqaruvi
- Foydalanuvchilar boshqaruvi
- Rasm miniatyurasi

---

## 🗄️ PostgreSQL (ixtiyoriy)

`core/settings.py` faylida SQLite o'rniga PostgreSQL ishlatish uchun:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ecommerce',
        'USER': 'postgres',
        'PASSWORD': 'admin',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}
```

PostgreSQL uchun:
```bash
pip install psycopg2-binary
```

---

## 📝 Eslatmalar

- `DEBUG = True` — ishlab chiqishda. Production'da `False` qiling.
- `SECRET_KEY` — production'da o'zgartiring.
- `MEDIA_ROOT` — yuklangan fayllar saqlanadigan papka.
- Signal orqali foydalanuvchi yaratilganda profil avtomatik yaratiladi.
