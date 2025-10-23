from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.users.models import User
from apps.users.serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer
)
from shared.permissions import IsSuperAdmin, IsAdminOrSuperAdmin


class UserListCreateView(generics.ListCreateAPIView):
    """
    List all users or create a new user
    
    GET: All authenticated users can list
    POST: Only super_admin and admin can create
    """
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'is_staff', 'is_super_admin', 'organization_id']
    search_fields = ['login_id', 'email', 'name', 'employee_id']
    ordering_fields = ['login_id', 'email', 'created_at', 'last_login']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """Different permissions for GET vs POST"""
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsAdminOrSuperAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer
    
    def get_queryset(self):
        """Filter users by organization for non-super-admins"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Super admin can see all users
        if user.is_super_admin:
            return queryset
        
        # Others can only see users from their organization
        return queryset.filter(organization_id=user.organization_id)
    
    @swagger_auto_schema(
        operation_description="List all users with filtering and search",
        manual_parameters=[
            openapi.Parameter('organization_id', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('is_active', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new user (ROLE-FIRST: role_ids required)",
        request_body=UserCreateSerializer
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a user
    
    GET: All authenticated users
    PUT/PATCH/DELETE: Only super_admin and admin
    """
    queryset = User.objects.all()
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsAdminOrSuperAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_queryset(self):
        """Filter by organization for non-super-admins"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_super_admin:
            return queryset
        
        return queryset.filter(organization_id=user.organization_id)
    
    def perform_destroy(self, instance):
        """Soft delete - deactivate user"""
        instance.is_active = False
        instance.save()


class ChangePasswordView(APIView):
    """Change user password"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Change current user's password",
        request_body=PasswordChangeSerializer
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Password change failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    """Get current user profile"""
    serializer = UserSerializer(request.user)
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_permissions(request):
    """Get current user permissions"""
    user = request.user
    
    # Get all permissions from roles
    permissions_list = set()
    for group in user.groups.all():
        permissions_list.update(
            group.permissions.values_list('codename', flat=True)
        )
    
    # Group by app
    grouped = {}
    for perm in permissions_list:
        app = perm.split('.')[0] if '.' in perm else 'general'
        if app not in grouped:
            grouped[app] = []
        grouped[app].append(perm)
    
    return Response({
        'success': True,
        'data': {
            'user': user.login_id,
            'permissions': list(permissions_list),
            'grouped_permissions': grouped,
            'roles': [
                {
                    'id': str(role.id),
                    'name': role.name,
                    'display_name': role.display_name
                }
                for role in user.groups.all()
            ]
        }
    })




