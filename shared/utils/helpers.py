"""
Shared utility helper functions
"""
import random
import string
import re
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging

logger = logging.getLogger(__name__)


def generate_random_string(length: int = 8, include_digits: bool = True, include_special: bool = False) -> str:
    """
    Generate random string
    
    Args:
        length: Length of string
        include_digits: Include digits in string
        include_special: Include special characters
    
    Returns:
        Random string
    """
    characters = string.ascii_letters
    
    if include_digits:
        characters += string.digits
    
    if include_special:
        characters += '!@#$%^&*'
    
    return ''.join(random.choice(characters) for _ in range(length))


def format_phone_number(phone: str, country_code: str = '+880') -> str:
    """
    Format phone number with country code
    
    Args:
        phone: Phone number
        country_code: Country code (default: Bangladesh)
    
    Returns:
        Formatted phone number
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Remove leading zeros
    digits = digits.lstrip('0')
    
    # Add country code if not present
    if not digits.startswith(country_code.replace('+', '')):
        digits = f"{country_code.replace('+', '')}{digits}"
    
    return f"+{digits}"


def calculate_date_difference(start_date: date, end_date: date) -> Dict[str, int]:
    """
    Calculate difference between two dates
    
    Args:
        start_date: Start date
        end_date: End date
    
    Returns:
        Dictionary with years, months, days
    """
    delta = end_date - start_date
    
    years = delta.days // 365
    remaining_days = delta.days % 365
    months = remaining_days // 30
    days = remaining_days % 30
    
    return {
        'years': years,
        'months': months,
        'days': days,
        'total_days': delta.days
    }


def paginate_queryset(queryset, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """
    Paginate Django queryset
    
    Args:
        queryset: Django queryset
        page: Page number
        page_size: Items per page
    
    Returns:
        Dictionary with pagination data
    """
    paginator = Paginator(queryset, page_size)
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    return {
        'results': list(page_obj.object_list),
        'pagination': {
            'page': page_obj.number,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        }
    }


def format_currency(amount: float, currency: str = 'BDT', symbol: str = '৳') -> str:
    """
    Format currency amount
    
    Args:
        amount: Amount to format
        currency: Currency code
        symbol: Currency symbol
    
    Returns:
        Formatted currency string
    """
    return f"{symbol} {amount:,.2f}"


def clean_dict(data: Dict) -> Dict:
    """
    Remove None and empty string values from dictionary
    
    Args:
        data: Dictionary to clean
    
    Returns:
        Cleaned dictionary
    """
    return {k: v for k, v in data.items() if v is not None and v != ''}


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Split list into chunks
    
    Args:
        lst: List to split
        chunk_size: Size of each chunk
    
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to integer
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Integer value
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Float value
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
    
    