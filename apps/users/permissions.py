from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.profile.role == 'admin'
        )


class IsChemist(BasePermission):
    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.profile.role in ('admin', 'chemist')
        )


class IsLaborant(BasePermission):
    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.profile.role in ('admin', 'chemist', 'laborant')
        )


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
                request.user.profile.role == 'admin' or
                obj == request.user
        )
