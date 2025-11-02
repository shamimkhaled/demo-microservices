import uuid
from django.db import models
from django.contrib.auth.models import Group, Permission
from django.utils import timezone


class Role(models.Model):
    """
    Extended Django Group model for roles.
    Links to Django's Permission model for permissions management.
    
    - Role is for organizational role-based access control
    - Role assignments are tracked via RoleAssignment
    - Django's Group is NOT used with Roles
    """
    
    # Use UUID as primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    
    # Additional metadata
    display_name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    
    # Organization (Tenant) - Store as UUID
    organization_id = models.UUIDField(
        help_text='Organization UUID from Organization Service',
        db_index=True
    )
    
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='roles',
        help_text='Django permissions assigned to this role'
    )
    
    # Role hierarchy & control
    role_level = models.PositiveIntegerField(
        default=10, 
        help_text='Lower = higher authority (1=SuperAdmin, 2=Admin, etc.)'
    )
    is_system_role = models.BooleanField(
        default=False, 
        help_text='System-defined role, cannot be deleted'
    )
    is_active = models.BooleanField(default=True)
    can_assign_roles = models.BooleanField(default=False)
    max_assignments = models.PositiveIntegerField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by_id = models.UUIDField(blank=True, null=True)
    
    class Meta:
        db_table = 'roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        indexes = [
            models.Index(fields=['organization_id', 'is_active']),
            models.Index(fields=['role_level']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.display_name} (Org: {self.organization_id})"
    
    def get_permissions_list(self):
        """Get list of permission codenames"""
        return list(self.permissions.values_list('codename', flat=True))
    
    def get_permissions_detail(self):
        """Get detailed permissions"""
        return self.permissions.select_related('content_type').all()
    
    def assign_to_user(self, user):
        """
        Assign this role to a user
        Now only uses RoleAssignment for tracking
        """

        
        # Create assignment record
        RoleAssignment.objects.create(
            user=user,
            role=self,
            assigned_by_id=user.id,
            is_active=True
        )
        return True
    
    def remove_from_user(self, user):
        """Remove this role from a user"""
        
        # Update assignment record
        RoleAssignment.objects.filter(
            user=user,
            role=self,
            is_active=True
        ).update(
            is_active=False,
            revoked_at=timezone.now()
        )
        return True


class RoleAssignment(models.Model):
    """
    Track role assignments with audit trail
    
    This is the ONLY way to track which users have which roles.
    Do NOT use Django's Group model for this.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='role_assignments'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_assignments'
    )
    
    # Assignment tracking
    assigned_by_id = models.UUIDField()
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    assignment_reason = models.TextField(blank=True)
    revocation_reason = models.TextField(blank=True)
    
    revoked_by_id = models.UUIDField(blank=True, null=True)
    revoked_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'role_assignments'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['role', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.name} - {self.role.display_name}"



