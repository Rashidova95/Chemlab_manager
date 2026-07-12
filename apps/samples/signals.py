from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Sample, SampleStatusLog


@receiver(pre_save, sender=Sample)
def generate_sample_id(sender, instance, **kwargs):
    if not instance.sample_id:
        year = timezone.now().year

        last = Sample.objects.filter(
            sample_id__startswith=f'CHEM-{year}-'
        ).order_by('-id').first()
        new_num = int(last.sample_id.split('-')[-1]) + 1 if last else 1
        instance.sample_id = f'CHEM-{year}-{new_num:05d}'


@receiver(pre_save, sender=Sample)
def log_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = Sample.objects.get(pk=instance.pk)
    except Sample.DoesNotExist:
        return

    if old.status != instance.status:
        SampleStatusLog.objects.create(
            sample=instance,
            old_status=old.status,
            new_status=instance.status,
            changed_by=None,
        )
