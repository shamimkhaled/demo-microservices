from rest_framework import serializers
from apps.organizations.models import Organization, BillingSettings, SyncSettings


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model"""

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'code', 'org_type', 'email', 'phone', 'mobile',
            'website', 'address', 'city', 'postal_code', 'country',
            'trade_license', 'tin_number', 'registration_number',
            'logo_img', 'dark_logo_img', 'lite_logo_img', 'banner_img',
            'og_image', 'favicon', 'currency', 'currency_symbol',
            'seo_title', 'seo_description', 'seo_keywords', 'meta_description',
            'revenue_sharing_enabled', 'default_reseller_share',
            'default_sub_reseller_share', 'default_ktl_share_with_sub',
            'default_reseller_share_with_sub', 'api_version',
            'is_active', 'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating organizations"""

    class Meta:
        model = Organization
        fields = [
            'name', 'code', 'org_type', 'email', 'phone', 'mobile',
            'website', 'address', 'city', 'postal_code', 'country',
            'trade_license', 'tin_number', 'registration_number',
            'logo_img', 'dark_logo_img', 'lite_logo_img', 'banner_img',
            'og_image', 'favicon', 'currency', 'currency_symbol',
            'seo_title', 'seo_description', 'seo_keywords', 'meta_description',
            'revenue_sharing_enabled', 'default_reseller_share',
            'default_sub_reseller_share', 'default_ktl_share_with_sub',
            'default_reseller_share_with_sub', 'api_version'
        ]

    def validate_code(self, value):
        """Ensure organization code is unique"""
        if Organization.objects.filter(code__iexact=value).exists():
            raise serializers.ValidationError("Organization with this code already exists.")
        return value.upper()

    def validate_email(self, value):
        """Ensure organization email is unique"""
        if Organization.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Organization with this email already exists.")
        return value


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating organizations"""

    class Meta:
        model = Organization
        fields = [
            'name', 'org_type', 'email', 'phone', 'mobile', 'website',
            'address', 'city', 'postal_code', 'country',
            'trade_license', 'tin_number', 'registration_number',
            'logo_img', 'dark_logo_img', 'lite_logo_img', 'banner_img',
            'og_image', 'favicon', 'currency', 'currency_symbol',
            'seo_title', 'seo_description', 'seo_keywords', 'meta_description',
            'revenue_sharing_enabled', 'default_reseller_share',
            'default_sub_reseller_share', 'default_ktl_share_with_sub',
            'default_reseller_share_with_sub', 'api_version',
            'is_active', 'is_verified'
        ]

    def validate_email(self, value):
        """Ensure organization email is unique (excluding current instance)"""
        instance = self.instance
        if instance and Organization.objects.filter(email__iexact=value).exclude(id=instance.id).exists():
            raise serializers.ValidationError("Organization with this email already exists.")
        elif not instance and Organization.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Organization with this email already exists.")
        return value


class BillingSettingsSerializer(serializers.ModelSerializer):
    """Serializer for BillingSettings model"""

    class Meta:
        model = BillingSettings
        fields = [
            'id', 'max_manual_grace_days', 'disable_expiry',
            'default_grace_days', 'jump_billing', 'default_grace_hours',
            'max_inactive_days', 'delete_permanent_disable_secret_from_mikrotik',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SyncSettingsSerializer(serializers.ModelSerializer):
    """Serializer for SyncSettings model"""

    class Meta:
        model = SyncSettings
        fields = [
            'id', 'sync_area_to_mikrotik', 'sync_address_to_mikrotik',
            'sync_customer_mobile_to_mikrotik', 'last_sync_status',
            'sync_frequency', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrganizationStatsSerializer(serializers.Serializer):
    """Serializer for organization statistics"""

    total_organizations = serializers.IntegerField()
    active_organizations = serializers.IntegerField()
    verified_organizations = serializers.IntegerField()
    organizations_by_type = serializers.DictField()


class OrganizationProfileSerializer(serializers.Serializer):
    """Serializer for organization profile data"""

    id = serializers.UUIDField()
    name = serializers.CharField()
    code = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    is_active = serializers.BooleanField()
    is_verified = serializers.BooleanField()