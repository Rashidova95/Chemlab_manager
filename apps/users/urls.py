from django.urls import path
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView, LoginView, MeView, ChangePasswordView,
    AdminUserListView, AdminUserRoleUpdateView, AdminUserCreateView, AdminUserDetailView,
)


class TaggedTokenRefreshView(TokenRefreshView):
    @extend_schema(tags=['Auth'])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', TaggedTokenRefreshView.as_view(), name='auth-refresh'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
    path('users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('users/create/', AdminUserCreateView.as_view(), name='admin-user-create'),
    path('users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('users/<int:pk>/role/', AdminUserRoleUpdateView.as_view(), name='admin-user-role-update'),
]
