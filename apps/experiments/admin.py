from django.contrib import admin

from .models import Experiment


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ['title', 'sample', 'status', 'performed_by',
                    'approved_by', 'created_at']
    list_filter = ['status']
    search_fields = ['title', 'sample__sample_id']
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    filter_horizontal = ['chemicals_used']

    class Meta:
        verbose_name = 'Tajriba'
        verbose_name_plural = 'Tajribalar'