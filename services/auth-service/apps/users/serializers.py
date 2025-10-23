from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from apps.users.models import User, District, Thana, Department, Designation



class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ['id', 'name', 'name_bn', 'division', 'is_active']

class ThanaSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True)
    class Meta:
        model = Thana
        fields = ['id', 'name', 'name_bn', 'district', 'district_name', 'is_active']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'organization_id', 'is_active', 'created_at', 'updated_at']

class DesignationSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    class Meta:
        model = Designation
        fields = ['id', 'name', 'description', 'department', 'department_name', 'organization_id', 'is_active', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """User serializer for read operations"""
    
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'login_id', 'email', 'name', 'mobile',
            'organization_id', 'employee_id', 'date_of_joining',
            'address', 'district_id', 'thana_id', 'postal_code',
            'is_active', 'is_staff', 'is_super_admin',
            'is_email_verified', 'is_phone_verified',
            'profile_photo', 'language_preference', 'timezone',
            'roles', 'permissions', 'last_login', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_login', 'created_at', 'updated_at']
    
    def get_roles(self, obj):
        """Get user roles"""
        return [
            {
                'id': str(role.id),
                'name': role.name,
                'display_name': role.display_name
            }
            for role in obj.groups.all()
        ]
    
    def get_permissions(self, obj):
        """Get user permissions"""
        perms = set()
        for group in obj.groups.all():
            perms.update(group.permissions.values_list('codename', flat=True))
        return list(perms)


class UserCreateSerializer(serializers.ModelSerializer):
    """User creation serializer - ROLE-FIRST APPROACH"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    role_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=True,
        help_text="REQUIRED: List of role UUIDs - User MUST have at least one role"
    )
    
    class Meta:
        model = User
        fields = [
            'login_id', 'email', 'password', 'password_confirm',
            'name', 'mobile', 'organization_id', 'employee_id',
            'date_of_joining', 'address', 'district', 'thana', 'department', 'designation',
            'postal_code', 'role_ids'
        ]
    
    def validate(self, attrs):
        """Validate user creation"""
        # Check password confirmation
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match"
            })
        
        # CRITICAL: Validate role_ids is not empty
        if not attrs.get('role_ids'):
            raise serializers.ValidationError({
                "role_ids": "User must have at least one role assigned"
            })
        
        # Validate organization exists (call Organization Service)
        from shared.utils.service_client import OrganizationServiceClient
        org_client = OrganizationServiceClient()
        if not org_client.organization_exists(attrs['organization_id']):
            raise serializers.ValidationError({
                "organization_id": "Organization does not exist"
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create user with role assignment"""
        from apps.roles.models import Role
        
        # Extract role_ids and passwords
        role_ids = validated_data.pop('role_ids')
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Create user
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Assign roles
        roles = Role.objects.filter(
            id__in=role_ids,
            organization_id=user.organization_id,
            is_active=True
        )
        
        if not roles.exists():
            user.delete()
            raise serializers.ValidationError({
                "role_ids": "No valid roles found for the given IDs"
            })
        
        user.groups.set(roles)
        
        # Create role assignment records
        from apps.roles.models import RoleAssignment
        for role in roles:
            RoleAssignment.objects.create(
                user=user,
                role=role,
                assigned_by_id=self.context['request'].user.id,
                assignment_reason="Initial role assignment during user creation"
            )
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """User update serializer"""
    
    class Meta:
        model = User
        fields = [
            'name', 'mobile', 'employee_id', 'date_of_joining',
            'address', 'district_id', 'thana_id', 'postal_code',
            'profile_photo', 'language_preference', 'timezone'
        ]


class PasswordChangeSerializer(serializers.Serializer):
    """Password change serializer"""
    
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password_confirm": "New passwords do not match"
            })
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
    

