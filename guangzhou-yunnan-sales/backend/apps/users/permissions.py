from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """仅管理员可访问"""
    message = '需要管理员权限'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')


class IsAdminOrReadOnly(BasePermission):
    """管理员可写，其他人只读"""
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')
