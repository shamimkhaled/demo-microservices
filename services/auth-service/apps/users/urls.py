from django.urls import path
from apps.users.views import (
    UserListCreateView,
    UserDetailView,
    ChangePasswordView,
    user_profile,
    user_permissions
)

app_name = 'users'

urlpatterns = [
    path('', UserListCreateView.as_view(), name='user-list-create'),
    path('<uuid:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('profile/', user_profile, name='user-profile'),
    path('permissions/', user_permissions, name='user-permissions'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]