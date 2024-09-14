from rest_framework.permissions import BasePermission

def is_manager(user):
    return user.is_staff