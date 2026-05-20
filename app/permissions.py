from rest_framework.permissions import BasePermission


class IsAdminStaff(BasePermission):

    def has_permission(self, request, view):

        return request.user.is_staff


class IsPatient(BasePermission):

    def has_permission(self, request, view):

        return request.user.is_authenticated and not request.user.is_staff

class IsOwnerOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user



