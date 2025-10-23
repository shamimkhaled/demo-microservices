from django.contrib import admin
from .models import Organization, SyncSettings, BillingSettings

# Register your models here.
admin.site.register(Organization)
admin.site.register(SyncSettings)
admin.site.register(BillingSettings)
