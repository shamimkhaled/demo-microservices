from django.urls import path
from apps.authentication.views import (
    LoginView,
    TokenRefreshView,
    LogoutView,
    VerifyTokenView
)

app_name = 'authentication'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('verify/', VerifyTokenView.as_view(), name='verify-token'),
]