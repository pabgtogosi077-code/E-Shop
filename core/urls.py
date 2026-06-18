from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('', include('products.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Admin panel sozlamalari
admin.site.site_header = "E-Shop Admin Panel"
admin.site.site_title = "E-Shop"
admin.site.index_title = "Boshqaruv Paneli"
