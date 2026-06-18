from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name = "Profil"
    verbose_name_plural = "Profil"
    extra = 0
    fields = ['profile_picture', 'date_of_birth', 'bio', 'website']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = ['username', 'email', 'phone', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['username', 'email', 'phone', 'first_name', 'last_name']
    ordering = ['-date_joined']
    list_per_page = 20

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('phone', 'address'),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('email', 'phone', 'address'),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'date_of_birth', 'website']
    list_filter = ['date_of_birth']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['user']
