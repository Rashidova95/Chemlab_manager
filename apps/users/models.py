from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Elektron pochta")
    first_name = models.CharField(max_length=150, verbose_name="Ism")
    last_name = models.CharField(max_length=150, verbose_name="Familiya")
    username = models.CharField(max_length=150, verbose_name="Foydalanuvchi nomi")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('chemist', 'Kimyogar'),
        ('laborant', 'Laborant'),
        ('viewer', 'Kuzatuvchi'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer', verbose_name="Rol")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon raqami")
    lab_name = models.CharField(max_length=200, blank=True, verbose_name="Laboratoriya nomi")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan sana")

    class Meta:
        verbose_name = 'Foydalanuvchi profili'
        verbose_name_plural = 'Foydalanuvchi profillari'

    def __str__(self):
        return f"{self.user.email} - {self.role}"

    def is_admin(self):
        return self.role == "admin"

    def is_chemist(self):
        return self.role == "chemist"

    def is_laborant(self):
        return self.role == "laborant"

    def is_viewer(self):
        return self.role == "viewer"


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
