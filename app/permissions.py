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
from rest_framework import permissions


class AppointmentPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):

        #  Admin can do everything
        if request.user.is_staff:
            return True

        # User must own appointment
        if obj.patient.user != request.user:
            return False

        #  User can only update if doctor is None
        if request.method in ['PUT', 'PATCH']:
            return obj.doctor is None

        # Delete own appointment allowed
        if request.method == 'DELETE':
            return True

        # Read allowed
        return True