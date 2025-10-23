# KTL Microservices: Tenancy & Authentication Guide

## Overview

This guide explains how the KTL microservices architecture implements multi-tenancy and authentication. The system consists of two main services:

1. **Auth Service** (Port 8000) - Handles user authentication, roles, and permissions
2. **Organization Service** (Port 8002) - Manages organizations/tenants and their settings

## Architecture Overview

### Multi-Tenancy Implementation

The system uses **organization-based multi-tenancy** where each organization (ISP/business) is a separate tenant. Key concepts:

- **Organization**: The tenant entity (ISP, corporate client, etc.)
- **User**: Belongs to an organization via `organization_id`
- **Role**: Scoped to organizations (roles are organization-specific)
- **Permissions**: Django permissions assigned to roles

### Service Communication

Services communicate via HTTP REST APIs using service clients:
- `OrganizationServiceClient` - Auth service calls organization service
- `AuthServiceClient` - Organization service calls auth service

## Step-by-Step Setup and Usage

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd ktl-microservices

# Install dependencies
pip install -r services/auth-service/requirements.txt
pip install -r services/organization-service/requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 2. Database Setup

```bash
# Auth Service
cd services/auth-service
python manage.py makemigrations
python manage.py migrate

# Organization Service
cd ../organization-service
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Super Admin User

The super admin user has access to all organizations and can manage the entire system.

#### Method 1: Using Django Management Command
```bash
# In auth-service directory
cd services/auth-service
python manage.py createsuperuser
```

Follow the prompts:
- Username (leave blank to use login_id): [press enter]
- Login ID: admin@ktl.com
- Email: admin@ktl.com
- Password: [enter secure password]
- Password (again): [repeat password]

#### Method 2: Using Django Shell (For Automation)
```bash
cd services/auth-service
python manage.py shell
```

```python
from apps.users.models import User
from apps.organizations.models import Organization

# First, ensure KTL organization exists
org, created = Organization.objects.get_or_create(
    code='KTL',
    defaults={
        'name': 'Kloud Technologies Ltd',
        'email': 'admin@kloudtech.com',
        'phone': '+8801712345678',
        'address': '123 Tech Street, Dhaka',
        'city': 'Dhaka',
        'org_type': 'isp'
    }
)

# Create super admin user
super_admin = User.objects.create_superuser(
    login_id='admin@ktl.com',
    email='admin@ktl.com',
    password='securepassword123',
    name='System Administrator',
    organization_id=str(org.id)
)

print(f"Super admin created: {super_admin.login_id}")
print(f"Organization: {org.name} ({org.code})")
```

#### Method 3: Using API (After Services are Running)

**POST** `http://localhost:8000/api/v1/users/`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "login_id": "admin@ktl.com",
  "email": "admin@ktl.com",
  "name": "System Administrator",
  "password": "securepassword123",
  "organization_id": "your-org-uuid-here",
  "is_super_admin": true
}
```

**Note:** This method requires an existing admin user or direct database access to set the `is_super_admin` flag.

#### Super Admin Capabilities:
- Access to all organizations
- Create/manage organizations
- Create/manage users across all organizations
- Assign roles to any user
- View system-wide statistics
- Configure organization settings
- Override organization-level restrictions

#### Verification:
After creating the super admin, test login:

**POST** `http://localhost:8000/api/v1/auth/login/`

**Request Body:**
```json
{
  "login_id": "admin@ktl.com",
  "password": "securepassword123"
}
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "is_super_admin": true,
      "organization_id": "org-uuid"
    },
    "tokens": {
      "access": "jwt-token-here",
      "refresh": "refresh-token-here"
    }
  }
}
```

### 4. Start Services

```bash
# Terminal 1 - Auth Service
cd services/auth-service
python manage.py runserver 8000

# Terminal 2 - Organization Service
cd services/organization-service
python manage.py runserver 8002
```

## API Endpoints and Usage

### Organization Service APIs

#### Create Organization
**POST** `http://localhost:8002/api/v1/organizations/`

**Request Body:**
```json
{
  "name": "Kloud Technologies Ltd",
  "code": "KTL",
  "org_type": "isp",
  "email": "admin@kloudtech.com",
  "phone": "+8801712345678",
  "address": "123 Tech Street, Dhaka",
  "city": "Dhaka",
  "postal_code": "1205",
  "country": "Bangladesh"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid-here",
    "name": "Kloud Technologies Ltd",
    "code": "KTL",
    "org_type": "isp",
    "email": "admin@kloudtech.com",
    "phone": "+8801712345678",
    "address": "123 Tech Street, Dhaka",
    "city": "Dhaka",
    "postal_code": "1205",
    "country": "Bangladesh",
    "is_active": true,
    "is_verified": false,
    "created_at": "2025-01-16T04:40:19.274Z",
    "updated_at": "2025-01-16T04:40:19.274Z"
  }
}
```

#### List Organizations
**GET** `http://localhost:8002/api/v1/organizations/`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-here",
      "name": "Kloud Technologies Ltd",
      "code": "KTL",
      "org_type": "isp",
      "email": "admin@kloudtech.com",
      "is_active": true,
      "is_verified": false
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_pages": 1,
    "total_count": 1
  }
}
```

#### Get Organization Details
**GET** `http://localhost:8002/api/v1/organizations/{organization_id}/`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid-here",
    "name": "Kloud Technologies Ltd",
    "code": "KTL",
    "billing_settings": {
      "id": "uuid",
      "max_manual_grace_days": 9,
      "disable_expiry": false,
      "default_grace_days": 1,
      "jump_billing": true
    },
    "sync_settings": {
      "id": "uuid",
      "sync_area_to_mikrotik": false,
      "sync_address_to_mikrotik": false,
      "sync_customer_mobile_to_mikrotik": false
    }
  }
}
```

### Auth Service APIs

#### User Registration/Login

**POST** `http://localhost:8000/api/v1/auth/login/`

**Request Body:**
```json
{
  "login_id": "admin@ktl.com",
  "password": "securepassword123",
  "remember_me": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": "uuid-here",
      "login_id": "admin@ktl.com",
      "email": "admin@ktl.com",
      "name": "Admin User",
      "organization_id": "org-uuid-here",
      "is_active": true,
      "is_super_admin": true
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "token_type": "Bearer"
    },
    "remember_me": false
  }
}
```

#### Create User (Admin Only)
**POST** `http://localhost:8000/api/v1/users/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "login_id": "john.doe@ktl.com",
  "email": "john.doe@ktl.com",
  "name": "John Doe",
  "password": "securepass123",
  "organization_id": "org-uuid-here",
  "department": "IT",
  "designation": "System Administrator",
  "role_ids": ["role-uuid-here"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "user-uuid-here",
    "login_id": "john.doe@ktl.com",
    "email": "john.doe@ktl.com",
    "name": "John Doe",
    "organization_id": "org-uuid-here",
    "department": "IT",
    "designation": "System Administrator",
    "is_active": true,
    "created_at": "2025-01-16T04:40:19.274Z"
  }
}
```

#### Create Role
**POST** `http://localhost:8000/api/v1/roles/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "admin",
  "display_name": "Administrator",
  "description": "Full system access",
  "organization_id": "org-uuid-here",
  "role_level": 2,
  "permissions": ["add_user", "change_user", "delete_user", "view_user"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "role-uuid-here",
    "name": "admin",
    "display_name": "Administrator",
    "description": "Full system access",
    "organization_id": "org-uuid-here",
    "role_level": 2,
    "is_active": true,
    "created_at": "2025-01-16T04:40:19.274Z"
  }
}
```

#### Assign Role to User
**POST** `http://localhost:8000/api/v1/roles/assign/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "user_id": "user-uuid-here",
  "role_id": "role-uuid-here",
  "action": "assign"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Role assigned successfully"
}
```

## How Tenancy Works

### Organization Hierarchy and Customer Types

In this ISP billing system, each organization (tenant) can have multiple types of customers and resellers:

#### Customer Hierarchy Example (KTL Organization):

```
KTL Organization (Main ISP)
├── Direct Customers (ktl_direct)
│   ├── Individual home users
│   └── Small businesses
├── Corporate Customers (corporate)
│   ├── Large companies
│   └── Enterprise clients
├── Resellers (reseller)
│   ├── Authorized resellers who sell KTL services
│   └── Regional distributors
│       └── Sub-Resellers (sub_reseller)
│           ├── Agents under resellers
│           └── Local dealers
```

#### Revenue Sharing Model:
- **Direct Customers**: KTL gets 100% of revenue
- **Corporate Customers**: Revenue sharing based on contract terms
- **Resellers**: Get percentage (default 50%) of revenue from their customers
- **Sub-Resellers**: Revenue split between KTL, Reseller, and Sub-Reseller

### 1. Organization Creation
- Organizations are created in the Organization Service
- Each organization gets a unique UUID and code
- Organizations can be ISPs, corporates, or other business types
- Revenue sharing settings are configured per organization

### 2. User-Organization Relationship
- Users belong to organizations via `organization_id` field
- This field is a UUID reference to the organization in Organization Service
- Users can only access data from their own organization
- Different user roles: Super Admin, Admin, Reseller, Sub-Reseller, Customer

### 3. Role Scoping
- Roles are scoped to organizations
- Same role name can exist in different organizations
- Permissions are assigned at the role level
- Role hierarchy: Super Admin > Admin > Reseller > Sub-Reseller > Customer

### 4. Data Isolation
- Users can only see users from their organization
- Roles are filtered by organization
- All queries include organization-based filtering
- Customers under resellers are still part of the main organization but tagged by customer type

## Shared Folder Architecture

The `shared/` folder contains common utilities and middleware used across all microservices:

### Key Components:

#### 1. **shared/models/base.py**
- `TimeStampedModel`: Adds created_at/updated_at to all models
- `UUIDModel`: Provides UUID primary keys
- `SoftDeleteModel`: Enables soft deletion functionality
- `AuditModel`: Adds audit trails (created_by, updated_by)
- `BaseModel`: Combines UUID and timestamp (most commonly used)

#### 2. **shared/utils/**
- **service_client.py**: HTTP clients for inter-service communication
  - `OrganizationServiceClient`: Auth service calls organization APIs
  - `AuthServiceClient`: Organization service calls auth APIs
- **helpers.py**: Utility functions (pagination, formatting, validation)
- **validators.py**: Custom validation functions (phone, email, IP, etc.)

#### 3. **shared/middleware/**
- **authentication.py**:
  - `JWTAuthenticationMiddleware`: Validates JWT tokens
  - `OrganizationContextMiddleware`: Adds organization_id to requests
  - `RequestLoggingMiddleware`: Logs all API requests
  - `ErrorHandlingMiddleware`: Centralized error handling
- **permissions.py**: Custom permission classes for RBAC

#### 4. **shared/permissions.py**
- `IsSuperAdmin`: Super admin access
- `IsAdminOrSuperAdmin`: Admin or super admin access
- `IsSameOrganization`: Ensures user belongs to same organization as resource
- `HasPermission`: Check specific Django permissions
- `HasAnyRole`: Check if user has any of specified roles

### How Shared Folder Works:

1. **Cross-Service Consistency**: All services use same base models, utilities, and permissions
2. **Inter-Service Communication**: Service clients handle HTTP calls between microservices
3. **Authentication Flow**:
   - JWT tokens validated by middleware
   - Organization context added to all requests
   - Permissions checked based on user roles and organization
4. **Data Validation**: Shared validators ensure consistent data format across services
5. **Error Handling**: Centralized error responses and logging

### Service Communication Example:

```python
# Auth Service creating a user
from shared.utils.service_client import OrganizationServiceClient

org_client = OrganizationServiceClient()
if org_client.organization_exists(user.organization_id):
    # Organization exists, proceed with user creation
    user.save()
```

### Middleware Flow:

```
Request → JWTAuthenticationMiddleware → OrganizationContextMiddleware → View → Response
    ↓              ↓                              ↓
Validate JWT    Add org_id to request        Check permissions
```

## Revenue Sharing Configuration

Each organization has configurable revenue sharing:

```json
{
  "revenue_sharing_enabled": true,
  "default_reseller_share": 50.00,
  "default_sub_reseller_share": 45.00,
  "default_ktl_share_with_sub": 50.00,
  "default_reseller_share_with_sub": 5.00
}
```

### Commission Calculation Example:
For a sub-reseller customer paying $100:
- KTL gets: $50 (50%)
- Reseller gets: $5 (5%)
- Sub-Reseller gets: $45 (45%)

## Service Communication Flow

### User Creation Flow:
1. Admin creates organization in Organization Service
2. Admin creates user in Auth Service with `organization_id`
3. Auth Service validates organization exists via OrganizationServiceClient
4. User is created and linked to organization

### Authentication Flow:
1. User logs in via Auth Service
2. JWT token includes `organization_id` in payload
3. Subsequent requests include organization context
4. All data access is filtered by user's organization

## How Auth Service Gets Organization ID from Organization Service

The Auth Service uses the `OrganizationServiceClient` to communicate with the Organization Service and retrieve organization information. Here's how it works:

### 1. Organization Service Client Usage

```python
from shared.utils.service_client import OrganizationServiceClient

# Initialize client
org_client = OrganizationServiceClient()

# Check if organization exists
exists = org_client.organization_exists("org-uuid-here")
# Returns: True or False

# Get full organization details
org_data = org_client.get_organization("org-uuid-here", token="jwt-token")
# Returns: Organization dict or None
```

### 2. User Creation with Organization Validation

When creating a user, the Auth Service validates the organization exists:

```python
# In auth-service/apps/users/views.py - UserCreateSerializer
def create(self, validated_data):
    from shared.utils.service_client import OrganizationServiceClient

    organization_id = validated_data.get('organization_id')

    # Validate organization exists
    org_client = OrganizationServiceClient()
    if not org_client.organization_exists(organization_id):
        raise serializers.ValidationError("Organization does not exist")

    # Organization exists, create user
    user = User.objects.create_user(**validated_data)
    return user
```

### 3. API Endpoints for Organization Data Retrieval

#### Check Organization Existence
**GET** `http://localhost:8002/api/v1/organizations/{organization_id}/exists/`

**Response:**
```json
{
  "exists": true,
  "organization": {
    "id": "org-uuid",
    "name": "Kloud Technologies Ltd",
    "code": "KTL",
    "is_active": true
  }
}
```

#### Get Organization Details
**GET** `http://localhost:8002/api/v1/organizations/{organization_id}/`

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "org-uuid",
    "name": "Kloud Technologies Ltd",
    "code": "KTL",
    "email": "admin@kloudtech.com",
    "org_type": "isp",
    "is_active": true,
    "is_verified": true,
    "billing_settings": {...},
    "sync_settings": {...}
  }
}
```

### 4. Organization ID Validation in User Registration

```python
# Example: Creating a user with organization validation
POST http://localhost:8000/api/v1/users/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "login_id": "john.doe@company.com",
  "email": "john.doe@company.com",
  "name": "John Doe",
  "password": "securepass123",
  "organization_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Validation Process:**
1. Auth Service receives user creation request
2. Extracts `organization_id` from request
3. Calls Organization Service to verify organization exists
4. If organization exists → Create user
5. If organization doesn't exist → Return validation error

### 5. Service Client Configuration

The service client URLs are configured in environment variables:

```bash
# .env file
AUTH_SERVICE_URL=http://localhost:8000
ORG_SERVICE_URL=http://localhost:8002
```

**In settings:**
```python
# services/auth-service/config/settings/base.py
ORG_SERVICE_URL = config('ORG_SERVICE_URL', default='http://organization-service:8002')

# services/organization-service/config/settings/base.py
AUTH_SERVICE_URL = config('AUTH_SERVICE_URL', default='http://auth-service:8000')
```

### 6. Error Handling

```python
try:
    org_data = org_client.get_organization(org_id, token=user_token)
    if not org_data:
        return Response({
            'success': False,
            'message': 'Organization not found or access denied'
        }, status=404)
except ServiceCommunicationError as e:
    return Response({
        'success': False,
        'message': 'Unable to verify organization'
    }, status=503)
```

### 7. Caching Organization Data

For performance, organization data can be cached:

```python
from django.core.cache import cache

def get_cached_organization(org_id):
    cache_key = f"org:{org_id}"
    org_data = cache.get(cache_key)

    if not org_data:
        org_client = OrganizationServiceClient()
        org_data = org_client.get_organization(org_id)
        if org_data:
            cache.set(cache_key, org_data, timeout=300)  # 5 minutes

    return org_data
```

This ensures the Auth Service always has valid, up-to-date organization information while maintaining loose coupling between services.

## Postman Collection Setup

### Environment Variables:
```
base_auth_url: http://localhost:8000/api/v1
base_org_url: http://localhost:8002/api/v1
access_token: <set after login>
organization_id: <set after creating organization>
```

### Sample Postman Requests:

#### 1. Login
```
Method: POST
URL: {{base_auth_url}}/auth/login/
Body:
{
  "login_id": "admin@ktl.com",
  "password": "password"
}
```

#### 2. Create Organization
```
Method: POST
URL: {{base_org_url}}/organizations/
Body: <organization data>
```

#### 3. Create User
```
Method: POST
URL: {{base_auth_url}}/users/
Headers:
  Authorization: Bearer {{access_token}}
Body:
{
  "login_id": "user@example.com",
  "email": "user@example.com",
  "name": "Test User",
  "password": "password123",
  "organization_id": "{{organization_id}}"
}
```

## Security Features

### Authentication:
- JWT-based authentication
- Token refresh mechanism
- Account lockout after failed attempts
- Two-factor authentication support

### Authorization:
- Role-based access control (RBAC)
- Organization-scoped permissions
- Super admin bypass for all organizations

### Data Protection:
- Organization-based data isolation
- Soft deletes for users and organizations
- Audit trails for role assignments

## Common Issues and Solutions

### 1. Service Communication Errors
- Check service URLs in `.env`
- Ensure both services are running
- Verify network connectivity

### 2. Organization Not Found
- Verify organization UUID is correct
- Check if organization exists in Organization Service
- Ensure user has access to the organization

### 3. Permission Denied
- Check user's roles and permissions
- Verify organization membership
- Ensure super admin status if needed

## Managing Auth Service and Organization Service in Same Database

While this system is designed as separate microservices, you can run both services using the **same database** and **same Django admin panel** for development or simplified deployment. Here's how:

### 1. Shared Database Configuration

#### Update Environment Variables (.env)
```bash
# Use same database for both services
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_secure_pass

# Auth Service DB
AUTH_DB_NAME=ktl_microservices_db
AUTH_DB_HOST=localhost
AUTH_DB_PORT=5432

# Organization Service DB (same database)
ORG_DB_NAME=ktl_microservices_db
ORG_DB_HOST=localhost
ORG_DB_PORT=5432

# Or use SQLite for both (simpler for development)
# Comment out PostgreSQL settings above and use:
# DATABASE_URL=sqlite:///ktl_microservices.db
```

#### Database Settings for Both Services
```python
# In both services' settings/base.py, use same database:

# For SQLite (development):
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'ktl_microservices.db',  # Same file for both services
    }
}

# For PostgreSQL:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ktl_microservices_db',  # Same database
        'USER': config('POSTGRES_USER', default='postgres'),
        'PASSWORD': config('POSTGRES_PASSWORD', default='postgres'),
        'HOST': config('AUTH_DB_HOST', default='localhost'),  # Same host
        'PORT': config('AUTH_DB_PORT', default='5432'),
    }
}
```

### 2. Django Admin Panel Setup

#### Create Unified Admin Service
Create a new Django project that includes both apps:

```bash
# Create new admin project
mkdir admin-panel
cd admin-panel
django-admin startproject config .
python manage.py startapp admin_panel
```

#### Settings Configuration for Admin Panel
```python
# admin-panel/config/settings.py
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Add service paths to Python path
sys.path.append(str(BASE_DIR.parent / 'services' / 'auth-service'))
sys.path.append(str(BASE_DIR.parent / 'services' / 'organization-service'))
sys.path.append(str(BASE_DIR.parent / 'shared'))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'django_filters',

    # Service apps
    'apps.users',  # From auth-service
    'apps.roles',  # From auth-service
    'apps.organizations',  # From organization-service
]

# Use same database as services
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR.parent / 'services' / 'auth-service' / 'ktl_microservices.db',
    }
}

# Use same user model
AUTH_USER_MODEL = 'users.User'

# Admin URL
ROOT_URLCONF = 'config.urls'
```

#### URLs Configuration
```python
# admin-panel/config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/roles/', include('apps.roles.urls')),
    path('api/organizations/', include('apps.organizations.urls')),
]
```

### 3. Database Migration Strategy

#### Run Migrations in Order
```bash
# 1. Create shared database
cd admin-panel
python manage.py makemigrations

# 2. Run organization service migrations first
cd ../services/organization-service
python manage.py makemigrations organizations
python manage.py migrate

# 3. Run auth service migrations
cd ../auth-service
python manage.py makemigrations users roles authentication
python manage.py migrate

# 4. Update admin panel migrations if needed
cd ../../admin-panel
python manage.py migrate
```

### 4. Admin Panel Registration

#### Create admin.py for Both Services
```python
# admin-panel/admin_panel/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.users.models import User, Role, RoleAssignment
from apps.organizations.models import Organization, BillingSettings, SyncSettings

# Register Auth Service models
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('login_id', 'email', 'name', 'organization_id', 'is_active', 'is_super_admin')
    list_filter = ('is_active', 'is_super_admin', 'organization_id')
    search_fields = ('login_id', 'email', 'name')
    ordering = ('login_id',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'organization_id', 'role_level', 'is_active')
    list_filter = ('organization_id', 'is_active', 'role_level')
    search_fields = ('name', 'display_name')

@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_at', 'is_active')
    list_filter = ('is_active', 'assigned_at')
    search_fields = ('user__login_id', 'role__name')

# Register Organization Service models
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'org_type', 'email', 'is_active', 'is_verified')
    list_filter = ('org_type', 'is_active', 'is_verified')
    search_fields = ('name', 'code', 'email')

@admin.register(BillingSettings)
class BillingSettingsAdmin(admin.ModelAdmin):
    list_display = ('organization', 'max_manual_grace_days', 'default_grace_days')
    search_fields = ('organization__name',)

@admin.register(SyncSettings)
class SyncSettingsAdmin(admin.ModelAdmin):
    list_display = ('organization', 'sync_area_to_mikrotik', 'last_sync_status')
    list_filter = ('last_sync_status', 'sync_frequency')
    search_fields = ('organization__name',)
```

### 5. Running the Unified Setup

#### Start Admin Panel
```bash
cd admin-panel
python manage.py runserver 8003
```

#### Access Admin Panel
- URL: `http://localhost:8003/admin/`
- Login with superuser credentials
- Manage all models from both services in one interface

### 6. Service Communication in Shared Database

When using shared database, services can still communicate via HTTP, or you can create direct database access:

#### Option 1: Keep HTTP Communication
- Services still use `OrganizationServiceClient` and `AuthServiceClient`
- Maintains microservices architecture
- Services run on different ports

#### Option 2: Direct Database Access (Monolithic Mode)
```python
# In auth service, access organization data directly
from apps.organizations.models import Organization

def validate_organization(org_id):
    try:
        org = Organization.objects.get(id=org_id, is_active=True)
        return True
    except Organization.DoesNotExist:
        return False
```

### 7. Development Workflow

#### For Development with Shared Database:
1. **Run Admin Panel**: `python manage.py runserver 8003`
2. **Create Organizations**: Use admin panel to create organizations
3. **Create Users**: Use admin panel or API to create users
4. **Test APIs**: Run individual services on their ports (8000, 8002)

#### For Production Microservices:
1. **Separate Databases**: Each service has its own database
2. **Service Discovery**: Use proper service discovery
3. **API Gateway**: Route requests through API gateway
4. **Monitoring**: Implement proper monitoring and logging

### 8. Benefits of Shared Database Approach

- **Simpler Development**: Single database to manage
- **Unified Admin**: One admin panel for all models
- **Easier Testing**: Direct database access for testing
- **Faster Development**: No need for service communication during development

### 9. Migration to Microservices

When ready to move to full microservices:

1. **Create Separate Databases**
2. **Implement Service Clients** (already done)
3. **Add API Gateway**
4. **Implement Circuit Breakers**
5. **Add Service Monitoring**

This approach allows you to start with a simplified architecture and evolve to full microservices as needed.

## Development Notes

### Database Schema:
- Auth Service: Users, roles, permissions
- Organization Service: Organizations, settings
- Shared: Common utilities and permissions

### Key Models:
- **User**: Custom Django user with organization_id
- **Role**: Extended Django Group with organization scoping
- **Organization**: Tenant entity with business details
- **RoleAssignment**: Audit trail for role assignments

### Middleware:
- JWT authentication middleware
- Organization context middleware
- Request logging middleware

This architecture provides scalable multi-tenancy with proper data isolation and service separation.