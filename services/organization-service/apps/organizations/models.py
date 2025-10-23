import uuid
from django.db import models
from django.core.validators import URLValidator, EmailValidator, RegexValidator


class Organization(models.Model):
    """
    Main Organization/Tenant model
    Each organization is a separate ISP or business entity
    """

    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        app_label = 'organizations'
    name = models.CharField(max_length=255, unique=True,  default='Kloud Technologies Ltd')
    code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        default='KTL',
        validators=[
            RegexValidator(
                regex=r'^[A-Z0-9_-]+$',
                message='Organization code must contain only uppercase letters, numbers, underscores, and hyphens'
            )
        ],
        help_text='Unique organization code (e.g., KTL, DHKRES01)'
    )
    
    # Organization type
    ORG_TYPE_CHOICES = [
        ('isp', 'Internet Service Provider'),
        ('corporate', 'Corporate/Enterprise'),
        ('other', 'Other'),
        
    ]
    org_type = models.CharField(max_length=20, choices=ORG_TYPE_CHOICES, default='isp')
    
    # Contact information
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(max_length=20)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True, validators=[URLValidator()])
    
    # Address
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='Bangladesh')
    
    # Business details
    trade_license = models.CharField(max_length=100, blank=True, null=True)
    tin_number = models.CharField(max_length=50, blank=True, null=True)
    registration_number = models.CharField(max_length=100, blank=True, null=True)



    # Media Files
    logo_img = models.ImageField(
        upload_to='organization_logos/', 
        blank=True, 
        null=True,
        help_text='Main organization logo'
    )
    dark_logo_img = models.ImageField(
        upload_to='organization_logos/', 
        blank=True, 
        null=True,
        help_text='Dark theme logo'
    )
    lite_logo_img = models.ImageField(
        upload_to='organization_logos/', 
        blank=True, 
        null=True,
        help_text='Light theme logo'
    )
    banner_img = models.ImageField(
        upload_to='organization_banners/', 
        blank=True, 
        null=True,
        help_text='Banner image for portal'
    )
    og_image = models.ImageField(
        upload_to='organization_og_images/', 
        blank=True, 
        null=True,
        help_text='Open Graph image for social sharing'
    )
    favicon = models.ImageField(
        upload_to='organization_favicons/', 
        blank=True, 
        null=True,
        help_text='Website favicon'
    )


    # Currency & payment
    currency = models.CharField(max_length=10, default='BDT')
    currency_symbol = models.CharField(max_length=5, default='৳')
    
    # SEO fields for dynamic configuration
    seo_title = models.CharField(max_length=255, blank=True, null=True)
    seo_description = models.TextField(blank=True, null=True)
    seo_keywords = models.TextField(blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)


    # Revenue Sharing Configuration
    revenue_sharing_enabled = models.BooleanField(default=True)
    default_reseller_share = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)
    default_sub_reseller_share = models.DecimalField(max_digits=5, decimal_places=2, default=45.00)
    default_ktl_share_with_sub = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)
    default_reseller_share_with_sub = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    
    # API Version Handling (dynamic per organization)
    api_version = models.CharField(max_length=10, default='v1.0', help_text='Dynamic API version for this organization')
    
    
    # Status & control
    is_active = models.BooleanField(default=True, db_index=True)
    is_verified = models.BooleanField(default=False)
    
    # Hierarchy (for resellers/sub-resellers)
    # parent_organization = models.ForeignKey(
    #     'self',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name='child_organizations'
    # )
    
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by_id = models.UUIDField(blank=True, null=True)
    
    class Meta:
        db_table = 'organizations'
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['org_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"


    def calculate_commission_split(self, amount, customer_type, has_sub_reseller=False):
        """Calculate commission split based on customer type"""
        if customer_type == 'ktl_direct':
            return {'organization': amount}
        
        elif customer_type == 'reseller':
            if has_sub_reseller:
                org_share = amount * (self.default_ktl_share_with_sub / 100)
                reseller_share = amount * (self.default_reseller_share_with_sub / 100)
                sub_reseller_share = amount - org_share - reseller_share
                return {
                    'organization': org_share,
                    'reseller': reseller_share,
                    'sub_reseller': sub_reseller_share
                }
            else:
                reseller_share = amount * (self.default_reseller_share / 100)
                org_share = amount - reseller_share
                return {
                    'organization': org_share,
                    'reseller': reseller_share
                }
        
        # elif customer_type == 'corporate':
        #     commission = amount * (self.corporate_commission_rate / 100)
        #     org_share = amount - commission
        #     return {
        #         'organization': org_share,
        #         'commission': commission
        #     }
        
        return {'organization': amount}
    


class BillingSettings(models.Model):
    """
    Billing configuration for each organization
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        app_label = 'organizations'
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name='billing_settings'
    )
    
    
    max_manual_grace_days = models.IntegerField(
        default=9,
        help_text='Maximum manual grace days allowed'
    )
    disable_expiry = models.BooleanField(
        default=False,
        help_text='Disable automatic account expiry'
    )

    default_grace_days = models.IntegerField(
        default=1,
        help_text='Default grace period in days'
    )
    jump_billing = models.BooleanField(
        default=True,
        help_text='Enable jump billing for overdue accounts'
    )
   
    default_grace_hours = models.IntegerField(
        default=14,
        help_text='Default grace period in hours for hourly plans'
    )
    max_inactive_days = models.IntegerField(
        default=3,
        help_text='Maximum inactive days before account is disabled')
    
    delete_permanent_disable_secret_from_mikrotik = models.IntegerField(
        default=1,
        help_text='Days before permanent disable is triggered'
    )  # 0 for immediate delete

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_settings'
        verbose_name = 'Billing Setting'
        verbose_name_plural = 'Billing Settings'
    
    def __str__(self):
        return f"Billing Settings - {self.organization.name}"


class SyncSettings(models.Model):
    """
    Synchronization settings for RouterOS, OLT, etc.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        app_label = 'organizations'
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name='sync_settings'
    )
    
   # MikroTik Sync Settings
    sync_area_to_mikrotik = models.BooleanField(
        default=False,
        help_text='Sync area information to MikroTik'
    )
    sync_address_to_mikrotik = models.BooleanField(
        default=False,
        help_text='Sync customer address to MikroTik'
    )
    sync_customer_mobile_to_mikrotik = models.BooleanField(
        default=False,
        help_text='Sync customer mobile number to MikroTik'
    )
    # telegram_bot_token = models.CharField(max_length=255, blank=True, null=True)
    SYNC_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    )

    SYNC_FREQUENCY_CHOICES = (
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    )

    last_sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default='pending'
    )
    sync_frequency = models.CharField(
        max_length=20,
        choices=SYNC_FREQUENCY_CHOICES,
        default='daily'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sync_settings'
        verbose_name = 'Sync Setting'
        verbose_name_plural = 'Sync Settings'
    
    def __str__(self):
        return f"Sync Settings - {self.organization.name}"
    

    