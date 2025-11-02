from django.contrib import admin

# Register your models here.
from .models import Role, RoleAssignment


from django.contrib import admin
from .models import Role

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'organization_id', 'role_level')
    filter_horizontal = ('permissions',)  # ← Add this line
    search_fields = ('name', 'display_name')


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_at', 'is_active')
    search_fields = ('user__username', 'role__name')
    

