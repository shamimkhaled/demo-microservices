from django.contrib import admin

# Register your models here.
from .models import Role, RoleAssignment
admin.site.register(Role)
admin.site.register(RoleAssignment)

