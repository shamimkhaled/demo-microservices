"""
Shared middleware for authentication and organization context
"""
import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.utils.functional import SimpleLazyObject
import logging
import uuid

logger = logging.getLogger(__name__)


def get_user_from_token(request):
    """
    Extract user from JWT token in request headers
    This is a simplified version - in production, you'd want to:
    1. Validate token signature
    2. Check token expiration
    3. Fetch user from database or cache
    """
    
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header.startswith('Bearer '):
        return AnonymousUser()
    
    token = auth_header.split(' ')[1]
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        
        # In production, fetch user from database using payload['user_id']
        # For now, we'll create a mock user object from payload
        class MockUser:
            def __init__(self, payload):
                # Convert string IDs to UUID objects
                self.id = uuid.UUID(payload.get('user_id')) if payload.get('user_id') else None
                self.organization_id = uuid.UUID(payload.get('organization_id')) if payload.get('organization_id') else None
                self.is_authenticated = True
                self.is_active = True
                self.is_super_admin = payload.get('is_super_admin', False)
                self.login_id = payload.get('login_id')
                self.email = payload.get('email')
                self.name = payload.get('name')
            
            def has_perm(self, perm):
                return self.is_super_admin
            
            def has_perms(self, perm_list):
                return self.is_super_admin
                
            def __str__(self):
                return self.login_id or str(self.id)
        
        return MockUser(payload)
    
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return AnonymousUser()
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return AnonymousUser()
    except ValueError as e:
        logger.error(f"Invalid UUID in token: {e}")
        return AnonymousUser()
    except Exception as e:
        logger.error(f"Error decoding JWT token: {e}")
        return AnonymousUser()


class JWTAuthenticationMiddleware:
    """
    Middleware to authenticate users via JWT token
    Should be used after Django's AuthenticationMiddleware
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add user to request from JWT token
        request.user = SimpleLazyObject(lambda: get_user_from_token(request))
        
        response = self.get_response(request)
        return response


class OrganizationContextMiddleware:
    """
    Middleware to add organization context to request
    Adds organization_id from authenticated user
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add organization context
        if hasattr(request.user, 'organization_id'):
            request.organization_id = request.user.organization_id
        else:
            request.organization_id = None
        
        response = self.get_response(request)
        return response


class RequestLoggingMiddleware:
    """
    Middleware to log all API requests
    Useful for debugging and audit trail
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log request
        logger.info(
            f"Request: {request.method} {request.path} "
            f"User: {getattr(request.user, 'login_id', 'anonymous')} "
            f"Org: {getattr(request, 'organization_id', 'N/A')}"
        )
        
        response = self.get_response(request)
        
        # Log response
        logger.info(
            f"Response: {response.status_code} for "
            f"{request.method} {request.path}"
        )
        
        return response


class ErrorHandlingMiddleware:
    """
    Middleware for centralized error handling
    Catches exceptions and returns standardized error responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            logger.error(f"Unhandled exception: {e}", exc_info=True)
            
            from django.http import JsonResponse
            return JsonResponse({
                'success': False,
                'message': 'An unexpected error occurred',
                'error': str(e) if settings.DEBUG else 'Internal server error'
            }, status=500)