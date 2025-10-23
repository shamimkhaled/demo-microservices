from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# Development-specific settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable caching in development
CACHES['default']['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'