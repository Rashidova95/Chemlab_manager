from django.contrib import admin

from .models import Chemical


@admin.register(Chemical)
class ChemicalAdmin(admin.ModelAdmin):
    list_display = [
        'name_uz', 'formula', 'cas_number', 'quantity', 'unit',
        'hazard_level', 'expiry_date',
        'get_low_stock', 'get_expiring_soon', 'get_expired',
        'is_active',
    ]
    list_filter = ['hazard_level', 'unit', 'is_active']
    search_fields = ['name_uz', 'name_iupac', 'cas_number', 'formula']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']

    @admin.display(description="Kam qolganmi")
    def get_low_stock(self, obj):
        return "Ha" if obj.is_low_stock else "Yo'q"

    @admin.display(description="Muddati tugayaptimi")
    def get_expiring_soon(self, obj):
        return "Ha" if obj.is_expiring_soon else "Yo'q"

    @admin.display(description="Muddati o'tganmi")
    def get_expired(self, obj):
        return "Ha" if obj.is_expired else "Yo'q"
