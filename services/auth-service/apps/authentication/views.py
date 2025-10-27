from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.users.models import User
from apps.users.serializers import UserSerializer
from django_ratelimit.decorators import ratelimit

class LoginView(APIView):
    """User login with JWT token generation"""
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Login with login_id and password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['login_id', 'password'],
            properties={
                'login_id': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
                'remember_me': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
            }
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                                'tokens': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                )
                            }
                        )
                    }
                )
            )
        }
    )



    @ratelimit(key='ip', rate='5/m', method='POST')
    def post(self, request):
        login_id = request.data.get('login_id')
        password = request.data.get('password')
        remember_me = request.data.get('remember_me', False)
        
        if not login_id or not password:
            return Response({
                'success': False,
                'message': 'Login ID and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate user
        user = authenticate(request, username=login_id, password=password)
        
        if not user:
            # Check if user exists to provide better error message
            try:
                user = User.objects.get(login_id=login_id)
                user.failed_login_attempts += 1
                
                # Lock account after 5 failed attempts
                if user.failed_login_attempts >= 5:
                    user.locked_until = timezone.now() + timezone.timedelta(minutes=30)
                
                user.save(update_fields=['failed_login_attempts', 'locked_until'])
                
                return Response({
                    'success': False,
                    'message': 'Invalid password'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'User not found'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user is active
        if not user.is_active:
            return Response({
                'success': False,
                'message': 'Account is deactivated'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if account is locked
        if user.locked_until and user.locked_until > timezone.now():
            return Response({
                'success': False,
                'message': f'Account is locked until {user.locked_until}'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Reset failed login attempts
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save(update_fields=['failed_login_attempts', 'locked_until'])
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Store tokens for remember me
        if remember_me:
            user.access_token = access_token
            user.refresh_token = refresh_token
            user.token_created_at = timezone.now()
            user.token_expires_at = timezone.now() + timezone.timedelta(days=30)
            user.remember_me = True
            user.save(update_fields=[
                'access_token', 'refresh_token',
                'token_created_at', 'token_expires_at', 'remember_me'
            ])
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Serialize user data
        user_serializer = UserSerializer(user)
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': user_serializer.data,
                'tokens': {
                    'access': access_token,
                    'refresh': refresh_token,
                    'token_type': 'Bearer'
                },
                'remember_me': remember_me
            }
        }, status=status.HTTP_200_OK)


class TokenRefreshView(APIView):
    """Refresh JWT access token"""
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Refresh access token using refresh token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh_token'],
            properties={
                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING),
            }
        )
    )
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'success': False,
                'message': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            
            return Response({
                'success': True,
                'message': 'Token refreshed successfully',
                'data': {
                    'access': access_token,
                    'token_type': 'Bearer'
                }
            }, status=status.HTTP_200_OK)
        
        except TokenError as e:
            return Response({
                'success': False,
                'message': 'Invalid or expired refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)





class LogoutView(APIView):
    """User logout with token blacklisting"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Logout user and blacklist tokens",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING),
                'logout_all_devices': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
            }
        )
    )
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        logout_all_devices = request.data.get('logout_all_devices', False)
        
        user = request.user
        
        # Blacklist refresh token if provided
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass
        
        # Clear stored tokens
        if logout_all_devices or refresh_token:
            user.access_token = None
            user.refresh_token = None
            user.token_created_at = None
            user.token_expires_at = None
            user.remember_me = False
            user.save(update_fields=[
                'access_token', 'refresh_token',
                'token_created_at', 'token_expires_at', 'remember_me'
            ])
        
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)


class VerifyTokenView(APIView):
    """Verify JWT token validity"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Verify token validity and get user info"
    )
    def post(self, request):
        user = request.user
        user_serializer = UserSerializer(user)
        
        return Response({
            'success': True,
            'message': 'Token is valid',
            'data': {
                'user': user_serializer.data
            }
        }, status=status.HTTP_200_OK)
    


