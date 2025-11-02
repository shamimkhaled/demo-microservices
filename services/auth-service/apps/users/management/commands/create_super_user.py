from django.contrib.auth.management.commands.createsuperuser import Command as BaseCommand
from django.db import transaction
import sys


class Command(BaseCommand):
    """
    Custom createsuperuser with auto Super Admin role assignment
    
    Removed user.groups.add(role) - that's for Django Group, not Role
    Now only uses RoleAssignment for role tracking
    """
    
    help = 'Create a superuser with automatic Super Admin role assignment'
    
    def add_arguments(self, parser):
        """Add custom arguments"""
        super().add_arguments(parser)
        parser.add_argument(
            '--organization-id',
            type=str,
            help='UUID of organization (uses user\'s org if not provided)',
        )
        parser.add_argument(
            '--no-role',
            action='store_true',
            help='Skip role assignment (create user only)',
        )
    
    def handle(self, *args, **options):
        """Override handle to add role assignment"""
        try:
            from apps.users.models import User
            
            # Get the username/login_id from options
            username = options.get('username')
            
            # Call parent handle to create the user
            super().handle(*args, **options)
            
            # Retrieve the created user from database
            try:
                # Try to get by username (which is set to login_id in our model)
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # If that fails, get the most recent superuser
                user = User.objects.filter(is_superuser=True).latest('created_at')
            
            if user:
                # Ensure is_super_admin is set
                user.is_super_admin = True
                user.save(update_fields=['is_super_admin'])
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Set is_super_admin=True for {user.login_id}')
                )
                
                # Assign role if not --no-role
                if not options.get('no_role'):
                    self._assign_super_admin_role(user, options)
                else:
                    self.stdout.write(
                        self.style.WARNING('⊘ Skipping role assignment (--no-role flag used)')
                    )
            else:
                self.stdout.write(self.style.ERROR('✗ Could not retrieve created user'))
                sys.exit(1)
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def _assign_super_admin_role(self, user, options):
        """
        Assign Super Admin role to user
        
        Removed user.groups.add(role)
        Now only creates RoleAssignment records
        """
        from apps.roles.models import Role, RoleAssignment
        from django.contrib.auth.models import Permission
        
        try:
            # Get organization ID
            org_id = options.get('organization_id')
            if not org_id:
                org_id = str(user.organization_id)  # Use user's existing organization
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Using user\'s organization: {org_id}'
                    )
                )
            else:
                org_id = str(org_id)
            
            # Use atomic transaction
            with transaction.atomic():
                # CrRemoved useate or get Super Admin role for this organization
                role, created = Role.objects.get_or_create(
                    name='super_admin',
                    organization_id=org_id,
                    defaults={
                        'display_name': 'Super Administrator',
                        'description': 'System-wide administrator with full access',
                        'role_level': 1,
                        'is_system_role': True,
                        'is_active': True,
                        'can_assign_roles': True,
                        'created_by_id': user.id,
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✓ Created Super Admin role'))
                    
                    # Assign all permissions to the role 
                    all_permissions = Permission.objects.all()
                    role.permissions.set(all_permissions)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Assigned {all_permissions.count()} system permissions to role'
                        )
                    )
                else:
                    self.stdout.write(self.style.SUCCESS(f'✓ Using existing Super Admin role'))
                
              
                # This creates the RoleAssignment record
                existing_assignment = RoleAssignment.objects.filter(
                    user=user,
                    role=role,
                    is_active=True
                ).exists()
                
                if not existing_assignment:
                    # Use the model's assign_to_user method (now fixed)
                    role.assign_to_user(user)
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Assigned Super Admin role to {user.login_id}'
                        )
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS('✓ Role assignment record created')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⊘ User already has Super Admin role')
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Super admin user created successfully!')
                )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to assign role: {str(e)}')
            )
            import traceback
            traceback.print_exc()
            raise



