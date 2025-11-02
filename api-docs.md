# API Documentation

This document provides detailed information about the endpoints available in the auth-service and organization-service, including complete request and response examples for testing.

## Table of Contents
- [Auth Service](#auth-service)
  - [Authentication](#authentication)
  - [User Management](#user-management)
- [Organization Service](#organization-service)
  - [Organization Management](#organization-management)
  - [Settings Management](#settings-management)
- [Testing Guide](#testing-guide)
  - [Postman Setup](#postman-setup)
  - [Example Test Cases](#example-test-cases)

## Auth Service

Base URL: `http://localhost:8000/api/v1`

### Authentication

#### Login
- **Endpoint**: `POST /auth/login/`
- **Access**: Public
- **Description**: Authenticate user and get JWT tokens
- **Request Body**:
  ```json
  {
    "login_id": "string",
    "password": "string",
    "remember_me": false
  }
  ```
- **Success Response** (200):
  ```json
  {
    "success": true,
    "message": "Login successful",
    "data": {
      "user": {
        "id": "uuid",
        "login_id": "string",
        "email": "string",
        "name": "string",
        "is_active": true,
        "is_staff": true,
        "is_super_admin": true,
        "organization_id": "uuid"
      },
      "tokens": {
        "access": "string",
        "refresh": "string",
        "token_type": "Bearer"
      },
      "remember_me": false
    }
  }
  ```
- **Note**: Rate limited to 5 requests per minute per IP

#### Refresh Token
- **Endpoint**: `POST /auth/token/refresh/`
- **Access**: Public
- **Description**: Get new access token using refresh token
- **Request Body**:
  ```json
  {
    "refresh_token": "string"
  }
  ```
- **Success Response** (200):
  ```json
  {
    "success": true,
    "message": "Token refreshed successfully",
    "data": {
      "access": "string",
      "token_type": "Bearer"
    }
  }
  ```

#### Logout
- **Endpoint**: `POST /auth/logout/`
- **Access**: Authenticated users
- **Description**: Logout and invalidate tokens
- **Request Body**:
  ```json
  {
    "refresh_token": "string",
    "logout_all_devices": false
  }
  ```
- **Success Response** (200):
  ```json
  {
    "success": true,
    "message": "Logout successful"
  }
  ```

#### Verify Token
- **Endpoint**: `POST /auth/token/verify/`
- **Access**: Authenticated users
- **Description**: Verify token validity and get user info
- **Success Response** (200):
  ```json
  {
    "success": true,
    "message": "Token is valid",
    "data": {
      "user": {
        "id": "uuid",
        "login_id": "string",
        "email": "string",
        // ... other user fields
      }
    }
  }
  ```

### User Management

#### List/Create Users
- **Endpoint**: `GET, POST /users/`
- **Access**: 
  - GET: All authenticated users
  - POST: Admin or Super Admin only
- **Query Parameters** (GET):
  - `organization_id`: Filter by organization
  - `is_active`: Filter by active status
  - `search`: Search in login_id, email, name, employee_id
  - `ordering`: Sort by login_id, email, created_at, last_login
- **Request Body** (POST):
  ```json
  {
    "login_id": "string",
    "email": "string",
    "password": "string",
    "name": "string",
    "role_ids": ["uuid"],
    "organization_id": "uuid",
    "employee_id": "string"
  }
  ```

#### User Details
- **Endpoint**: `GET, PUT, PATCH, DELETE /users/{id}/`
- **Access**:
  - GET: All authenticated users
  - PUT/PATCH/DELETE: Admin or Super Admin only
- **Path Parameters**:
  - `id`: User ID (UUID)
- **Request Body** (PUT/PATCH):
  ```json
  {
    "email": "string",
    "name": "string",
    "role_ids": ["uuid"],
    "is_active": true
  }
  ```

#### Change Password
- **Endpoint**: `POST /users/change-password/`
- **Access**: Authenticated users
- **Request Body**:
  ```json
  {
    "current_password": "string",
    "new_password": "string"
  }
  ```

#### User Profile
- **Endpoint**: `GET /users/profile/`
- **Access**: Authenticated users
- **Description**: Get current user's profile

#### User Permissions
- **Endpoint**: `GET /users/permissions/`
- **Access**: Authenticated users
- **Description**: Get current user's permissions and roles

## Organization Service

Base URL: `http://localhost:8001/api/v1`

### Organization Management

#### List/Create Organizations
- **Endpoint**: `GET, POST /organizations/`
- **Access**:
  - GET: All authenticated users
  - POST: Super Admin only
- **Query Parameters** (GET):
  - `is_active`: Filter by active status
  - `org_type`: Filter by organization type
  - `search`: Search in name, code, email, city
  - `ordering`: Sort by name, code, created_at, updated_at
- **Request Body** (POST):
  ```json
  {
    "name": "string",
    "code": "string",
    "org_type": "string",
    "email": "string",
    "phone": "string",
    "address": "string",
    "city": "string",
    "state": "string",
    "country": "string",
    "postal_code": "string"
  }
  ```

#### Organization Details
- **Endpoint**: `GET, PUT, PATCH, DELETE /organizations/{id}/`
- **Access**:
  - GET: Users of same organization or Super Admin
  - PUT/PATCH/DELETE: Organization Admin or Super Admin
- **Path Parameters**:
  - `id`: Organization ID (UUID)
- **Success Response** (200):
  ```json
  {
    "id": "uuid",
    "name": "string",
    "code": "string",
    "org_type": "string",
    "is_active": true,
    "is_verified": true,
    "billing_settings": {
      // billing settings fields
    },
    "sync_settings": {
      // sync settings fields
    }
  }
  ```

### Settings Management

#### Billing Settings
- **Endpoint**: `GET, PUT, PATCH /organizations/{organization_id}/billing/`
- **Access**: Organization Admin or Super Admin
- **Path Parameters**:
  - `organization_id`: Organization ID (UUID)

#### Sync Settings
- **Endpoint**: `GET, PUT, PATCH /organizations/{organization_id}/sync/`
- **Access**: Organization Admin or Super Admin
- **Path Parameters**:
  - `organization_id`: Organization ID (UUID)

#### Organization Existence Check
- **Endpoint**: `GET /organizations/{id}/exists/`
- **Access**: Public
- **Success Response** (200):
  ```json
  {
    "success": true,
    "exists": true,
    "organization": {
      "id": "uuid",
      "name": "string",
      "code": "string",
      "org_type": "string"
    }
  }
  ```

#### Organization Statistics
- **Endpoint**: `GET /organizations/stats/`
- **Access**: Super Admin only
- **Description**: Get organization statistics

#### Verify Organization
- **Endpoint**: `POST /organizations/{organization_id}/verify/`
- **Access**: Super Admin only
- **Description**: Verify an organization

#### Organization Profile
- **Endpoint**: `GET /organizations/profile/`
- **Access**: Authenticated users
- **Description**: Get organization profile for current user

## Authentication

All endpoints except those marked as "Public" require authentication using JWT Bearer token:

```http
Authorization: Bearer <access_token>
```

## Response Format

All endpoints follow a consistent response format:

```json
{
  "success": true|false,
  "message": "string",
  "data": {
    // Response data specific to the endpoint
  }
}
```

## Error Responses

Common error responses:

```json
{
  "success": false,
  "message": "Error message",
  "errors": {
    // Detailed error information
  }
}
```

HTTP Status Codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

## Testing Guide

### Postman Setup

1. Set up environment variables in Postman:
   ```
   BASE_URL_AUTH: http://localhost:8000/api/v1
   BASE_URL_ORG: http://localhost:8001/api/v1
   ACCESS_TOKEN: <your_jwt_token>
   ```

2. Add a request header for authenticated endpoints:
   ```
   Authorization: Bearer {{ACCESS_TOKEN}}
   ```

### Example Test Cases

#### 1. Authentication Flow

##### a. Login
```http
POST {{BASE_URL_AUTH}}/auth/login/
Content-Type: application/json

{
    "login_id": "admin123",
    "password": "your_password",
    "remember_me": true
}
```

Example Response:
```json
{
    "success": true,
    "message": "Login successful",
    "data": {
        "user": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "login_id": "admin123",
            "email": "admin@example.com",
            "name": "Admin User",
            "is_active": true,
            "is_staff": true,
            "is_super_admin": true,
            "organization_id": "550e8400-e29b-41d4-a716-446655440001"
        },
        "tokens": {
            "access": "eyJ0eXAiOiJKV1QiLCJhbG...",
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbG...",
            "token_type": "Bearer"
        }
    }
}
```

##### b. Create User
```http
POST {{BASE_URL_AUTH}}/users/
Content-Type: application/json

{
    "login_id": "newuser",
    "email": "newuser@example.com",
    "password": "StrongPass123!",
    "password_confirm": "StrongPass123!",
    "name": "New User",
    "mobile": "+1234567890",
    "organization_id": "550e8400-e29b-41d4-a716-446655440001",
    "employee_id": "EMP001",
    "date_of_joining": "2025-01-01",
    "address": "123 Main St",
    "postal_code": "12345",
    "role_ids": ["550e8400-e29b-41d4-a716-446655440002"]
}
```

Example Response:
```json
{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "login_id": "newuser",
        "email": "newuser@example.com",
        "name": "New User",
        "is_active": true,
        "roles": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "name": "staff",
                "display_name": "Staff Member"
            }
        ]
    }
}
```

#### 2. Organization Management

##### a. Create Organization
```http
POST {{BASE_URL_ORG}}/organizations/
Content-Type: application/json

{
    "name": "Test Organization",
    "code": "TEST-ORG",
    "org_type": "business",
    "email": "org@example.com",
    "phone": "+1234567890",
    "mobile": "+1234567891",
    "website": "https://example.com",
    "address": "456 Business Ave",
    "city": "Test City",
    "postal_code": "54321",
    "country": "Test Country",
    "trade_license": "TL123456",
    "tin_number": "TIN123456",
    "registration_number": "REG123456",
    "currency": "USD",
    "currency_symbol": "$"
}
```

Example Response:
```json
{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440004",
        "name": "Test Organization",
        "code": "TEST-ORG",
        "is_active": true,
        "is_verified": false,
        "created_at": "2025-10-27T12:00:00Z"
    }
}
```

##### b. Update Organization Settings
```http
PATCH {{BASE_URL_ORG}}/organizations/550e8400-e29b-41d4-a716-446655440004/billing/
Content-Type: application/json

{
    "max_manual_grace_days": 7,
    "default_grace_days": 3,
    "default_grace_hours": 72,
    "max_inactive_days": 30
}
```

Example Response:
```json
{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440005",
        "max_manual_grace_days": 7,
        "default_grace_days": 3,
        "default_grace_hours": 72,
        "max_inactive_days": 30,
        "updated_at": "2025-10-27T12:00:00Z"
    }
}
```

#### 3. Common Scenarios

1. **Complete User Management Flow:**
   - Create user with roles
   - Update user profile
   - Change user password
   - Get user permissions
   - Deactivate user

2. **Organization Setup Flow:**
   - Create organization
   - Configure billing settings
   - Configure sync settings
   - Verify organization
   - Add users to organization

3. **Authentication Flow:**
   - Login
   - Use access token
   - Refresh token when expired
   - Verify token
   - Logout
   - Logout from all devices

4. **Error Handling:**
   - Invalid credentials
   - Expired tokens
   - Missing permissions
   - Validation errors
   - Rate limiting