from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import transaction
import uuid
import logging

from .models import Organization, BillingSettings, SyncSettings
from .serializers import (
    OrganizationSerializer,
    OrganizationCreateSerializer,
    OrganizationUpdateSerializer,
    BillingSettingsSerializer,
    SyncSettingsSerializer
)
from shared.permissions import IsSuperAdmin, IsAdminOrSuperAdmin, IsSameOrganization
from shared.utils.service_client import AuthServiceClient

logger = logging.getLogger(__name__)


class OrganizationListCreateView(generics.ListCreateAPIView):
    """
    List all organizations or create a new organization

    GET: All authenticated users can list
    POST: Only super_admin can create
    """
    queryset = Organization.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'org_type', 'is_verified']
    search_fields = ['name', 'code', 'email', 'city']
    ordering_fields = ['name', 'code', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_permissions(self):
        """Different permissions for GET vs POST"""
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsSuperAdmin()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrganizationCreateSerializer
        return OrganizationSerializer

    def get_queryset(self):
        """Filter organizations for non-super-admins"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Super admin can see all organizations
        if getattr(user, 'is_super_admin', False):
            return queryset
        
        # Non-super-admins can only see their own organization
        organization_id = getattr(user, 'organization_id', None)
        if organization_id:
            try:
                # Convert string UUID to UUID object if needed
                if isinstance(organization_id, str):
                    organization_id = uuid.UUID(organization_id)
                return queryset.filter(id=organization_id)
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid organization_id: {organization_id} - {e}")
                return queryset.none()
        
        # If no organization_id, return empty queryset (user shouldn't see anything)
        return queryset.none()

    def perform_create(self, serializer):
        """Auto-create billing and sync settings"""
        with transaction.atomic():
            org = serializer.save()
            BillingSettings.objects.get_or_create(organization=org)
            SyncSettings.objects.get_or_create(organization=org)

    @swagger_auto_schema(
        operation_description="List all organizations with filtering and search",
        manual_parameters=[
            openapi.Parameter('is_active', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('org_type', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new organization",
        request_body=OrganizationCreateSerializer
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class OrganizationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an organization

    GET: Users of the same organization or super admins
    PUT/PATCH/DELETE: Only organization admin or super admin
    """
    queryset = Organization.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsSameOrganization]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsAdminOrSuperAdmin(), IsSameOrganization()]
        return [permissions.IsAuthenticated(), IsSameOrganization()]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return OrganizationUpdateSerializer
        return OrganizationSerializer

    def perform_destroy(self, instance):
        """Soft delete - deactivate organization"""
        instance.is_active = False
        instance.save()

    @swagger_auto_schema(
        operation_description="Get organization details with related settings"
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        data = serializer.data.copy()

        try:
            billing_settings = instance.billing_settings
            data['billing_settings'] = BillingSettingsSerializer(billing_settings).data
        except BillingSettings.DoesNotExist:
            data['billing_settings'] = None

        try:
            sync_settings = instance.sync_settings
            data['sync_settings'] = SyncSettingsSerializer(sync_settings).data
        except SyncSettings.DoesNotExist:
            data['sync_settings'] = None

        return Response(data)


class BillingSettingsView(generics.RetrieveUpdateAPIView):
    """Manage billing settings for an organization"""
    serializer_class = BillingSettingsSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin, IsSameOrganization]

    def get_object(self):
        organization_id = self.kwargs['organization_id']
        
        try:
            # Convert string UUID to UUID object if needed
            if isinstance(organization_id, str):
                organization_id = uuid.UUID(organization_id)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid organization_id: {organization_id} - {e}")
            return generics.get_object_or_404(Organization, id=organization_id)
        
        organization = generics.get_object_or_404(Organization, id=organization_id)
        self.check_object_permissions(self.request, organization)

        billing_settings, created = BillingSettings.objects.get_or_create(
            organization=organization
        )
        return billing_settings


class SyncSettingsView(generics.RetrieveUpdateAPIView):
    """Manage sync settings for an organization"""
    serializer_class = SyncSettingsSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin, IsSameOrganization]

    def get_object(self):
        organization_id = self.kwargs['organization_id']
        
        try:
            # Convert string UUID to UUID object if needed
            if isinstance(organization_id, str):
                organization_id = uuid.UUID(organization_id)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid organization_id: {organization_id} - {e}")
            return generics.get_object_or_404(Organization, id=organization_id)
        
        organization = generics.get_object_or_404(Organization, id=organization_id)
        self.check_object_permissions(self.request, organization)

        sync_settings, created = SyncSettings.objects.get_or_create(
            organization=organization
        )
        return sync_settings


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def organization_exists(request, pk):
    """Check if organization exists and is active"""
    try:
        # Convert string UUID to UUID object if needed
        if isinstance(pk, str):
            pk = uuid.UUID(pk)
        
        organization = Organization.objects.get(id=pk, is_active=True)
        return Response({
            'success': True,
            'exists': True,
            'organization': {
                'id': str(organization.id),
                'name': organization.name,
                'code': organization.code,
                'org_type': organization.org_type,
            }
        }, status=status.HTTP_200_OK)
    except (Organization.DoesNotExist, ValueError, TypeError):
        return Response({
            'success': False,
            'exists': False
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsSuperAdmin])
def organization_stats(request):
    """Get organization statistics"""
    total_orgs = Organization.objects.count()
    active_orgs = Organization.objects.filter(is_active=True).count()
    verified_orgs = Organization.objects.filter(is_verified=True).count()

    org_types = {}
    for org_type_choice in Organization.ORG_TYPE_CHOICES:
        org_type_key = org_type_choice[0]
        org_types[org_type_key] = Organization.objects.filter(org_type=org_type_key).count()

    return Response({
        'success': True,
        'data': {
            'total_organizations': total_orgs,
            'active_organizations': active_orgs,
            'verified_organizations': verified_orgs,
            'organizations_by_type': org_types
        }
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsSuperAdmin])
def verify_organization(request, organization_id):
    """Verify an organization (admin only)"""
    try:
        # Convert string UUID to UUID object if needed
        if isinstance(organization_id, str):
            organization_id = uuid.UUID(organization_id)
        
        organization = Organization.objects.get(id=organization_id)
    except (Organization.DoesNotExist, ValueError, TypeError):
        return Response({
            'success': False,
            'message': 'Organization not found'
        }, status=status.HTTP_404_NOT_FOUND)

    organization.is_verified = True
    organization.save()

    return Response({
        'success': True,
        'message': 'Organization verified successfully'
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def organization_profile(request):
    """Get the organization profile for the currently authenticated user."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({
            'success': False,
            'message': 'Authorization header not found or invalid'
        }, status=status.HTTP_401_UNAUTHORIZED)

    token = auth_header.split(' ')[1]

    auth_client = AuthServiceClient()
    user_data = auth_client.verify_token(token)

    if not user_data:
        return Response({
            'success': False,
            'message': 'Invalid or expired token. Could not retrieve user data.'
        }, status=status.HTTP_401_UNAUTHORIZED)

    organization_id = user_data.get('organization_id')
    if not organization_id:
        return Response({
            'success': False,
            'message': 'Organization ID not found in user token.'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Convert string UUID to UUID object if needed
        if isinstance(organization_id, str):
            organization_id = uuid.UUID(organization_id)
        
        organization = Organization.objects.get(id=organization_id)
        serializer = OrganizationSerializer(organization)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except (Organization.DoesNotExist, ValueError, TypeError) as e:
        logger.error(f"Error fetching organization: {e}")
        return Response({
            'success': False,
            'message': 'Organization not found'
        }, status=status.HTTP_404_NOT_FOUND)



        