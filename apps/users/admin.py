from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fields = ('role', 'phone', 'lab_name', 'is_active')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def has_add_permission(self, request, obj=None):
        if obj is not None:
            return not UserProfile.objects.filter(user=obj).exists()
        return True

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ['email', 'first_name', 'last_name', 'get_role', 'is_staff']
    list_filter = ['profile__role', 'is_staff', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name',
                       'password1', 'password2'),
        }),
    )

    @admin.display(description='Rol')
    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except UserProfile.DoesNotExist:
            return '—'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'lab_name', 'phone', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['user__email', 'lab_name']
    list_editable = ['role', 'is_active']
