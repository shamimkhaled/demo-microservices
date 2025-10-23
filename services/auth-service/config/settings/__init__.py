from .base import *

# Load environment-specific settings
import os
env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
else:
    from .development import *