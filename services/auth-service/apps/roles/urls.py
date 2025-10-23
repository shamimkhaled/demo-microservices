from django.urls import path
from apps.roles.views import (
    RoleListCreateView,
    RoleDetailView,
    RoleAssignmentView,
    PermissionListView,
    role_users
)

app_name = 'roles'

urlpatterns = [
    path('', RoleListCreateView.as_view(), name='role-list-create'),
    path('<uuid:pk>/', RoleDetailView.as_view(), name='role-detail'),
    path('assign/', RoleAssignmentView.as_view(), name='role-assignment'),
    path('<uuid:role_id>/users/', role_users, name='role-users'),
    path('permissions/', PermissionListView.as_view(), name='permission-list'),
]


