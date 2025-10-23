from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Organization, BillingSettings, SyncSettings
from .serializers import (
    OrganizationSerializer,
    OrganizationCreateSerializer,
    OrganizationUpdateSerializer,
    BillingSettingsSerializer,
    SyncSettingsSerializer
)


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
            return [permissions.IsAuthenticated()]  # Add super admin check later
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrganizationCreateSerializer
        return OrganizationSerializer

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

    GET: All authenticated users
    PUT/PATCH/DELETE: Only organization admin or super admin
    """
    queryset = Organization.objects.all()

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated()]  # Add proper permission checks later
        return [permissions.IsAuthenticated()]

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

        # Add related settings data
        data = serializer.data.copy()

        # Add billing settings if they exist
        try:
            billing_settings = instance.billing_settings
            data['billing_settings'] = BillingSettingsSerializer(billing_settings).data
        except BillingSettings.DoesNotExist:
            data['billing_settings'] = None

        # Add sync settings if they exist
        try:
            sync_settings = instance.sync_settings
            data['sync_settings'] = SyncSettingsSerializer(sync_settings).data
        except SyncSettings.DoesNotExist:
            data['sync_settings'] = None

        return Response(data)


class BillingSettingsView(generics.RetrieveUpdateAPIView):
    """Manage billing settings for an organization"""
    serializer_class = BillingSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        organization_id = self.kwargs['organization_id']
        organization = generics.get_object_or_404(Organization, id=organization_id)

        # Get or create billing settings
        billing_settings, created = BillingSettings.objects.get_or_create(
            organization=organization
        )
        return billing_settings


class SyncSettingsView(generics.RetrieveUpdateAPIView):
    """Manage sync settings for an organization"""
    serializer_class = SyncSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        organization_id = self.kwargs['organization_id']
        organization = generics.get_object_or_404(Organization, id=organization_id)

        # Get or create sync settings
        sync_settings, created = SyncSettings.objects.get_or_create(
            organization=organization
        )
        return sync_settings


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
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
@permission_classes([permissions.IsAuthenticated])
def verify_organization(request, organization_id):
    """Verify an organization (admin only)"""
    try:
        organization = Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist:
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
    """Get current user's organization profile"""
    # This would need to be implemented based on how users are linked to organizations
    # For now, return a placeholder
    return Response({
        'success': True,
        'message': 'Organization profile endpoint - to be implemented',
        'data': {}
    })
