from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth.models import Permission

from apps.roles.models import Role, RoleAssignment
from apps.roles.serializers import (
    RoleSerializer,
    RoleAssignmentSerializer,
    PermissionSerializer
)
from shared.permissions import IsSuperAdmin, IsAdminOrSuperAdmin


class RoleListCreateView(generics.ListCreateAPIView):
    """
    List all roles or create a new role
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'is_system_role', 'role_level', 'organization_id']
    search_fields = ['name', 'display_name', 'description']
    ordering_fields = ['role_level', 'display_name', 'created_at']
    ordering = ['role_level', 'display_name']
    
    def get_queryset(self):
        """Filter roles by organization"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Super admin can see all roles
        if user.is_super_admin:
            return queryset
        
        # Others can only see roles from their organization
        return queryset.filter(organization_id=user.organization_id)
    
    @swagger_auto_schema(
        operation_description="Create a new role with permissions",
        request_body=RoleSerializer
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a role
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]
    
    def get_queryset(self):
        """Filter by organization"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_super_admin:
            return queryset
        
        return queryset.filter(organization_id=user.organization_id)
    
    def perform_destroy(self, instance):
        """Prevent deletion of system roles"""
        if instance.is_system_role:
            raise serializers.ValidationError(
                "System roles cannot be deleted"
            )
        
        # Check if role has active assignments
        if instance.user_set.filter(is_active=True).exists():
            raise serializers.ValidationError(
                "Cannot delete role with active user assignments"
            )
        
        super().perform_destroy(instance)


class RoleAssignmentView(APIView):
    """Assign or revoke roles from users"""
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]
    
    @swagger_auto_schema(
        operation_description="Assign or revoke role from user",
        request_body=RoleAssignmentSerializer
    )
    def post(self, request):
        serializer = RoleAssignmentSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            result = serializer.save()
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PermissionListView(generics.ListAPIView):
    """List all available Django permissions"""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'codename']
    
    @swagger_auto_schema(
        operation_description="List all Django permissions for role assignment",
        manual_parameters=[
            openapi.Parameter('app_label', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by app_label if provided
        app_label = self.request.query_params.get('app_label')
        if app_label:
            queryset = queryset.filter(content_type__app_label=app_label)
        
        return queryset.select_related('content_type')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsAdminOrSuperAdmin])
def role_users(request, role_id):
    """Get all users with a specific role"""
    try:
        role = Role.objects.get(id=role_id)
        
        # Check organization access
        if not request.user.is_super_admin:
            if role.organization_id != request.user.organization_id:
                return Response({
                    'success': False,
                    'message': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
        
        users = role.user_set.filter(is_active=True)
        
        from apps.users.serializers import UserSerializer
        serializer = UserSerializer(users, many=True)
        
        return Response({
            'success': True,
            'data': {
                'role': {
                    'id': str(role.id),
                    'name': role.name,
                    'display_name': role.display_name
                },
                'users': serializer.data
            }
        })
    
    except Role.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Role not found'
        }, status=status.HTTP_404_NOT_FOUND)