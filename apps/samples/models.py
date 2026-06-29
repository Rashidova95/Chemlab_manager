from django.db import models

from apps.users.models import CustomUser


class Sample(models.Model):
    SOURCE_CHOICES = [
        ('industrial', 'Sanoat'),
        ('field', 'Dala'),
        ('medical', 'Tibbiy'),
        ('educational', 'O\'quv'),
    ]

    STATUS_CHOICES = [
        ('received', 'Qabul qilindi'),
        ('in_progress', 'Tahlil jarayonida'),
        ('completed', 'Tugallandi'),
        ('archived', 'Arxivlandi'),
    ]
    UNIT_CHOICES = [
        ('g', 'Gram'),
        ('mg', 'Milligram'),
        ('ml', 'Millilitr'),
        ('l', 'Litr'),
    ]

    # Status tartib — faqat oldinga o'tadi
    STATUS_ORDER = ['received', 'in_progress', 'completed', 'archived']

    sample_id = models.CharField(max_length=20, unique=True, editable=False, verbose_name="Namuna ID")
    name = models.CharField(max_length=255, verbose_name="Namuna nomi")
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, verbose_name="Manba turi")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received', verbose_name="Holat")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Miqdori")
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, verbose_name="O'lchov birligi")
    notes = models.TextField(blank=True, verbose_name="Izohlar")
    received_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='samples',
        verbose_name="Qabul qilgan"
    )
    received_at = models.DateTimeField(auto_now_add=True, verbose_name="Qabul sanasi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan sana")

    class Meta:
        ordering = ['-received_at']
        verbose_name = 'Namuna'
        verbose_name_plural = 'Namunalar'

    def __str__(self):
        return f"{self.sample_id} — {self.name}"

    def can_move_to(self, new_status):
        """Status faqat oldinga o'tishi mumkin."""
        current_index = self.STATUS_ORDER.index(self.status)
        new_index = self.STATUS_ORDER.index(new_status)
        return new_index == current_index + 1


class SampleStatusLog(models.Model):
    """
    FR-04: Har bir status o'zgarishida vaqt va foydalanuvchi qayd etiladi.
    """
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name='logs')
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Status tarixi'
        verbose_name_plural = 'Status tarixi'

    def __str__(self):
        return f"{self.sample.sample_id}: {self.old_status} → {self.new_status}"
