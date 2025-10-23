from django.urls import path
from .views import (
    OrganizationListCreateView,
    OrganizationDetailView,
    BillingSettingsView,
    SyncSettingsView,
    organization_stats,
    verify_organization,
    organization_profile
)

app_name = 'organizations'

urlpatterns = [
    # Organization CRUD
    path('', OrganizationListCreateView.as_view(), name='organization-list-create'),
    path('<uuid:pk>/', OrganizationDetailView.as_view(), name='organization-detail'),

    # Organization settings
    path('<uuid:organization_id>/billing-settings/', BillingSettingsView.as_view(), name='billing-settings'),
    path('<uuid:organization_id>/sync-settings/', SyncSettingsView.as_view(), name='sync-settings'),

    # Organization actions
    path('<uuid:organization_id>/verify/', verify_organization, name='verify-organization'),

    # Organization utilities
    path('stats/', organization_stats, name='organization-stats'),
    path('profile/', organization_profile, name='organization-profile'),
]