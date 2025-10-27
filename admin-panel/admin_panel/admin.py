"""
Unified Admin Panel - Model Registration
Registers all models from auth-service and organization-service
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

# ============================================================================
# AUTH SERVICE - USERS
# ============================================================================
from users.models import User, District, Thana, Department, Designation


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Custom User Admin with organization and role information"""
    list_display = (
        'login_id', 'email', 'name', 'organization_id',
        'is_active', 'is_super_admin', 'last_login'
    )
    list_filter = (
        'is_active', 'is_super_admin', 'is_staff',
        'is_email_verified', 'is_phone_verified', 'created_at'
    )
    search_fields = ('login_id', 'email', 'name', 'employee_id')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Authentication', {
            'fields': ('login_id', 'email', 'password')
        }),
        ('Personal Info', {
            'fields': ('name', 'mobile', 'profile_photo')
        }),
        ('Employment', {
            'fields': ('employee_id', 'date_of_joining', 'department', 'designation')
        }),
        ('Address', {
            'fields': ('address', 'district', 'thana', 'postal_code')
        }),
        ('Organization', {
            'fields': ('organization_id',)
        }),
        ('Verification', {
            'fields': ('is_email_verified', 'is_phone_verified')
        }),
        ('Security', {
            'fields': (
                'is_active', 'is_staff', 'is_super_admin',
                'failed_login_attempts', 'locked_until',
                'two_factor_enabled'
            )
        }),
        ('Preferences', {
            'fields': ('language_preference', 'timezone')
        }),
        ('Timestamps', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'last_login')


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    """District Admin"""
    list_display = ('name', 'name_bn', 'division', 'is_active')
    list_filter = ('is_active', 'division')
    search_fields = ('name', 'name_bn', 'division')


@admin.register(Thana)
class ThanaAdmin(admin.ModelAdmin):
    """Thana/Upazila Admin"""
    list_display = ('name', 'name_bn', 'district', 'is_active')
    list_filter = ('is_active', 'district')
    search_fields = ('name', 'name_bn', 'district__name')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Department Admin"""
    list_display = ('name', 'organization_id', 'is_active', 'created_at')
    list_filter = ('is_active', 'organization_id')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    """Designation Admin"""
    list_display = ('name', 'department', 'organization_id', 'is_active', 'created_at')
    list_filter = ('is_active', 'organization_id', 'department')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


# ============================================================================
# AUTH SERVICE - ROLES
# ============================================================================
from roles.models import Role, RoleAssignment


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Role Admin"""
    list_display = (
        'name', 'display_name', 'organization_id',
        'role_level', 'is_active', 'is_system_role'
    )
    list_filter = (
        'is_active', 'is_system_role', 'organization_id',
        'role_level', 'created_at'
    )
    search_fields = ('name', 'display_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Role Information', {
            'fields': ('name', 'display_name', 'description')
        }),
        ('Organization & Level', {
            'fields': ('organization_id', 'role_level')
        }),
        ('Settings', {
            'fields': (
                'is_active', 'is_system_role',
                'can_assign_roles', 'max_assignments'
            )
        }),
        ('Audit', {
            'fields': ('created_by_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    """Role Assignment Admin - Audit Trail"""
    list_display = (
        'user', 'role', 'is_active',
        'assigned_at', 'expires_at', 'revoked_at'
    )
    list_filter = (
        'is_active', 'assigned_at', 'revoked_at', 'role'
    )
    search_fields = ('user__login_id', 'user__email', 'role__name')
    readonly_fields = ('assigned_at', 'revoked_at')
    
    fieldsets = (
        ('Assignment', {
            'fields': ('user', 'role', 'is_active')
        }),
        ('Timeline', {
            'fields': ('assigned_at', 'expires_at', 'revoked_at')
        }),
        ('Audit', {
            'fields': (
                'assigned_by_id', 'revoked_by_id',
                'assignment_reason', 'revocation_reason'
            ),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# ORGANIZATION SERVICE - ORGANIZATIONS
# ============================================================================
from organizations.models import Organization, BillingSettings, SyncSettings


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Organization Admin"""
    list_display = (
        'name', 'code', 'org_type', 'email',
        'is_active', 'is_verified', 'created_at'
    )
    list_filter = (
        'org_type', 'is_active', 'is_verified',
        'created_at', 'updated_at'
    )
    search_fields = ('name', 'code', 'email', 'city')
    readonly_fields = ('created_at', 'updated_at', 'id')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'code', 'org_type')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'mobile', 'website')
        }),
        ('Address', {
            'fields': ('address', 'city', 'postal_code', 'country')
        }),
        ('Legal Information', {
            'fields': ('trade_license', 'tin_number', 'registration_number')
        }),
        ('Branding', {
            'fields': (
                'logo_img', 'dark_logo_img', 'lite_logo_img',
                'banner_img', 'og_image', 'favicon'
            ),
            'classes': ('collapse',)
        }),
        ('Currency & SEO', {
            'fields': (
                'currency', 'currency_symbol',
                'seo_title', 'seo_description', 'seo_keywords', 'meta_description'
            ),
            'classes': ('collapse',)
        }),
        ('Revenue Sharing', {
            'fields': (
                'revenue_sharing_enabled',
                'default_reseller_share', 'default_sub_reseller_share',
                'default_ktl_share_with_sub', 'default_reseller_share_with_sub'
            ),
            'classes': ('collapse',)
        }),
        ('API Configuration', {
            'fields': ('api_version',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified')
        }),
        ('Audit', {
            'fields': ('created_by_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BillingSettings)
class BillingSettingsAdmin(admin.ModelAdmin):
    """Billing Settings Admin"""
    list_display = (
        'organization', 'max_manual_grace_days',
        'default_grace_days', 'jump_billing'
    )
    list_filter = ('jump_billing', 'disable_expiry')
    search_fields = ('organization__name', 'organization__code')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Organization', {
            'fields': ('organization',)
        }),
        ('Grace & Expiry Settings', {
            'fields': (
                'max_manual_grace_days', 'default_grace_days',
                'default_grace_hours', 'disable_expiry'
            )
        }),
        ('Billing Configuration', {
            'fields': (
                'jump_billing', 'max_inactive_days',
                'delete_permanent_disable_secret_from_mikrotik'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SyncSettings)
class SyncSettingsAdmin(admin.ModelAdmin):
    """Sync Settings Admin"""
    list_display = (
        'organization', 'last_sync_status',
        'sync_frequency', 'updated_at'
    )
    list_filter = ('last_sync_status', 'sync_frequency')
    search_fields = ('organization__name', 'organization__code')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Organization', {
            'fields': ('organization',)
        }),
        ('MikroTik Sync Configuration', {
            'fields': (
                'sync_area_to_mikrotik',
                'sync_address_to_mikrotik',
                'sync_customer_mobile_to_mikrotik'
            )
        }),
        ('Sync Status & Schedule', {
            'fields': ('last_sync_status', 'sync_frequency')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )