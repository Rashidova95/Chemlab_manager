from django.contrib import admin

from .models import Sample, SampleStatusLog


class SampleStatusLogInline(admin.TabularInline):
    model = SampleStatusLog
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'changed_by', 'changed_at']
    can_delete = False


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    inlines = [SampleStatusLogInline]
    list_display = ['sample_id', 'name', 'source_type', 'status', 'received_by', 'received_at']
    list_filter = ['status', 'source_type']
    search_fields = ['sample_id', 'name']
    readonly_fields = ['sample_id', 'received_at', 'updated_at']
    ordering = ['-received_at']


@admin.register(SampleStatusLog)
class SampleStatusLogAdmin(admin.ModelAdmin):
    list_display = ['sample', 'old_status', 'new_status', 'changed_by', 'changed_at']
    readonly_fields = ['sample', 'old_status', 'new_status', 'changed_by', 'changed_at']
