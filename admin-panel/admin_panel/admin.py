from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.users.models import User
from apps.roles.models import Role, RoleAssignment
from apps.organizations.models import Organization
from apps.organizations.models import SyncSettings, BillingSettings

# Register Auth Service models
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('login_id', 'email', 'name', 'organization_id', 'is_active', 'is_super_admin')
    list_filter = ('is_active', 'is_super_admin', 'organization_id')
    search_fields = ('login_id', 'email', 'name')
    ordering = ('login_id',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'organization_id', 'role_level', 'is_active')
    list_filter = ('organization_id', 'is_active', 'role_level')
    search_fields = ('name', 'display_name')

@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_at', 'is_active')
    list_filter = ('is_active', 'assigned_at')
    search_fields = ('user__login_id', 'role__name')

# Register Organization Service models
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'org_type', 'email', 'is_active', 'is_verified')
    list_filter = ('org_type', 'is_active', 'is_verified')
    search_fields = ('name', 'code', 'email')

@admin.register(BillingSettings)
class BillingSettingsAdmin(admin.ModelAdmin):
    list_display = ('organization', 'max_manual_grace_days', 'default_grace_days')
    search_fields = ('organization__name',)

@admin.register(SyncSettings)
class SyncSettingsAdmin(admin.ModelAdmin):
    list_display = ('organization', 'sync_area_to_mikrotik', 'last_sync_status')
    list_filter = ('last_sync_status', 'sync_frequency')
    search_fields = ('organization__name',)