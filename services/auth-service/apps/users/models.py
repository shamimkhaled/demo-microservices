import uuid
import re
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from phonenumber_field.modelfields import PhoneNumberField




class District(models.Model):
    """
    Bangladesh Districts (64 total). UUID PK for consistency.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)  # e.g., "Dhaka"
    name_bn = models.CharField(max_length=100, blank=True)  # Bengali name
    division = models.CharField(max_length=50)  # e.g., "Dhaka Division"
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'districts'
        verbose_name = 'District'
        verbose_name_plural = 'Districts'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Thana(models.Model):
    """
    Upazilas/Thanas (495 total), grouped by district.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)  # e.g., "Sadar Upazila"
    name_bn = models.CharField(max_length=100, blank=True)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='thanas')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'thanas'
        verbose_name = 'Thana/Upazila'
        verbose_name_plural = 'Thanas/Upazilas'
        unique_together = ['name', 'district']  # Prevent duplicates per district
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.district.name})"


class Department(models.Model):
    """
    Dynamic departments (e.g., IT, Billing). Admins can add/edit.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)  # e.g., "Billing"
    description = models.TextField(blank=True)
    organization_id = models.UUIDField(db_index=True)  # Scoped to org
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'departments'
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Designation(models.Model):
    """
    Dynamic designations (e.g., Manager, Technician). Can be tied to department if needed.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)  # e.g., "Billing Manager"
    description = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='designations')

    organization_id = models.UUIDField(db_index=True)  # Scoped to org
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'designations'
        verbose_name = 'Designation'
        verbose_name_plural = 'Designations'
        ordering = ['name']
    
    def __str__(self):
        return self.name



def validate_login_id(value):
    """Validate login_id format: alphanumeric, @, _, and - only"""
    if not re.match(r'^[a-zA-Z0-9@_-]+$', value):
        raise ValidationError(
            'Login ID can only contain letters, numbers, @, _, and - characters.'
        )


class UserManager(BaseUserManager):
    """Custom user manager"""
    
    def create_user(self, login_id, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        if not login_id:
            raise ValueError('Login ID is required')
        
        email = self.normalize_email(email)
        extra_fields.setdefault('username', login_id)
        
        user = self.model(login_id=login_id, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, login_id, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_super_admin', True)
        # Set a default organization_id for superuser
        extra_fields.setdefault('organization_id', uuid.uuid4())
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(login_id, email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model with role-based access control.
    NO user_type field - roles drive everything.
    """
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    login_id = models.CharField(
        max_length=150, 
        unique=True, 
        validators=[validate_login_id],
        db_index=True,
        help_text='Login ID: alphanumeric, @, _, - only'
    )
    email = models.EmailField(unique=True, db_index=True)
    mobile = PhoneNumberField(blank=True, null=True)
    
    # Organization (Tenant) - Store as UUID to avoid cross-service FK
    organization_id = models.UUIDField(
        help_text='Organization UUID from Organization Service',
        db_index=True
    )
    
    # Profile
    name = models.CharField(max_length=255)
    profile_photo = models.ImageField(upload_to='users/profile_photos/', blank=True, null=True)
    
    # Employment details
    employee_id = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    date_of_joining = models.DateField(blank=True, null=True)
    
    # Contact & Address
    address = models.TextField(blank=True, null=True)

    district = models.ForeignKey(
        'users.District',  # Adjust app name if separate
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    thana = models.ForeignKey(
        'users.Thana',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    
    # Add dynamic employment fields
    department = models.ForeignKey(
        'users.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    designation = models.ForeignKey(
        'users.Designation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Status flags
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_super_admin = models.BooleanField(default=False, db_index=True)
    
    # Security
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    
    # Token management
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    token_created_at = models.DateTimeField(blank=True, null=True)
    token_expires_at = models.DateTimeField(blank=True, null=True)
    remember_me = models.BooleanField(default=False)
    
    # Preferences
    language_preference = models.CharField(
        max_length=10, 
        choices=[('en', 'English'), ('bn', 'Bengali')],
        default='en'
    )
    timezone = models.CharField(max_length=50, default='Asia/Dhaka')

      # Additional Information
    remarks = models.TextField(blank=True, null=True)

    # Override the groups and user_permissions fields with custom related_names
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set'
    )
    
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set'
    )
    
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Manager
    objects = UserManager()
    
    # Auth fields
    USERNAME_FIELD = 'login_id'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['login_id']),
            models.Index(fields=['email']),
            models.Index(fields=['organization_id', 'is_active']),
            models.Index(fields=['is_super_admin']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.login_id})"
    
    def save(self, *args, **kwargs):
        # Ensure username is set to login_id
        if not self.username:
            self.username = self.login_id
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        return self.name
    
    def get_roles(self):
        """Get all active roles for this user"""
        return self.groups.all()
    
    def has_role(self, role_name):
        """Check if user has a specific role"""
        return self.groups.filter(name=role_name).exists()
    
    def is_token_valid(self):
        """Check if current token is valid"""
        from django.utils import timezone
        if not self.access_token or not self.token_expires_at:
            return False
        return timezone.now() < self.token_expires_at
    

