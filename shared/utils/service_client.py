"""
Service clients for inter-service communication
These clients handle HTTP requests between microservices
"""
import requests
import logging
from django.conf import settings
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)


class BaseServiceClient:
    """
    Base class for service-to-service HTTP communication
    """
    
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Get default headers for requests"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        return headers
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to service
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (e.g., '/users/')
            data: Request body data
            params: Query parameters
            token: JWT token for authentication
        
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(token)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {'data': response.text}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Service request failed: {method} {url} - {e}")
            raise ServiceCommunicationError(f"Failed to communicate with service: {e}")
    
    def get(self, endpoint: str, params: Optional[Dict] = None, token: Optional[str] = None):
        """Make GET request"""
        return self._make_request('GET', endpoint, params=params, token=token)
    
    def post(self, endpoint: str, data: Dict, token: Optional[str] = None):
        """Make POST request"""
        return self._make_request('POST', endpoint, data=data, token=token)
    
    def put(self, endpoint: str, data: Dict, token: Optional[str] = None):
        """Make PUT request"""
        return self._make_request('PUT', endpoint, data=data, token=token)
    
    def patch(self, endpoint: str, data: Dict, token: Optional[str] = None):
        """Make PATCH request"""
        return self._make_request('PATCH', endpoint, data=data, token=token)
    
    def delete(self, endpoint: str, token: Optional[str] = None):
        """Make DELETE request"""
        return self._make_request('DELETE', endpoint, token=token)


class OrganizationServiceClient(BaseServiceClient):
    """
    Client for Organization Service
    Handles all organization-related inter-service calls
    """
    
    def __init__(self):
        org_service_url = getattr(
            settings,
            'ORG_SERVICE_URL',
            'http://organization-service:8002'
        )
        super().__init__(base_url=f"{org_service_url}/api/v1")
    
    def organization_exists(self, organization_id: str) -> bool:
        """
        Check if organization exists and is active
        
        Args:
            organization_id: UUID of organization
        
        Returns:
            True if organization exists and is active, False otherwise
        """
        try:
            response = self.get(f'/organizations/{organization_id}/exists/')
            return response.get('exists', False)
        except Exception as e:
            logger.error(f"Failed to check organization existence: {e}")
            return False
    
    def get_organization(self, organization_id: str, token: Optional[str] = None) -> Optional[Dict]:
        """
        Get organization details
        
        Args:
            organization_id: UUID of organization
            token: JWT token for authentication
        
        Returns:
            Organization data or None
        """
        try:
            response = self.get(f'/organizations/{organization_id}/', token=token)
            return response.get('data') if response.get('success') else None
        except Exception as e:
            logger.error(f"Failed to get organization: {e}")
            return None
    
    def get_billing_settings(self, organization_id: str, token: Optional[str] = None) -> Optional[Dict]:
        """Get billing settings for organization"""
        try:
            response = self.get(
                f'/organizations/{organization_id}/billing-settings/',
                token=token
            )
            return response.get('data') if response.get('success') else None
        except Exception as e:
            logger.error(f"Failed to get billing settings: {e}")
            return None
    
    def get_sync_settings(self, organization_id: str, token: Optional[str] = None) -> Optional[Dict]:
        """Get sync settings for organization"""
        try:
            response = self.get(
                f'/organizations/{organization_id}/sync-settings/',
                token=token
            )
            return response.get('data') if response.get('success') else None
        except Exception as e:
            logger.error(f"Failed to get sync settings: {e}")
            return None
    
    def generate_customer_code(self, organization_id: str, token: Optional[str] = None) -> Optional[str]:
        """
        Generate unique customer code for organization
        
        Args:
            organization_id: UUID of organization
            token: JWT token for authentication
        
        Returns:
            Generated customer code or None
        """
        try:
            response = self.post(
                '/organizations/generate-customer-code/',
                data={'organization_id': organization_id},
                token=token
            )
            return response.get('customer_code') if response.get('success') else None
        except Exception as e:
            logger.error(f"Failed to generate customer code: {e}")
            return None


class AuthServiceClient(BaseServiceClient):
    """
    Client for Auth Service
    Handles all authentication and user-related inter-service calls
    """
    
    def __init__(self):
        # ✅ CRITICAL FIX: Changed port from 8001 to 8000
        auth_service_url = getattr(
            settings,
            'AUTH_SERVICE_URL',
            'http://auth-service:8000'  # ✅ Correct port (was 8001)
        )
        super().__init__(base_url=f"{auth_service_url}/api/v1")
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify JWT token and get user info
        
        Args:
            token: JWT token
        
        Returns:
            User data or None
        """
        try:
            response = self.post('/auth/verify/', data={}, token=token)
            return response.get('data', {}).get('user') if response.get('success') else None
        except Exception as e:
            logger.error(f"Failed to verify token: {e}")
            return None
    
    def get_user(self, user_id: str, token: str) -> Optional[Dict]:
        """
        Get user details by ID
        
        Args:
            user_id: UUID of user
            token: JWT token for authentication
        
        Returns:
            User data or None
        """
        try:
            response = self.get(f'/users/{user_id}/', token=token)
            return response.get('data') if response.get('success') else None
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
    
    def get_user_permissions(self, user_id: str, token: str) -> list:
        """
        Get user permissions
        
        Args:
            user_id: UUID of user
            token: JWT token for authentication
        
        Returns:
            List of permission codenames
        """
        try:
            response = self.get('/users/permissions/', token=token)
            if response.get('success'):
                return response.get('data', {}).get('permissions', [])
            return []
        except Exception as e:
            logger.error(f"Failed to get user permissions: {e}")
            return []
    
    def get_role(self, role_id: str, token: str) -> Optional[Dict]:
        """Get role details by ID"""
        try:
            response = self.get(f'/roles/{role_id}/', token=token)
            return response.get('data') if response.get('success') else None
        except Exception as e:
            logger.error(f"Failed to get role: {e}")
            return None


class ServiceCommunicationError(Exception):
    """Exception raised when service-to-service communication fails"""
    pass