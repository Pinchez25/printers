from django.utils.functional import SimpleLazyObject
from django.core.exceptions import ImproperlyConfigured
from django.db import OperationalError
from django.conf import settings

def _get_company_config():
    """Helper function to get company config with error handling"""
    try:
        from gallery.models import CompanyConfig
    except ImportError:
        return None

    try:
        return CompanyConfig.get_instance()
    except (CompanyConfig.DoesNotExist, OperationalError, ImproperlyConfigured):
        return None

def company_config(request):
    """Context processor to make CompanyConfig and email settings available globally"""
    return {
        'config': SimpleLazyObject(func=_get_company_config),
        'admin_email': settings.EMAIL_HOST_USER,
    }
