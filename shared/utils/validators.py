"""
Shared validation utilities
"""
import re
from typing import Optional
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError as DjangoValidationError
import phonenumbers


def validate_phone_number(phone: str, country_code: str = 'BD') -> bool:
    """
    Validate phone number
    
    Args:
        phone: Phone number to validate
        country_code: Country code (ISO 3166-1 alpha-2)
    
    Returns:
        True if valid, False otherwise
    """
    try:
        parsed = phonenumbers.parse(phone, country_code)
        return phonenumbers.is_valid_number(parsed)
    except phonenumbers.NumberParseException:
        return False


def validate_email(email: str) -> bool:
    """
    Validate email address
    
    Args:
        email: Email to validate
    
    Returns:
        True if valid, False otherwise
    """
    validator = EmailValidator()
    try:
        validator(email)
        return True
    except DjangoValidationError:
        return False


def validate_url(url: str) -> bool:
    """
    Validate URL
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid, False otherwise
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return url_pattern.match(url) is not None


def validate_ip_address(ip: str) -> bool:
    """
    Validate IPv4 address
    
    Args:
        ip: IP address to validate
    
    Returns:
        True if valid, False otherwise
    """
    pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    
    if not pattern.match(ip):
        return False
    
    parts = ip.split('.')
    return all(0 <= int(part) <= 255 for part in parts)


def validate_mac_address(mac: str) -> bool:
    """
    Validate MAC address
    
    Args:
        mac: MAC address to validate
    
    Returns:
        True if valid, False otherwise
    """
    pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return pattern.match(mac) is not None


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength
    
    Args:
        password: Password to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, None


def validate_bangladeshi_nid(nid: str) -> bool:
    """
    Validate Bangladeshi National ID (NID)
    
    Args:
        nid: NID to validate
    
    Returns:
        True if valid, False otherwise
    """
    # NID can be 10, 13, or 17 digits
    pattern = re.compile(r'^(\d{10}|\d{13}|\d{17})$')
    return pattern.match(nid) is not None


def validate_bangladeshi_mobile(mobile: str) -> bool:
    """
    Validate Bangladeshi mobile number
    
    Args:
        mobile: Mobile number to validate
    
    Returns:
        True if valid, False otherwise
    """
    # Remove country code and spaces
    mobile = re.sub(r'[\s\+]', '', mobile)
    
    # Remove leading 880 if present
    if mobile.startswith('880'):
        mobile = mobile[3:]
    
    # Remove leading 0 if present
    mobile = mobile.lstrip('0')
    
    # Valid BD mobile starts with 13, 14, 15, 16, 17, 18, 19
    pattern = re.compile(r'^1[3-9]\d{8}$')
    return pattern.match(mobile) is not None