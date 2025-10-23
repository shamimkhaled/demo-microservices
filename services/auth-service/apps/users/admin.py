from django.contrib import admin

# Register your models here.

from .models import User, District, Thana, Department, Designation

admin.site.register(User)
admin.site.register(District)
admin.site.register(Thana)
admin.site.register(Department)
admin.site.register(Designation)
