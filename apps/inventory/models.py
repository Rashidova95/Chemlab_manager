from django.db import models


class Chemical(models.Model):
    UNIT_CHOICES = [
        ('g', 'Gram'),
        ('kg', 'Kilogram'),
        ('mg', 'Milligram'),
        ('ml', 'Millilitr'),
        ('l', 'Litr'),
        ('mol', 'Mol'),
    ]

    HAZARD_CHOICES = [
        (1, 'Past xavf'),
        (2, 'O\'rta xavf'),
        (3, 'Yuqori xavf'),
        (4, 'Juda yuqori xavf'),
    ]

    name_uz = models.CharField(max_length=255, verbose_name="O'zbekcha nomi")
    name_iupac = models.CharField(max_length=255, verbose_name="IUPAC nomi")
    cas_number = models.CharField(max_length=20, unique=True, verbose_name="CAS raqami")
    formula = models.CharField(max_length=50, blank=True, verbose_name="Kimyoviy formula")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Miqdor")
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, verbose_name="O'lchov birligi")
    min_threshold = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Minimum chegara")
    expiry_date = models.DateField(verbose_name="Muddati tugash sanasi")
    hazard_level = models.IntegerField(choices=HAZARD_CHOICES, verbose_name="Xavflilik darajasi")
    supplier = models.CharField(max_length=255, blank=True, verbose_name="Etkazib beruvchi")
    storage_condition = models.CharField(max_length=255, blank=True, verbose_name="Saqlash sharoiti")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan sana")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan sana")
    is_active = models.BooleanField(default=True, verbose_name='Faolmi')

    class Meta:
        ordering = ['name_uz']
        verbose_name = 'Kimyoviy modda'
        verbose_name_plural = 'Kimyoviy moddalar'

    def __str__(self):
        return f"{self.name_uz} ({self.cas_number})"

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_threshold

    @property
    def is_expired(self):
        from datetime import date
        return self.expiry_date < date.today()

    @property
    def is_expiring_soon(self):
        from datetime import date, timedelta
        today = date.today()
        return today <= self.expiry_date <= today + timedelta(days=30)
