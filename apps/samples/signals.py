from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Sample


@receiver(pre_save, sender=Sample)
def generate_sample_id(sender, instance, **kwargs):
    if not instance.sample_id:
        year = timezone.now().year

        last = Sample.objects.filter(
            sample_id__startswith=f'CHEM-{year}-'
        ).order_by('-id').first()
        new_num = int(last.sample_id.split('-')[-1]) + 1 if last else 1
        instance.sample_id = f'CHEM-{year}-{new_num:05d}'
