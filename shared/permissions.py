"""
Shared permission classes for all microservices
"""
from rest_framework import permissions


from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    message = "Only super administrators can perform this action"
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_super_admin

class IsAdminOrSuperAdmin(permissions.BasePermission):
    message = "Only administrators can perform this action"
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_super_admin or 
            request.user.is_staff
        )

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class to check if user is owner of object or admin
    """
    
    message = "You do not have permission to access this resource"
    
    def has_object_permission(self, request, view, obj):
        """Check if user is owner or admin"""
        # Super admin always has access
        if getattr(request.user, 'is_super_admin', False):
            return True
        
        # Check if user is admin
        if hasattr(request.user, 'groups'):
            if request.user.groups.filter(name__in=['admin', 'Admin', 'ADMIN']).exists():
                return True
        
        # Check if user is owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False


class IsSameOrganization(permissions.BasePermission):
    """
    Permission class to check if user belongs to same organization as object
    """
    
    message = "You do not have access to resources from other organizations"
    
    def has_object_permission(self, request, view, obj):
        """Check if user belongs to same organization"""
        # Super admin can access all organizations
        if getattr(request.user, 'is_super_admin', False):
            return True
        
        # Check organization match
        if hasattr(obj, 'organization_id'):
            return str(obj.organization_id) == str(request.user.organization_id)
        elif hasattr(obj, 'organization'):
            return str(obj.organization.id) == str(request.user.organization_id)
        
        return False


class HasPermission(permissions.BasePermission):
    """
    Custom permission class to check specific Django permissions
    Usage: permission_classes = [HasPermission('app_label.permission_codename')]
    """
    
    def __init__(self, perm):
        self.perm = perm
    
    def has_permission(self, request, view):
        """Check if user has specific permission"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admin always has access
        if getattr(request.user, 'is_super_admin', False):
            return True
        
        # Check permission
        return request.user.has_perm(self.perm)


class HasAnyRole(permissions.BasePermission):
    """
    Permission class to check if user has any of the specified roles
    Usage: permission_classes = [HasAnyRole(['admin', 'manager'])]
    """
    
    def __init__(self, roles):
        self.roles = roles if isinstance(roles, list) else [roles]
    
    def has_permission(self, request, view):
        """Check if user has any of the specified roles"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admin always has access
        if getattr(request.user, 'is_super_admin', False):
            return True
        
        # Check roles
        if hasattr(request.user, 'groups'):
            user_roles = request.user.groups.values_list('name', flat=True)
            return any(role in user_roles for role in self.roles)
        
        return False


class IsActive(permissions.BasePermission):
    """
    Permission class to check if user account is active
    """
    
    message = "Your account is not active"
    
    def has_permission(self, request, view):
        """Check if user is active"""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_active
        )


class IsEmailVerified(permissions.BasePermission):
    """
    Permission class to check if user email is verified
    """
    
    message = "Please verify your email address to access this resource"
    
    def has_permission(self, request, view):
        """Check if user email is verified"""
        return (
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'is_email_verified', False)
        )