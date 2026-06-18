from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True, verbose_name="Telefon raqami")
    address = models.TextField(blank=True, null=True, verbose_name="Manzil")

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile", verbose_name="Foydalanuvchi")
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True, verbose_name="Profil rasmi")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Tug'ilgan sana")
    bio = models.TextField(blank=True, null=True, verbose_name="Bio")
    website = models.URLField(blank=True, null=True, verbose_name="Veb-sayt")

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profillar"

    def __str__(self):
        return f"Profil: {self.user.username}"
