from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.db import models

User = get_user_model()


class Experiment(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Loyiha'),
        ('in_progress', 'Jarayonda'),
        ('review', 'Tekshiruvda'),
        ('approved', 'Tasdiqlangan'),
        ('rejected', 'Qaytarilgan'),
    ]

    # Faqat oldinga o'tish + rejected dan qayta ishlash
    VALID_TRANSITIONS = {
        'draft': ['in_progress'],
        'in_progress': ['review'],
        'review': ['approved', 'rejected'],
        'approved': [],
        'rejected': ['in_progress'],
    }

    sample = models.ForeignKey(
        'samples.Sample',
        on_delete=models.CASCADE,
        related_name='experiments',
        verbose_name="Namuna"
    )
    title = models.CharField(max_length=255, verbose_name="Tajriba nomi")
    method = models.CharField(max_length=255, verbose_name="Tahlil metodi")
    objective = models.TextField(verbose_name="Maqsad")
    observations = models.TextField(blank=True, verbose_name="Kuzatuvlar")
    results = models.JSONField(default=dict, blank=True, verbose_name="Natijalar")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Holat"
    )

    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='experiments',
        verbose_name="Bajargan"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_experiments',
        verbose_name="Tasdiqlagan"
    )
    approved_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Tasdiqlangan sana"
    )

    chemicals_used = models.ManyToManyField(
        'inventory.Chemical',
        blank=True,
        related_name='experiments',
        verbose_name="Foydalanilgan reaktivlar"
    )

    attachment = models.FileField(
        upload_to='experiments/%Y/%m/',
        null=True, blank=True,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'png'])],
        verbose_name="Fayl"
    )

    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Qaytarish sababi"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan sana")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Tajriba'
        verbose_name_plural = 'Tajribalar'

    def __str__(self):
        return f"{self.title} — {self.sample.sample_id}"

    def can_move_to(self, new_status):
        allowed = self.VALID_TRANSITIONS.get(self.status, [])
        return new_status in allowed
