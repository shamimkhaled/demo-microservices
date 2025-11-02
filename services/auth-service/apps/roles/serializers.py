from rest_framework import serializers
from django.contrib.auth.models import Permission
from apps.roles.models import Role, RoleAssignment


class PermissionSerializer(serializers.ModelSerializer):
    """Permission serializer"""
    
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'content_type']


class RoleSerializer(serializers.ModelSerializer):
    """Role serializer with proper permissions handling"""
    
    # Read permissions as PermissionSerializer objects
    permissions = PermissionSerializer(many=True, read_only=True)
    
    # Write permission IDs as a list of integers
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    users_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'display_name', 'description',
            'organization_id', 'role_level', 'is_system_role',
            'is_active', 'can_assign_roles', 'max_assignments',
            'permissions', 'permission_ids', 'users_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'permissions', 'users_count']
    
    def get_users_count(self, obj):
        """Get count of users with this role"""
        # Count users in the role_assignments (active assignments)
        return obj.user_assignments.filter(is_active=True).count()
    
    def validate(self, attrs):
        """Validate role creation"""
        # Validate organization exists (only on create)
        if self.instance is None:  # Creating new role
            from shared.utils.service_client import OrganizationServiceClient
            org_client = OrganizationServiceClient()
            if not org_client.organization_exists(attrs.get('organization_id')):
                raise serializers.ValidationError({
                    "organization_id": "Organization does not exist"
                })
            
            # Check if role name already exists for this organization
            if Role.objects.filter(
                name=attrs['name'],
                organization_id=attrs['organization_id']
            ).exists():
                raise serializers.ValidationError({
                    "name": "Role with this name already exists in this organization"
                })
        
        return attrs
    
    def create(self, validated_data):
        """Create role with permissions"""
        permission_ids = validated_data.pop('permission_ids', [])
        
        # Set created_by
        validated_data['created_by_id'] = self.context['request'].user.id
        
        # Create the role
        role = Role.objects.create(**validated_data)
        
        # Assign permissions if provided
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids)
            role.permissions.set(permissions)
        
        return role
    
    def update(self, instance, validated_data):
        """Update role"""
        permission_ids = validated_data.pop('permission_ids', None)
        
        # Update role fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update permissions if provided
        if permission_ids is not None:
            permissions = Permission.objects.filter(id__in=permission_ids)
            instance.permissions.set(permissions)
        
        return instance


class RoleAssignmentSerializer(serializers.Serializer):
    """Role assignment serializer"""
    
    user_id = serializers.UUIDField()
    role_id = serializers.UUIDField()
    action = serializers.ChoiceField(choices=['assign', 'revoke'])
    reason = serializers.CharField(required=False, allow_blank=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Validate role assignment"""
        from apps.users.models import User
        
        # Validate user exists
        try:
            user = User.objects.get(id=attrs['user_id'])
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_id": "User not found"})
        
        # Validate role exists
        try:
            role = Role.objects.get(id=attrs['role_id'], is_active=True)
        except Role.DoesNotExist:
            raise serializers.ValidationError({"role_id": "Role not found or inactive"})
        
        # Validate same organization
        if user.organization_id != role.organization_id:
            raise serializers.ValidationError(
                "User and role must belong to the same organization"
            )
        
        attrs['user'] = user
        attrs['role'] = role
        return attrs
    
    def save(self):
        """Perform role assignment/revocation"""
        user = self.validated_data['user']
        role = self.validated_data['role']
        action = self.validated_data['action']
        
        if action == 'assign':
            role.assign_to_user(user)
            return {'action': 'assigned', 'user': user.id, 'role': role.id}
        else:
            role.remove_from_user(user)
            return {'action': 'revoked', 'user': user.id, 'role': role.id}



            